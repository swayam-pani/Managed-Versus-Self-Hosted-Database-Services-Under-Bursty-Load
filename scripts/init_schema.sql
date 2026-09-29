-- Database Initialization Schema for DB Tail-Latency & TCO Study

DROP TABLE IF EXISTS audit_logs CASCADE;
DROP TABLE IF EXISTS transactions CASCADE;
DROP TABLE IF EXISTS accounts CASCADE;

-- Accounts Table (Simulating User Account Balances)
CREATE TABLE accounts (
    id SERIAL PRIMARY KEY,
    account_uuid VARCHAR(64) UNIQUE NOT NULL,
    customer_name VARCHAR(100) NOT NULL,
    balance NUMERIC(12, 2) NOT NULL DEFAULT 1000.00,
    status VARCHAR(20) DEFAULT 'ACTIVE',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Transactions Table (High-frequency Read/Write workload)
CREATE TABLE transactions (
    transaction_id BIGSERIAL PRIMARY KEY,
    sender_id INT REFERENCES accounts(id),
    receiver_id INT REFERENCES accounts(id),
    amount NUMERIC(10, 2) NOT NULL,
    transaction_type VARCHAR(20) NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Audit Logs Table (Append-only write-intensive load)
CREATE TABLE audit_logs (
    log_id BIGSERIAL PRIMARY KEY,
    action VARCHAR(50) NOT NULL,
    details TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Performance Indexes
CREATE INDEX idx_accounts_uuid ON accounts(account_uuid);
CREATE INDEX idx_transactions_sender ON transactions(sender_id);
CREATE INDEX idx_transactions_receiver ON transactions(receiver_id);
CREATE INDEX idx_transactions_timestamp ON transactions(timestamp);

-- Seed Initial Benchmark Data (10,000 baseline accounts)
INSERT INTO accounts (account_uuid, customer_name, balance)
SELECT 
    md5(random()::text || clock_timestamp()::text),
    'Customer_' || i,
    round((random() * 5000 + 100)::numeric, 2)
FROM generate_series(1, 10000) s(i);

VACUUM ANALYZE accounts;
