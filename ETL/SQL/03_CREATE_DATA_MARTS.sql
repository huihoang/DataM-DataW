-- ============================================================================
-- DATA MARTS - MATERIALIZED TABLES
-- Aggregated tables for specific business needs
-- ============================================================================

-- ============================================================================
-- 1. DATA MART: MERCHANT FRAUD ANALYSIS
-- Purpose: Track fraud by merchant, category, and risk profile
-- ============================================================================

DROP TABLE IF EXISTS dm_merchant_fraud CASCADE;

CREATE TABLE dm_merchant_fraud AS
SELECT 
    m.merchant_id,
    m.merchant_name,
    m.merchant_category,
    m.merch_lat,
    m.merch_long,
    COUNT(*) as total_transactions,
    COUNT(CASE WHEN f.is_fraud = 1 THEN 1 END) as fraud_count,
    ROUND(COUNT(CASE WHEN f.is_fraud = 1 THEN 1 END)::NUMERIC / COUNT(*)::NUMERIC * 100, 2) as fraud_rate_pct,
    ROUND(SUM(f.amount), 2) as total_amount,
    ROUND(SUM(CASE WHEN f.is_fraud = 1 THEN f.amount ELSE 0 END), 2) as fraud_amount,
    ROUND(AVG(f.amount), 2) as avg_transaction_amount,
    MIN(f.amount) as min_transaction_amount,
    MAX(f.amount) as max_transaction_amount,
    COUNT(DISTINCT f.customer_id) as unique_customers,
    COUNT(DISTINCT f.time_id) as unique_timestamps,
    ROUND(AVG(CASE WHEN f.is_fraud = 1 THEN f.amount END), 2) as avg_fraud_amount
FROM fact_transactions f
INNER JOIN dim_merchant m ON f.merchant_id = m.merchant_id
GROUP BY m.merchant_id, m.merchant_name, m.merchant_category, m.merch_lat, m.merch_long;

CREATE INDEX idx_dm_merchant_fraud_rate ON dm_merchant_fraud (fraud_rate_pct DESC);

CREATE INDEX idx_dm_merchant_fraud_amount ON dm_merchant_fraud (fraud_amount DESC);

-- ============================================================================
-- 2. DATA MART: LOCATION RISK PROFILE
-- Purpose: Geographic analysis of fraud patterns
-- ============================================================================

DROP TABLE IF EXISTS dm_location_fraud CASCADE;

CREATE TABLE dm_location_fraud AS
SELECT 
    l.location_id,
    l.city,
    l.state,
    l.zip,
    l.lat,
    l.long,
    l.city_pop,
    COUNT(*) as total_transactions,
    COUNT(CASE WHEN f.is_fraud = 1 THEN 1 END) as fraud_count,
    ROUND(COUNT(CASE WHEN f.is_fraud = 1 THEN 1 END)::NUMERIC / COUNT(*)::NUMERIC * 100, 2) as fraud_rate_pct,
    ROUND(SUM(f.amount), 2) as total_amount,
    ROUND(SUM(CASE WHEN f.is_fraud = 1 THEN f.amount ELSE 0 END), 2) as fraud_amount,
    ROUND(AVG(f.amount), 2) as avg_transaction_amount,
    COUNT(DISTINCT f.customer_id) as unique_customers,
    COUNT(DISTINCT f.merchant_id) as unique_merchants,
    ROUND(l.city_pop::NUMERIC / COUNT(*)::NUMERIC, 2) as transactions_per_capita
FROM fact_transactions f
INNER JOIN dim_location l ON f.location_id = l.location_id
GROUP BY l.location_id, l.city, l.state, l.zip, l.lat, l.long, l.city_pop;

CREATE INDEX idx_dm_location_fraud_rate ON dm_location_fraud (fraud_rate_pct DESC);

CREATE INDEX idx_dm_location_fraud_state ON dm_location_fraud (state);

-- ============================================================================
-- 3. DATA MART: CUSTOMER RISK PROFILE
-- Purpose: Identify high-risk customers and their behavior
-- ============================================================================

DROP TABLE IF EXISTS dm_customer_risk CASCADE;

CREATE TABLE dm_customer_risk AS
SELECT 
    c.customer_id,
    c.first_name,
    c.last_name,
    c.gender,
    c.state,
    c.job,
    COUNT(*) as total_transactions,
    COUNT(CASE WHEN f.is_fraud = 1 THEN 1 END) as fraud_count,
    ROUND(COUNT(CASE WHEN f.is_fraud = 1 THEN 1 END)::NUMERIC / COUNT(*)::NUMERIC * 100, 2) as fraud_rate_pct,
    ROUND(SUM(f.amount), 2) as total_spent,
    ROUND(SUM(CASE WHEN f.is_fraud = 1 THEN f.amount ELSE 0 END), 2) as fraud_amount,
    ROUND(AVG(f.amount), 2) as avg_transaction_amount,
    MIN(f.amount) as min_transaction_amount,
    MAX(f.amount) as max_transaction_amount,
    COUNT(DISTINCT f.merchant_id) as unique_merchants_visited,
    COUNT(DISTINCT f.location_id) as unique_locations,
    COUNT(DISTINCT f.time_id) as unique_transaction_times,
    ROUND(AVG(EXTRACT(HOUR FROM t.trans_date_trans_time))::NUMERIC, 2) as avg_transaction_hour
FROM fact_transactions f
INNER JOIN dim_customer c ON f.customer_id = c.customer_id
INNER JOIN dim_time t ON f.time_id = t.time_id
GROUP BY c.customer_id, c.first_name, c.last_name, c.gender, c.state, c.job;

CREATE INDEX idx_dm_customer_risk_fraud_rate ON dm_customer_risk (fraud_rate_pct DESC);

CREATE INDEX idx_dm_customer_risk_fraud_amount ON dm_customer_risk (fraud_amount DESC);

CREATE INDEX idx_dm_customer_risk_state ON dm_customer_risk (state);

-- ============================================================================
-- 4. DATA MART: TEMPORAL FRAUD PATTERNS
-- Purpose: Analyze fraud trends over time
-- ============================================================================

DROP TABLE IF EXISTS dm_time_fraud CASCADE;

CREATE TABLE dm_time_fraud AS
SELECT 
    t.time_id,
    t.trans_date_trans_time,
    t.hour,
    t.day_of_week,
    t.day_of_week_name,
    t.month,
    t.month_name,
    t.year,
    t.is_weekend,
    t.quarter,
    COUNT(*) as total_transactions,
    COUNT(CASE WHEN f.is_fraud = 1 THEN 1 END) as fraud_count,
    ROUND(COUNT(CASE WHEN f.is_fraud = 1 THEN 1 END)::NUMERIC / COUNT(*)::NUMERIC * 100, 2) as fraud_rate_pct,
    ROUND(SUM(f.amount), 2) as total_amount,
    ROUND(SUM(CASE WHEN f.is_fraud = 1 THEN f.amount ELSE 0 END), 2) as fraud_amount,
    ROUND(AVG(f.amount), 2) as avg_transaction_amount,
    COUNT(DISTINCT f.customer_id) as unique_customers,
    COUNT(DISTINCT f.merchant_id) as unique_merchants,
    COUNT(DISTINCT f.location_id) as unique_locations
FROM fact_transactions f
INNER JOIN dim_time t ON f.time_id = t.time_id
GROUP BY t.time_id, t.trans_date_trans_time, t.hour, t.day_of_week, t.day_of_week_name,
         t.month, t.month_name, t.year, t.is_weekend, t.quarter;

CREATE INDEX idx_dm_time_fraud_hour ON dm_time_fraud (hour);

CREATE INDEX idx_dm_time_fraud_day ON dm_time_fraud (day_of_week);

CREATE INDEX idx_dm_time_fraud_rate ON dm_time_fraud (fraud_rate_pct DESC);

-- ============================================================================
-- 5. DATA MART: FRAUD SUMMARY DASHBOARD
-- Purpose: Executive summary of all fraud metrics
-- ============================================================================

DROP TABLE IF EXISTS dm_fraud_summary CASCADE;

CREATE TABLE dm_fraud_summary AS
SELECT 
    'All' as dimension,
    'All' as dimension_value,
    COUNT(*) as total_transactions,
    COUNT(CASE WHEN is_fraud = 1 THEN 1 END) as fraud_count,
    ROUND(COUNT(CASE WHEN is_fraud = 1 THEN 1 END)::NUMERIC / COUNT(*)::NUMERIC * 100, 2) as fraud_rate_pct,
    ROUND(SUM(amount), 2) as total_amount,
    ROUND(SUM(CASE WHEN is_fraud = 1 THEN amount ELSE 0 END), 2) as fraud_amount,
    ROUND(AVG(amount), 2) as avg_transaction_amount,
    COUNT(DISTINCT customer_id) as unique_customers,
    COUNT(DISTINCT merchant_id) as unique_merchants,
    COUNT(DISTINCT location_id) as unique_locations,
    MAX(amount) as max_transaction_amount,
    MIN(amount) as min_transaction_amount,
    COUNT(DISTINCT time_id) as unique_timestamps
FROM fact_transactions;

-- ============================================================================
-- REFRESH STRATEGY (for future updates)
-- ============================================================================

-- Note: To refresh data marts with new data, run:
-- DROP TABLE dm_merchant_fraud; CREATE TABLE dm_merchant_fraud AS ... (see above)
--
-- For production, consider using materialized views with REFRESH:
-- CREATE MATERIALIZED VIEW dm_merchant_fraud AS ... (same query above)
-- REFRESH MATERIALIZED VIEW dm_merchant_fraud;
--
-- Or trigger automated refresh on fact_transactions updates