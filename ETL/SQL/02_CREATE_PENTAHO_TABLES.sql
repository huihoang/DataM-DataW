-- ============================================================
-- Pentaho ETL Pipeline: Create Tables
-- Database: fraud_detection_dw
-- ============================================================

-- 1. STAGING TABLE
CREATE TABLE IF NOT EXISTS fraud_data (
    trans_num BIGINT PRIMARY KEY,
    trans_date_trans_time TIMESTAMP,
    cc_num BIGINT,
    merchant VARCHAR(100),
    category VARCHAR(50),
    amt DECIMAL(10, 2),
    first VARCHAR(50),
    last VARCHAR(50),
    gender VARCHAR(1),
    dob DATE,
    job VARCHAR(100),
    street VARCHAR(100),
    city VARCHAR(50),
    state VARCHAR(2),
    zip INT,
    lat DECIMAL(10, 8),
    long DECIMAL(11, 8),
    city_pop INT,
    merch_lat DECIMAL(10, 8),
    merch_long DECIMAL(11, 8),
    is_fraud INT DEFAULT 0,
    data_split VARCHAR(10),
    created_date TIMESTAMP DEFAULT NOW(),
    updated_date TIMESTAMP DEFAULT NOW()
);

-- 2. DIMENSION: CUSTOMER
CREATE TABLE IF NOT EXISTS dim_customer (
    customer_id SERIAL PRIMARY KEY,
    cc_num BIGINT UNIQUE NOT NULL,
    first_name VARCHAR(50),
    last_name VARCHAR(50),
    gender VARCHAR(1),
    dob DATE,
    job VARCHAR(100),
    street VARCHAR(100),
    city VARCHAR(50),
    state VARCHAR(2),
    zip VARCHAR(10),
    lat DECIMAL(10, 8),
    long DECIMAL(11, 8),
    created_date TIMESTAMP DEFAULT NOW(),
    updated_date TIMESTAMP DEFAULT NOW()
);

-- 3. DIMENSION: MERCHANT
CREATE TABLE IF NOT EXISTS dim_merchant (
    merchant_id SERIAL PRIMARY KEY,
    merchant_name VARCHAR(100) UNIQUE NOT NULL,
    merchant_category VARCHAR(50),
    merch_lat DECIMAL(10, 8),
    merch_long DECIMAL(11, 8),
    created_date TIMESTAMP DEFAULT NOW(),
    updated_date TIMESTAMP DEFAULT NOW()
);

-- 4. DIMENSION: LOCATION
CREATE TABLE IF NOT EXISTS dim_location (
    location_id SERIAL PRIMARY KEY,
    city VARCHAR(50),
    state VARCHAR(2),
    zip VARCHAR(10),
    lat DECIMAL(10, 8),
    long DECIMAL(11, 8),
    city_pop INT,
    location_key VARCHAR(100),
    created_date TIMESTAMP DEFAULT NOW(),
    updated_date TIMESTAMP DEFAULT NOW(),
    UNIQUE (city, state, zip)
);

-- 5. DIMENSION: TIME
CREATE TABLE IF NOT EXISTS dim_time (
    time_id SERIAL PRIMARY KEY,
    trans_date_trans_time TIMESTAMP,
    trans_hour TIMESTAMP,
    hour INT,
    day_of_week INT,
    day_of_week_name VARCHAR(20),
    month INT,
    month_name VARCHAR(20),
    year INT,
    is_weekend INT DEFAULT 0,
    quarter INT,
    created_date TIMESTAMP DEFAULT NOW(),
    UNIQUE (trans_date_trans_time)
);

-- 6. FACT: TRANSACTIONS
CREATE TABLE IF NOT EXISTS fact_transactions (
    transaction_id SERIAL PRIMARY KEY,
    trans_num BIGINT UNIQUE NOT NULL,
    customer_id INT,
    merchant_id INT,
    location_id INT,
    time_id INT,
    amount DECIMAL(10, 2),
    is_fraud INT DEFAULT 0,
    data_split VARCHAR(10),
    fraud_probability DECIMAL(5, 4) DEFAULT 0.0,
    created_date TIMESTAMP DEFAULT NOW(),
    FOREIGN KEY (customer_id) REFERENCES dim_customer (customer_id),
    FOREIGN KEY (merchant_id) REFERENCES dim_merchant (merchant_id),
    FOREIGN KEY (location_id) REFERENCES dim_location (location_id),
    FOREIGN KEY (time_id) REFERENCES dim_time (time_id)
);

-- Create indexes for performance
CREATE INDEX idx_fraud_data_cc_num ON fraud_data (cc_num);

CREATE INDEX idx_fraud_data_merchant ON fraud_data (merchant);

CREATE INDEX idx_fraud_data_city_state ON fraud_data (city, state, zip);

CREATE INDEX idx_dim_customer_cc ON dim_customer (cc_num);

CREATE INDEX idx_dim_merchant_name ON dim_merchant (merchant_name);

CREATE INDEX idx_dim_location_key ON dim_location (city, state, zip);

CREATE INDEX idx_dim_time_hour ON dim_time (trans_hour);

CREATE INDEX idx_fact_customer ON fact_transactions (customer_id);

CREATE INDEX idx_fact_merchant ON fact_transactions (merchant_id);

CREATE INDEX idx_fact_location ON fact_transactions (location_id);

CREATE INDEX idx_fact_time ON fact_transactions (time_id);

-- Grant permissions
GRANT
SELECT,
INSERT
,
UPDATE,
DELETE ON ALL TABLES IN SCHEMA public TO whuser;

COMMIT;