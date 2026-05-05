import streamlit as st
from db import run_query
import plotly.express as px
def render_dashboard() -> None:
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown(
            """
        <div class="metric-card">
            <h3>Models</h3>
            <div class="value">4</div>
            <div class="unit">Algorithms</div>
        </div>
        """,
            unsafe_allow_html=True,
        )

    with col2:
        st.markdown(
            """
        <div class="metric-card">
            <h3>Strategies</h3>
            <div class="value">2</div>
            <div class="unit">Training Methods</div>
        </div>
        """,
            unsafe_allow_html=True,
        )

    with col3:
        st.markdown(
            """
        <div class="metric-card">
            <h3>Features</h3>
            <div class="value">20</div>
            <div class="unit">Engineered</div>
        </div>
        """,
            unsafe_allow_html=True,
        )

    with col4:
        st.markdown(
            """
        <div class="metric-card">
            <h3>Thresholds</h3>
            <div class="value">3</div>
            <div class="unit">Tested</div>
        </div>
        """,
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(
        """
    <div class="section-card">
        <h2>📊 Dataset Overview</h2>
    </div>
    """,
        unsafe_allow_html=True,
    )

import streamlit as st
from db import run_query

def render_dashboard() -> None:
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown(
            """
        <div class="metric-card">
            <h3>Models</h3>
            <div class="value">4</div>
            <div class="unit">Algorithms</div>
        </div>
        """,
            unsafe_allow_html=True,
        )

    with col2:
        st.markdown(
            """
        <div class="metric-card">
            <h3>Strategies</h3>
            <div class="value">2</div>
            <div class="unit">Training Methods</div>
        </div>
        """,
            unsafe_allow_html=True,
        )

    with col3:
        st.markdown(
            """
        <div class="metric-card">
            <h3>Features</h3>
            <div class="value">20</div>
            <div class="unit">Engineered</div>
        </div>
        """,
            unsafe_allow_html=True,
        )

    with col4:
        st.markdown(
            """
        <div class="metric-card">
            <h3>Thresholds</h3>
            <div class="value">3</div>
            <div class="unit">Tested</div>
        </div>
        """,
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(
        """
    <div class="section-card">
        <h2>📊 Dataset Overview</h2>
    </div>
    """,
        unsafe_allow_html=True,
    )

    st.title("📊 Fraud Detection Dashboard")

    # ============================================================
    # LOAD DATA
    # ============================================================
    df_summary = run_query("SELECT * FROM dm_fraud_summary")

    df_time = run_query("""
        SELECT 
            hour,
            COUNT(*) as total_tx,
            SUM(CASE WHEN is_fraud = 1 THEN 1 ELSE 0 END) as fraud_count,
            ROUND(SUM(CASE WHEN is_fraud = 1 THEN 1 ELSE 0 END)*100.0/COUNT(*),2) as fraud_rate,
            AVG(amount) as avg_amount
        FROM fact_transactions f
        JOIN dim_time t ON f.time_id = t.time_id
        GROUP BY hour
        ORDER BY hour;
    """)

    df_merchant = run_query("""
        SELECT 
            merchant_name,
            COUNT(*) as total_transactions,
            SUM(CASE WHEN is_fraud = 1 THEN 1 ELSE 0 END) as fraud_count,
            ROUND(SUM(CASE WHEN is_fraud = 1 THEN 1 ELSE 0 END)*100.0/COUNT(*),2) as fraud_rate_pct,

            SUM(amount) as total_amount,
            SUM(CASE WHEN is_fraud = 1 THEN amount ELSE 0 END) as fraud_amount,

            AVG(amount) as avg_amount,
            MAX(amount) as max_amount,
            MIN(amount) as min_amount,

            COUNT(DISTINCT customer_id) as unique_customers

        FROM fact_transactions f
        JOIN dim_merchant m ON f.merchant_id = m.merchant_id
        GROUP BY merchant_name
        ORDER BY fraud_rate_pct DESC
        LIMIT 20;
    """)

    df_location = run_query("""
        SELECT 
            state,
            COUNT(*) as total_tx,
            SUM(CASE WHEN is_fraud = 1 THEN 1 ELSE 0 END) as fraud_count,
            ROUND(SUM(CASE WHEN is_fraud = 1 THEN 1 ELSE 0 END)*100.0/COUNT(*),2) as fraud_rate,
            SUM(amount) as total_amount
        FROM fact_transactions f
        JOIN dim_location l ON f.location_id = l.location_id
        GROUP BY state
        ORDER BY fraud_rate DESC;
    """)

    df_customer = run_query("""
        SELECT first_name, last_name, fraud_rate_pct
        FROM dm_customer_risk
        ORDER BY fraud_rate_pct DESC
        LIMIT 10
    """)
    # df_customer = run_query("""
    #     SELECT 
    #         customer_id,
    #         COUNT(*) as total_tx,
    #         SUM(CASE WHEN is_fraud = 1 THEN 1 ELSE 0 END) as fraud_count,
    #         ROUND(SUM(CASE WHEN is_fraud = 1 THEN 1 ELSE 0 END)*100.0/COUNT(*),2) as fraud_rate,
    #         SUM(amount) as total_spent
    #     FROM fact_transactions
    #     GROUP BY customer_id
    #     HAVING COUNT(*) > 10
    #     ORDER BY fraud_rate DESC
    #     LIMIT 20;
    # """)

    # ============================================================
    # LOAD: FRAUD BY MONTH
    # ============================================================
    df_month = run_query("""
        SELECT 
            month,
            month_name,
            SUM(total_transactions) as total_tx,
            SUM(fraud_count) as fraud_count,
            ROUND(SUM(fraud_count) * 100.0 / SUM(total_transactions), 2) as fraud_rate
        FROM dm_time_fraud
        GROUP BY month, month_name
        ORDER BY month
    """)
        # ============================================================
    # LOAD: CORRELATION DATA (STAGING)
    # ============================================================
    df_corr = run_query("""
        SELECT 
            amt,
            city_pop,
            unix_time,
            lat,
            long,
            merch_lat,
            merch_long,
            is_fraud
        FROM fraud_data
        LIMIT 5000
    """)
    # ============================================================
    # KPI
    # ============================================================
    if not df_summary.empty:
        total_tx = int(df_summary["total_transactions"][0])
        fraud_tx = int(df_summary["fraud_count"][0])
        fraud_rate = float(df_summary["fraud_rate_pct"][0])
        total_amount = float(df_summary["total_amount"][0])
    else:
        total_tx, fraud_tx, fraud_rate, total_amount = 0, 0, 0, 0

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("💳 Total Transactions", f"{total_tx:,}")
    col2.metric("⚠️ Fraud Transactions", f"{fraud_tx:,}")
    col3.metric("📉 Fraud Rate", f"{fraud_rate:.2f}%")
    col4.metric("💰 Total Amount", f"${total_amount:,.2f}")

    st.markdown("---")

    # ============================================================
    # CHARTS
    # ============================================================

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("⏰ Fraud Rate by Hour")
        if not df_time.empty:
            st.line_chart(df_time.set_index("hour"))

    with col2:
        st.subheader("🏪 Top Risky Merchants")
        if not df_merchant.empty:
            st.bar_chart(df_merchant.set_index("merchant_name"))


    col3, col4 = st.columns(2)

    with col3:
        st.subheader("🌍 Top Risky States")
        if not df_location.empty:
            st.bar_chart(df_location.set_index("state"))

    with col4:
        st.subheader("👤 High Risk Customers")
        if not df_customer.empty:
            df_customer["name"] = df_customer["first_name"] + " " + df_customer["last_name"]
            st.bar_chart(df_customer.set_index("name")["fraud_rate_pct"])
    st.markdown("---")
    st.subheader("📊 Advanced Analytics")

    col5, col6 = st.columns(2)

    # ============================================================
    # CHART: FRAUD BY GENDER
    # ============================================================
    # with col5:
    #     st.subheader("📅 Fraud Rate by Month")
    #     st.write(df_month)
    #     if not df_month.empty:
    #         fig = px.bar(
    #             df_month,
    #             x="month_name",
    #             y="fraud_rate",
    #             text="fraud_rate"
    #         )

    #         fig.update_traces(
    #             texttemplate='%{text:.2f}%',
    #             textposition='outside'
    #         )

    #         fig.update_layout(
    #             yaxis_title="Fraud Rate (%)",
    #             xaxis_title="Month"
    #         )

    #         st.plotly_chart(fig, width=True)
    with col5:
        st.subheader("📅 Fraud Rate by Month")

        if not df_month.empty:
            # đảm bảo đúng thứ tự tháng
            df_month = df_month.sort_values("month")

            # convert sang float + scale %
            df_month["fraud_rate"] = df_month["fraud_rate"].astype(float) * 100

            # tạo biểu đồ
            fig = px.bar(
                df_month,
                x="month_name",
                y="fraud_rate",
                text="fraud_rate"
            )

            # hiển thị % trên đầu cột
            fig.update_traces(
                texttemplate='%{text:.2f}%',
                textposition='outside'
            )

            # layout đẹp hơn
            fig.update_layout(
                yaxis_title="Fraud Rate (%)",
                xaxis_title="Month",
                yaxis=dict(range=[0, df_month["fraud_rate"].max() + 5])
            )

            # streamlit render (fix warning mới)
            st.plotly_chart(fig, width="stretch")

        else:
            st.warning("No data available for Fraud by Month")


    # ============================================================
    # CHART: CORRELATION MATRIX
    # ============================================================
    with col6:
        st.subheader("🔗 Correlation Matrix")

        if not df_corr.empty:
            import pandas as pd

            corr = df_corr.corr(numeric_only=True)
            st.dataframe(corr)



    st.markdown("---")
    st.subheader("🧠 Insights")

    peak_hour = df_time.loc[df_time["fraud_rate"].idxmax(), "hour"] if not df_time.empty else "N/A"
    top_merchant = df_merchant.iloc[0]["merchant_name"] if not df_merchant.empty else "N/A"
    top_state = df_location.iloc[0]["state"] if not df_location.empty else "N/A"

    st.markdown(f"""
    <div class="section-card" style="font-size:18px; line-height:1.8">

    <h2>🔎 Key Findings</h2>

    <ul>
    <li>⏰ Peak fraud hour: <b>{peak_hour}:00</b></li>
    <li>🏪 Most risky merchant: <b>{top_merchant}</b></li>
    <li>🌍 Highest fraud state: <b>{top_state}</b></li>
    <li>📉 Overall fraud rate: <b>{fraud_rate:.2f}%</b></li>
    </ul>

    <h2>📊 Behavior Patterns</h2>

    <ul>
    <li>Fraud tăng mạnh vào các khung giờ đêm</li>
    <li>Một số merchant có mức độ rủi ro vượt trội (outliers)</li>
    <li>Fraud có xu hướng phân bố theo khu vực địa lý</li>
    <li>Hành vi khách hàng có phân bố lệch (skewed distribution)</li>
    </ul>

    </div>
    """, unsafe_allow_html=True)

    # ============================================================
    # RAW DATA
    # ============================================================
    with st.expander("📋 View Raw Data"):
        st.dataframe(df_merchant)
        st.dataframe(df_location)
        st.dataframe(df_customer)