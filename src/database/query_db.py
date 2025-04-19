import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
from tabulate import tabulate
from colorama import init, Fore, Style
from .config import DB_CONFIG, SESSION_STATUS, TRADE_STATUS

init()  # Initialize colorama

def get_db_connection():
    """Create a database connection"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except Exception as e:
        print(f"❌ Error connecting to database: {e}")
        return None

def get_active_sessions():
    """Get all active trading sessions"""
    conn = get_db_connection()
    if not conn:
        return []
        
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT * FROM sessions
                WHERE status = %s
                ORDER BY start_time DESC
            """, (SESSION_STATUS['ACTIVE'],))
            return cur.fetchall()
    except Exception as e:
        print(f"❌ Error fetching active sessions: {e}")
        return []
    finally:
        conn.close()

def get_session_trades(session_id: int):
    """Get all trades for a specific session"""
    conn = get_db_connection()
    if not conn:
        return []
        
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT * FROM trades
                WHERE session_id = %s
                ORDER BY entry_time
            """, (session_id,))
            return cur.fetchall()
    except Exception as e:
        print(f"❌ Error fetching session trades: {e}")
        return []
    finally:
        conn.close()

def get_session_summary(session_id: int):
    """Get summary statistics for a session"""
    conn = get_db_connection()
    if not conn:
        return None
        
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Get session details
            cur.execute("""
                SELECT * FROM sessions
                WHERE session_id = %s
            """, (session_id,))
            session = cur.fetchone()
            
            if not session:
                return None
                
            # Get trade statistics
            cur.execute("""
                SELECT 
                    COUNT(*) as total_trades,
                    SUM(CASE WHEN type = 'buy' THEN 1 ELSE 0 END) as long_trades,
                    SUM(CASE WHEN type = 'sell' THEN 1 ELSE 0 END) as short_trades,
                    SUM(CASE WHEN status = 'closed' AND profit_loss > 0 THEN 1 ELSE 0 END) as winning_trades,
                    SUM(CASE WHEN status = 'closed' AND profit_loss < 0 THEN 1 ELSE 0 END) as losing_trades,
                    SUM(profit_loss) as total_profit_loss,
                    AVG(CASE WHEN status = 'closed' AND profit_loss > 0 THEN profit_loss ELSE NULL END) as avg_win,
                    AVG(CASE WHEN status = 'closed' AND profit_loss < 0 THEN profit_loss ELSE NULL END) as avg_loss
                FROM trades
                WHERE session_id = %s
            """, (session_id,))
            stats = cur.fetchone()
            
            return {
                'session': session,
                'stats': stats
            }
    except Exception as e:
        print(f"❌ Error fetching session summary: {e}")
        return None
    finally:
        conn.close()

def display_sessions():
    """Display all active sessions"""
    sessions = get_active_sessions()
    if not sessions:
        print("\nNo active sessions found.")
        return
        
    table_data = []
    for session in sessions:
        row = [
            session['session_id'],
            session['start_time'].strftime('%Y-%m-%d %H:%M:%S'),
            f"${session['initial_balance']:.2f}",
            f"${session['final_balance']:.2f}" if session['final_balance'] else "N/A",
            f"{session['profit_loss_percentage']:.2f}%" if session['profit_loss_percentage'] else "N/A",
            session['status']
        ]
        table_data.append(row)
        
    headers = ['Session ID', 'Start Time', 'Initial Balance', 'Final Balance', 'Return %', 'Status']
    print("\n" + Fore.CYAN + "=== Active Trading Sessions ===" + Style.RESET_ALL)
    print(tabulate(table_data, headers=headers, tablefmt='grid'))

def display_session_trades(session_id: int):
    """Display all trades for a session"""
    trades = get_session_trades(session_id)
    if not trades:
        print(f"\nNo trades found for session {session_id}.")
        return
        
    table_data = []
    for trade in trades:
        row = [
            trade['trade_id'],
            trade['entry_time'].strftime('%Y-%m-%d %H:%M:%S'),
            trade['type'].upper(),
            trade['symbol'],
            f"${trade['entry_price']:.2f}",
            f"${trade['exit_price']:.2f}" if trade['exit_price'] else "N/A",
            f"${trade['quantity']:.2f}",
            f"${trade['profit_loss']:.2f}" if trade['profit_loss'] else "N/A",
            trade['status']
        ]
        table_data.append(row)
        
    headers = ['Trade ID', 'Entry Time', 'Type', 'Symbol', 'Entry', 'Exit', 'Quantity', 'P&L', 'Status']
    print(f"\n{Fore.CYAN}=== Trades for Session {session_id} ==={Style.RESET_ALL}")
    print(tabulate(table_data, headers=headers, tablefmt='grid'))

def display_session_summary(session_id: int):
    """Display summary statistics for a session"""
    summary = get_session_summary(session_id)
    if not summary:
        print(f"\nNo summary found for session {session_id}.")
        return
        
    session = summary['session']
    stats = summary['stats']
    
    # Session info
    session_info = [
        ['Session ID', session['session_id']],
        ['Start Time', session['start_time'].strftime('%Y-%m-%d %H:%M:%S')],
        ['End Time', session['end_time'].strftime('%Y-%m-%d %H:%M:%S') if session['end_time'] else 'N/A'],
        ['Initial Balance', f"${session['initial_balance']:.2f}"],
        ['Final Balance', f"${session['final_balance']:.2f}" if session['final_balance'] else 'N/A'],
        ['Profit/Loss', f"${session['profit_loss']:.2f}" if session['profit_loss'] else 'N/A'],
        ['Return %', f"{session['profit_loss_percentage']:.2f}%" if session['profit_loss_percentage'] else 'N/A'],
        ['Status', session['status']]
    ]
    
    # Trade statistics
    trade_stats = [
        ['Total Trades', stats['total_trades']],
        ['Long Trades', stats['long_trades']],
        ['Short Trades', stats['short_trades']],
        ['Winning Trades', stats['winning_trades']],
        ['Losing Trades', stats['losing_trades']],
        ['Total P&L', f"${stats['total_profit_loss']:.2f}" if stats['total_profit_loss'] else 'N/A'],
        ['Average Win', f"${stats['avg_win']:.2f}" if stats['avg_win'] else 'N/A'],
        ['Average Loss', f"${stats['avg_loss']:.2f}" if stats['avg_loss'] else 'N/A']
    ]
    
    print(f"\n{Fore.CYAN}=== Session {session_id} Summary ==={Style.RESET_ALL}")
    print("\nSession Information:")
    print(tabulate(session_info, tablefmt='simple'))
    print("\nTrade Statistics:")
    print(tabulate(trade_stats, tablefmt='simple'))

def main():
    """Main function to display database information"""
    print("\n" + Fore.CYAN + "📊 Trading Bot Database Query Tool" + Style.RESET_ALL)
    
    while True:
        print("\nOptions:")
        print("1. Show active sessions")
        print("2. Show session trades")
        print("3. Show session summary")
        print("4. Exit")
        
        choice = input("\nEnter your choice (1-4): ")
        
        if choice == '1':
            display_sessions()
        elif choice == '2':
            session_id = input("Enter session ID: ")
            try:
                display_session_trades(int(session_id))
            except ValueError:
                print("❌ Invalid session ID")
        elif choice == '3':
            session_id = input("Enter session ID: ")
            try:
                display_session_summary(int(session_id))
            except ValueError:
                print("❌ Invalid session ID")
        elif choice == '4':
            print("\nGoodbye!")
            break
        else:
            print("❌ Invalid choice")

if __name__ == "__main__":
    main() 