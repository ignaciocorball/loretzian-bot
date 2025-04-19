import os
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List
from colorama import Fore, Style
from tabulate import tabulate
from src.core.positions import ActivePositions
from src.utils.config import DATA_DIR
from src.database import DatabaseManager, DB_CONFIG, SESSION_STATUS, TRADE_STATUS, TRADE_TYPE

class TradingSession:
    def __init__(self, initial_balance=1000):
        # Initialize database connection
        self.db = DatabaseManager(**DB_CONFIG)
        
        # Create new session in database
        self.session_id = self.db.create_session(initial_balance)
        if not self.session_id:
            raise Exception("Failed to create trading session in database")
            
        self.trades = []
        self.session_start = datetime.now()
        self.initial_balance = initial_balance
        self.current_balance = initial_balance
        self.summary = {
            'total_trades': 0,
            'long_trades': 0,
            'short_trades': 0,
            'winning_trades': 0,
            'losing_trades': 0,
            'tp_hits': 0,
            'sl_hits': 0,
            'total_profit': 0.0,
            'total_loss': 0.0,
            'largest_win': 0.0,
            'largest_loss': 0.0,
            'average_win': 0.0,
            'average_loss': 0.0,
            'win_rate': 0.0,
            'profit_factor': 0.0,
            'initial_balance': initial_balance,
            'final_balance': initial_balance,
            'return_percentage': 0.0,
            'max_drawdown': 0.0,
            'start_time': self.session_start,
            'end_time': None,
            'duration': None
        }
        
        self.equity_curve = [initial_balance]
        self.max_balance = initial_balance
        
        # Create directory for reports if it doesn't exist
        os.makedirs(DATA_DIR, exist_ok=True)
        
        # Initialize active positions with session_id
        self.active_positions = ActivePositions(self.session_id)
        
        self.last_candle_time = None
        self.last_trade_time = None
        self.min_time_between_trades = timedelta(minutes=15)
        
    def simulate_trade_outcome(self, trade_data: Dict) -> tuple[float, str]:
        """Simulate trade outcome based on price movements"""
        entry_price = trade_data['entry_price']
        stop_loss = trade_data['stop_loss']
        take_profit = trade_data['take_profit']
        position_size = trade_data['position_size']
        
        if trade_data['signal'] > 0:  # Long position
            if take_profit <= entry_price or stop_loss >= entry_price:
                return 0, 'INVALID'
                
            profit = position_size * (take_profit - entry_price) / entry_price
            loss = position_size * (entry_price - stop_loss) / entry_price
            
            if trade_data['hit_price'] >= take_profit:
                return profit, 'TP'
            elif trade_data['hit_price'] <= stop_loss:
                return -loss, 'SL'
                
        else:  # Short position
            if take_profit >= entry_price or stop_loss <= entry_price:
                return 0, 'INVALID'
                
            profit = position_size * (entry_price - take_profit) / entry_price
            loss = position_size * (stop_loss - entry_price) / entry_price
            
            if trade_data['hit_price'] <= take_profit:
                return profit, 'TP'
            elif trade_data['hit_price'] >= stop_loss:
                return -loss, 'SL'
                
        return 0, 'OPEN'
        
    def add_trade(self, trade_data: Dict):
        """Add a new trade to the session and database"""
        # Calculate position size based on risk percentage
        position_size = self.current_balance * trade_data['risk_percentage']
        trade_data['position_size'] = position_size
        
        # Simulate trade outcome
        pnl, outcome = self.simulate_trade_outcome(trade_data)
        
        trade_data.update({
            'outcome': outcome,
            'pnl': pnl,
            'balance_after_trade': self.current_balance + pnl
        })
        
        # Add trade to database
        trade_id = self.db.create_trade(
            session_id=self.session_id,
            symbol=trade_data['symbol'],
            trade_type=TRADE_TYPE['BUY'] if trade_data['signal'] > 0 else TRADE_TYPE['SELL'],
            entry_price=trade_data['entry_price'],
            quantity=position_size,
            stop_loss=trade_data['stop_loss'],
            take_profit=trade_data['take_profit']
        )
        
        if not trade_id:
            print("❌ Failed to create trade in database")
            return
            
        trade_data['trade_id'] = trade_id
        self.trades.append(trade_data)
        self.summary['total_trades'] += 1
        
        if trade_data['signal'] > 0:
            self.summary['long_trades'] += 1
        else:
            self.summary['short_trades'] += 1
            
        # Update statistics based on outcome
        if outcome == 'TP':
            self.summary['tp_hits'] += 1
            self.summary['winning_trades'] += 1
            self.summary['total_profit'] += pnl
            self.summary['largest_win'] = max(self.summary['largest_win'], pnl)
            # Update trade in database
            self.db.update_trade(
                trade_id=trade_id,
                exit_price=trade_data['take_profit'],
                profit_loss=pnl,
                status=TRADE_STATUS['CLOSED']
            )
        elif outcome == 'SL':
            self.summary['sl_hits'] += 1
            self.summary['losing_trades'] += 1
            self.summary['total_loss'] -= pnl  # Convert loss to positive for stats
            self.summary['largest_loss'] = max(self.summary['largest_loss'], -pnl)
            # Update trade in database
            self.db.update_trade(
                trade_id=trade_id,
                exit_price=trade_data['stop_loss'],
                profit_loss=pnl,
                status=TRADE_STATUS['CLOSED']
            )
            
        # Update balance and equity curve
        self.current_balance += pnl
        self.equity_curve.append(self.current_balance)
        self.max_balance = max(self.max_balance, self.current_balance)
        
        # Update session in database
        self.db.update_session(
            session_id=self.session_id,
            final_balance=self.current_balance,
            profit_loss=self.current_balance - self.initial_balance
        )
        
    def print_trades_table(self):
        """Print table of all trades"""
        if not self.trades:
            print("\nNo trades generated yet.")
            return
            
        table_data = []
        for trade in self.trades:
            row = [
                trade['timestamp'].strftime('%Y-%m-%d %H:%M'),
                'LONG' if trade['signal'] > 0 else 'SHORT',
                f"${trade['position_size']:.2f}",
                f"${trade['entry_price']:.2f}",
                f"${trade['stop_loss']:.2f}",
                f"${trade['take_profit']:.2f}",
                trade['outcome'],
                f"${trade['pnl']:.2f}",
                f"${trade['balance_after_trade']:.2f}"
            ]
            table_data.append(row)
            
        headers = ['Timestamp', 'Signal', 'Position Size', 'Entry', 'Stop Loss', 'Take Profit', 'Outcome', 'P&L', 'Balance']
        print("\n" + Fore.CYAN + "=== Trading Signals ===" + Style.RESET_ALL)
        print(tabulate(table_data, headers=headers, tablefmt='grid'))
        
    def print_summary(self):
        """Print detailed session summary"""
        self._update_summary_stats()
        
        print(f"\n{Fore.CYAN}╔═══════════════════════ Trading Session Summary ══════════════════════╗{Style.RESET_ALL}")
        
        # Balance and Return
        balance_data = [
            ['Initial Balance', f"${self.summary['initial_balance']:.2f}"],
            ['Current Balance', f"{Fore.GREEN if self.current_balance >= self.initial_balance else Fore.RED}${self.summary['final_balance']:.2f}{Style.RESET_ALL}"],
            ['Return', f"{Fore.GREEN if self.summary['return_percentage'] >= 0 else Fore.RED}{self.summary['return_percentage']:.2f}%{Style.RESET_ALL}"],
            ['Max Drawdown', f"{Fore.RED}{self.summary['max_drawdown']:.2f}%{Style.RESET_ALL}"],
        ]
        print(f"\n{Fore.CYAN}┌─ 💰 Account Summary ─┐{Style.RESET_ALL}")
        print(tabulate(balance_data, tablefmt='simple'))
        
        # Trading Statistics
        trading_stats = [
            ['Total Trades', f"{self.summary['total_trades']}"],
            ['Long Trades', f"{self.summary['long_trades']}"],
            ['Short Trades', f"{self.summary['short_trades']}"],
            ['Winning Trades', f"{Fore.GREEN}{self.summary['winning_trades']}{Style.RESET_ALL}"],
            ['Losing Trades', f"{Fore.RED}{self.summary['losing_trades']}{Style.RESET_ALL}"],
            ['Win Rate', f"{Fore.GREEN}{self.summary['win_rate']:.2f}%{Style.RESET_ALL}"],
        ]
        print(f"\n{Fore.CYAN}┌─ 📊 Trading Statistics ─┐{Style.RESET_ALL}")
        print(tabulate(trading_stats, tablefmt='simple'))
        
        # Financial Results
        financial_stats = [
            ['Total Profit', f"{Fore.GREEN}${self.summary['total_profit']:.2f}{Style.RESET_ALL}"],
            ['Total Loss', f"{Fore.RED}${self.summary['total_loss']:.2f}{Style.RESET_ALL}"],
            ['Largest Win', f"{Fore.GREEN}${self.summary['largest_win']:.2f}{Style.RESET_ALL}"],
            ['Largest Loss', f"{Fore.RED}${self.summary['largest_loss']:.2f}{Style.RESET_ALL}"],
            ['Average Win', f"{Fore.GREEN}${self.summary['average_win']:.2f}{Style.RESET_ALL}"],
            ['Average Loss', f"{Fore.RED}${self.summary['average_loss']:.2f}{Style.RESET_ALL}"],
            ['Profit Factor', f"{Fore.CYAN}{self.summary['profit_factor']:.2f}{Style.RESET_ALL}"],
        ]
        print(f"\n{Fore.CYAN}┌─ 💹 Financial Results ─┐{Style.RESET_ALL}")
        print(tabulate(financial_stats, tablefmt='simple'))
        
        # Session Information
        session_info = [
            ['Session Duration', f"{self.summary['duration']:.1f} minutes"],
            ['Start Time', self.summary['start_time'].strftime('%Y-%m-%d %H:%M:%S')],
            ['Last Update', self.summary['end_time'].strftime('%Y-%m-%d %H:%M:%S')],
        ]
        print(f"\n{Fore.CYAN}┌─ ⏰ Session Information ─┐{Style.RESET_ALL}")
        print(tabulate(session_info, tablefmt='simple'))
        print(f"\n{Fore.CYAN}╚════════════════════════════════════════════════════════════════════╝{Style.RESET_ALL}")

    def _update_summary_stats(self):
        """Update session summary statistics"""
        self.summary['end_time'] = datetime.now()
        self.summary['duration'] = (self.summary['end_time'] - self.summary['start_time']).total_seconds() / 60
        self.summary['final_balance'] = self.current_balance
        self.summary['return_percentage'] = ((self.current_balance - self.initial_balance) / self.initial_balance) * 100
        
        # Calculate statistics
        total_trades = self.summary['total_trades']
        winning_trades = self.summary['winning_trades']
        
        if total_trades > 0:
            self.summary['win_rate'] = (winning_trades / total_trades) * 100
        if self.summary['total_loss'] > 0:
            self.summary['profit_factor'] = self.summary['total_profit'] / self.summary['total_loss']
        if winning_trades > 0:
            self.summary['average_win'] = self.summary['total_profit'] / winning_trades
        if self.summary['losing_trades'] > 0:
            self.summary['average_loss'] = self.summary['total_loss'] / self.summary['losing_trades']
        
        # Calculate drawdown
        peak = self.initial_balance
        max_dd = 0
        for balance in self.equity_curve:
            if balance > peak:
                peak = balance
            dd = (peak - balance) / peak * 100
            max_dd = max(max_dd, dd)
        self.summary['max_drawdown'] = max_dd

    def save_report(self):
        """Save session report and update database"""
        try:
            # Update summary statistics
            self._update_summary_stats()
            
            # Update session in database
            self.db.update_session(
                session_id=self.session_id,
                final_balance=self.current_balance,
                profit_loss=self.current_balance - self.initial_balance,
                status=SESSION_STATUS['COMPLETED']
            )
            
            # Save local report
            report_path = os.path.join(DATA_DIR, f"session_{self.session_id}.csv")
            df = pd.DataFrame(self.trades)
            df.to_csv(report_path, index=False)
            
            print(f"📊 Session report saved to {report_path}")
            
        except Exception as e:
            print(f"❌ Error saving session report: {e}")

    def update_active_positions(self, current_price: float):
        """Update active positions and process closed ones"""
        closed_positions = self.active_positions.update_positions(current_price)
        for position in closed_positions:
            position['hit_price'] = current_price
            self.add_trade(position)
        return closed_positions  # Retornamos las posiciones cerradas

    def can_open_new_position(self, current_time: datetime) -> bool:
        """Check if a new position can be opened"""
        if self.last_trade_time is None:
            return True
            
        time_since_last_trade = current_time - self.last_trade_time
        return time_since_last_trade >= self.min_time_between_trades

    def print_summary_compact(self):
        """Print compact version of trading summary"""
        self._update_summary_stats()
        
        # Compact balance info
        balance_info = [
            ['Balance', f"${self.current_balance:.2f}"],
            ['Return', f"{self.summary['return_percentage']:.2f}%"],
            ['Drawdown', f"{self.summary['max_drawdown']:.2f}%"]
        ]
        
        # Compact trade stats
        trade_stats = [
            ['Trades', f"{self.summary['total_trades']}"],
            ['Win/Loss', f"{self.summary['winning_trades']}/{self.summary['losing_trades']}"],
            ['Win Rate', f"{self.summary['win_rate']:.1f}%"]
        ]
        
        # Print compact tables
        print(f"\n{Fore.CYAN}┌─ Performance ─┐{Style.RESET_ALL}")
        print(tabulate(balance_info, tablefmt='simple', colalign=('right','left')))
        
        print(f"\n{Fore.GREEN}┌─ Trade Stats ─┐{Style.RESET_ALL}")
        print(tabulate(trade_stats, tablefmt='simple', colalign=('right','left')))

    def __del__(self):
        """Cleanup when session is destroyed"""
        if hasattr(self, 'db'):
            del self.db 