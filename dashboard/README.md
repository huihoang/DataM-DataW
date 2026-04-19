# Fraud Detection Dashboard

## 📊 Overview
Interactive Streamlit dashboard for analyzing fraud patterns from the PostgreSQL Data Warehouse.

**Features:**
- ✅ Real-time connection to `fraud_detection_dw` database
- ✅ 5 analytical views (Merchant, Location, Customer, Time, Summary)
- ✅ Interactive filters & drill-down capabilities
- ✅ Data export to CSV
- ✅ Geospatial visualization
- ✅ Key metrics & statistics

---

## 🚀 Quick Start

### 1. Install Dependencies
```bash
cd d:\Code\BTL\Data mining\Fraud detection\dashboard
pip install -r requirements.txt
```

### 2. Run Dashboard
```bash
streamlit run app.py
```

The app will open at: `http://localhost:8501`

---

## 📑 Dashboard Sections

### 1️⃣ Overall Statistics
- Total transactions: 1.85M
- Fraudulent transactions & fraud rate
- Average transaction amount
- Unique customers, merchants, locations

### 2️⃣ Fraud by Merchant (Tab 1)
- Top 10 merchants by fraud count
- Filter by fraud count & fraud rate
- Merchant category & transaction details
- Download filtered data

### 3️⃣ Fraud by Location (Tab 2)
- Geographic distribution (scatter plot)
- Top locations bar chart
- State-level filtering
- Population-based analysis

### 4️⃣ Fraud by Customer (Tab 3)
- High-risk customers (only those with fraud)
- Fraud distribution histogram
- Filter by minimum fraud count
- Customer state & transaction history

### 5️⃣ Fraud by Time (Tab 4)
- Fraud patterns by hour of day
- Weekday vs. weekend comparison
- Temporal trend analysis
- Top time periods

### 6️⃣ Data Export (Tab 5)
- Download all merchants, locations, customers, time data
- CSV format for external analysis

---

## 🔧 Configuration

Edit database credentials in `app.py` line 87-93:
```python
DB_USER = 'whuser'
DB_PASSWORD = '123456'
DB_HOST = 'localhost'
DB_PORT = 5432
DB_NAME = 'fraud_detection_dw'
```

---

## 📊 Data Sources

All data comes from PostgreSQL analytical views:
- `vw_fraud_summary` - Overall metrics
- `vw_fraud_by_merchant` - Merchant-level fraud analysis
- `vw_fraud_by_location` - Geographic fraud patterns
- `vw_fraud_by_customer` - Customer-level fraud profiles
- `vw_fraud_by_time` - Temporal fraud patterns

---

## ⚡ Performance Notes

- **Caching**: 5-minute TTL for all database queries
- **Load Time**: First load ~10-30 seconds, subsequent loads instant
- **Concurrent Users**: Single instance, not production-ready for >10 users

---

## 📋 Requirements Met

✅ **BTL Assignment:**
- ✅ Data Source: fraudTrain.csv + fraudTest.csv
- ✅ ETL: Complete pipeline (1.85M rows)
- ✅ Data Warehouse: PostgreSQL with star schema
- ✅ Dashboard: Streamlit interactive analytics
- ⏳ AI: modeling.ipynb (separate pipeline)

---

## 🎯 Next Steps

1. **Integrate ML Models**:
   - Train XGBoost/Random Forest in modeling.ipynb
   - Update `fraud_probability` in fact_transactions
   - Add model predictions to dashboard

2. **Performance Optimization**:
   - Implement pagination for large result sets
   - Add indexes to slow queries
   - Consider materialized views for faster aggregations

3. **Production Deployment**:
   - Docker containerization
   - Streamlit Cloud hosting
   - Authentication & RBAC

---

## 📞 Support

For issues:
1. Check PostgreSQL connection: `psql -U whuser -d fraud_detection_dw`
2. Verify venv is activated
3. Check Streamlit logs: `streamlit logs`

