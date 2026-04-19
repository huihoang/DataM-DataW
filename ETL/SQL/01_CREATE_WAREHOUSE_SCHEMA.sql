-- ============================================================================
-- DATA WAREHOUSE - FRAUD DETECTION
-- Star Schema Design with 4 Dimensions + 1 Fact Table
-- ============================================================================

-- ============================================================================
-- STAGING TABLE
-- ============================================================================

-- FRAUD_DATA: Staging table for raw transaction data
CREATE TABLE fraud_data (
    trans_num VARCHAR(50) PRIMARY KEY,
    trans_date_trans_time TIMESTAMP,
    cc_num BIGINT,
    merchant VARCHAR(255),
    category VARCHAR(100),
    amt DECIMAL(10, 2),
    first VARCHAR(100),
    last VARCHAR(100),
    gender CHAR(1),
    street VARCHAR(255),
    city VARCHAR(100),
    state VARCHAR(50),
    zip VARCHAR(10),
    lat DECIMAL(10, 6),
    long DECIMAL(10, 6),
    city_pop INT,
    job VARCHAR(255),
    dob DATE,
    unix_time INT,
    merch_lat DECIMAL(10, 6),
    merch_long DECIMAL(10, 6),
    is_fraud INT,
    data_split VARCHAR(10),
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- DIMENSION TABLES
-- ============================================================================

-- DIM_CUSTOMER: Cardholder Profile (1.3M unique)
CREATE TABLE dim_customer (
    customer_id SERIAL PRIMARY KEY,
    cc_num BIGINT UNIQUE NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    gender CHAR(1),
    dob DATE,
    job VARCHAR(255),
    street VARCHAR(255),
    city VARCHAR(100),
    state VARCHAR(50),
    zip VARCHAR(10),
    lat DECIMAL(10, 6),
    long DECIMAL(10, 6),
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- DIM_MERCHANT: Merchant/Shop Information (3.6K unique)
CREATE TABLE dim_merchant (
    merchant_id SERIAL PRIMARY KEY,
    merchant_name VARCHAR(255) UNIQUE NOT NULL,
    merchant_category VARCHAR(100),
    merch_lat DECIMAL(10, 6),
    merch_long DECIMAL(10, 6),
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- DIM_LOCATION: Geographic Location (50K unique)
CREATE TABLE dim_location (
    location_id SERIAL PRIMARY KEY,
    city VARCHAR(100),
    state VARCHAR(50),
    zip VARCHAR(10),
    lat DECIMAL(10, 6),
    long DECIMAL(10, 6),
    city_pop INT,
    location_key VARCHAR(50) UNIQUE,
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- DIM_TIME: Time Dimension (8.76K hourly: 365 days * 24 hours)
CREATE TABLE dim_time (
    time_id SERIAL PRIMARY KEY,
    trans_date_trans_time TIMESTAMP UNIQUE NOT NULL,
    hour INT,
    day_of_week INT,
    day_of_week_name VARCHAR(20),
    month INT,
    month_name VARCHAR(20),
    year INT,
    is_weekend BOOLEAN,
    quarter INT,
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- FACT TABLE
-- ============================================================================

-- FACT_TRANSACTIONS: Main Fact Table (1.9M rows)
CREATE TABLE fact_transactions (
    transaction_id BIGSERIAL PRIMARY KEY,
    trans_num VARCHAR(50) UNIQUE NOT NULL,
    customer_id INT NOT NULL,
    merchant_id INT NOT NULL,
    location_id INT NOT NULL,
    time_id INT NOT NULL,

-- Measures
amount DECIMAL(10, 2),

-- Fraud Indicators
is_fraud INT, fraud_probability DECIMAL(5, 4),

-- Metadata
data_split VARCHAR(10),
created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

-- Foreign Keys
FOREIGN KEY (customer_id) REFERENCES dim_customer(customer_id),
    FOREIGN KEY (merchant_id) REFERENCES dim_merchant(merchant_id),
    FOREIGN KEY (location_id) REFERENCES dim_location(location_id),
    FOREIGN KEY (time_id) REFERENCES dim_time(time_id)
);

-- ============================================================================
-- INDEXES
-- ============================================================================

-- Fact table indexes
CREATE INDEX idx_fact_customer ON fact_transactions (customer_id);

CREATE INDEX idx_fact_merchant ON fact_transactions (merchant_id);

CREATE INDEX idx_fact_location ON fact_transactions (location_id);

CREATE INDEX idx_fact_time ON fact_transactions (time_id);

CREATE INDEX idx_fact_fraud ON fact_transactions (is_fraud);

CREATE INDEX idx_fact_trans_num ON fact_transactions (trans_num);

CREATE INDEX idx_fact_data_split ON fact_transactions (data_split);

-- Dimension table indexes
CREATE INDEX idx_dim_customer_cc_num ON dim_customer (cc_num);

CREATE INDEX idx_dim_customer_state ON dim_customer (state);

CREATE INDEX idx_dim_merchant_name ON dim_merchant (merchant_name);

CREATE INDEX idx_dim_merchant_category ON dim_merchant (merchant_category);

CREATE INDEX idx_dim_location_city_state ON dim_location (city, state);

CREATE INDEX idx_dim_time_hour ON dim_time (hour);

CREATE INDEX idx_dim_time_month ON dim_time (month);

CREATE INDEX idx_dim_time_is_weekend ON dim_time (is_weekend);

-- ============================================================================
-- VIEWS FOR ANALYSIS
-- ============================================================================

-- VW_FRAUD_BY_MERCHANT: Fraud analysis by merchant
CREATE OR REPLACE VIEW vw_fraud_by_merchant AS
SELECT
    dm.merchant_id,
    dm.merchant_name,
    dm.merchant_category,
    COUNT(*) as total_transactions,
    SUM(
        CASE
            WHEN ft.is_fraud = 1 THEN 1
            ELSE 0
        END
    ) as fraud_count,
    ROUND(
        SUM(
            CASE
                WHEN ft.is_fraud = 1 THEN 1
                ELSE 0
            END
        ) * 100.0 / COUNT(*),
        4
    ) as fraud_rate,
    SUM(ft.amount) as total_amount,
    ROUND(AVG(ft.amount), 2) as avg_amount,
    COUNT(DISTINCT ft.customer_id) as unique_customers
FROM
    fact_transactions ft
    JOIN dim_merchant dm ON ft.merchant_id = dm.merchant_id
GROUP BY
    dm.merchant_id,
    dm.merchant_name,
    dm.merchant_category
ORDER BY fraud_count DESC;

-- VW_FRAUD_BY_LOCATION: Fraud analysis by location
CREATE OR REPLACE VIEW vw_fraud_by_location AS
SELECT
    dl.location_id,
    dl.city,
    dl.state,
    dl.zip,
    COUNT(*) as total_transactions,
    SUM(
        CASE
            WHEN ft.is_fraud = 1 THEN 1
            ELSE 0
        END
    ) as fraud_count,
    ROUND(
        SUM(
            CASE
                WHEN ft.is_fraud = 1 THEN 1
                ELSE 0
            END
        ) * 100.0 / COUNT(*),
        4
    ) as fraud_rate,
    SUM(ft.amount) as total_amount,
    dl.city_pop
FROM
    fact_transactions ft
    JOIN dim_location dl ON ft.location_id = dl.location_id
GROUP BY
    dl.location_id,
    dl.city,
    dl.state,
    dl.zip,
    dl.city_pop
ORDER BY fraud_count DESC;

-- VW_FRAUD_BY_CUSTOMER: Fraud analysis by customer
CREATE OR REPLACE VIEW vw_fraud_by_customer AS
SELECT
    dc.customer_id,
    dc.first_name,
    dc.last_name,
    dc.state,
    COUNT(*) as transaction_count,
    SUM(
        CASE
            WHEN ft.is_fraud = 1 THEN 1
            ELSE 0
        END
    ) as fraud_count,
    ROUND(
        SUM(
            CASE
                WHEN ft.is_fraud = 1 THEN 1
                ELSE 0
            END
        ) * 100.0 / COUNT(*),
        4
    ) as fraud_rate,
    ROUND(AVG(ft.amount), 2) as avg_amount,
    MAX(ft.fraud_probability) as max_fraud_prob
FROM
    fact_transactions ft
    JOIN dim_customer dc ON ft.customer_id = dc.customer_id
GROUP BY
    dc.customer_id,
    dc.first_name,
    dc.last_name,
    dc.state
HAVING
    SUM(
        CASE
            WHEN ft.is_fraud = 1 THEN 1
            ELSE 0
        END
    ) > 0
ORDER BY fraud_count DESC;

-- VW_FRAUD_BY_TIME: Fraud analysis by time/hour
CREATE OR REPLACE VIEW vw_fraud_by_time AS
SELECT
    dt.time_id,
    dt.trans_date_trans_time,
    dt.hour,
    dt.day_of_week_name,
    dt.month,
    COUNT(*) as total_transactions,
    SUM(
        CASE
            WHEN ft.is_fraud = 1 THEN 1
            ELSE 0
        END
    ) as fraud_count,
    ROUND(
        SUM(
            CASE
                WHEN ft.is_fraud = 1 THEN 1
                ELSE 0
            END
        ) * 100.0 / COUNT(*),
        4
    ) as fraud_rate,
    ROUND(AVG(ft.amount), 2) as avg_amount,
    dt.is_weekend
FROM
    fact_transactions ft
    JOIN dim_time dt ON ft.time_id = dt.time_id
GROUP BY
    dt.time_id,
    dt.trans_date_trans_time,
    dt.hour,
    dt.day_of_week_name,
    dt.month,
    dt.is_weekend
ORDER BY fraud_count DESC;

-- VW_FRAUD_SUMMARY: Overall fraud summary statistics
CREATE OR REPLACE VIEW vw_fraud_summary AS
SELECT
    COUNT(*) as total_transactions,
    SUM(
        CASE
            WHEN is_fraud = 1 THEN 1
            ELSE 0
        END
    ) as total_fraud_count,
    ROUND(
        SUM(
            CASE
                WHEN is_fraud = 1 THEN 1
                ELSE 0
            END
        ) * 100.0 / COUNT(*),
        4
    ) as overall_fraud_rate,
    SUM(amount) as total_amount,
    ROUND(AVG(amount), 2) as avg_amount,
    ROUND(MAX(amount), 2) as max_amount,
    COUNT(DISTINCT customer_id) as unique_customers,
    COUNT(DISTINCT merchant_id) as unique_merchants,
    COUNT(DISTINCT location_id) as unique_locations
FROM fact_transactions;