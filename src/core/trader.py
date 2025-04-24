import os
import warnings
import logging
import pandas as pd
import numpy as np
from datetime import datetime, timezone, timedelta
import time
import asyncio
from typing import Optional, Dict

from termcolor import colored

from src.api.capital import CapitalAPI
from src.api.capital_ws import CapitalWebSocket
from src.core.session import TradingSession
from src.core.positions import ActivePositions
from src.models.neural import LorentzianModel
from ..features.signals import SignalGenerator
from src.utils.config import TRADING_CONFIG, DEFAULT_PAIR, DEFAULT_TIMEFRAME, ENV_CONFIG
from src.utils.visualization import (
    print_header, print_market_data, print_bot_config,
    print_active_filters, print_positions, print_error, print_trading_signal, print_account_info, print_account_status
)

# Configure warnings and environment
warnings.filterwarnings('ignore')
for key, value in ENV_CONFIG.items():
    os.environ[key] = value

class LorentzianTrader:
    def __init__(self):
        # Trading parameters
        self.trading_pair = DEFAULT_PAIR
        self.timeframe = DEFAULT_TIMEFRAME
        self.config = TRADING_CONFIG.copy()
        
        # Initialize Capital.com API
        self.capital_api = CapitalAPI()
        if not self.capital_api.create_session():
            raise Exception("Could not create session with Capital.com")

        # Initialize WebSocket
        self.ws_client = CapitalWebSocket(
            self.capital_api.cst,
            self.capital_api.security_token
        )
        self.ws_client.set_quote_callback(self.handle_quote_update)
        
        # Historical data control
        self.last_historical_update = None
        self.historical_update_interval = 300  # 5 minutes
        self.historical_data = None
        
        # Initialize components
        self.model = LorentzianModel()
        self.signal_generator = SignalGenerator(
            self.model,
            timeframe=self.timeframe
        )
        self.session = TradingSession(self.capital_api.account_info['accountInfo']['balance'])
        
        # Initialize active positions with session ID
        self.active_positions = ActivePositions(self.session.session_id)
        
        self.last_report_save = time.time()
        self.report_save_interval = 300
        
    def handle_quote_update(self, quote_data: Dict):
        """Handle real-time quote updates from WebSocket"""
        try:
            # Throttle updates
            current_time = time.time()
            if hasattr(self, 'last_update_time') and current_time - self.last_update_time < 5:
                return
            self.last_update_time = current_time
            
            # Get current market price
            market_data = self.capital_api.get_price_history('BTCUSD', resolution='MINUTE_5', max_bars=1)
            
            if market_data and 'prices' in market_data and len(market_data['prices']) > 0:
                current_price = float(market_data['prices'][0]['closePrice']['bid'])
            else:
                current_price = float(quote_data['bid'])
            
            timestamp = datetime.fromtimestamp(quote_data['timestamp'] / 1000)
            
            # Update historical data
            if self.historical_data is not None and len(self.historical_data) > 0:
                self.historical_data.iloc[-1, self.historical_data.columns.get_loc('close')] = current_price
                
                # Display market information
                self._display_market_info(timestamp, current_price, quote_data)
                
                # Process trading logic
                self._process_trading_logic(timestamp, current_price)
                
        except Exception as e:
            print_error("Error processing quote update", e)

    def _display_market_info(self, timestamp: datetime, current_price: float, quote_data: Dict):
        """Display current market information"""
        # Clear screen and show header
        os.system('cls' if os.name == 'nt' else 'clear')
        print_header(timestamp, current_price)
        
        # Market data
        market_data = [
            ["Pair", self.trading_pair],
            ["Price", f"${current_price:.2f}"],
            ["Bid", f"${float(quote_data['bid']):.2f}"],
            ["Ask", f"${float(quote_data['ofr']):.2f}"],
            ["Spread", f"${float(quote_data['ofr']) - float(quote_data['bid']):.2f}"]
        ]
        print_market_data(market_data)

        # Account info
        account = self.capital_api.account_info
        account_info = [
            ["Account Balance", f"${account['accountInfo']['balance']:.2f}"],
            ["Account Equity", f"${account['accountInfo']['deposit']:.2f}"],
            ["Account Free Margin", f"${account['accountInfo']['available']:.2f}"],
            ["Account Margin", f"${account['accountInfo']['profitLoss']:.2f}"]
        ]
        print_account_info(account_info)
        
        # Bot configuration
        config_data = [
            ["Risk per Trade", f"{self.config['risk_per_trade']*100}%"],
            ["Take Profit", f"{self.config['take_profit']*100}%"],
            ["Stop Loss", f"{self.config['stop_loss']*100}%"],
            ["ADX Threshold", f"{self.config['adx_threshold']}"],
            ["Min Time Between Trades", f"{self.config['min_time_between_trades']} minutes"]
        ]
        print_bot_config(config_data)
        
        # Active filters
        filters_data = [
            ["Volatility Filter", "✅" if self.config['use_volatility_filter'] else "❌"],
            ["Regime Filter", "✅" if self.config['use_regime_filter'] else "❌"],
            ["ADX Filter", "✅" if self.config['use_adx_filter'] else "❌"],
            ["EMA Filter", "✅" if self.config['use_ema_filter'] else "❌"],
            ["SMA Filter", "✅" if self.config['use_sma_filter'] else "❌"]
        ]
        print_active_filters(filters_data)
        
        # Active positions
        positions = self.capital_api.get_positions()
        print_positions(positions)

        # Print trading signal
        print(colored("\n🔍 Looking for a signal...", "cyan"))
        #current_idx = len(self.historical_data) - 1
        #signal = self.signal_generator.get_trading_signal(self.historical_data, current_idx)
        #signal_type = 'LONG' if signal > 0 else 'SHORT'
        #stop_loss, take_profit = self.signal_generator.get_trade_levels(current_price, signal)
        #print_trading_signal(signal_type, current_price, stop_loss, take_profit)

    def _process_trading_logic(self, timestamp: datetime, current_price: float):
        """Process trading logic based on current market conditions"""
        try:
            # Check if it's time to save the report
            current_time = time.time()
            if current_time - self.last_report_save >= self.report_save_interval:
                self.session.save_report()
                self.last_report_save = current_time
                print("📊 Session report updated - Periodic save")
            
            # Update active positions
            closed_positions = self.active_positions.update_positions(current_price)
            
            # If positions were closed, save the report
            if closed_positions:
                self.session.save_report()
                print(f"📊 Session report updated - {len(closed_positions)} position(s) closed")
            
            # Check for new trading opportunities
            if self.session.can_open_new_position(timestamp):
                current_idx = len(self.historical_data) - 1
                signal = self.signal_generator.get_trading_signal(self.historical_data, current_idx)
                
                if signal != 0:
                    stop_loss, take_profit = self.signal_generator.get_trade_levels(current_price, signal)
                    size = self._calculate_position_size(current_price)
                    
                    if size > 0:
                        direction = 'BUY' if signal > 0 else 'SELL'
                        position = self.capital_api.create_position(
                            epic='BTCUSD',
                            direction=direction,
                            size=size,
                            stop_level=stop_loss,
                            profit_level=take_profit
                        )
                        
                        if position:
                            # Add position to tracking
                            position_data = {
                                'symbol': 'BTCUSD',
                                'signal': 1 if direction == 'BUY' else -1,
                                'entry_price': current_price,
                                'position_size': size,
                                'stop_loss': stop_loss,
                                'take_profit': take_profit,
                                'entry_time': timestamp
                            }
                            self.active_positions.add_position(position_data)
                            
                            self.session.last_trade_time = timestamp
                            print(f"🚀 Opened {direction} position with size {size} at {current_price}")
                            self.session.save_report()
                            print("📊 Session report updated - New position opened")
            
        except Exception as e:
            print_error("Error in trading logic", e)

    def _calculate_position_size(self, current_price: float) -> float:
        """Calculate position size based on risk parameters"""
        account_info = self.capital_api.account_info
        
        if not account_info:
            print_error("No account info available")
            return 0.0
            
        try:
            balance = float(account_info.get('accountInfo', {}).get('balance', 0))
            print(f"💰 Balance: ${balance:.2f}")
            if balance <= 0:
                print_error("Invalid account balance")
                return 0.0
                
            risk_amount = balance * self.config['risk_per_trade']
            stop_loss_pct = self.config['stop_loss']
            position_size = risk_amount / (current_price * stop_loss_pct)
            print(f"💰 Position Size: ${position_size:.2f}")
            print(f"💰 Risk Amount: ${risk_amount:.2f}")
            print(f"💰 Stop Loss Percentage: {stop_loss_pct:.2f}")
            print(f"💰 Current Price: ${current_price:.2f}")
            
            # Ensure position size limits
            position_size = max(0.01, min(0.5, position_size))
            
            return position_size
            
        except Exception as e:
            print_error("Error calculating position size", e)
            return 0.0

    def load_historical_data(self, start_date: Optional[str] = None, end_date: Optional[str] = None) -> bool:
        """Load historical price data"""
        try:
            print("\n📈 Loading Historical Data...")
            
            end_time = datetime.now(timezone.utc) if end_date is None else datetime.strptime(end_date, '%Y-%m-%dT%H:%M:%S').replace(tzinfo=timezone.utc)
            
            minutes_per_candle = self.get_timeframe_minutes()
            candles_per_request = 10
            minutes_per_request = minutes_per_candle * candles_per_request
            
            total_minutes_needed = minutes_per_candle * self.config['max_bars_back']
            start_time = end_time - timedelta(minutes=total_minutes_needed)
            
            if start_date is not None:
                start_time = datetime.strptime(start_date, '%Y-%m-%dT%H:%M:%S').replace(tzinfo=timezone.utc)
            
            all_candles = []
            current_start = end_time - timedelta(minutes=minutes_per_request)
            remaining_candles = self.config['max_bars_back']
            
            while remaining_candles > 0 and current_start >= start_time:
                from_date = current_start.strftime('%Y-%m-%dT%H:%M:%S')
                to_date = (current_start + timedelta(minutes=minutes_per_request)).strftime('%Y-%m-%dT%H:%M:%S')
                
                historical_data = self.capital_api.get_price_history(
                    epic="BTCUSD",
                    resolution=f"MINUTE_{minutes_per_candle}" if minutes_per_candle > 1 else "MINUTE",
                    from_date=from_date,
                    to_date=to_date,
                    max_bars=candles_per_request
                )
                
                if historical_data and 'prices' in historical_data:
                    batch_candles = historical_data['prices']
                    if batch_candles:
                        all_candles.extend(batch_candles)
                        remaining_candles -= len(batch_candles)
                
                current_start = current_start - timedelta(minutes=minutes_per_request)
                # Print pretty progress bar with library
                print(f"Loading historical data: {remaining_candles} candles remaining")

                time.sleep(0.5)  # Avoid rate limits
            
            if all_candles:
                df = pd.DataFrame([{
                    'timestamp': pd.to_datetime(candle['snapshotTime']),
                    'open': float(candle['openPrice']['bid']),
                    'high': float(candle['highPrice']['bid']),
                    'low': float(candle['lowPrice']['bid']),
                    'close': float(candle['closePrice']['bid']),
                    'volume': float(candle.get('lastTradedVolume', 0))
                } for candle in all_candles])
                
                df.set_index('timestamp', inplace=True)
                df.sort_index(inplace=True)
                df = df[~df.index.duplicated(keep='last')]
                
                self.historical_data = df
                self.last_historical_update = time.time()
                return True
            
            return False
            
        except Exception as e:
            print_error("Error loading historical data", e)
            return False

    def get_timeframe_minutes(self) -> int:
        """Convert timeframe string to minutes"""
        timeframe = self.timeframe.lower()
        if timeframe.endswith('m'):
            return int(timeframe[:-1])
        elif timeframe.endswith('h'):
            return int(timeframe[:-1]) * 60
        elif timeframe.endswith('d'):
            return int(timeframe[:-1]) * 1440
        return 5  # default to 5 minutes

    async def start_websocket(self):
        """Start WebSocket connection and subscription"""
        try:
            print("\n🔌 Initializing WebSocket connection...")
            
            if await self.ws_client.connect_with_retry():
                print("\n📊 Subscribing to market data...")
                if await self.ws_client.subscribe_market_data("BTCUSD"):
                    print("✅ WebSocket initialization complete")
                    await self.ws_client.listen()
                else:
                    print_error("Failed to subscribe to market data")
            else:
                print_error("Failed to establish WebSocket connection")
                
        except Exception as e:
            print_error("Error in WebSocket initialization", e)

    def should_update_historical(self) -> bool:
        """Check if historical data should be updated"""
        if self.last_historical_update is None:
            return True
            
        time_since_update = time.time() - self.last_historical_update
        return time_since_update >= self.historical_update_interval 