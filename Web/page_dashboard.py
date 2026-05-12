import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

from db import run_query


def _section_title(icon_html: str, text: str) -> None:
    st.markdown(
        f"""
        <div style="display:flex;align-items:center;gap:8px;margin:8px 0 10px 0;">
            {icon_html}
            <h3 style="margin:0;color:#0f172a;font-size:1.05rem;font-weight:700;">{text}</h3>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _safe_query(query: str) -> pd.DataFrame:
    try:
        return run_query(query)
    except Exception as exc:
        st.warning(f"Unable to load a dashboard block: {exc}")
        return pd.DataFrame()


def _apply_modern_plot_style(fig, height: int = 420):
    fig.update_layout(
        height=height,
        margin=dict(l=10, r=10, t=45, b=10),
        template="plotly_white",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(255,255,255,0.95)",
    )
    return fig


def _render_kpi_strip(
    total_tx: int,
    fraud_tx: int,
    fraud_rate: float,
    total_amount: float,
) -> None:
    tx_fmt = f"{total_tx:,}"
    fraud_fmt = f"{fraud_tx:,}"
    rate_fmt = f"{fraud_rate:.2f}%"
    amt_fmt = f"${total_amount:,.2f}"

    st.markdown(
        f"""
        <div class="kpi-strip">
            <div class="kpi-card kpi-card--indigo">
                <div class="kpi-card__icon"><i class="fa-solid fa-layer-group" aria-hidden="true"></i></div>
                <div class="kpi-card__body">
                    <span class="kpi-card__label">Total Transactions</span>
                    <span class="kpi-card__value">{tx_fmt}</span>
                </div>
            </div>
            <div class="kpi-card kpi-card--rose">
                <div class="kpi-card__icon"><i class="fa-solid fa-shield-virus" aria-hidden="true"></i></div>
                <div class="kpi-card__body">
                    <span class="kpi-card__label">Fraud Transactions</span>
                    <span class="kpi-card__value">{fraud_fmt}</span>
                </div>
            </div>
            <div class="kpi-card kpi-card--amber">
                <div class="kpi-card__icon"><i class="fa-solid fa-chart-pie" aria-hidden="true"></i></div>
                <div class="kpi-card__body">
                    <span class="kpi-card__label">Fraud Rate</span>
                    <span class="kpi-card__value">{rate_fmt}</span>
                </div>
            </div>
            <div class="kpi-card kpi-card--violet">
                <div class="kpi-card__icon"><i class="fa-solid fa-sack-dollar" aria-hidden="true"></i></div>
                <div class="kpi-card__body">
                    <span class="kpi-card__label">Total Amount</span>
                    <span class="kpi-card__value">{amt_fmt}</span>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_dashboard() -> None:
    st.title("Fraud Intelligence Dashboard")
    st.caption("Live monitoring of transaction fraud risk across time, merchants, customers, and geography.")

    df_summary = _safe_query("SELECT * FROM dm_fraud_summary")

    df_time = _safe_query(
        """
        SELECT
            hour,
            COUNT(*) AS total_tx,
            SUM(CASE WHEN is_fraud = 1 THEN 1 ELSE 0 END) AS fraud_count,
            ROUND(SUM(CASE WHEN is_fraud = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) AS fraud_rate
        FROM fact_transactions f
        JOIN dim_time t ON f.time_id = t.time_id
        GROUP BY hour
        ORDER BY hour;
        """
    )

    df_merchant = _safe_query(
        """
        SELECT
            merchant_name,
            COUNT(*) AS total_transactions,
            SUM(CASE WHEN is_fraud = 1 THEN 1 ELSE 0 END) AS fraud_count,
            ROUND(SUM(CASE WHEN is_fraud = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) AS fraud_rate_pct,
            SUM(CASE WHEN is_fraud = 1 THEN amount ELSE 0 END) AS fraud_amount
        FROM fact_transactions f
        JOIN dim_merchant m ON f.merchant_id = m.merchant_id
        GROUP BY merchant_name
        ORDER BY fraud_rate_pct DESC
        LIMIT 20;
        """
    )

    df_location = _safe_query(
        """
        SELECT
            state,
            COUNT(*) AS total_tx,
            SUM(CASE WHEN is_fraud = 1 THEN 1 ELSE 0 END) AS fraud_count,
            ROUND(SUM(CASE WHEN is_fraud = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) AS fraud_rate
        FROM fact_transactions f
        JOIN dim_location l ON f.location_id = l.location_id
        GROUP BY state
        ORDER BY fraud_rate DESC;
        """
    )

    df_geo = _safe_query(
        """
        SELECT
            l.state,
            AVG(l.lat) AS lat,
            AVG(l.long) AS lon,
            COUNT(*) AS total_tx,
            SUM(CASE WHEN f.is_fraud = 1 THEN 1 ELSE 0 END) AS fraud_count,
            ROUND(SUM(CASE WHEN f.is_fraud = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) AS fraud_rate
        FROM fact_transactions f
        JOIN dim_location l ON f.location_id = l.location_id
        GROUP BY l.state
        HAVING AVG(l.lat) IS NOT NULL AND AVG(l.long) IS NOT NULL
        ORDER BY fraud_rate DESC;
        """
    )

    df_customer = _safe_query(
        """
        SELECT first_name, last_name, fraud_rate_pct
        FROM dm_customer_risk
        ORDER BY fraud_rate_pct DESC
        LIMIT 10;
        """
    )

    df_month = _safe_query(
        """
        SELECT
            month,
            month_name,
            SUM(total_transactions) AS total_tx,
            SUM(fraud_count) AS fraud_count,
            ROUND(SUM(fraud_count) * 100.0 / SUM(total_transactions), 2) AS fraud_rate
        FROM dm_time_fraud
        GROUP BY month, month_name
        ORDER BY month;
        """
    )

    df_corr = _safe_query(
        """
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
        LIMIT 5000;
        """
    )

    if not df_summary.empty:
        total_tx = int(df_summary["total_transactions"].iloc[0])
        fraud_tx = int(df_summary["fraud_count"].iloc[0])
        fraud_rate = float(df_summary["fraud_rate_pct"].iloc[0])
        total_amount = float(df_summary["total_amount"].iloc[0])
    else:
        total_tx, fraud_tx, fraud_rate, total_amount = 0, 0, 0.0, 0.0

    _render_kpi_strip(total_tx, fraud_tx, fraud_rate, total_amount)

    row_1_col_1, row_1_col_2 = st.columns(2)
    with row_1_col_1:
        with st.container(border=True):
            _section_title(
                '<i class="fa-solid fa-chart-line" style="color:#4f46e5;"></i>',
                "Fraud Trend by Hour",
            )
            if not df_time.empty:
                fig_time = px.line(
                    df_time,
                    x="hour",
                    y="fraud_rate",
                    markers=True,
                    labels={"hour": "Hour of Day", "fraud_rate": "Fraud Rate (%)"},
                    color_discrete_sequence=["#6366f1"],
                )
                _apply_modern_plot_style(fig_time)
                st.plotly_chart(fig_time, width="stretch")
            else:
                st.info("No hourly trend data available.")

    with row_1_col_2:
        with st.container(border=True):
            _section_title(
                '<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" fill="none" viewBox="0 0 24 24" stroke="#4f46e5" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M3 7h18M6 7v11a2 2 0 0 0 2 2h8a2 2 0 0 0 2-2V7M9 7V5a3 3 0 0 1 6 0v2"/></svg>',
                "Top Risky Merchants",
            )
            if not df_merchant.empty:
                fig_merchant = px.bar(
                    df_merchant.head(12),
                    x="merchant_name",
                    y="fraud_rate_pct",
                    color="fraud_count",
                    labels={"merchant_name": "Merchant", "fraud_rate_pct": "Fraud Rate (%)"},
                    color_continuous_scale="Reds",
                )
                fig_merchant.update_layout(xaxis_tickangle=-30)
                _apply_modern_plot_style(fig_merchant)
                st.plotly_chart(fig_merchant, width="stretch")
            else:
                st.info("No merchant risk data available.")

    _section_title(
        '<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" fill="none" viewBox="0 0 24 24" stroke="#4f46e5" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M12 21c-4.97 0-9-4.03-9-9 0-4.97 4.03-9 9-9 4.97 0 9 4.03 9 9 0 4.97-4.03 9-9 9Z"/><path stroke-linecap="round" stroke-linejoin="round" d="M12 7v5l3 3"/></svg>',
        "Geospatial Fraud Risk",
    )
    geo_col_1, geo_col_2 = st.columns([2, 1])

    _geo_chart_h = 480

    with geo_col_1:
        with st.container(border=True):
            _section_title(
                '<i class="fa-solid fa-map-location-dot" style="color:#4f46e5;"></i>',
                "US risk map",
            )
            if not df_geo.empty:
                df_geo_plot = df_geo.copy()
                # Use percentile-based color so close fraud_rate values are still distinguishable.
                df_geo_plot["risk_percentile"] = df_geo_plot["fraud_rate"].rank(pct=True) * 100
                fig_map = px.choropleth(
                    df_geo_plot,
                    locations="state",
                    locationmode="USA-states",
                    color="risk_percentile",
                    hover_data={
                        "fraud_rate": ":.2f",
                        "risk_percentile": ":.1f",
                        "fraud_count": True,
                        "total_tx": True,
                    },
                    color_continuous_scale=[
                        [0.0, "#dbeafe"],
                        [0.25, "#93c5fd"],
                        [0.5, "#60a5fa"],
                        [0.75, "#2563eb"],
                        [1.0, "#1e3a8a"],
                    ],
                    scope="usa",
                )
                fig_map.update_layout(
                    height=_geo_chart_h,
                    margin=dict(l=0, r=0, t=8, b=36),
                    coloraxis_colorbar=dict(title="Risk percentile"),
                    geo=dict(
                        bgcolor="rgba(0,0,0,0)",
                        showlakes=True,
                        lakecolor="#f1f5f9",
                    ),
                    annotations=[
                        dict(
                            text="Color = relative fraud risk percentile by state",
                            xref="paper",
                            yref="paper",
                            x=0.5,
                            y=-0.02,
                            showarrow=False,
                            font=dict(size=11, color="#64748b"),
                            xanchor="center",
                        )
                    ],
                )
                st.plotly_chart(fig_map, width="stretch")
            else:
                st.info("No coordinate data found for location map.")

    with geo_col_2:
        with st.container(border=True):
            _section_title(
                '<i class="fa-solid fa-location-dot" style="color:#4f46e5;"></i>',
                "State Risk Ranking",
            )
            if not df_location.empty:
                top_states = df_location[["state", "fraud_rate", "fraud_count"]].head(10).copy()
                top_states = top_states.sort_values("fraud_rate", ascending=True)
                fig_state_rank = px.bar(
                    top_states,
                    x="fraud_rate",
                    y="state",
                    orientation="h",
                    color="fraud_count",
                    text="fraud_rate",
                    labels={"fraud_rate": "Fraud Rate (%)", "state": ""},
                    color_continuous_scale="Blues",
                )
                fig_state_rank.update_traces(texttemplate="%{text:.2f}%", textposition="outside")
                fig_state_rank.update_layout(
                    height=_geo_chart_h,
                    margin=dict(l=0, r=0, t=8, b=36),
                    xaxis_title="Fraud Rate (%)",
                    yaxis_title="",
                    coloraxis_colorbar=dict(title="Fraud cases"),
                )
                st.plotly_chart(fig_state_rank, width="stretch")
            else:
                st.info("No state-level fraud data available.")

    row_3_col_1, row_3_col_2 = st.columns(2)
    with row_3_col_1:
        with st.container(border=True):
            _section_title(
                '<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" fill="none" viewBox="0 0 24 24" stroke="#4f46e5" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M8 2v4M16 2v4M3 10h18M5 5h14a2 2 0 0 1 2 2v12a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V7a2 2 0 0 1 2-2Z"/></svg>',
                "Fraud Rate by Month",
            )
            if not df_month.empty:
                df_month_plot = df_month.sort_values("month").copy()
                fig_month = px.bar(
                    df_month_plot,
                    x="month_name",
                    y="fraud_rate",
                    text="fraud_rate",
                    color="fraud_rate",
                    color_continuous_scale="Blues",
                    labels={"month_name": "Month", "fraud_rate": "Fraud Rate (%)"},
                )
                fig_month.update_traces(texttemplate="%{text:.2f}%", textposition="outside")
                _apply_modern_plot_style(fig_month)
                st.plotly_chart(fig_month, width="stretch")
            else:
                st.info("No monthly fraud data available.")

    with row_3_col_2:
        with st.container(border=True):
            _section_title(
                '<i class="fa-solid fa-table-cells-large" style="color:#4f46e5;"></i>',
                "Correlation Matrix",
            )
            if not df_corr.empty:
                corr = df_corr.corr(numeric_only=True)
                fig_corr = px.imshow(
                    corr,
                    text_auto=".2f",
                    color_continuous_scale="RdBu",
                    zmin=-1,
                    zmax=1,
                    aspect="auto",
                )
                _apply_modern_plot_style(fig_corr)
                st.plotly_chart(fig_corr, width="stretch")
            else:
                st.info("No feature correlation data available.")

    row_4_col_1, row_4_col_2 = st.columns(2)
    with row_4_col_1:
        with st.container(border=True):
            _section_title(
                '<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" fill="none" viewBox="0 0 24 24" stroke="#4f46e5" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M17 21v-2a4 4 0 0 0-4-4H7a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path stroke-linecap="round" stroke-linejoin="round" d="M23 21v-2a4 4 0 0 0-3-3.87"/><path stroke-linecap="round" stroke-linejoin="round" d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>',
                "High Risk Customers",
            )
            if not df_customer.empty:
                df_customer_plot = df_customer.copy()
                df_customer_plot["name"] = df_customer_plot["first_name"] + " " + df_customer_plot["last_name"]
                fig_customer = px.bar(
                    df_customer_plot,
                    x="name",
                    y="fraud_rate_pct",
                    color="fraud_rate_pct",
                    color_continuous_scale="OrRd",
                    labels={"name": "Customer", "fraud_rate_pct": "Fraud Rate (%)"},
                )
                fig_customer.update_layout(xaxis_tickangle=-25)
                _apply_modern_plot_style(fig_customer)
                st.plotly_chart(fig_customer, width="stretch")
            else:
                st.info("No customer risk data available.")

    with row_4_col_2:
        with st.container(border=True):
            peak_hour = df_time.loc[df_time["fraud_rate"].idxmax(), "hour"] if not df_time.empty else "N/A"
            top_merchant = df_merchant.iloc[0]["merchant_name"] if not df_merchant.empty else "N/A"
            top_state = df_location.iloc[0]["state"] if not df_location.empty else "N/A"
            _section_title(
                '<i class="fa-solid fa-lightbulb" style="color:#4f46e5;"></i>',
                "Key Insights",
            )
            st.markdown(
                f"""
                <div class="section-card">
                    <p><strong>Peak fraud hour:</strong> {peak_hour}:00</p>
                    <p><strong>Most risky merchant:</strong> {top_merchant}</p>
                    <p><strong>Highest risk state:</strong> {top_state}</p>
                    <p><strong>Overall fraud rate:</strong> {fraud_rate:.2f}%</p>
                </div>
                """,
                unsafe_allow_html=True,
            )
