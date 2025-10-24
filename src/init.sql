-- Initialize dYdX Trading Service Database

-- Create users table
CREATE TABLE IF NOT EXISTS users (
    wallet_address VARCHAR(42) PRIMARY KEY,
    webhook_uuid VARCHAR(36) UNIQUE NOT NULL,
    encrypted_webhook_secret VARCHAR(500),
    encrypted_dydx_mnemonic VARCHAR(500),
    encrypted_telegram_token VARCHAR(500),
    encrypted_telegram_chat_id VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create positions table
CREATE TABLE IF NOT EXISTS positions (
    id SERIAL PRIMARY KEY,
    user_address VARCHAR(42) REFERENCES users(wallet_address) ON DELETE CASCADE,
    symbol VARCHAR(20) NOT NULL,
    status VARCHAR(20) DEFAULT 'open',
    entry_price DECIMAL(20,10) NOT NULL,
    size DECIMAL(20,10) NOT NULL,
    dydx_order_id VARCHAR(100),
    tp_order_id VARCHAR(100),
    sl_order_id VARCHAR(100),
    opened_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_users_webhook_uuid ON users(webhook_uuid);
CREATE INDEX IF NOT EXISTS idx_positions_user_address ON positions(user_address);
CREATE INDEX IF NOT EXISTS idx_positions_status ON positions(status);
CREATE INDEX IF NOT EXISTS idx_positions_symbol ON positions(symbol);

-- Insert sample data for testing (optional)
-- INSERT INTO users (wallet_address, webhook_uuid) VALUES
-- ('0x1234567890abcdef', '550e8400-e29b-41d4-a716-446655440000');