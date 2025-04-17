import asyncio
import os
from colorama import init
from termcolor import colored
from src.core.trader import LorentzianTrader

def run_live_monitoring():
    """Run the live trading bot"""
    init()  # Initialize colorama

    os.system('cls' if os.name == 'nt' else 'clear')
    
    print(colored("\n╔═══════════════ 🤖 Lorentzian Bot ════════════════╗", "cyan"))
    print(colored("║ Starting trading session with Capital.com...     ║", "yellow"))
    print(colored("╚══════════════════════════════════════════════════╝\n", "cyan"))

    trader = LorentzianTrader()
    
    async def main_loop():
        try:
            # Print initial strategy status
            print(colored("\n📈 Loading initial historical data...", "cyan"))
            if trader.load_historical_data(None, None):
                print(colored("✅ Initial historical data loaded", "green"))
            else:
                print(colored("⚠️ Failed to load initial historical data", "yellow"))
            
            # Start WebSocket connection
            print(colored("\n🔌 Starting WebSocket connection...", "cyan"))
            await trader.ws_client.connect_with_retry()
            
            if await trader.ws_client.subscribe_market_data("BTCUSD"):
                print(colored("✅ Successfully subscribed to market data", "green"))
                await trader.ws_client.listen()
            else:
                print(colored("❌ Failed to subscribe to market data", "red"))
            
        except Exception as e:
            print(colored(f"\n❌ Error in main loop: {e}", "red"))
            raise e
        finally:
            print(colored("\nClosing WebSocket connection...", "yellow"))
            await trader.ws_client.close()

    # Create event loop
    loop = asyncio.get_event_loop()
    
    try:
        loop.run_until_complete(main_loop())
    except KeyboardInterrupt:
        print(colored("\n\nStopping bot...", "yellow"))
        trader.session.save_report()
        print(colored("Session report saved", "green"))
    finally:
        loop.close()

if __name__ == "__main__":
    run_live_monitoring() 