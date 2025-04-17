import os
import json
import time
import base64
import requests
from typing import Dict, List, Optional, Union
from datetime import datetime
from dotenv import load_dotenv
from termcolor import colored

class CapitalAPI:
    def __init__(self):
        load_dotenv()
        
        self.api_key = os.getenv('CAPITAL_API_KEY')
        self.demo_mode = os.getenv('CAPITAL_DEMO_MODE', 'true').lower() == 'true'
        self.identifier = os.getenv('CAPITAL_API_IDENTIFIER')
        self.password = os.getenv('CAPITAL_API_PASSWORD')
        
        # Set base URL based on demo/live mode
        self.base_url = (
            'https://demo-api-capital.backend-capital.com' if self.demo_mode 
            else 'https://api-capital.backend-capital.com'
        )
        
        # Session tokens
        self.cst = None
        self.security_token = None
        self.account_info = None
        self.last_account_update = None
        self.account_update_interval = 60  # Update account info every 60 seconds
        
    def _headers(self, with_auth: bool = True) -> Dict[str, str]:
        """Generate headers for API requests"""
        headers = {
            'X-CAP-API-KEY': self.api_key,
            'Content-Type': 'application/json'
        }
        
        if with_auth and self.cst and self.security_token:
            headers.update({
                'CST': self.cst,
                'X-SECURITY-TOKEN': self.security_token
            })
            
        return headers

    def create_session(self) -> bool:
        """Create a new trading session"""
        endpoint = f"{self.base_url}/api/v1/session"
        
        payload = {
            "identifier": self.identifier,
            "password": self.password,
            "encryptedPassword": False
        }
        
        try:
            response = requests.post(
                endpoint,
                headers=self._headers(with_auth=False),
                json=payload
            )
            
            if response.status_code == 200:
                self.cst = response.headers.get('CST')
                self.security_token = response.headers.get('X-SECURITY-TOKEN')
                
                # Get initial account information
                self.update_account_info()
                return True
            else:
                print(colored(f"❌ Error creating session: {response.text}", "red"))
                return False
        except Exception as e:
            print(colored(f"❌ Error creating session: {e}", "red"))
            return False

    def update_account_info(self) -> bool:
        """Update account information"""
        if (self.last_account_update is not None and 
            time.time() - self.last_account_update < self.account_update_interval):
            return True
            
        try:
            account_info = self.get_account_info()
            if account_info:
                self.account_info = account_info
                self.last_account_update = time.time()
                return True
            return False
        except Exception as e:
            print(colored(f"❌ Error updating account info: {e}", "red"))
            return False

    def get_market_info(self, epic: str) -> Dict:
        """Get market information for a specific instrument"""
        endpoint = f"{self.base_url}/api/v1/markets/{epic}"
        
        response = requests.get(
            endpoint,
            headers=self._headers()
        )
        
        return response.json() if response.status_code == 200 else None

    def get_positions(self) -> List[Dict]:
        """Get all open positions"""
        endpoint = f"{self.base_url}/api/v1/positions"
        
        response = requests.get(
            endpoint,
            headers=self._headers()
        )
        
        return response.json().get('positions', []) if response.status_code == 200 else []

    def create_position(self, epic: str, direction: str, size: float, stop_level: float = None, profit_level: float = None) -> Dict:
        """Create a new position with Capital.com API"""
        try:
            # Format the position size to 2 decimal places
            size = round(size, 2)
            
            # Validate position size
            if size < 0.01:
                print("❌ Position size too small (minimum 0.01)")
                return None
                
            # Validate stop loss and take profit levels
            current_price = self.get_market_info(epic).get('snapshot', {}).get('bid', 0)
            if current_price == 0:
                print("❌ Could not get current market price")
                return None
                
            if stop_level:
                # Validate stop loss distance
                if direction == 'BUY':
                    if stop_level >= current_price:
                        print("❌ Stop loss must be below current price for long positions")
                        return None
                else:  # SELL
                    if stop_level <= current_price:
                        print("❌ Stop loss must be above current price for short positions")
                        return None
                        
            if profit_level:
                # Validate take profit distance
                if direction == 'BUY':
                    if profit_level <= current_price:
                        print("❌ Take profit must be above current price for long positions")
                        return None
                else:  # SELL
                    if profit_level >= current_price:
                        print("❌ Take profit must be below current price for short positions")
                        return None
            
            # Prepare the payload
            payload = {
                "epic": epic,
                "direction": direction,
                "size": size,
                "guaranteedStop": False,
                "forceOpen": True
            }
            
            # Add stop loss if provided
            if stop_level:
                payload["stopLevel"] = round(stop_level, 2)
                
            # Add take profit if provided
            if profit_level:
                payload["profitLevel"] = round(profit_level, 2)
            
            # Print trying to open position
            print(f"🚀 Trying to open {direction} position with size {size} at {current_price}")
            
            # Make the request with correct endpoint
            response = requests.post(
                f"{self.base_url}/api/v1/positions",
                headers=self._headers(),
                json=payload
            )
            
            # Log the status code with color
            print(f"Response status: {colored(response.status_code, 'green' if response.status_code == 200 else 'red')}")
            
            if response.status_code == 200:
                position_data = response.json()
                deal_reference = position_data.get('dealReference')
                
                if deal_reference:
                    # Wait for position confirmation
                    confirmed = self.wait_for_position_confirmation(deal_reference)
                    if confirmed:
                        print(f"✅ Position created successfully with deal reference: {deal_reference}")
                        return position_data
                    else:
                        print("❌ Position creation not confirmed")
                        return None
                else:
                    print("❌ No deal reference in response")
                    return None
            else:
                print(f"❌ Failed to create position. Status code: {response.status_code}")
                print(f"Error response: {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ Error creating position: {e}")
            return None

    def wait_for_position_confirmation(self, deal_reference: str, max_attempts: int = 2, delay: float = 1.0) -> bool:
        """Wait for position confirmation from Capital.com API"""
        for attempt in range(max_attempts):
            try:
                response = requests.get(
                    f"{self.base_url}/api/v1/confirms/{deal_reference}",
                    headers=self._headers()
                )
                
                if response.status_code == 200:
                    confirm_data = response.json()
                    status = confirm_data.get('status')
                    
                    if status == 'OPEN':
                        print(f"✅ Position confirmed: {deal_reference}")
                        return True
                    elif status == 'REJECTED':
                        print(f"❌ Position rejected: {deal_reference}")
                        print(f"Reason: {confirm_data.get('reason', 'No reason provided')}")
                        return False
                    elif status == 'DELETED':
                        print(f"❌ Position deleted: {deal_reference}")
                        return False
                    else:
                        print(f"⏳ Waiting for position confirmation... Status: {status}")
                
                # Wait before next attempt
                time.sleep(delay)
                
            except Exception as e:
                print(f"Error checking position confirmation: {e}")
                time.sleep(delay)
        
        print(f"❌ Position confirmation timeout for deal reference: {deal_reference}")
        return False

    def close_position(self, dealId: str) -> Dict:
        """Close a specific position"""
        endpoint = f"{self.base_url}/api/v1/positions/{dealId}"
        
        response = requests.delete(
            endpoint,
            headers=self._headers()
        )
        
        return response.json() if response.status_code == 200 else None

    def get_price_history(
        self,
        epic: str,
        resolution: str = 'MINUTE',
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        max_bars: int = 1000
    ) -> Dict:
        """
        Get historical price data
        
        Args:
            epic: Instrument identifier
            resolution: Time resolution (MINUTE, HOUR_1, HOUR_4, DAY, WEEK)
            from_date: Start date in ISO format (YYYY-MM-DDTHH:mm:ss)
            to_date: End date in ISO format (YYYY-MM-DDTHH:mm:ss)
            max_bars: Maximum number of bars to return
        """
        endpoint = f"{self.base_url}/api/v1/prices/{epic}"
        
        params = {
            'resolution': resolution,
            'max_bars': max_bars
        }
        
        if from_date:
            params['from'] = from_date
        if to_date:
            params['to'] = to_date
            
        response = requests.get(
            endpoint,
            headers=self._headers(),
            params=params
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error getting price history: {response.status_code}")
            print(f"Response: {response.text}")
            return None

    def get_account_info(self) -> Dict:
        """Get account information and balance"""
        endpoint = f"{self.base_url}/api/v1/accounts"
        
        try:
            response = requests.get(
                endpoint,
                headers=self._headers()
            )
            
            if response.status_code == 200:
                data = response.json()
                if 'accounts' in data and len(data['accounts']) > 0:
                    account = data['accounts'][0]  # Get the first account
                    balance_info = account.get('balance', {})
                    
                    return {
                        'accountInfo': {
                            'balance': float(balance_info.get('balance', 0)),
                            'available': float(balance_info.get('available', 0)),
                            'profitLoss': float(balance_info.get('profitLoss', 0)),
                            'deposit': float(balance_info.get('deposit', 0)),
                            'usedMargin': float(balance_info.get('usedMargin', 0))
                        }
                    }
                print(colored("❌ No accounts found in response", "red"))
                return None
            print(colored(f"❌ Failed to get account info: {response.status_code}", "red"))
            return None
        except Exception as e:
            print(colored(f"❌ Error getting account info: {e}", "red"))
            return None

    def get_market_details(self, epic: str) -> Dict:
        """Get detailed market information for a specific instrument"""
        endpoint = f"{self.base_url}/api/v1/markets/{epic}"
        
        response = requests.get(
            endpoint,
            headers=self._headers()
        )
        
        return response.json() if response.status_code == 200 else None
