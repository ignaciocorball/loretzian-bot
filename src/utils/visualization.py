from datetime import datetime
from typing import Dict, List
from termcolor import colored
from tabulate import tabulate
from colorama import Fore, Style
import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

def print_header(timestamp: datetime, current_price: float = None):
    """Print the main header of the bot"""
    print(colored("\n╔═════ 🤖 Lorentzian Bot ═══════════════╗", "cyan"))
    print(colored(f"║ {timestamp.strftime('%Y-%m-%d %H:%M:%S')}                   ║", "yellow"))
    if current_price:
        print(colored(f"║ Price: ${current_price:.2f}                      ║", "green"))
    print(colored("╚═══════════════════════════════════════╝\n", "cyan"))

def print_market_data(market_data: List[List[str]]):
    """Print market data in a formatted table"""
    print(colored("=== 📊 Market Data ===", "cyan"))
    print(tabulate(market_data, tablefmt='simple'))
    print()

def print_account_info(account_info: Dict):
    """Print account information in a formatted table"""
    print(colored("=== 💰 Account Information ===", "cyan"))
    print(tabulate(account_info, tablefmt='simple'))
    print()

def print_bot_config(config_data: List[List[str]]):
    """Print bot configuration in a formatted table"""
    print(colored("=== ⚙️ Bot Configuration ===", "cyan"))
    print(tabulate(config_data, tablefmt='simple'))
    print()

def print_active_filters(filters_data: List[List[str]]):
    """Print active filters in a formatted table"""
    print(colored("=== 🔍 Active Filters ===", "cyan"))
    print(tabulate(filters_data, tablefmt='simple'))
    print()

def print_positions(positions: List[Dict]):
    """Print active positions in a formatted table"""
    print(colored("=== 📈 Active Positions ===", "cyan"))
    if not positions:
        print("No active positions\n")
        return

    table_data = []
    total_pnl = 0

    for pos in positions:
        try:
            position_data = pos.get('position', {})
            market_data = pos.get('market', {})
            pnl = float(position_data.get('upl', 0))
            total_pnl += pnl

            row = format_position_row(position_data, market_data, pnl)
            table_data.append(row)
        except Exception as e:
            print(colored(f"❌ Error processing position: {e}", "red"))
            continue

    headers = ['Type', 'Size', 'Entry', 'SL', 'TP', 'SL', 'P&L']
    print(tabulate(table_data, headers=headers, tablefmt='simple'))
    print(f"\nTotal P&L: {Fore.GREEN if total_pnl >= 0 else Fore.RED}${total_pnl:.2f}{Style.RESET_ALL}\n")

def print_trading_signal(signal_type: str, current_price: float, stop_loss: float, take_profit: float):
    """Print trading signal information"""
    signal_color = "green" if signal_type == "LONG" else "red"
    arrow = "▲" if signal_type == "LONG" else "▼"
    
    print(colored("\n=== 🎯 Trading Signal ===", "cyan"))
    signal_data = [
        ["Direction", colored(f"{arrow} {signal_type}", signal_color)],
        ["Entry", f"${current_price:.2f}"],
        ["Stop Loss", f"${stop_loss:.2f} ({abs((stop_loss - current_price) / current_price * 100):.2f}%)"],
        ["Take Profit", f"${take_profit:.2f} ({abs((take_profit - current_price) / current_price * 100):.2f}%)"]
    ]
    print(tabulate(signal_data, tablefmt='simple'))

def format_position_row(position_data: Dict, market_data: Dict, pnl: float) -> List:
    """Format a single position row for the table"""
    direction = "🟢 LONG" if position_data.get('direction') == 'BUY' else "🔴 SHORT"
    pnl_color = Fore.GREEN if pnl >= 0 else Fore.RED

    return [
        direction,
        f"{float(position_data.get('size', 0)):.2f} BTC",
        f"${float(position_data.get('level', 0)):.2f}",
        f"${float(position_data.get('stopLevel', 0)):.2f}",
        f"${float(position_data.get('profitLevel', 0)):.2f}",
        f"{pnl_color}${pnl:.2f}{Style.RESET_ALL}"
    ]

def print_trading_signal(signal_type: str, current_price: float, stop_loss: float, take_profit: float):
    """Print trading signal information"""
    signal_color = "green" if signal_type == "LONG" else "red"
    arrow = "▲" if signal_type == "LONG" else "▼"
    
    print(colored("\n=== 🎯 Trading Signal ===", "cyan"))
    signal_data = [
        ["Direction", colored(f"{arrow} {signal_type}", signal_color)],
        ["Entry", f"${current_price:.2f}"],
        ["Stop Loss", f"${stop_loss:.2f} ({abs((stop_loss - current_price) / current_price * 100):.2f}%)"],
        ["Take Profit", f"${take_profit:.2f} ({abs((take_profit - current_price) / current_price * 100):.2f}%)"]
    ]
    print(tabulate(signal_data, tablefmt='simple'))

def print_error(message: str, error: Exception = None):
    """Print error message"""
    print(colored(f"\n❌ Error: {message}", "red"))
    if error:
        print(colored(f"Details: {str(error)}", "red"))

def print_account_status(account_info: Dict):
    """Print account status information in a formatted table"""
    print(colored("=== 💰 Account Status ===", "cyan"))
    if not account_info:
        print("No account information available\n")
        return

    account_data = [
        ["Balance", f"${float(account_info.get('balance', 0)):.2f}"],
        ["Available", f"${float(account_info.get('available', 0)):.2f}"],
        ["Profit/Loss", f"${float(account_info.get('profitLoss', 0)):.2f}"],
        ["Initial Deposit", f"${float(account_info.get('deposit', 0)):.2f}"]
    ]
    print(tabulate(account_data, tablefmt='simple'))
    print()

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
    
    # Account status (new section)
    if self.capital_api.account_info:
        account_info = self.capital_api.account_info.get('accountInfo', {})
        print_account_status(account_info)
    
    # Bot configuration
    config_data = [
        ["Risk per Trade", f"{self.config['risk_per_trade']*100}%"],
        ["Take Profit", f"{self.config['take_profit']*100}%"],
        ["Stop Loss", f"{self.config['stop_loss']*100}%"],
        ["ADX Threshold", f"{self.config['adx_threshold']}"],
        ["Min Time Between Trades", f"{self.config['min_time_between_trades']} minutes"]
    ]
    print_bot_config(config_data) 