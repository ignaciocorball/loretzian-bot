from typing import Dict, Any

# Database configuration
DB_CONFIG: Dict[str, Any] = {
    'dbname': 'trading_bot',
    'user': 'postgres',
    'password': 'postgres',
    'host': 'localhost',
    'port': '5432'
}

# Session status constants
SESSION_STATUS = {
    'ACTIVE': 'active',
    'COMPLETED': 'completed',
    'CANCELLED': 'cancelled'
}

# Trade status constants
TRADE_STATUS = {
    'OPEN': 'open',
    'CLOSED': 'closed',
    'CANCELLED': 'cancelled'
}

# Trade type constants
TRADE_TYPE = {
    'BUY': 'buy',
    'SELL': 'sell'
} 