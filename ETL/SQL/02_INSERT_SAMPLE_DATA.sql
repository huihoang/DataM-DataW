-- =====================================================
-- FRAUD DETECTION DATA WAREHOUSE
-- Sample Data Insertion for Testing
-- =====================================================

-- ==========================================
-- 1. DIMENSION TABLES - SAMPLE DATA
-- ==========================================

-- Clear existing data (for testing)
TRUNCATE TABLE dim_customer;
TRUNCATE TABLE dim_shop;
TRUNCATE TABLE dim_employee;
TRUNCATE TABLE dim_time;
TRUNCATE TABLE dim_contract;
TRUNCATE TABLE fact_transactions;

-- ========== DIM_CUSTOMER ==========
INSERT INTO dim_customer 
  (customer_id, age, gender, state, age_group, is_customer, created_date, updated_date)
VALUES
  (1001, 25, 'M', 'NY', '18-25', TRUE, NOW(), NOW()),
  (1002, 35, 'F', 'CA', '25-35', TRUE, NOW(), NOW()),
  (1003, 45, 'M', 'TX', '35-50', TRUE, NOW(), NOW()),
  (1004, 55, 'F', 'FL', '50-65', TRUE, NOW(), NOW()),
  (1005, 22, 'M', 'WA', '18-25', TRUE, NOW(), NOW()),
  (1006, 38, 'F', 'IL', '25-35', TRUE, NOW(), NOW()),
  (1007, 48, 'M', 'PA', '35-50', TRUE, NOW(), NOW()),
  (1008, 62, 'F', 'OH', '50-65', TRUE, NOW(), NOW()),
  (1009, 28, 'M', 'GA', '25-35', TRUE, NOW(), NOW()),
  (1010, 41, 'F', 'NC', '35-50', TRUE, NOW(), NOW());

-- ========== DIM_SHOP ==========
INSERT INTO dim_shop 
  (shop_id, shop_category, merchant_avg_amount, merchant_fraud_rate, merchant_trans_count)
VALUES
  (2001, 'GROCERY', 50.00, 0.15, 1500),
  (2002, 'ELECTRONICS', 250.00, 0.08, 800),
  (2003, 'CLOTHING', 80.00, 0.12, 2000),
  (2004, 'RESTAURANT', 45.00, 0.05, 3000),
  (2005, 'GAS_STATION', 55.00, 0.10, 2500),
  (2006, 'PHARMACY', 35.00, 0.03, 1800),
  (2007, 'RETAIL', 120.00, 0.18, 900),
  (2008, 'TRAVEL', 500.00, 0.07, 400),
  (2009, 'ENTERTAINMENT', 75.00, 0.11, 1200),
  (2010, 'HOTEL', 350.00, 0.06, 600);

-- ========== DIM_EMPLOYEE ==========
INSERT INTO dim_employee 
  (employee_id, employee_name, employee_role, department)
VALUES
  (3001, 'John Smith', 'Fraud Analyst', 'Risk Management'),
  (3002, 'Sarah Johnson', 'Senior Analyst', 'Risk Management'),
  (3003, 'Mike Brown', 'Data Specialist', 'Operations'),
  (3004, 'Emily Davis', 'Compliance Officer', 'Compliance'),
  (3005, 'Robert Wilson', 'Manager', 'Risk Management'),
  (3006, 'Lisa Anderson', 'Analyst', 'Risk Management'),
  (3007, 'James Taylor', 'Technical Lead', 'Technology'),
  (3008, 'Patricia Martinez', 'Director', 'Risk Management'),
  (3009, 'David Lee', 'Specialist', 'Operations'),
  (3010, 'Jennifer White', 'Analyst', 'Risk Management');

-- ========== DIM_TIME ==========
-- Insert sample days (sample from 2023)
-- Format: YYYYMMDDHH (e.g., 2023010100 = 2023-01-01 00:00)

INSERT INTO dim_time 
  (time_id, hour, day_of_week, month, year, is_weekend, is_holiday, quarter)
VALUES
  -- 2023-01-02 (Monday - New Years in US)
  (2023010200, 0, 1, 1, 2023, 0, 1, 1),
  (2023010201, 1, 1, 1, 2023, 0, 1, 1),
  (2023010202, 2, 1, 1, 2023, 0, 1, 1),
  (2023010203, 3, 1, 1, 2023, 0, 1, 1),
  (2023010204, 4, 1, 1, 2023, 0, 1, 1),
  
  -- 2023-01-07 (Saturday)
  (2023010700, 0, 6, 1, 2023, 1, 0, 1),
  (2023010701, 1, 6, 1, 2023, 1, 0, 1),
  (2023010702, 2, 6, 1, 2023, 1, 0, 1),
  
  -- 2023-02-14 (Tuesday - Valentine's)
  (2023021400, 0, 2, 2, 2023, 0, 0, 1),
  (2023021401, 1, 2, 2, 2023, 0, 0, 1),
  
  -- 2023-07-04 (Tuesday - Independence Day)
  (2023070400, 0, 2, 7, 2023, 0, 1, 3),
  (2023070401, 1, 2, 7, 2023, 0, 1, 3),
  
  -- 2023-12-25 (Monday - Christmas)
  (2023122500, 0, 1, 12, 2023, 0, 1, 4),
  (2023122501, 1, 1, 12, 2023, 0, 1, 4);

-- ========== DIM_CONTRACT ==========
INSERT INTO dim_contract 
  (contract_id, contract_type, contract_status)
VALUES
  (4001, 'CHECKING', 'ACTIVE'),
  (4002, 'SAVINGS', 'ACTIVE'),
  (4003, 'CREDIT_CARD', 'ACTIVE'),
  (4004, 'LOAN', 'ACTIVE'),
  (4005, 'INVESTMENT', 'ACTIVE'),
  (4006, 'CHECKING', 'INACTIVE'),
  (4007, 'SAVINGS', 'ACTIVE'),
  (4008, 'CREDIT_CARD', 'DEFAULTED'),
  (4009, 'CHECKING', 'ACTIVE'),
  (4010, 'SAVINGS', 'FROZEN');

-- ==========================================
-- 2. FACT TABLE - SAMPLE DATA
-- ==========================================

-- Normal transactions (fraud=0)
INSERT INTO fact_transactions 
  (transaction_id, customer_id, shop_id, employee_id, contract_id, time_id,
   amount, amount_log, distance_km, fraud_dist_percentile, 
   amt_x_distance, is_fraud, fraud_probability,
   trans_count_hourly, trans_count_daily, time_since_last_trans,
   transaction_date, created_date, updated_date)
VALUES
  -- Customer 1001 - Normal transactions
  (5001, 1001, 2001, 3001, 4001, 2023010200, 45.50, 3.82, 2.5, 0.25,
   113.75, FALSE, 0.05,
   2, 15, 3600, '2023-01-02 00:15:00', NOW(), NOW()),
   
  (5002, 1001, 2003, 3003, 4003, 2023010201, 75.00, 4.32, 5.0, 0.35,
   375.00, FALSE, 0.08,
   1, 15, 2100, '2023-01-02 01:10:00', NOW(), NOW()),
   
  -- Customer 1002 - Normal transactions
  (5003, 1002, 2002, 3005, 4004, 2023010202, 250.00, 5.52, 1.2, 0.10,
   300.00, FALSE, 0.03,
   3, 8, 1800, '2023-01-02 02:30:00', NOW(), NOW()),
   
  (5004, 1002, 2004, 3002, 4002, 2023010203, 42.75, 3.76, 3.2, 0.28,
   136.80, FALSE, 0.06,
   2, 8, 2700, '2023-01-02 03:45:00', NOW(), NOW()),
   
  -- Customer 1003 - Normal transactions
  (5005, 1003, 2005, 3007, 4005, 2023010204, 55.00, 4.01, 8.5, 0.62,
   467.50, FALSE, 0.07,
   1, 12, 5400, '2023-01-02 04:20:00', NOW(), NOW()),
   
  (5006, 1003, 2006, 3004, 4001, 2023010700, 32.50, 3.48, 1.8, 0.15,
   58.50, FALSE, 0.02,
   4, 18, 7200, '2023-01-07 00:10:00', NOW(), NOW()),
   
  -- Customer 1004 - Normal transactions
  (5007, 1004, 2007, 3006, 4003, 2023010701, 120.00, 4.79, 12.0, 0.75,
   1440.00, FALSE, 0.10,
   2, 10, 3600, '2023-01-07 01:25:00', NOW(), NOW()),
   
  (5008, 1004, 2008, 3008, 4004, 2023010702, 500.00, 6.21, 50.0, 0.95,
   25000.00, FALSE, 0.15,
   1, 7, 14400, '2023-01-07 02:40:00', NOW(), NOW()),
   
  -- ============ FRAUDULENT TRANSACTIONS ==========
  
  -- Customer 1005 - Unusual transaction (unusual distance)
  (5009, 1005, 2001, 3001, 4001, 2023021400, 450.00, 6.11, 1500.0, 0.99,
   675000.00, TRUE, 0.85,
   1, 3, 86400, '2023-02-14 00:30:00', NOW(), NOW()),
   
  -- Customer 1006 - Multiple rapid transactions
  (5010, 1006, 2009, 3003, 4005, 2023021401, 89.99, 4.50, 2.0, 0.20,
   179.98, TRUE, 0.75,
   12, 45, 10, '2023-02-14 01:15:00', NOW(), NOW()),
   
  -- Customer 1007 - Large amount unusual for category
  (5011, 1007, 2006, 3005, 4002, 2023070400, 999.99, 6.91, 0.5, 0.05,
   500.00, TRUE, 0.92,
   5, 22, 300, '2023-07-04 00:20:00', NOW(), NOW()),
   
  -- Customer 1008 - Transaction far from home (high distance percentile)
  (5012, 1008, 2004, 3002, 4003, 2023070401, 78.50, 4.36, 2000.0, 0.98,
   157000.00, TRUE, 0.88,
   2, 6, 18000, '2023-07-04 01:10:00', NOW(), NOW());

-- ==========================================
-- 3. VERIFICATION QUERIES
-- ==========================================

-- Count records by table
SELECT 
  'dim_customer' as table_name, COUNT(*) as record_count FROM dim_customer
UNION ALL
SELECT 'dim_shop', COUNT(*) FROM dim_shop
UNION ALL
SELECT 'dim_employee', COUNT(*) FROM dim_employee
UNION ALL
SELECT 'dim_time', COUNT(*) FROM dim_time
UNION ALL
SELECT 'dim_contract', COUNT(*) FROM dim_contract
UNION ALL
SELECT 'fact_transactions', COUNT(*) FROM fact_transactions;

-- ==========================================
-- 4. SAMPLE QUERIES FOR TESTING
-- ==========================================

-- Transaction details with dimensional attributes
SELECT 
  ft.transaction_id,
  dc.customer_id,
  dc.age_group,
  dc.state,
  ds.shop_category,
  ft.amount,
  ft.distance_km,
  ft.is_fraud,
  ROUND(ft.fraud_probability * 100, 2) as fraud_prob_pct,
  ft.transaction_date
FROM fact_transactions ft
JOIN dim_customer dc ON ft.customer_id = dc.customer_id
JOIN dim_shop ds ON ft.shop_id = ds.shop_id
ORDER BY ft.transaction_date DESC;

-- Fraud summary by shop category
SELECT 
  ds.shop_category,
  COUNT(*) as total_transactions,
  SUM(CASE WHEN ft.is_fraud = TRUE THEN 1 ELSE 0 END) as fraud_count,
  ROUND(SUM(CASE WHEN ft.is_fraud = TRUE THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as fraud_rate_pct,
  ROUND(AVG(ft.amount), 2) as avg_amount,
  ROUND(AVG(ft.fraud_probability), 3) as avg_fraud_prob
FROM fact_transactions ft
JOIN dim_shop ds ON ft.shop_id = ds.shop_id
GROUP BY ds.shop_category
ORDER BY fraud_rate_pct DESC;

-- Customer risk profile
SELECT 
  dc.customer_id,
  dc.age_group,
  dc.state,
  COUNT(*) as transaction_count,
  SUM(CASE WHEN ft.is_fraud = TRUE THEN 1 ELSE 0 END) as fraud_count,
  ROUND(SUM(CASE WHEN ft.is_fraud = TRUE THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as fraud_rate_pct,
  ROUND(AVG(ft.amount), 2) as avg_amount,
  MAX(ft.fraud_probability) as max_fraud_prob
FROM fact_transactions ft
JOIN dim_customer dc ON ft.customer_id = dc.customer_id
GROUP BY dc.customer_id, dc.age_group, dc.state
HAVING COUNT(*) > 0
ORDER BY fraud_rate_pct DESC;

-- Time-based fraud analysis
SELECT 
  dt.month,
  dt.day_of_week,
  COUNT(*) as total_trans,
  SUM(CASE WHEN ft.is_fraud = TRUE THEN 1 ELSE 0 END) as fraud_count,
  ROUND(AVG(ft.fraud_probability), 3) as avg_fraud_prob,
  ROUND(AVG(ft.amount), 2) as avg_amount
FROM fact_transactions ft
JOIN dim_time dt ON ft.time_id = dt.time_id
GROUP BY dt.month, dt.day_of_week
ORDER BY dt.month, dt.day_of_week;

-- Referential integrity check - Orphaned transactions
SELECT COUNT(*) as orphaned_customer_fks
FROM fact_transactions
WHERE customer_id NOT IN (SELECT customer_id FROM dim_customer);

SELECT COUNT(*) as orphaned_shop_fks
FROM fact_transactions
WHERE shop_id NOT IN (SELECT shop_id FROM dim_shop);

-- Data quality checks
SELECT 
  'Null customer_id' as check_type,
  COUNT(*) as issue_count
FROM fact_transactions
WHERE customer_id IS NULL
UNION ALL
SELECT 'Null shop_id', COUNT(*) FROM fact_transactions WHERE shop_id IS NULL
UNION ALL
SELECT 'Negative amount', COUNT(*) FROM fact_transactions WHERE amount < 0
UNION ALL
SELECT 'Fraud prob out of range', COUNT(*) FROM fact_transactions WHERE fraud_probability < 0 OR fraud_probability > 1
UNION ALL
SELECT 'Age < 18', COUNT(*) FROM dim_customer WHERE age < 18;

-- ==========================================
-- NOTES
-- ==========================================
/*
This script loads sample data for basic testing:
- 10 customers
- 10 shops
- 10 employees
- 13 time entries (hourly records)
- 10 contracts
- 12 transactions (8 normal, 4 fraudulent)

Expected results:
- Fraud rate: 33.3% (4 fraudulent out of 12 total)
- Average transaction amount: ~$203
- Fraud probability avg: ~0.53 (for fraudulent) vs ~0.06 (for normal)

For production ETL testing:
1. Run this script to populate sample data
2. Run verification queries to ensure data integrity
3. Test ETL transformations against this sample dataset
4. Scale up after confirming data flows correctly
*/
