import numpy as np
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
import sqlite3
import joblib
from pathlib import Path

from shared import FEATURE_NAMES, load_models

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PIPELINE_DIR = PROJECT_ROOT / "Source" / "artifacts" / "modeling_results" / "pipelines"


@st.cache_data(show_spinner=False)
def query_transactions_from_sqlite(
    db_path: str,
    table_name: str,
    datetime_col: str,
    year: int,
    month: int,
    day: int | None = None,
) -> pd.DataFrame:
    where_sql = f"""
        CAST(strftime('%Y', {datetime_col}) AS INTEGER) = ?
        AND CAST(strftime('%m', {datetime_col}) AS INTEGER) = ?
    """
    params: list[int] = [year, month]

    if day is not None:
        where_sql += f" AND CAST(strftime('%d', {datetime_col}) AS INTEGER) = ?"
        params.append(day)

    query = f"""
        SELECT *
        FROM {table_name}
        WHERE {where_sql}
        ORDER BY {datetime_col} ASC
    """
    with sqlite3.connect(db_path) as conn:
        return pd.read_sql_query(query, conn, params=params)


@st.cache_resource(show_spinner=False)
def load_inference_pipeline(pipeline_path: str):
    return joblib.load(pipeline_path)


def render_prediction() -> None:
    with st.expander("🎯 Single Transaction Prediction", expanded=True):
        st.markdown(
            """
        <div class="section-card">
            <h2>🎯 Single Transaction Prediction</h2>
            <p>Enter transaction details to get real-time fraud probability prediction</p>
        </div>
        """,
            unsafe_allow_html=True,
        )
        models = load_models()
        col1, _ = st.columns(2)

        with col1:
            selected_model = st.selectbox("🤖 Select Model", ["All Models"] + (list(models.keys()) if models else ["Demo"]))
        # with col2:
        #     threshold = st.slider(
        #         "📊 Decision Threshold",
        #         min_value=0.0,
        #         max_value=1.0,
        #         value=0.5,
        #         step=0.05
        #     )
        
        st.markdown("---")
        st.markdown("### 📝 Transaction Features")

        feature_values = {}
        field_descriptions = {
            "amt": "Raw transaction amount.",
            "trans_count_hourly": "Number of transactions in the current hour.",
            "hour": "Hour of transaction (0-23).",
            "merchant_avg_amount": "Average transaction amount for this merchant.",
            "merchant_fraud_rate": "Historical fraud rate of merchant.",
            "is_weekend": "1 if weekend, else 0.",
            "merchant_trans_count": "Total transactions of merchant.",
            "age": "Cardholder age.",
            "trans_count_daily": "Transactions in the current day.",
            "dayofweek": "Day of week (0=Mon, 6=Sun).",
            "time_since_last_transaction_min": "Minutes since last transaction.",
            "month": "Month (1-12).",
            "city_pop": "Population of the city.",
            "lat": "Cardholder latitude.",
            "long": "Cardholder longitude.",
            "distance_km": "Distance between user and merchant.",
            "merch_long": "Merchant longitude.",
            "merch_lat": "Merchant latitude.",
        }
        ranges = {
            "amt": (0, 10000, 100),
            "trans_count_hourly": (0, 50, 1),
            "hour": (0, 23, 12),
            "merchant_avg_amount": (0, 10000, 100),
            "merchant_fraud_rate": (0, 1, 0.1),
            "is_weekend": (0, 1, 0),
            "merchant_trans_count": (0, 100000, 100),
            "age": (18, 100, 30),
            "trans_count_daily": (0, 200, 5),
            "dayofweek": (0, 6, 3),
            "time_since_last_transaction_min": (0, 1e6, 1000),
            "month": (1, 12, 6),
            "city_pop": (0, 1e7, 500000),
            "lat": (-90, 90, 10),
            "long": (-180, 180, 106),
            "distance_km": (0, 20000, 50),
            "merch_long": (-180, 180, 106),
            "merch_lat": (-90, 90, 10),
        }
        steps = {
            "amt": 1.0,
            "trans_count_hourly": 1.0,
            "hour": 1,
            "merchant_avg_amount": 1.0,
            "merchant_fraud_rate": 0.01,
            "is_weekend": 1,
            "merchant_trans_count": 1.0,
            "age": 1,
            "trans_count_daily": 1.0,
            "dayofweek": 1,
            "time_since_last_transaction_min": 1.0,
            "month": 1,
            "city_pop": 1000,
            "lat": 0.0001,
            "long": 0.0001,
            "distance_km": 1.0,
            "merch_long": 0.0001,
            "merch_lat": 0.0001,
        }

        display_features = [f for f in FEATURE_NAMES if f not in ["amt_log", "amt_x_distance"]]
        col_count = 3
        for i in range(0, len(display_features), col_count):
            cols = st.columns(col_count)
            for j, feature in enumerate(display_features[i : i + col_count]):
                with cols[j]:
                    min_v, max_v, def_v = ranges.get(feature, (0, 100, 50))
                    step_v = steps.get(feature, 1.0)
                    help_text = field_descriptions.get(feature, "No description available.")

                    if feature == "is_weekend":
                        feature_values[feature] = st.radio(
                            feature, [0, 1], horizontal=True, key=f"pred_{feature}", help=help_text
                        )
                    else:
                        feature_values[feature] = st.slider(
                            feature,
                            min_value=float(min_v),
                            max_value=float(max_v),
                            value=float(def_v),
                            step=float(step_v),
                            key=f"pred_{feature}",
                            help=help_text,
                        )

        feature_values["amt_log"] = np.log1p(feature_values["amt"])
        feature_values["amt_x_distance"] = feature_values["amt"] * feature_values["distance_km"]

        st.markdown("---")
        if st.button("🔍 Predict Fraud", width="stretch"):
            features_array = [feature_values[f] for f in FEATURE_NAMES]
            df = pd.DataFrame([features_array], columns=FEATURE_NAMES)

            if selected_model == "All Models" and models:
                results = []
                for name, model in models.items():
                    try:
                        prob = model.predict_proba(df)[0, 1]
                        label = model.predict(df)[0]
                        results.append({"Model": name, "Fraud Probability": prob, "Prediction": "Fraud" if label == 1 else "Normal"})
                    except Exception:
                        results.append({"Model": name, "Fraud Probability": None, "Prediction": "Error"})

                results_df = pd.DataFrame(results).sort_values(by="Fraud Probability", ascending=False)
                styled_df = results_df.style.format({"Fraud Probability": "{:%}"}).background_gradient(
                    subset=["Fraud Probability"], cmap="Reds"
                )
                st.dataframe(styled_df, width="stretch")
            else:
                if models and selected_model in models:
                    try:
                        prob = models[selected_model].predict_proba(df)[0, 1]
                        label = models[selected_model].predict(df)[0]
                    except Exception:
                        st.toast("Error predicting probability", icon="❌")
                        st.error("Error predicting probability. Please another model!")
                        return
                else:
                    st.toast("Error loading model", icon="❌")
                    st.error("Check your model folder! There is no model to load.")
                    return

                st.markdown("<br>", unsafe_allow_html=True)
                col1, col2, col3 = st.columns(3)
                with col1:
                    if label == 1:
                        st.markdown(
                            """
                        <div class="fraud-alert">
                            <h3>🚨 FRAUD ALERT</h3>
                            <p>High-risk transaction detected</p>
                        </div>
                        """,
                            unsafe_allow_html=True,
                        )
                    else:
                        st.markdown(
                            """
                        <div class="safe-alert">
                            <h3>✅ LEGITIMATE</h3>
                            <p>Transaction appears safe</p>
                        </div>
                        """,
                            unsafe_allow_html=True,
                        )
                with col2:
                    st.metric("Fraud Probability", f"{prob}", f"{prob*100:.2f}%")
                with col3:
                    normal_prob = max(1 - prob, prob)
                    st.metric("Normal Probability", f"{normal_prob:.2%}")


    with st.expander("🎯 Pipline Transaction Prediction", expanded=True):
        st.markdown(
            """
        <div class="section-card">
            <h2>🎯 Pipline Transaction Prediction</h2>
            <p>Query transaction in Database to get real-time fraud probability prediction</p>
        </div>
        """,
            unsafe_allow_html=True,
        )

    st.markdown("### 🗃️ Query + Batch Predict")
    c1, c2, c3 = st.columns(3)
    with c1:
        db_path = st.text_input("SQLite DB Path", value=str(PROJECT_ROOT / "Source" / "data" / "fraud.db"))
    with c2:
        table_name = st.text_input("Table Name", value="transactions")
    with c3:
        datetime_col = st.text_input("Datetime Column", value="trans_date_trans_time")

    c4, c5, c6 = st.columns(3)
    with c4:
        q_year = st.number_input("Year", min_value=2000, max_value=2100, value=2020, step=1)
    with c5:
        q_month = st.selectbox("Month", list(range(1, 13)), index=0)
    with c6:
        day_options = ["All days (month)"] + [str(d) for d in range(1, 32)]
        q_day_opt = st.selectbox("Day", day_options, index=0)
        q_day = None if q_day_opt == "All days (month)" else int(q_day_opt)

    pipeline_files = sorted([p.name for p in PIPELINE_DIR.glob("*.pkl")]) if PIPELINE_DIR.exists() else []
    selected_pipeline = st.selectbox(
        "Inference Pipeline (.pkl)",
        pipeline_files if pipeline_files else ["No pipeline found"],
    )

    if st.button("📦 Query + Predict + Plot", width="stretch"):
        if not pipeline_files:
            st.error("No pipeline .pkl found. Please export one from notebook first.")
            return

        try:
            query_df = query_transactions_from_sqlite(
                db_path=db_path,
                table_name=table_name,
                datetime_col=datetime_col,
                year=int(q_year),
                month=int(q_month),
                day=q_day,
            )
        except Exception as exc:
            st.error(f"Query failed: {exc}")
            return

        if query_df.empty:
            st.warning("No data found for selected period.")
            return

        try:
            pipeline = load_inference_pipeline(str(PIPELINE_DIR / selected_pipeline))
            pred_labels = pipeline.predict(query_df)
            if hasattr(pipeline, "predict_proba"):
                pred_probs = pipeline.predict_proba(query_df)[:, 1]
            else:
                pred_probs = np.full(shape=len(pred_labels), fill_value=np.nan)
        except Exception as exc:
            st.error(f"Predict failed: {exc}")
            return

        result_df = query_df.copy().reset_index(drop=True)
        result_df["pred_label"] = pred_labels
        result_df["pred_prob"] = pred_probs
        result_df[datetime_col] = pd.to_datetime(result_df[datetime_col], errors="coerce")
        result_df["day"] = result_df[datetime_col].dt.day

        grouped = (
            result_df.groupby(["day", "pred_label"])
            .size()
            .unstack(fill_value=0)
            .rename(columns={0: "Normal", 1: "Fraud"})
        )
        grouped = grouped.reindex(range(1, 31), fill_value=0)

        st.success(f"Predicted {len(result_df):,} rows using `{selected_pipeline}`")
        st.dataframe(result_df[[datetime_col, "pred_prob", "pred_label"]].head(200), width="stretch")

        fig, ax = plt.subplots(figsize=(14, 5))
        x = np.arange(len(grouped.index))
        bar_w = 0.42
        ax.bar(x - bar_w / 2, grouped["Normal"].values, width=bar_w, label="Normal")
        ax.bar(x + bar_w / 2, grouped["Fraud"].values, width=bar_w, label="Fraud")
        ax.set_xticks(x)
        ax.set_xticklabels(grouped.index)
        ax.set_xlabel("Day of month")
        ax.set_ylabel("Transaction count")
        ax.set_title("Normal vs Fraud predictions by day (30 days)")
        ax.legend()
        ax.grid(axis="y", alpha=0.3)
        plt.tight_layout()
        st.pyplot(fig)
    