from datetime import datetime
from typing import Dict, List, Tuple
from src.utils.visualization import print_positions
from src.database import DatabaseManager, DB_CONFIG, TRADE_STATUS
import pandas as pd
import numpy as np
import talib

class ActivePositions:
    def __init__(self, session_id: int):
        self.positions = []
        self.session_id = session_id
        self.db = DatabaseManager(**DB_CONFIG)
        
    def add_position(self, position_data: Dict):
        """Add a new position to track and database"""
        # Add to local tracking
        self.positions.append(position_data)
        
        # Add to database
        trade_id = self.db.create_trade(
            session_id=self.session_id,
            symbol=position_data['symbol'],
            trade_type='buy' if position_data['signal'] > 0 else 'sell',
            entry_price=position_data['entry_price'],
            quantity=position_data['position_size'],
            stop_loss=position_data['stop_loss'],
            take_profit=position_data['take_profit']
        )
        
        if trade_id:
            position_data['trade_id'] = trade_id
            print(f"✅ Position added to database with ID: {trade_id}")
        else:
            print("❌ Failed to add position to database")
        
    def update_positions(self, current_price: float) -> List[Dict]:
        """Update all positions and return closed ones"""
        updated_positions = []
        closed_positions = []
        
        for position in self.positions:
            pnl = self.calculate_position_pnl(position, current_price)
            position['current_pnl'] = pnl
            
            entry_time = position.get('entry_time')
            if entry_time:
                # Calculate time in minutes
                time_in_trade = (datetime.now() - entry_time).total_seconds() / 60
                
                # Get historical data according to timeframe
                resolution = position.get('timeframe', 'MINUTE_5')
                bars_needed = 30 if resolution == 'MINUTE_1' else 12
                
                market_data = self.capital_api.get_price_history(
                    position['symbol'],
                    resolution=resolution,
                    max_bars=bars_needed
                )
                
                if market_data and 'prices' in market_data:
                    df = pd.DataFrame([{
                        'close': float(price['closePrice']['bid'])
                    } for price in market_data['prices']])
                    
                    # Calculate volatility adapted to timeframe
                    if resolution == 'MINUTE_1':
                        volatility = df['close'].pct_change().std() * np.sqrt(1440)  # Scale to daily
                    else:  # MINUTE_5
                        volatility = df['close'].pct_change().std() * np.sqrt(288)   # Scale to daily
                    
                    # Calculate EMAs adapted to timeframe
                    if resolution == 'MINUTE_1':
                        ema_fast = talib.EMA(df['close'], timeperiod=10)  # 10 minutes
                        ema_slow = talib.EMA(df['close'], timeperiod=30)  # 30 minutes
                    else:  # MINUTE_5
                        ema_fast = talib.EMA(df['close'], timeperiod=6)   # 30 minutes
                        ema_slow = talib.EMA(df['close'], timeperiod=12)  # 1 hour
                    
                    trend_strength = (ema_fast[-1] - ema_slow[-1]) / ema_slow[-1]
                    
                    # Parameters adapted to timeframe
                    params = {
                        'MINUTE_1': {
                            'min_hold_time': 5,        # 5 minutes minimum
                            'trend_threshold': 0.0005,  # 0.05%
                            'volatility_threshold': 0.10,  # 10% daily
                            'max_loss': -0.015         # -1.5%
                        },
                        'MINUTE_5': {
                            'min_hold_time': 15,       # 15 minutes minimum
                            'trend_threshold': 0.001,   # 0.1%
                            'volatility_threshold': 0.15,  # 15% daily
                            'max_loss': -0.02          # -2%
                        }
                    }
                    
                    current_params = params.get(resolution, params['MINUTE_5'])
                    
                    should_close = False
                    
                    if position['signal'] > 0:  # Long position
                        if pnl > 0:  # In profit
                            if trend_strength < -current_params['trend_threshold'] and volatility > current_params['volatility_threshold']:
                                should_close = True
                                print(f"🔄 Closing winning long position - Weak trend and high volatility")
                        else:  # In loss
                            if trend_strength > current_params['trend_threshold'] and time_in_trade > current_params['min_hold_time']:
                                print(f"💪 Holding losing long position - Recovery signals detected")
                            elif (pnl < current_params['max_loss'] and trend_strength < -current_params['trend_threshold']):
                                should_close = True
                                print(f"🔄 Closing losing long position - No recovery signals")
                    
                    else:  # Short position
                        if pnl > 0:  # In profit
                            if trend_strength > current_params['trend_threshold'] and volatility > current_params['volatility_threshold']:
                                should_close = True
                                print(f"🔄 Closing winning short position - Weak trend and high volatility")
                        else:  # In loss
                            if trend_strength < -current_params['trend_threshold'] and time_in_trade > current_params['min_hold_time']:
                                print(f"💪 Holding losing short position - Recovery signals detected")
                            elif (pnl < current_params['max_loss'] and trend_strength > current_params['trend_threshold']):
                                should_close = True
                                print(f"🔄 Closing losing short position - No recovery signals")
                    
                    if should_close:
                        position['exit_price'] = current_price
                        position['exit_time'] = datetime.now()
                        closed_positions.append(position)
                        
                        # Update trade in database
                        if 'trade_id' in position:
                            self.db.update_trade(
                                trade_id=position['trade_id'],
                                exit_price=current_price,
                                profit_loss=pnl,
                                status=TRADE_STATUS['CLOSED']
                            )
                            print(f"✅ Updated closed position {position['trade_id']} in database")
                    else:
                        updated_positions.append(position)
        
        self.positions = updated_positions
        return closed_positions
        
    def calculate_position_pnl(self, position: Dict, current_price: float) -> float:
        """Calculate current P&L for a position"""
        if position['signal'] > 0:  # Long position
            return position['position_size'] * (current_price - position['entry_price']) / position['entry_price']
        else:  # Short position
            return position['position_size'] * (position['entry_price'] - current_price) / position['entry_price']
            
    def check_position_exit(self, position: Dict, current_price: float) -> bool:
        """Check if position should be closed"""
        # Update hit price for P&L calculation
        position['hit_price'] = current_price
        
        if position['signal'] > 0:  # Long position
            return current_price >= position['take_profit'] or current_price <= position['stop_loss']
        else:  # Short position
            return current_price <= position['take_profit'] or current_price >= position['stop_loss']
            
    def get_positions_summary(self) -> Tuple[int, float]:
        """Get summary of active positions"""
        total_positions = len(self.positions)
        total_pnl = sum(pos.get('current_pnl', 0) for pos in self.positions)
        return total_positions, total_pnl

    def display_positions(self):
        """Display current active positions"""
        print_positions(self.positions)

    def has_positions(self) -> bool:
        """Check if there are any active positions"""
        return len(self.positions) > 0
        
    def __del__(self):
        """Cleanup when object is destroyed"""
        if hasattr(self, 'db'):
            del self.db 