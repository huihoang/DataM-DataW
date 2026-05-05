#!/usr/bin/env python
# coding: utf-8

# # ETL Pipeline: Fraud Detection Data Warehouse
# 
# ## Overview
# This notebook implements the complete ETL (Extract → Transform → Load) pipeline for the fraud detection data warehouse.
# 
# **Architecture:**
# ```
# Phase 1: EXTRACT
# ├─ fraudTrain.csv → fraud_data (staging)
# └─ fraudTest.csv → fraud_data (append)
# 
# Phase 2: TRANSFORM
# ├─ fraud_data → dim_customer (1.3M)
# ├─ fraud_data → dim_merchant (3.6K)
# ├─ fraud_data → dim_location (50K)
# ├─ fraud_data → dim_time (8.76K)
# └─ all dims → fact_transactions (1.9M)
# 
# Phase 3: LOAD
# ├─ vw_fraud_by_merchant
# ├─ vw_fraud_by_location
# ├─ vw_fraud_by_customer
# ├─ vw_fraud_by_time
# └─ vw_fraud_summary
# ```
# 
# **Expected Output:**
# - fraud_data: 1.9M rows (staging)
# - dim_customer: 1.3M rows
# - dim_merchant: 3.6K rows
# - dim_location: 50K rows
# - dim_time: 8.76K rows
# - fact_transactions: 1.9M rows
# - 5 analytical views

# ## Step 1: Setup & Imports

# In[1]:


# Install required packages
import subprocess
import sys

print("Installing required packages...")
packages = ['sqlalchemy', 'pymysql', 'psycopg2-binary', 'pandas', 'numpy']

for package in packages:
    try:
        __import__(package)
        print(f"✓ {package} already installed")
    except ImportError:
        print(f"Installing {package}...")
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', package, '-q'])
        print(f"✓ {package} installed successfully")

print("\n✓ All required packages ready!")


# In[2]:


# Standard imports
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

# Database
from sqlalchemy import create_engine, text, inspect, Column, Integer, String, Float, DateTime, Boolean, DECIMAL
from sqlalchemy.orm import sessionmaker

# Config
import os

print("✓ All imports successful")


# ## Step 2: Database Configuration

# In[ ]:


# ============================================================
# DATABASE CONNECTION
# ============================================================
# Update these values based on your database setup

DB_TYPE = 'postgresql' 
DB_USER = 'dwuser'      
DB_PASSWORD = '123456'  
DB_HOST = 'localhost'  
DB_PORT = 5432        
DB_NAME = 'fraud_detection_dw'  

# Create connection string based on database type
if DB_TYPE == 'mysql':
    # Using PyMySQL driver (pip install pymysql)
    connection_string = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
elif DB_TYPE == 'postgresql':
    connection_string = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
elif DB_TYPE == 'sqlite':
    connection_string = f"sqlite:///{DB_NAME}.db"

# Create SQLAlchemy engine
try:
    engine = create_engine(connection_string, echo=False)
    # Test connection
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1"))
    print(f"✓ Database connection successful: {DB_NAME}")
except Exception as e:
    print(f"✗ Database connection failed: {e}")
    print(f"Connection string: {connection_string}")
    print("\nTroubleshooting:")
    print("1. Ensure database server is running")
    print("2. Check username/password")
    print("3. Verify database exists (create if needed)")
    print("4. For MySQL: pip install pymysql sqlalchemy")
    print("5. For PostgreSQL: pip install psycopg2 sqlalchemy")


# ## Step 3: Create Database Schema

# In[4]:


# Execute the SQL schema creation script
# SQL file is in the SQL subfolder relative to current working directory
sql_schema_file = Path("SQL") / "01_CREATE_WAREHOUSE_SCHEMA.sql"

print(f"Loading SQL schema from: {sql_schema_file.resolve()}")

try:
    with open(sql_schema_file, 'r') as f:
        sql_script = f.read()

    # Split by semicolons and execute each statement
    statements = [s.strip() for s in sql_script.split(';') if s.strip()]

    success_count = 0
    error_count = 0

    for i, stmt in enumerate(statements, 1):
        try:
            # Execute each statement in its OWN transaction
            with engine.begin() as conn:  # Automatically commits/rollbacks
                conn.execute(text(stmt))
            print(f"✓ Statement {i}: OK")
            success_count += 1
        except Exception as e:
            error_msg = str(e)
            # Some errors are expected (e.g., "table already exists", "does not exist")
            if 'already exists' in error_msg.lower() or 'does not exist' in error_msg.lower():
                print(f"⊘ Statement {i}: {error_msg[:80]} (expected)")
            else:
                print(f"✗ Statement {i}: {error_msg[:100]}")
                error_count += 1

    print(f"\n✓ Schema processing completed")
    print(f"  ✓ Successful: {success_count}")
    print(f"  ✗ Failed: {error_count}")
    print(f"  Total: {len(statements)} statements")

except Exception as e:
    print(f"✗ Error reading or executing schema: {e}")
    print(f"\nTroubleshooting:")
    print(f"  Current working directory: {Path.cwd()}")
    print(f"  SQL file expected at: {Path('SQL').resolve() / '01_CREATE_WAREHOUSE_SCHEMA.sql'}")


# ## Phase 1: EXTRACT - Load Raw Data

# In[5]:


# ============================================================
# Prepare dataset files + chunked ETL settings
# ============================================================

import shutil
import subprocess

# Use relative path - data folder is at parent level
data_dir = Path("..") / "data"
data_dir.mkdir(parents=True, exist_ok=True)
train_file = data_dir / "fraudTrain.csv"
test_file = data_dir / "fraudTest.csv"
KAGGLE_DATASET = "kartik2112/fraud-detection"
CSV_CHUNK_SIZE = 10_000


def ensure_dataset_files(train_path: Path, test_path: Path) -> None:
    if train_path.exists() and test_path.exists():
        return

    print("Dataset not found locally. Attempting download...")

    # 1) Try kagglehub first
    try:
        import kagglehub

        downloaded_dir = Path(kagglehub.dataset_download(KAGGLE_DATASET))
        for name in ["fraudTrain.csv", "fraudTest.csv"]:
            src = downloaded_dir / name
            dst = data_dir / name
            if not src.exists():
                raise FileNotFoundError(f"Missing {name} in kagglehub directory: {downloaded_dir}")
            if not dst.exists():
                shutil.copy2(src, dst)
        print(f"✓ Downloaded via kagglehub to: {data_dir.resolve()}")
        return
    except Exception as e:
        print(f"[Info] kagglehub download failed: {e}")

    # 2) Fallback to kaggle CLI
    if shutil.which("kaggle"):
        try:
            cmd = [
                "kaggle", "datasets", "download",
                "-d", KAGGLE_DATASET,
                "-p", str(data_dir),
                "--unzip",
            ]
            subprocess.run(cmd, check=True)
            if train_path.exists() and test_path.exists():
                print(f"✓ Downloaded via kaggle CLI to: {data_dir.resolve()}")
                return
        except Exception as e:
            print(f"[Info] kaggle CLI download failed: {e}")

    raise FileNotFoundError(
        "Could not find/download fraudTrain.csv and fraudTest.csv. "
        "Please put them into Source/data or configure Kaggle credentials."
    )


ensure_dataset_files(train_file, test_file)

print(f"Train CSV: {train_file.resolve()}")
print(f"Test CSV:  {test_file.resolve()}")
print(f"CSV chunk size: {CSV_CHUNK_SIZE:,}")

# Light preview only (avoid OOM)
preview_train = pd.read_csv(train_file, nrows=1, low_memory=False)
print(f"Train columns: {list(preview_train.columns)}")
print("\nFirst row preview (train):")
print(preview_train)


# In[6]:


# ============================================================
# Preview fraudTest.csv (lightweight)
# ============================================================

print(f"Loading fraudTest.csv preview from: {test_file.resolve()}")
preview_test = pd.read_csv(test_file, nrows=3, low_memory=False)
preview_test['data_split'] = 'test'
preview_test['created_date'] = datetime.now()

print(f"Preview rows: {preview_test.shape[0]}")
print(f"\nData split preview:")
print(preview_test[['trans_num', 'data_split']].head(3))


# In[7]:


# ============================================================
# Plan chunked load to fraud_data (Staging Table)
# ============================================================

print("Chunked ETL mode enabled (avoid loading full CSV into RAM).")
print(f"Train file: {train_file.name}")
print(f"Test file:  {test_file.name}")
print(f"Chunk size: {CSV_CHUNK_SIZE:,}")
print("Rows will be loaded chunk-by-chunk to table `fraud_data`.")


# In[8]:


# Load to database in chunks (train -> replace, test -> append)
print("Loading to fraud_data table in chunks...")

import gc


def load_csv_in_chunks_to_sql(csv_path: Path, split_label: str, if_exists_mode: str) -> tuple[int, int]:
    total_rows = 0
    chunk_count = 0

    for chunk in pd.read_csv(csv_path, chunksize=CSV_CHUNK_SIZE, low_memory=False):
        chunk['data_split'] = split_label
        chunk['created_date'] = datetime.now()
        chunk = chunk.drop_duplicates(subset=['trans_num'])

        chunk.to_sql(
            'fraud_data',
            con=engine,
            if_exists=if_exists_mode if chunk_count == 0 else 'append',
            index=False,
            chunksize=10000,
            method='multi',
        )

        loaded_rows = len(chunk)
        total_rows += loaded_rows
        chunk_count += 1
        print(f"  [{split_label}] chunk {chunk_count}: +{loaded_rows:,} rows (total {total_rows:,})")

        # Free memory aggressively after each chunk
        del chunk
        gc.collect()

    return total_rows, chunk_count


try:
    train_rows, train_chunks = load_csv_in_chunks_to_sql(train_file, 'train', 'replace')
    test_rows, test_chunks = load_csv_in_chunks_to_sql(test_file, 'test', 'append')

    with engine.connect() as conn:
        total_count = conn.execute(text("SELECT COUNT(*) FROM fraud_data")).scalar()
        split_result = conn.execute(
            text("SELECT data_split, COUNT(*) AS cnt FROM fraud_data GROUP BY data_split ORDER BY data_split")
        ).fetchall()
        dup_count = conn.execute(
            text("SELECT COUNT(*) - COUNT(DISTINCT trans_num) FROM fraud_data")
        ).scalar()

    print(f"\n✓ Chunked load completed")
    print(f"  Train: {train_rows:,} rows across {train_chunks} chunks")
    print(f"  Test:  {test_rows:,} rows across {test_chunks} chunks")
    print(f"  Total rows in fraud_data: {total_count:,}")
    print(f"  Duplicate trans_num rows in fraud_data: {dup_count:,}")

    print("\nData split breakdown:")
    for split, cnt in split_result:
        print(f"  {split}: {cnt:,}")
except Exception as e:
    print(f"✗ Error: {e}")


# ## Phase 2: TRANSFORM - Create Dimension Tables

# In[9]:


# ============================================================
# DIM_CUSTOMER: Extract unique customers using SQL
# ============================================================

print("Creating dim_customer via SQL...")

# Clear fact_transactions first (has FK to dim_customer)
with engine.connect() as conn:
    conn.execute(text("DELETE FROM fact_transactions"))
    conn.execute(text("DELETE FROM dim_customer"))
    conn.commit()

# Insert using SQL - DISTINCT handles duplicates  
insert_customer_sql = """
INSERT INTO dim_customer (cc_num, first_name, last_name, gender, dob, job, street, city, state, zip, lat, long, created_date, updated_date)
SELECT DISTINCT 
    cc_num,
    first as first_name,
    last as last_name,
    gender,
    dob::DATE,
    job,
    street,
    city,
    state,
    zip::VARCHAR,
    lat,
    long,
    NOW(),
    NOW()
FROM fraud_data
ORDER BY cc_num
ON CONFLICT (cc_num) DO NOTHING;
"""

try:
    with engine.connect() as conn:
        conn.execute(text(insert_customer_sql))
        conn.commit()

    with engine.connect() as conn:
        result = conn.execute(text("SELECT COUNT(*) FROM dim_customer"))
        count = result.scalar()
    print(f"✓ Loaded {count:,} customers")
except Exception as e:
    print(f"✗ Error: {e}")


# In[10]:


# ============================================================
# DIM_MERCHANT: Extract unique merchants using SQL
# ============================================================

print("Creating dim_merchant via SQL...")

# Clear existing data properly
with engine.connect() as conn:
    conn.execute(text("DELETE FROM fact_transactions"))
    conn.execute(text("DELETE FROM dim_merchant"))
    conn.commit()

# Insert using SQL - DISTINCT handles duplicates
insert_merchant_sql = """
INSERT INTO dim_merchant (merchant_name, merchant_category, merch_lat, merch_long, created_date, updated_date)
SELECT DISTINCT 
    merchant,
    category,
    merch_lat,
    merch_long,
    NOW(),
    NOW()
FROM fraud_data
ORDER BY merchant
ON CONFLICT (merchant_name) DO NOTHING;
"""

try:
    with engine.connect() as conn:
        conn.execute(text(insert_merchant_sql))
        conn.commit()

    with engine.connect() as conn:
        result = conn.execute(text("SELECT COUNT(*) FROM dim_merchant"))
        count = result.scalar()
    print(f"✓ Loaded {count:,} merchants")
except Exception as e:
    print(f"✗ Error: {e}")


# In[11]:


# ============================================================
# DIM_LOCATION: Extract unique geographic locations using SQL
# ============================================================

print("Creating dim_location via SQL...")

# Clear existing data
with engine.connect() as conn:
    conn.execute(text("TRUNCATE TABLE dim_location CASCADE"))
    conn.commit()

# Insert using SQL for efficiency
insert_location_sql = """
INSERT INTO dim_location (city, state, zip, lat, long, city_pop, location_key, created_date, updated_date)
SELECT DISTINCT 
    city,
    state,
    zip::VARCHAR,
    lat,
    long,
    city_pop,
    city || '|' || state || '|' || zip::VARCHAR as location_key,
    NOW(),
    NOW()
FROM fraud_data
ORDER BY state, city, zip;
"""

try:
    with engine.connect() as conn:
        conn.execute(text(insert_location_sql))
        conn.commit()

    with engine.connect() as conn:
        result = conn.execute(text("SELECT COUNT(*) FROM dim_location"))
        count = result.scalar()
    print(f"✓ Loaded {count:,} locations")
except Exception as e:
    print(f"✗ Error: {e}")


# In[12]:


# ============================================================
# DIM_TIME: Generate hourly time dimension using SQL
# ============================================================

print("Creating dim_time via SQL...")

# Clear fact_transactions first (has FK to dim_time)
with engine.connect() as conn:
    conn.execute(text("DELETE FROM fact_transactions"))
    conn.execute(text("DELETE FROM dim_time"))
    conn.commit()

# Insert using SQL - DISTINCT handles duplicates
insert_time_sql = """
INSERT INTO dim_time (trans_date_trans_time, hour, day_of_week, day_of_week_name, month, month_name, year, is_weekend, quarter, created_date)
SELECT DISTINCT 
    DATE_TRUNC('hour', trans_date_trans_time::TIMESTAMP) as trans_date_trans_time,
    EXTRACT(HOUR FROM trans_date_trans_time::TIMESTAMP)::INT as hour,
    EXTRACT(DOW FROM trans_date_trans_time::TIMESTAMP)::INT as day_of_week,
    TO_CHAR(trans_date_trans_time::TIMESTAMP, 'Day') as day_of_week_name,
    EXTRACT(MONTH FROM trans_date_trans_time::TIMESTAMP)::INT as month,
    TO_CHAR(trans_date_trans_time::TIMESTAMP, 'Month') as month_name,
    EXTRACT(YEAR FROM trans_date_trans_time::TIMESTAMP)::INT as year,
    (EXTRACT(DOW FROM trans_date_trans_time::TIMESTAMP)::INT IN (0, 6))::BOOLEAN as is_weekend,
    EXTRACT(QUARTER FROM trans_date_trans_time::TIMESTAMP)::INT as quarter,
    NOW()
FROM fraud_data
ORDER BY trans_date_trans_time
ON CONFLICT (trans_date_trans_time) DO NOTHING;
"""

try:
    with engine.connect() as conn:
        conn.execute(text(insert_time_sql))
        conn.commit()

    with engine.connect() as conn:
        result = conn.execute(text("SELECT COUNT(*) FROM dim_time"))
        count = result.scalar()
    print(f"✓ Loaded {count:,} time records")
except Exception as e:
    print(f"✗ Error: {e}")


# In[13]:


# ============================================================
# FACT_TRANSACTIONS: Create fact table using SQL INSERT SELECT
# ============================================================

print("Creating fact_transactions using SQL INSERT...")

# Use SQL to populate fact_transactions more efficiently
fact_insert_sql = """
INSERT INTO fact_transactions (trans_num, customer_id, merchant_id, location_id, time_id, amount, is_fraud, data_split, fraud_probability, created_date)
SELECT 
    fd.trans_num,
    dc.customer_id,
    dm.merchant_id,
    dl.location_id,
    dt.time_id,
    fd.amt as amount,
    fd.is_fraud,
    fd.data_split,
    0.0 as fraud_probability,
    fd.created_date
FROM fraud_data fd
LEFT JOIN dim_customer dc ON fd.cc_num = dc.cc_num
LEFT JOIN dim_merchant dm ON fd.merchant = dm.merchant_name
LEFT JOIN dim_location dl ON fd.city = dl.city AND fd.state = dl.state AND fd.zip::VARCHAR = dl.zip
LEFT JOIN dim_time dt ON DATE_TRUNC('hour', fd.trans_date_trans_time::TIMESTAMP) = dt.trans_date_trans_time
WHERE dc.customer_id IS NOT NULL 
  AND dm.merchant_id IS NOT NULL 
  AND dl.location_id IS NOT NULL 
  AND dt.time_id IS NOT NULL;
"""

try:
    with engine.connect() as conn:
        conn.execute(text(fact_insert_sql))
        conn.commit()

    # Verify
    with engine.connect() as conn:
        result = conn.execute(text("SELECT COUNT(*) FROM fact_transactions"))
        count = result.scalar()

    print(f"✓ Loaded {count:,} transactions to fact_transactions")

    # Get fraud statistics
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT 
                data_split,
                COUNT(*) as total,
                SUM(CASE WHEN is_fraud = 1 THEN 1 ELSE 0 END) as fraud_count
            FROM fact_transactions
            GROUP BY data_split
            ORDER BY data_split
        """))
        print(f"\nData split breakdown:")
        for row in result:
            fraud_rate = (row[2] / row[1]) * 100
            print(f"  {row[0]:8s}: {row[1]:>12,} total | {row[2]:>8,} fraud ({fraud_rate:>6.2f}%)")

except Exception as e:
    print(f"✗ Error: {e}")


# In[14]:


# Debug: Check why fact table has 0 rows
print("\n" + "=" * 60)
print("DEBUG: Fact table join debugging")
print("=" * 60)

with engine.connect() as conn:
    # Check each join separately
    result = conn.execute(text("""
        SELECT 
            'customer' as join_type,
            COUNT(*) as total,
            COUNT(CASE WHEN dc.customer_id IS NOT NULL THEN 1 END) as matched
        FROM fraud_data fd
        LEFT JOIN dim_customer dc ON fd.cc_num = dc.cc_num

        UNION ALL

        SELECT 
            'merchant' as join_type,
            COUNT(*) as total,
            COUNT(CASE WHEN dm.merchant_id IS NOT NULL THEN 1 END) as matched
        FROM fraud_data fd
        LEFT JOIN dim_merchant dm ON fd.merchant = dm.merchant_name

        UNION ALL

        SELECT 
            'location' as join_type,
            COUNT(*) as total,
            COUNT(CASE WHEN dl.location_id IS NOT NULL THEN 1 END) as matched
        FROM fraud_data fd
        LEFT JOIN dim_location dl ON fd.city = dl.city AND fd.state = dl.state AND fd.zip::VARCHAR = dl.zip

        UNION ALL

        SELECT 
            'time' as join_type,
            COUNT(*) as total,
            COUNT(CASE WHEN dt.time_id IS NOT NULL THEN 1 END) as matched
        FROM fraud_data fd
        LEFT JOIN dim_time dt ON DATE_TRUNC('hour', fd.trans_date_trans_time::TIMESTAMP) = dt.trans_date_trans_time
    """))

    print("\nJoin match results:")
    for row in result:
        match_rate = (row[2] / row[1]) * 100 if row[1] > 0 else 0
        print(f"  {row[0]:12s}: {row[1]:>10,} total | {row[2]:>10,} matched ({match_rate:>6.2f}%)")


# In[15]:


# Check dim_time contents
print("\ndim_time status:")
with engine.connect() as conn:
    result = conn.execute(text("SELECT COUNT(*) FROM dim_time"))
    count = result.scalar()
    print(f"  Total rows: {count:,}")

    if count > 0:
        result = conn.execute(text("SELECT time_id, trans_date_trans_time FROM dim_time LIMIT 3"))
        print("  Sample rows:")
        for row in result:
            print(f"    {row[0]}: {row[1]}")

    # Check unique times in fraud_data
    result = conn.execute(text("""
        SELECT COUNT(DISTINCT DATE_TRUNC('hour', trans_date_trans_time::TIMESTAMP))
        FROM fraud_data
    """))
    print(f"  Unique hourly periods in fraud_data: {result.scalar():,}")


# In[16]:


# Debug: Check fraud_data sample and schema
print("=" * 60)
print("DEBUG: Detailed fraud_data inspection")
print("=" * 60)

with engine.connect() as conn:
    # Check columns
    result = conn.execute(text("SELECT column_name, data_type FROM information_schema.columns WHERE table_name='fraud_data' ORDER BY ordinal_position"))
    print("\nfraud_data columns:")
    for row in result:
        print(f"  {row[0]:30s} {row[1]}")

    # Sample data
    result = conn.execute(text("SELECT trans_num, cc_num, merchant, first, last, CAST(cc_num AS VARCHAR) FROM fraud_data LIMIT 3"))
    print("\nSample fraud_data rows:")
    for row in result:
        print(f"  trans_num: {row[0]}, cc_num: {row[1]}, merchant: {row[2]}")

    # Check unique values
    result = conn.execute(text("SELECT COUNT(DISTINCT cc_num), COUNT(DISTINCT merchant) FROM fraud_data"))
    unique_cc, unique_merch = result.fetchone()
    print(f"\nUnique cc_num: {unique_cc:,}")
    print(f"Unique merchants: {unique_merch:,}")


# In[17]:


# Debug: Test merchant insert with error handling
print("\n" + "=" * 60)
print("DEBUG: Testing merchant insert")
print("=" * 60)

insert_merchant_sql = """
INSERT INTO dim_merchant (merchant_name, merchant_category, merch_lat, merch_long, created_date, updated_date)
SELECT DISTINCT 
    merchant,
    category,
    merch_lat,
    merch_long,
    NOW(),
    NOW()
FROM fraud_data
ORDER BY merchant;
"""

try:
    with engine.connect() as conn:
        result = conn.execute(text(insert_merchant_sql))
        print(f"Rows affected: {result.rowcount}")
        conn.commit()
except Exception as e:
    print(f"Error: {type(e).__name__}: {e}")

# Check result
with engine.connect() as conn:
    result = conn.execute(text("SELECT COUNT(*) FROM dim_merchant"))
    print(f"dim_merchant now has: {result.scalar():,} rows")


# In[18]:


# Verify fact_transactions loaded successfully
print("Verifying fact_transactions...")

try:
    with engine.connect() as conn:
        # Get row count
        result = conn.execute(text("SELECT COUNT(*) FROM fact_transactions"))
        count = result.scalar()

    print(f"✓ Loaded {count:,} transactions to fact_transactions")

    # Data split breakdown
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT data_split, COUNT(*) as cnt
            FROM fact_transactions
            GROUP BY data_split
            ORDER BY data_split
        """))
        print(f"\nData split:")
        for row in result:
            print(f"  {row[0]}: {row[1]:,}")

    # Fraud statistics
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN is_fraud = 1 THEN 1 ELSE 0 END) as fraud_count
            FROM fact_transactions
        """))
        row = result.fetchone()
        total = row[0]
        fraud_count = row[1]
        fraud_rate = (fraud_count / total) * 100

    print(f"\nFraud statistics:")
    print(f"  Total transactions: {total:,}")
    print(f"  Fraudulent: {fraud_count:,} ({fraud_rate:.2f}%)")
    print(f"  Non-fraudulent: {total - fraud_count:,}")

except Exception as e:
    print(f"✗ Error: {e}")


# ## Phase 3: LOAD - Create Analytical Views

# In[19]:


# ============================================================
# Create Analytical Views
# ============================================================

views_sql = """
-- View 1: Fraud by Merchant
CREATE OR REPLACE VIEW vw_fraud_by_merchant AS
SELECT 
    dm.merchant_id,
    dm.merchant_name,
    dm.merchant_category,
    COUNT(*) as total_transactions,
    SUM(CASE WHEN ft.is_fraud = 1 THEN 1 ELSE 0 END) as fraud_count,
    ROUND(SUM(CASE WHEN ft.is_fraud = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 4) as fraud_rate,
    SUM(ft.amount) as total_amount,
    ROUND(AVG(ft.amount), 2) as avg_amount,
    COUNT(DISTINCT ft.customer_id) as unique_customers
FROM fact_transactions ft
JOIN dim_merchant dm ON ft.merchant_id = dm.merchant_id
GROUP BY dm.merchant_id, dm.merchant_name, dm.merchant_category
ORDER BY fraud_count DESC;

-- View 2: Fraud by Location
CREATE OR REPLACE VIEW vw_fraud_by_location AS
SELECT 
    dl.location_id,
    dl.city,
    dl.state,
    dl.zip,
    COUNT(*) as total_transactions,
    SUM(CASE WHEN ft.is_fraud = 1 THEN 1 ELSE 0 END) as fraud_count,
    ROUND(SUM(CASE WHEN ft.is_fraud = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 4) as fraud_rate,
    SUM(ft.amount) as total_amount,
    dl.city_pop
FROM fact_transactions ft
JOIN dim_location dl ON ft.location_id = dl.location_id
GROUP BY dl.location_id, dl.city, dl.state, dl.zip, dl.city_pop
ORDER BY fraud_count DESC;

-- View 3: Fraud by Customer
CREATE OR REPLACE VIEW vw_fraud_by_customer AS
SELECT 
    dc.customer_id,
    dc.first_name,
    dc.last_name,
    dc.state,
    COUNT(*) as transaction_count,
    SUM(CASE WHEN ft.is_fraud = 1 THEN 1 ELSE 0 END) as fraud_count,
    ROUND(SUM(CASE WHEN ft.is_fraud = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 4) as fraud_rate,
    ROUND(AVG(ft.amount), 2) as avg_amount,
    MAX(ft.fraud_probability) as max_fraud_prob
FROM fact_transactions ft
JOIN dim_customer dc ON ft.customer_id = dc.customer_id
GROUP BY dc.customer_id, dc.first_name, dc.last_name, dc.state
HAVING SUM(CASE WHEN ft.is_fraud = 1 THEN 1 ELSE 0 END) > 0
ORDER BY fraud_count DESC;

-- View 4: Fraud by Time/Hour
CREATE OR REPLACE VIEW vw_fraud_by_time AS
SELECT 
    dt.time_id,
    dt.trans_date_trans_time,
    dt.hour,
    dt.day_of_week_name,
    dt.month,
    COUNT(*) as total_transactions,
    SUM(CASE WHEN ft.is_fraud = 1 THEN 1 ELSE 0 END) as fraud_count,
    ROUND(SUM(CASE WHEN ft.is_fraud = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 4) as fraud_rate,
    ROUND(AVG(ft.amount), 2) as avg_amount,
    dt.is_weekend
FROM fact_transactions ft
JOIN dim_time dt ON ft.time_id = dt.time_id
GROUP BY dt.time_id, dt.trans_date_trans_time, dt.hour, dt.day_of_week_name, dt.month, dt.is_weekend
ORDER BY fraud_count DESC;

-- View 5: Overall Fraud Summary
CREATE OR REPLACE VIEW vw_fraud_summary AS
SELECT 
    COUNT(*) as total_transactions,
    SUM(CASE WHEN is_fraud = 1 THEN 1 ELSE 0 END) as total_fraud_count,
    ROUND(SUM(CASE WHEN is_fraud = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 4) as overall_fraud_rate,
    SUM(amount) as total_amount,
    ROUND(AVG(amount), 2) as avg_amount,
    ROUND(MAX(amount), 2) as max_amount,
    COUNT(DISTINCT customer_id) as unique_customers,
    COUNT(DISTINCT merchant_id) as unique_merchants,
    COUNT(DISTINCT location_id) as unique_locations
FROM fact_transactions;
"""

print("Creating analytical views...")

try:
    with engine.connect() as conn:
        statements = [s.strip() for s in views_sql.split(';') if s.strip()]
        for stmt in statements:
            conn.execute(text(stmt))
        conn.commit()
    print("✓ All 5 views created successfully")
except Exception as e:
    print(f"✗ Error creating views: {e}")


# ## Step 4: Data Quality & Verification

# In[20]:


# ============================================================
# Verify Row Counts
# ============================================================

print("=" * 60)
print("DATA WAREHOUSE - ROW COUNTS")
print("=" * 60)

verification_queries = {
    'fraud_data': 'SELECT COUNT(*) FROM fraud_data',
    'dim_customer': 'SELECT COUNT(*) FROM dim_customer',
    'dim_merchant': 'SELECT COUNT(*) FROM dim_merchant',
    'dim_location': 'SELECT COUNT(*) FROM dim_location',
    'dim_time': 'SELECT COUNT(*) FROM dim_time',
    'fact_transactions': 'SELECT COUNT(*) FROM fact_transactions'
}

with engine.connect() as conn:
    for table_name, query in verification_queries.items():
        result = conn.execute(text(query))
        count = result.scalar()
        print(f"{table_name:20s}: {count:>15,} rows")

print()


# In[21]:


# ============================================================
# Verify Foreign Key Relationships (No Orphans)
# ============================================================

print("=" * 60)
print("FOREIGN KEY INTEGRITY")
print("=" * 60)

fk_check_query = """
SELECT 
    COUNT(*) as total_rows,
    SUM(CASE WHEN customer_id IS NULL THEN 1 ELSE 0 END) as null_customer_id,
    SUM(CASE WHEN merchant_id IS NULL THEN 1 ELSE 0 END) as null_merchant_id,
    SUM(CASE WHEN location_id IS NULL THEN 1 ELSE 0 END) as null_location_id,
    SUM(CASE WHEN time_id IS NULL THEN 1 ELSE 0 END) as null_time_id
FROM fact_transactions
"""

with engine.connect() as conn:
    result = conn.execute(text(fk_check_query))
    row = result.fetchone()

print(f"Total transactions: {row[0]:,}")
print(f"Null customer_id: {row[1]:,}")
print(f"Null merchant_id: {row[2]:,}")
print(f"Null location_id: {row[3]:,}")
print(f"Null time_id: {row[4]:,}")

if row[1] == 0 and row[2] == 0 and row[3] == 0 and row[4] == 0:
    print("\n✓ All foreign keys are valid (no NULL values)")
else:
    print("\n⚠ WARNING: Some NULL values detected in foreign keys")

print()


# In[22]:


# ============================================================
# Verify Fraud Distribution
# ============================================================

print("=" * 60)
print("FRAUD STATISTICS")
print("=" * 60)

fraud_query = """
SELECT 
    data_split,
    COUNT(*) as total,
    SUM(CASE WHEN is_fraud = 1 THEN 1 ELSE 0 END) as fraud_count,
    ROUND(SUM(CASE WHEN is_fraud = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 4) as fraud_rate
FROM fact_transactions
GROUP BY data_split
ORDER BY data_split
"""

with engine.connect() as conn:
    result = conn.execute(text(fraud_query))
    for row in result:
        print(f"{row[0]:8s}: {row[1]:>12,} total | {row[2]:>8,} fraud ({row[3]:>6.2f}%)")

print()


# In[23]:


# ============================================================
# Query Analytical Views
# ============================================================

print("=" * 60)
print("ANALYTICAL VIEWS - SAMPLE DATA")
print("=" * 60)

# View 1: Overall Summary
print("\n1. vw_fraud_summary:")
with engine.connect() as conn:
    result = conn.execute(text("SELECT * FROM vw_fraud_summary"))
    summary_df = pd.DataFrame(result.fetchall(), columns=result.keys())
print(summary_df.to_string(index=False))

# View 2: Top 5 Fraudulent Merchants
print("\n2. vw_fraud_by_merchant (Top 5):")
with engine.connect() as conn:
    result = conn.execute(text("SELECT * FROM vw_fraud_by_merchant LIMIT 5"))
    merchant_df = pd.DataFrame(result.fetchall(), columns=result.keys())
print(merchant_df[['merchant_id', 'merchant_name', 'fraud_count', 'fraud_rate']].to_string(index=False))

# View 3: Top 5 Fraudulent Locations
print("\n3. vw_fraud_by_location (Top 5):")
with engine.connect() as conn:
    result = conn.execute(text("SELECT * FROM vw_fraud_by_location LIMIT 5"))
    location_df = pd.DataFrame(result.fetchall(), columns=result.keys())
print(location_df[['city', 'state', 'fraud_count', 'fraud_rate']].to_string(index=False))

# View 4: Fraudulent Customers
print("\n4. vw_fraud_by_customer (First 5):")
with engine.connect() as conn:
    result = conn.execute(text("SELECT * FROM vw_fraud_by_customer LIMIT 5"))
    customer_df = pd.DataFrame(result.fetchall(), columns=result.keys())
print(customer_df[['first_name', 'last_name', 'fraud_count', 'fraud_rate']].to_string(index=False))

# View 5: High-fraud Time Periods
print("\n5. vw_fraud_by_time (Top 5 fraudulent hours):")
with engine.connect() as conn:
    result = conn.execute(text("SELECT * FROM vw_fraud_by_time LIMIT 5"))
    time_df = pd.DataFrame(result.fetchall(), columns=result.keys())
print(time_df[['hour', 'day_of_week_name', 'fraud_count', 'fraud_rate']].to_string(index=False))


# ## ✅ Summary
# 
# ETL pipeline complete! ✓
# 
# **What was created:**
# - ✓ Staging table: `fraud_data` (1.9M rows)
# - ✓ 4 Dimensions: customer (1.3M), merchant (3.6K), location (50K), time (8.76K)
# - ✓ Fact table: `fact_transactions` (1.9M rows)
# - ✓ 5 Analytical views for dashboards
# 
# **Data Quality:**
# - ✓ No NULL foreign keys (referential integrity OK)
# - ✓ Train/test split preserved (1.3M / 0.6M)
# - ✓ Fraud rate: ~0.17% (imbalanced, as expected)
# 
# **Next Steps:**
# 1. Connect Streamlit web app to database
# 2. Create ML models for `fraud_probability` column
# 3. Generate assignment report
# 

# ## Step 10: Create Materialized Data Marts
# 
# Create optimized data mart tables for dashboard queries (replacing virtual views).
# 
# **Data Marts Created:**
# - `dm_merchant_fraud`: Fraud analysis by merchant/category
# - `dm_location_fraud`: Geographic fraud distribution
# - `dm_customer_risk`: Customer risk profiles
# - `dm_time_fraud`: Temporal fraud patterns (hourly)
# - `dm_fraud_summary`: Executive summary metrics
# 
# **Benefits:**
# - Pre-computed aggregations (faster queries)
# - Indexes on fraud_rate_pct and fraud_amount
# - Ready for BI tools (Tableau, Power BI, Metabase)
# - 4.7 MB total size vs 1.85M raw transactions

# In[24]:


# ============================================================
# Create Materialized Data Marts (Inline - No subprocess)
# ============================================================

from sqlalchemy import inspect

print("=" * 80)
print("Creating Materialized Data Marts for Dashboard")
print("=" * 80)

# Load SQL file (using relative path from ETL folder)
sql_file = Path("SQL") / "03_CREATE_DATA_MARTS.sql"

print(f"\n📁 SQL File: {sql_file.resolve()}")
print(f"⏱️  Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("-" * 80)

try:
    with open(sql_file, 'r', encoding='utf-8') as f:
        sql_script = f.read()

    # Remove SQL comments for cleaner execution
    lines = sql_script.split('\n')
    clean_lines = [l for l in lines if not l.strip().startswith('--')]
    clean_script = '\n'.join(clean_lines)

    print("🔄 Creating Materialized Data Marts...")

    # Execute SQL
    try:
        # Try executing as one block first (more efficient)
        with engine.begin() as conn:
            conn.execute(text(clean_script))
        print(f"✅ Data marts created successfully")
    except Exception as e:
        # Fallback: execute statement by statement
        print(f"⚠️  Single block execution failed, trying statement-by-statement...")
        statements = [s.strip() for s in clean_script.split(';') if s.strip()]
        success = 0
        for i, statement in enumerate(statements, 1):
            try:
                with engine.begin() as conn:
                    conn.execute(text(statement))
                success += 1
            except Exception as e2:
                error_msg = str(e2)
                # Some errors are expected (e.g., "already exists")
                if 'already exists' not in error_msg.lower():
                    print(f"  Statement {i}: {error_msg[:100]}")
        print(f"✅ Created {success}/{len(statements)} statements successfully")

    print("-" * 80)

    # Verify creation
    inspector = inspect(engine)
    tables = [t for t in inspector.get_table_names() if t.startswith('dm_')]

    print(f"\n✅ Created {len(tables)} Data Marts:")
    for table in sorted(tables):
        with engine.connect() as conn:
            result = conn.execute(text(f"SELECT COUNT(*) as cnt FROM {table}"))
            count = result.scalar()
        print(f"   • {table}: {count:,} rows")

    # Get sizes
    print(f"\n📊 Data Mart Sizes:")
    for table in sorted(tables):
        with engine.connect() as conn:
            result = conn.execute(text(f"""
                SELECT pg_size_pretty(pg_total_relation_size('{table}')) as size
            """))
            size = result.scalar()
        print(f"   • {table}: {size}")

    print(f"\n⏱️  End Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("\n" + "=" * 80)
    print("✅ Data Marts Created Successfully!")
    print("=" * 80)

except FileNotFoundError:
    print(f"❌ Error: SQL file not found at {sql_file.resolve()}")
    print(f"Current working directory: {Path.cwd()}")
    sys.exit(1)
except Exception as e:
    print(f"❌ Error: {str(e)}")
    sys.exit(1)

