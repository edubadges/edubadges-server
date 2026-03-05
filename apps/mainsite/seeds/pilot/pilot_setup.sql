-- Pilot seedbank SQL setup script
-- This is a placeholder with dummy commands

-- Dummy command 1: Create a test table (if not exists)
CREATE TABLE IF NOT EXISTS pilot_test_table (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Dummy command 2: Insert test data
INSERT INTO pilot_test_table (name)
VALUES ('Pilot seedbank initialized')
ON CONFLICT (id) DO NOTHING;
