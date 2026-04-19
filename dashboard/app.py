"""
Fraud Detection Data Warehouse Dashboard
Interactive visualization of fraud analytics from PostgreSQL warehouse
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from sqlalchemy import create_engine, text
import warnings

warnings.filterwarnings('ignore')

# ============================================================
# PAGE CONFIG
# ============================================================
st.set_page_config(
    page_title="Fraud Detection Dashboard",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom styling
st.markdown("""
    <style>
    [data-testid="stMetricValue"] {
        font-size: 24px;
    }
    .header-style {
        font-size: 32px;
        font-weight: bold;
        color: #1f77b4;
        margin-bottom: 20px;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    </style>
    """, unsafe_allow_html=True)

# ============================================================
# DATABASE CONNECTION
# ============================================================
@st.cache_resource
def get_engine():
    """Create and cache database connection"""
    DB_TYPE = 'postgresql'
    DB_USER = 'whuser'
    DB_PASSWORD = '123456'
    DB_HOST = 'localhost'
    DB_PORT = 5432
    DB_NAME = 'fraud_detection_dw'
    
    connection_string = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    
    try:
        engine = create_engine(connection_string, echo=False, pool_pre_ping=True)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return engine
    except Exception as e:
        st.error(f"❌ Database Connection Failed: {str(e)}")
        st.stop()

engine = get_engine()

# ============================================================
# HELPER FUNCTIONS
# ============================================================
@st.cache_data(ttl=300)  # Cache for 5 minutes
def load_fraud_summary():
    """Load overall fraud summary"""
    query = "SELECT * FROM vw_fraud_summary"
    return pd.read_sql(query, engine)

@st.cache_data(ttl=300)
def load_fraud_by_merchant():
    """Load fraud by merchant"""
    query = "SELECT * FROM vw_fraud_by_merchant LIMIT 50"
    return pd.read_sql(query, engine)

@st.cache_data(ttl=300)
def load_fraud_by_location():
    """Load fraud by location"""
    query = "SELECT * FROM vw_fraud_by_location LIMIT 50"
    return pd.read_sql(query, engine)

@st.cache_data(ttl=300)
def load_fraud_by_customer():
    """Load fraud by customer (with fraud > 0)"""
    query = "SELECT * FROM vw_fraud_by_customer LIMIT 100"
    return pd.read_sql(query, engine)

@st.cache_data(ttl=300)
def load_fraud_by_time():
    """Load fraud by time"""
    query = "SELECT * FROM vw_fraud_by_time ORDER BY fraud_count DESC LIMIT 100"
    return pd.read_sql(query, engine)

@st.cache_data(ttl=300)
def load_warehouse_stats():
    """Load warehouse statistics"""
    query = """
    SELECT 
        'Customers' as metric_name, COUNT(DISTINCT customer_id) as value
    FROM fact_transactions
    UNION ALL
    SELECT 'Merchants', COUNT(DISTINCT merchant_id) FROM fact_transactions
    UNION ALL
    SELECT 'Locations', COUNT(DISTINCT location_id) FROM fact_transactions
    UNION ALL
    SELECT 'Total Transactions', COUNT(*) FROM fact_transactions
    """
    return pd.read_sql(query, engine)

# ============================================================
# MAIN APP
# ============================================================

# Header
st.markdown('<div class="header-style">🔍 Fraud Detection Dashboard</div>', unsafe_allow_html=True)
st.markdown("📊 Interactive analytics from PostgreSQL Data Warehouse")
st.divider()

# ============================================================
# SECTION 1: KEY METRICS
# ============================================================
st.subheader("📈 Overall Statistics")

try:
    summary_df = load_fraud_summary()
    
    if not summary_df.empty:
        summary = summary_df.iloc[0]
        
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            st.metric(
                "Total Transactions",
                f"{int(summary['total_transactions']):,}",
                help="Total transactions in warehouse"
            )
        
        with col2:
            st.metric(
                "Fraudulent",
                f"{int(summary['total_fraud_count']):,}",
                help="Number of fraud transactions"
            )
        
        with col3:
            st.metric(
                "Fraud Rate",
                f"{float(summary['overall_fraud_rate']):.2f}%",
                help="Percentage of fraudulent transactions"
            )
        
        with col4:
            st.metric(
                "Avg Amount",
                f"${float(summary['avg_amount']):.2f}",
                help="Average transaction amount"
            )
        
        with col5:
            st.metric(
                "Unique Customers",
                f"{int(summary['unique_customers']):,}",
                help="Number of unique customers"
            )
        
        st.divider()
except Exception as e:
    st.error(f"Error loading summary: {e}")

# ============================================================
# SECTION 2: WAREHOUSE STRUCTURE
# ============================================================
st.subheader("🏗️ Warehouse Structure")

try:
    warehouse_stats = load_warehouse_stats()
    
    col1, col2, col3, col4 = st.columns(4)
    
    stats_dict = dict(zip(warehouse_stats['metric_name'], warehouse_stats['value']))
    
    with col1:
        st.metric("Customers", f"{stats_dict.get('Customers', 0):,}")
    with col2:
        st.metric("Merchants", f"{stats_dict.get('Merchants', 0):,}")
    with col3:
        st.metric("Locations", f"{stats_dict.get('Locations', 0):,}")
    with col4:
        st.metric("Transactions", f"{stats_dict.get('Total Transactions', 0):,}")
    
    st.divider()
except Exception as e:
    st.error(f"Error loading warehouse stats: {e}")

# ============================================================
# SECTION 3: TABS FOR DIFFERENT VIEWS
# ============================================================

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "💰 Fraud by Merchant",
    "📍 Fraud by Location",
    "👤 Fraud by Customer",
    "⏰ Fraud by Time",
    "📊 Data Export"
])

# TAB 1: Fraud by Merchant
with tab1:
    st.subheader("Top Merchants by Fraud Count")
    
    try:
        merchant_df = load_fraud_by_merchant()
        
        if not merchant_df.empty:
            # Top 10 merchants
            top_merchants = merchant_df.head(10).copy()
            
            # Bar chart: Fraud count
            fig_count = px.bar(
                top_merchants,
                x='merchant_name',
                y='fraud_count',
                color='fraud_rate',
                color_continuous_scale='Reds',
                title="Top 10 Merchants by Fraud Count",
                labels={'merchant_name': 'Merchant', 'fraud_count': 'Fraud Count', 'fraud_rate': 'Fraud Rate (%)'},
                height=400
            )
            st.plotly_chart(fig_count, use_container_width=True)
            
            # Table with filters
            col1, col2 = st.columns([2, 1])
            
            with col1:
                min_fraud = st.slider(
                    "Minimum Fraud Count",
                    min_value=0,
                    max_value=int(merchant_df['fraud_count'].max()),
                    value=0,
                    key="merchant_fraud_slider"
                )
            
            with col2:
                min_fraud_rate = st.slider(
                    "Minimum Fraud Rate (%)",
                    min_value=0.0,
                    max_value=float(merchant_df['fraud_rate'].max()),
                    value=0.0,
                    key="merchant_rate_slider"
                )
            
            filtered_merchants = merchant_df[
                (merchant_df['fraud_count'] >= min_fraud) &
                (merchant_df['fraud_rate'] >= min_fraud_rate)
            ].copy()
            
            filtered_merchants = filtered_merchants[[
                'merchant_id', 'merchant_name', 'merchant_category',
                'fraud_count', 'fraud_rate', 'total_transactions', 'avg_amount'
            ]].head(20)
            
            st.dataframe(
                filtered_merchants,
                use_container_width=True,
                hide_index=True,
                column_config={
                    'fraud_rate': st.column_config.NumberColumn(format="%.2f%%"),
                    'avg_amount': st.column_config.NumberColumn(format="$%.2f"),
                }
            )
            
            # Download button
            csv_merchants = filtered_merchants.to_csv(index=False)
            st.download_button(
                label="📥 Download Merchant Data",
                data=csv_merchants,
                file_name="fraud_by_merchant.csv",
                mime="text/csv"
            )
    
    except Exception as e:
        st.error(f"Error loading merchant data: {e}")

# TAB 2: Fraud by Location
with tab2:
    st.subheader("Geographic Fraud Distribution")
    
    try:
        location_df = load_fraud_by_location()
        
        if not location_df.empty:
            top_locations = location_df.head(15).copy()
            
            # Scatter map (lat, long)
            fig_map = px.scatter_geo(
                top_locations,
                lat='lat',
                lon='long',
                color='fraud_rate',
                size='fraud_count',
                hover_name='city',
                hover_data={'state': True, 'zip': True, 'fraud_count': True, 'fraud_rate': ':.2f'},
                color_continuous_scale='Reds',
                title="Fraud Geographic Distribution",
                height=500
            )
            st.plotly_chart(fig_map, use_container_width=True)
            
            # Top locations by fraud
            fig_bar = px.bar(
                top_locations,
                x='city',
                y='fraud_count',
                color='fraud_rate',
                color_continuous_scale='Reds',
                title="Top Locations by Fraud Count",
                labels={'city': 'City', 'fraud_count': 'Fraud Count'},
                height=400
            )
            st.plotly_chart(fig_bar, use_container_width=True)
            
            # Filter by state
            states = location_df['state'].unique()
            selected_state = st.selectbox("Filter by State:", states, key="location_state")
            
            filtered_locations = location_df[location_df['state'] == selected_state]
            
            st.dataframe(
                filtered_locations[[
                    'location_id', 'city', 'state', 'zip',
                    'fraud_count', 'fraud_rate', 'total_transactions', 'city_pop'
                ]].head(20),
                use_container_width=True,
                hide_index=True,
                column_config={
                    'fraud_rate': st.column_config.NumberColumn(format="%.2f%%"),
                    'city_pop': st.column_config.NumberColumn(format="%d"),
                }
            )
    
    except Exception as e:
        st.error(f"Error loading location data: {e}")

# TAB 3: Fraud by Customer
with tab3:
    st.subheader("High-Risk Customers (with Fraud)")
    
    try:
        customer_df = load_fraud_by_customer()
        
        if not customer_df.empty:
            # Summary
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Customers with Fraud", len(customer_df))
            with col2:
                st.metric("Avg Fraud per Customer", f"{customer_df['fraud_count'].mean():.1f}")
            with col3:
                st.metric("Max Fraud per Customer", f"{customer_df['fraud_count'].max():.0f}")
            
            # Distribution
            fig_dist = px.histogram(
                customer_df,
                x='fraud_count',
                nbins=30,
                title="Distribution of Fraud Count per Customer",
                labels={'fraud_count': 'Fraud Count', 'count': 'Number of Customers'},
                height=400
            )
            st.plotly_chart(fig_dist, use_container_width=True)
            
            # Filter
            min_fraud_count = st.slider(
                "Minimum Fraud Count",
                min_value=1,
                max_value=int(customer_df['fraud_count'].max()),
                value=1,
                key="customer_fraud_slider"
            )
            
            filtered_customers = customer_df[
                customer_df['fraud_count'] >= min_fraud_count
            ].copy()
            
            st.dataframe(
                filtered_customers[[
                    'customer_id', 'first_name', 'last_name', 'state',
                    'fraud_count', 'fraud_rate', 'transaction_count', 'avg_amount'
                ]].sort_values('fraud_count', ascending=False).head(30),
                use_container_width=True,
                hide_index=True,
                column_config={
                    'fraud_rate': st.column_config.NumberColumn(format="%.2f%%"),
                    'avg_amount': st.column_config.NumberColumn(format="$%.2f"),
                }
            )
    
    except Exception as e:
        st.error(f"Error loading customer data: {e}")

# TAB 4: Fraud by Time
with tab4:
    st.subheader("Temporal Fraud Patterns")
    
    try:
        time_df = load_fraud_by_time()
        
        if not time_df.empty:
            # Fraud by hour of day
            hourly_df = time_df.groupby('hour').agg({
                'fraud_count': 'sum',
                'total_transactions': 'sum'
            }).reset_index()
            hourly_df['fraud_rate'] = (hourly_df['fraud_count'] / hourly_df['total_transactions']) * 100
            
            fig_hourly = px.bar(
                hourly_df,
                x='hour',
                y='fraud_count',
                color='fraud_rate',
                color_continuous_scale='Reds',
                title="Fraud Count by Hour of Day",
                labels={'hour': 'Hour', 'fraud_count': 'Fraud Count'},
                height=400
            )
            st.plotly_chart(fig_hourly, use_container_width=True)
            
            # Fraud by day of week
            day_df = time_df.groupby('day_of_week_name').agg({
                'fraud_count': 'sum',
                'is_weekend': 'first'
            }).reset_index()
            
            fig_day = px.bar(
                day_df,
                x='day_of_week_name',
                y='fraud_count',
                color='is_weekend',
                title="Fraud Count by Day of Week",
                labels={'day_of_week_name': 'Day', 'fraud_count': 'Fraud Count'},
                height=400,
                color_discrete_map={True: '#EF553B', False: '#636EFA'}
            )
            st.plotly_chart(fig_day, use_container_width=True)
            
            # Detailed time data
            st.subheader("Top Hours by Fraud Activity")
            top_hours = time_df.nlargest(20, 'fraud_count')
            
            st.dataframe(
                top_hours[[
                    'hour', 'day_of_week_name', 'fraud_count', 'fraud_rate',
                    'total_transactions', 'is_weekend'
                ]],
                use_container_width=True,
                hide_index=True,
                column_config={
                    'fraud_rate': st.column_config.NumberColumn(format="%.2f%%"),
                    'is_weekend': st.column_config.CheckboxColumn(),
                }
            )
    
    except Exception as e:
        st.error(f"Error loading time data: {e}")

# TAB 5: Data Export
with tab5:
    st.subheader("📊 Export Data")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.info("💡 Download filtered data from other tabs or get complete views below:")
        
        if st.button("📥 Download All Merchants", key="export_merchants"):
            merchant_df = load_fraud_by_merchant()
            csv = merchant_df.to_csv(index=False)
            st.download_button(
                label="Merchants CSV",
                data=csv,
                file_name="all_merchants.csv",
                mime="text/csv"
            )
        
        if st.button("📥 Download All Locations", key="export_locations"):
            location_df = load_fraud_by_location()
            csv = location_df.to_csv(index=False)
            st.download_button(
                label="Locations CSV",
                data=csv,
                file_name="all_locations.csv",
                mime="text/csv"
            )
    
    with col2:
        if st.button("📥 Download All Customers", key="export_customers"):
            customer_df = load_fraud_by_customer()
            csv = customer_df.to_csv(index=False)
            st.download_button(
                label="Customers CSV",
                data=csv,
                file_name="all_customers.csv",
                mime="text/csv"
            )
        
        if st.button("📥 Download All Time Data", key="export_time"):
            time_df = load_fraud_by_time()
            csv = time_df.to_csv(index=False)
            st.download_button(
                label="Time Data CSV",
                data=csv,
                file_name="time_fraud_data.csv",
                mime="text/csv"
            )

# Footer
st.divider()
st.markdown("""
    <div style='text-align: center; color: gray; font-size: 12px;'>
    🔍 Fraud Detection Data Warehouse Dashboard | 
    📊 PostgreSQL Backend | 
    ⚡ Real-time Analytics
    </div>
    """, unsafe_allow_html=True)
