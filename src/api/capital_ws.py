import websockets
import json
import asyncio
import time
from typing import Dict, Callable
from datetime import datetime
from termcolor import colored

class CapitalWebSocket:
    def __init__(self, cst: str, security_token: str):
        self.ws_url = "wss://api-streaming-capital.backend-capital.com/connect"
        self.cst = cst
        self.security_token = security_token
        self.websocket = None
        self.last_ping_time = None
        self.ping_interval = 540  # 9 minutes in seconds
        self.on_quote_callback = None
        self.is_connected = False
        self.correlation_id = 1
        self.message_count = 0
        self.last_message_time = None
        self.connection_time = None
        self.subscription_status = {}
        self.connection_attempts = 0
        self.max_retries = 5
        self.retry_delay = 5  # seconds

    def set_quote_callback(self, callback: Callable[[Dict], None]):
        """Set callback function for quote updates"""
        self.on_quote_callback = callback

    async def connect_with_retry(self):
        """Attempt to connect with retries"""
        while self.connection_attempts < self.max_retries:
            try:
                print(colored(f"\nAttempting to connect (attempt {self.connection_attempts + 1}/{self.max_retries})", "yellow"))
                print(f"CST Token: {self.cst[:10]}...")
                print(f"Security Token: {self.security_token[:10]}...")
                
                self.websocket = await websockets.connect(
                    self.ws_url,
                    ping_interval=None,  # Disable automatic ping
                    ping_timeout=None,   # Disable ping timeout
                    close_timeout=10     # 10 seconds close timeout
                )
                
                self.is_connected = True
                self.last_ping_time = time.time()
                self.connection_time = datetime.now()
                self.connection_attempts = 0  # Reset counter on successful connection
                
                print(colored("✅ WebSocket connected successfully", "green"))
                return True
                
            except Exception as e:
                self.connection_attempts += 1
                print(colored(f"❌ Connection attempt {self.connection_attempts} failed: {str(e)}", "red"))
                
                if self.connection_attempts < self.max_retries:
                    print(colored(f"Retrying in {self.retry_delay} seconds...", "yellow"))
                    await asyncio.sleep(self.retry_delay)
                else:
                    print(colored("❌ Maximum connection attempts reached", "red"))
                    return False
        
        return False

    async def reconnect(self):
        """Handle reconnection"""
        print(colored("\n🔄 Attempting to reconnect...", "yellow"))
        self.is_connected = False
        
        if self.websocket:
            try:
                await self.websocket.close()
            except:
                pass
            
        self.websocket = None
        self.connection_attempts = 0
        
        # Try to reconnect
        if await self.connect_with_retry():
            # Resubscribe to all active subscriptions
            for epic in self.subscription_status.keys():
                await self.subscribe_market_data(epic)
            return True
        return False

    async def subscribe_market_data(self, epic: str):
        """Subscribe to market data for a specific epic"""
        if not self.is_connected:
            print(colored("❌ Cannot subscribe: WebSocket not connected", "red"))
            return False

        subscribe_message = {
            "destination": "marketData.subscribe",
            "correlationId": str(self.correlation_id),
            "cst": self.cst,
            "securityToken": self.security_token,
            "payload": {
                "epics": [epic]
            }
        }
        
        try:
            print(colored(f"\n📡 Subscribing to {epic}...", "cyan"))
            await self.websocket.send(json.dumps(subscribe_message))
            self.correlation_id += 1
            self.subscription_status[epic] = {
                "subscribed_at": datetime.now(),
                "status": "pending",
                "retry_count": 0
            }
            print(colored(f"✅ Subscription request sent for {epic}", "green"))
            return True
        except Exception as e:
            print(colored(f"❌ Error subscribing to market data: {e}", "red"))
            return False

    async def listen(self):
        """Listen for WebSocket messages"""
        while True:  # Changed to infinite loop to handle reconnections
            try:
                if not self.is_connected:
                    if not await self.reconnect():
                        print(colored("Failed to reconnect, retrying in 5 seconds...", "red"))
                        await asyncio.sleep(5)
                        continue
                
                await self.check_ping()
                
                try:
                    message = await asyncio.wait_for(self.websocket.recv(), timeout=1.0)
                    data = json.loads(message)
                    
                    self.message_count += 1
                    self.last_message_time = datetime.now()
                    
                    if data.get("destination") == "quote" and self.on_quote_callback:
                        epic = data["payload"].get("epic")
                        if epic in self.subscription_status:
                            self.subscription_status[epic]["status"] = "active"
                            self.subscription_status[epic]["last_update"] = datetime.now()
                        self.on_quote_callback(data["payload"])
                    elif data.get("destination") == "marketData.subscribe":
                        if data.get("status") == "OK":
                            print(colored("✅ Market data subscription confirmed", "green"))
                        else:
                            print(colored(f"❌ Market data subscription failed: {data.get('status')}", "red"))
                    
                except asyncio.TimeoutError:
                    continue
                    
            except websockets.exceptions.ConnectionClosed as e:
                print(colored(f"❌ WebSocket connection closed: {e}", "red"))
                self.is_connected = False
                continue
            except Exception as e:
                print(colored(f"❌ Error in WebSocket listener: {e}", "red"))
                self.is_connected = False
                continue

    def print_status(self):
        """Print current WebSocket status"""
        status = []
        connection_status = '🟢 Connected' if self.is_connected else '🔴 Disconnected'
        status.append(f"Connection Status: {connection_status}")
        
        if not self.is_connected:
            status.append(f"Connection Attempts: {self.connection_attempts}/{self.max_retries}")
        
        if self.connection_time:
            uptime = datetime.now() - self.connection_time
            status.append(f"Uptime: {str(uptime).split('.')[0]}")
        
        status.append(f"Messages Received: {self.message_count}")
        
        if self.last_message_time:
            last_msg = datetime.now() - self.last_message_time
            status.append(f"Last Message: {last_msg.seconds}s ago")
        
        if self.last_ping_time:
            next_ping = self.ping_interval - (time.time() - self.last_ping_time)
            status.append(f"Next Ping in: {int(next_ping)}s")
        
        print("\n".join(status))
        
        if self.subscription_status:
            print("\nSubscriptions:")
            for epic, data in self.subscription_status.items():
                status = data["status"]
                subscribed_at = data["subscribed_at"]
                last_update = data.get("last_update", "Never")
                if isinstance(last_update, datetime):
                    last_update = last_update.strftime('%H:%M:%S')
                print(f"{epic}: {status} (since {subscribed_at.strftime('%H:%M:%S')}, last update: {last_update})")

    async def ping(self):
        """Send ping message to keep connection alive"""
        if not self.is_connected:
            return False

        ping_message = {
            "destination": "ping",
            "correlationId": str(self.correlation_id),
            "cst": self.cst,
            "securityToken": self.security_token
        }
        
        try:
            await self.websocket.send(json.dumps(ping_message))
            self.correlation_id += 1
            self.last_ping_time = time.time()
            print(colored("📡 Ping sent successfully", "green"))
            return True
        except Exception as e:
            print(colored(f"❌ Error sending ping: {e}", "red"))
            return False

    async def check_ping(self):
        """Check if ping is needed and send if necessary"""
        if self.last_ping_time and time.time() - self.last_ping_time >= self.ping_interval:
            await self.ping()

    async def close(self):
        """Close WebSocket connection"""
        if self.websocket:
            try:
                await self.websocket.close()
            finally:
                self.is_connected = False
                print(colored("WebSocket connection closed", "yellow")) 