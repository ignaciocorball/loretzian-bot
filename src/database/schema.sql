-- Trading Bot Database Schema
-- This script creates the necessary tables for tracking trading sessions and operations
-- To execute this script, run: psql -U your_username -d your_database -f schema.sql

-- Drop existing tables if they exist
DROP TABLE IF EXISTS trades;
DROP TABLE IF EXISTS sessions;

-- Create sessions table to track trading sessions
CREATE TABLE sessions (
    session_id SERIAL PRIMARY KEY,
    start_time TIMESTAMP WITH TIME ZONE NOT NULL,
    end_time TIMESTAMP WITH TIME ZONE,
    initial_balance DECIMAL(20, 8) NOT NULL,
    final_balance DECIMAL(20, 8),
    profit_loss DECIMAL(20, 8),
    profit_loss_percentage DECIMAL(10, 4),
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create trades table to track individual trading operations
CREATE TABLE trades (
    trade_id SERIAL PRIMARY KEY,
    session_id INTEGER NOT NULL REFERENCES sessions(session_id),
    symbol VARCHAR(20) NOT NULL,
    type VARCHAR(10) NOT NULL CHECK (type IN ('buy', 'sell')),
    entry_price DECIMAL(20, 8) NOT NULL,
    exit_price DECIMAL(20, 8),
    quantity DECIMAL(20, 8) NOT NULL,
    stop_loss DECIMAL(20, 8),
    take_profit DECIMAL(20, 8),
    profit_loss DECIMAL(20, 8),
    profit_loss_percentage DECIMAL(10, 4),
    entry_time TIMESTAMP WITH TIME ZONE NOT NULL,
    exit_time TIMESTAMP WITH TIME ZONE,
    status VARCHAR(20) NOT NULL DEFAULT 'open',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better query performance
CREATE INDEX idx_sessions_start_time ON sessions(start_time);
CREATE INDEX idx_sessions_status ON sessions(status);
CREATE INDEX idx_trades_session_id ON trades(session_id);
CREATE INDEX idx_trades_symbol ON trades(symbol);
CREATE INDEX idx_trades_entry_time ON trades(entry_time);
CREATE INDEX idx_trades_status ON trades(status);

-- Create function to update the updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers to automatically update the updated_at column
CREATE TRIGGER update_sessions_updated_at
    BEFORE UPDATE ON sessions
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_trades_updated_at
    BEFORE UPDATE ON trades
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Add comments to tables and columns
COMMENT ON TABLE sessions IS 'Stores information about trading sessions';
COMMENT ON TABLE trades IS 'Stores information about individual trades';

COMMENT ON COLUMN sessions.session_id IS 'Unique identifier for the trading session';
COMMENT ON COLUMN sessions.start_time IS 'Timestamp when the session started';
COMMENT ON COLUMN sessions.end_time IS 'Timestamp when the session ended';
COMMENT ON COLUMN sessions.initial_balance IS 'Initial balance at the start of the session';
COMMENT ON COLUMN sessions.final_balance IS 'Final balance at the end of the session';
COMMENT ON COLUMN sessions.profit_loss IS 'Total profit/loss for the session';
COMMENT ON COLUMN sessions.profit_loss_percentage IS 'Percentage of profit/loss for the session';
COMMENT ON COLUMN sessions.status IS 'Current status of the session (active, completed, cancelled)';

COMMENT ON COLUMN trades.trade_id IS 'Unique identifier for the trade';
COMMENT ON COLUMN trades.session_id IS 'Reference to the trading session';
COMMENT ON COLUMN trades.symbol IS 'Trading symbol (e.g., BTC/USDT)';
COMMENT ON COLUMN trades.type IS 'Type of trade (buy or sell)';
COMMENT ON COLUMN trades.entry_price IS 'Price at which the position was opened';
COMMENT ON COLUMN trades.exit_price IS 'Price at which the position was closed';
COMMENT ON COLUMN trades.quantity IS 'Quantity of the asset traded';
COMMENT ON COLUMN trades.stop_loss IS 'Stop loss price';
COMMENT ON COLUMN trades.take_profit IS 'Take profit price';
COMMENT ON COLUMN trades.profit_loss IS 'Profit/loss for this trade';
COMMENT ON COLUMN trades.profit_loss_percentage IS 'Percentage of profit/loss for this trade';
COMMENT ON COLUMN trades.entry_time IS 'Timestamp when the position was opened';
COMMENT ON COLUMN trades.exit_time IS 'Timestamp when the position was closed';
COMMENT ON COLUMN trades.status IS 'Current status of the trade (open, closed, cancelled)'; 