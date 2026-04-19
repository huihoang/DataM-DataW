"""
Pentaho ETL Pipeline - Python Alternative
Run this instead of Pentaho if you want faster execution
"""

import pandas as pd
import numpy as np
from sqlalchemy import create_engine, text
from datetime import datetime
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ============================================================
# DATABASE CONFIG
# ============================================================
DB_URL = "postgresql://whuser:123456@localhost:5432/fraud_detection_dw"
engine = create_engine(DB_URL, echo=False)

DATA_PATH = r"d:\Code\BTL\Data mining\Fraud detection\data"

# ============================================================
# TRANSFORMATION 1: EXTRACT_TRAIN
# ============================================================
def extract_train():
    """01_EXTRACT_TRAIN.ktr equivalent"""
    logger.info("=== TRANSFORMATION 1: EXTRACT_TRAIN ===")
    
    try:
        # CSV File Input
        df = pd.read_csv(f"{DATA_PATH}/fraudTrain.csv", low_memory=False)
        logger.info(f"  Loaded fraudTrain.csv: {len(df)} rows")
        
        # Add Constants
        df['data_split'] = 'train'
        df['created_date'] = datetime.now()
        
        # Table Output - Truncate first time
        df.to_sql('fraud_data', con=engine, if_exists='replace', index=False, chunksize=5000)
        
        with engine.connect() as conn:
            result = conn.execute(text("SELECT COUNT(*) FROM fraud_data"))
            count = result.scalar()
        
        logger.info(f"✓ Loaded {count:,} rows to fraud_data")
        return True
    except Exception as e:
        logger.error(f"✗ Error: {e}")
        return False

# ============================================================
# TRANSFORMATION 2: EXTRACT_TEST
# ============================================================
def extract_test():
    """02_EXTRACT_TEST.ktr equivalent"""
    logger.info("=== TRANSFORMATION 2: EXTRACT_TEST ===")
    
    try:
        # CSV File Input
        df = pd.read_csv(f"{DATA_PATH}/fraudTest.csv", low_memory=False)
        logger.info(f"  Loaded fraudTest.csv: {len(df)} rows")
        
        # Add Constants
        df['data_split'] = 'test'
        df['created_date'] = datetime.now()
        
        # Table Output - Append (if_exists='append')
        df.to_sql('fraud_data', con=engine, if_exists='append', index=False, chunksize=5000)
        
        with engine.connect() as conn:
            result = conn.execute(text("SELECT COUNT(*) FROM fraud_data"))
            count = result.scalar()
        
        logger.info(f"✓ Total rows in fraud_data: {count:,}")
        return True
    except Exception as e:
        logger.error(f"✗ Error: {e}")
        return False

# ============================================================
# TRANSFORMATION 3: CREATE_DIM_CUSTOMER
# ============================================================
def create_dim_customer():
    """03_CREATE_DIM_CUSTOMER.ktr equivalent"""
    logger.info("=== TRANSFORMATION 3: CREATE_DIM_CUSTOMER ===")
    
    try:
        # Table Input - Select distinct customers
        query = """
        SELECT DISTINCT
            cc_num,
            first as first_name,
            last as last_name,
            gender,
            dob,
            job,
            street,
            city,
            state,
            zip,
            lat,
            long
        FROM fraud_data
        WHERE cc_num IS NOT NULL
        ORDER BY cc_num
        """
        
        df = pd.read_sql(query, engine)
        logger.info(f"  Loaded {len(df)} distinct customers")
        
        # Remove duplicates (by cc_num - should be none, but just in case)
        df = df.drop_duplicates(subset=['cc_num'])
        
        # Add Sequence (customer_id) - pandas will handle via DB serial
        # Add Constants
        df['created_date'] = datetime.now()
        df['updated_date'] = datetime.now()
        
        # Table Output
        df.to_sql('dim_customer', con=engine, if_exists='replace', index=False, chunksize=5000)
        
        with engine.connect() as conn:
            result = conn.execute(text("SELECT COUNT(*) FROM dim_customer"))
            count = result.scalar()
        
        logger.info(f"✓ Loaded {count:,} customers to dim_customer")
        return True
    except Exception as e:
        logger.error(f"✗ Error: {e}")
        return False

# ============================================================
# TRANSFORMATION 4: CREATE_DIM_MERCHANT
# ============================================================
def create_dim_merchant():
    """04_CREATE_DIM_MERCHANT.ktr equivalent"""
    logger.info("=== TRANSFORMATION 4: CREATE_DIM_MERCHANT ===")
    
    try:
        # Table Input
        query = """
        SELECT DISTINCT
            merchant as merchant_name,
            category as merchant_category,
            merch_lat,
            merch_long
        FROM fraud_data
        WHERE merchant IS NOT NULL
        ORDER BY merchant
        """
        
        df = pd.read_sql(query, engine)
        logger.info(f"  Loaded {len(df)} distinct merchants")
        
        # Remove duplicates
        df = df.drop_duplicates(subset=['merchant_name'])
        
        # Add Constants
        df['created_date'] = datetime.now()
        df['updated_date'] = datetime.now()
        
        # Table Output
        df.to_sql('dim_merchant', con=engine, if_exists='replace', index=False, chunksize=5000)
        
        with engine.connect() as conn:
            result = conn.execute(text("SELECT COUNT(*) FROM dim_merchant"))
            count = result.scalar()
        
        logger.info(f"✓ Loaded {count:,} merchants to dim_merchant")
        return True
    except Exception as e:
        logger.error(f"✗ Error: {e}")
        return False

# ============================================================
# TRANSFORMATION 5: CREATE_DIM_LOCATION
# ============================================================
def create_dim_location():
    """05_CREATE_DIM_LOCATION.ktr equivalent"""
    logger.info("=== TRANSFORMATION 5: CREATE_DIM_LOCATION ===")
    
    try:
        # Table Input
        query = """
        SELECT DISTINCT
            city,
            state,
            zip,
            lat,
            long,
            city_pop
        FROM fraud_data
        WHERE city IS NOT NULL AND state IS NOT NULL
        ORDER BY state, city, zip
        """
        
        df = pd.read_sql(query, engine)
        logger.info(f"  Loaded {len(df)} distinct locations")
        
        # Remove duplicates
        df = df.drop_duplicates(subset=['city', 'state', 'zip'])
        
        # Create location_key
        df['location_key'] = df['city'].astype(str) + '|' + df['state'].astype(str) + '|' + df['zip'].astype(str)
        
        # Add Constants
        df['created_date'] = datetime.now()
        df['updated_date'] = datetime.now()
        
        # Table Output
        df.to_sql('dim_location', con=engine, if_exists='replace', index=False, chunksize=5000)
        
        with engine.connect() as conn:
            result = conn.execute(text("SELECT COUNT(*) FROM dim_location"))
            count = result.scalar()
        
        logger.info(f"✓ Loaded {count:,} locations to dim_location")
        return True
    except Exception as e:
        logger.error(f"✗ Error: {e}")
        return False

# ============================================================
# TRANSFORMATION 6: CREATE_DIM_TIME
# ============================================================
def create_dim_time():
    """06_CREATE_DIM_TIME.ktr equivalent"""
    logger.info("=== TRANSFORMATION 6: CREATE_DIM_TIME ===")
    
    try:
        # Table Input with SQL aggregation
        query = """
        SELECT DISTINCT
            DATE_TRUNC('hour', trans_date_trans_time::TIMESTAMP) as trans_hour,
            EXTRACT(HOUR FROM trans_date_trans_time::TIMESTAMP)::INT as hour,
            EXTRACT(DOW FROM trans_date_trans_time::TIMESTAMP)::INT as day_of_week,
            TO_CHAR(trans_date_trans_time::TIMESTAMP, 'Day') as day_of_week_name,
            EXTRACT(MONTH FROM trans_date_trans_time::TIMESTAMP)::INT as month,
            TO_CHAR(trans_date_trans_time::TIMESTAMP, 'Month') as month_name,
            EXTRACT(YEAR FROM trans_date_trans_time::TIMESTAMP)::INT as year,
            EXTRACT(QUARTER FROM trans_date_trans_time::TIMESTAMP)::INT as quarter
        FROM fraud_data
        WHERE trans_date_trans_time IS NOT NULL
        ORDER BY trans_hour
        """
        
        df = pd.read_sql(query, engine)
        logger.info(f"  Loaded {len(df)} distinct time periods")
        
        # Add is_weekend (0=weekday, 6=Saturday, 0=Sunday in PostgreSQL DOW)
        df['is_weekend'] = df['day_of_week'].isin([0, 6]).astype(int)
        
        # Add trans_date_trans_time (same as trans_hour for dimension)
        df['trans_date_trans_time'] = df['trans_hour']
        
        # Remove duplicates
        df = df.drop_duplicates(subset=['trans_hour'])
        
        # Add Constants
        df['created_date'] = datetime.now()
        
        # Table Output
        df.to_sql('dim_time', con=engine, if_exists='replace', index=False, chunksize=5000)
        
        with engine.connect() as conn:
            result = conn.execute(text("SELECT COUNT(*) FROM dim_time"))
            count = result.scalar()
        
        logger.info(f"✓ Loaded {count:,} time records to dim_time")
        return True
    except Exception as e:
        logger.error(f"✗ Error: {e}")
        return False

# ============================================================
# TRANSFORMATION 7: CREATE_FACT_TRANSACTIONS
# ============================================================
def create_fact_transactions():
    """07_CREATE_FACT_TRANSACTIONS.ktr equivalent"""
    logger.info("=== TRANSFORMATION 7: CREATE_FACT_TRANSACTIONS ===")
    
    try:
        # Use SQL to join with lookups (Database Lookup equivalent)
        query = """
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
        LEFT JOIN dim_location dl ON fd.city = dl.city AND fd.state = dl.state AND CAST(fd.zip AS VARCHAR) = dl.zip
        LEFT JOIN dim_time dt ON DATE_TRUNC('hour', fd.trans_date_trans_time::TIMESTAMP) = dt.trans_hour
        WHERE dc.customer_id IS NOT NULL 
          AND dm.merchant_id IS NOT NULL 
          AND dl.location_id IS NOT NULL 
          AND dt.time_id IS NOT NULL
        """
        
        with engine.connect() as conn:
            conn.execute(text("DELETE FROM fact_transactions"))  # Clear first
            conn.execute(text(query))
            conn.commit()
            
            result = conn.execute(text("SELECT COUNT(*) FROM fact_transactions"))
            count = result.scalar()
        
        logger.info(f"✓ Loaded {count:,} transactions to fact_transactions")
        return True
    except Exception as e:
        logger.error(f"✗ Error: {e}")
        return False

# ============================================================
# MAIN EXECUTION
# ============================================================
if __name__ == "__main__":
    logger.info("\n" + "="*60)
    logger.info("PENTAHO ETL PIPELINE - PYTHON EXECUTION")
    logger.info("="*60 + "\n")
    
    steps = [
        ("01_EXTRACT_TRAIN", extract_train),
        ("02_EXTRACT_TEST", extract_test),
        ("03_CREATE_DIM_CUSTOMER", create_dim_customer),
        ("04_CREATE_DIM_MERCHANT", create_dim_merchant),
        ("05_CREATE_DIM_LOCATION", create_dim_location),
        ("06_CREATE_DIM_TIME", create_dim_time),
        ("07_CREATE_FACT_TRANSACTIONS", create_fact_transactions),
    ]
    
    results = {}
    for step_name, step_func in steps:
        try:
            success = step_func()
            results[step_name] = "✓ SUCCESS" if success else "✗ FAILED"
        except Exception as e:
            logger.error(f"✗ {step_name} failed: {e}")
            results[step_name] = "✗ FAILED"
    
    logger.info("\n" + "="*60)
    logger.info("EXECUTION SUMMARY")
    logger.info("="*60)
    for step, status in results.items():
        logger.info(f"{step:40s} {status}")
    logger.info("="*60 + "\n")
