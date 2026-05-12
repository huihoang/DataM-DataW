import numpy as np
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
import joblib
from pathlib import Path
import re
import sys
from sqlalchemy import create_engine, text
from sklearn.base import BaseEstimator, TransformerMixin

from shared import FEATURE_NAMES, load_models

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PIPELINE_DIR = PROJECT_ROOT / "artifacts" / "pipeline_artifact"

IDENTIFIER_LIKE_COLS = [
    "Unnamed: 0",
    "cc_num",
    "first",
    "last",
    "street",
    "zip",
    "trans_num",
    "unix_time",
    "trans_date_trans_time",
    "dob",
    "city",
    "merchant",
]

ADVANCED_FEATURE_COLUMNS = [
    "trans_count_hourly",
    "trans_count_daily",
    "merchant_fraud_rate",
    "merchant_trans_count",
    "merchant_avg_amount",
    "amt_x_distance",
    "age_group",
    "time_since_last_transaction_min",
]


def haversine_np(lat1, lon1, lat2, lon2):
    lat1 = np.radians(pd.to_numeric(lat1, errors="coerce"))
    lon1 = np.radians(pd.to_numeric(lon1, errors="coerce"))
    lat2 = np.radians(pd.to_numeric(lat2, errors="coerce"))
    lon2 = np.radians(pd.to_numeric(lon2, errors="coerce"))
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = np.sin(dlat / 2.0) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2.0) ** 2
    c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a))
    return 6371.0 * c


def add_eda_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["trans_date_trans_time"] = pd.to_datetime(df["trans_date_trans_time"], errors="coerce")
    df["dob"] = pd.to_datetime(df["dob"], errors="coerce")
    df["hour"] = df["trans_date_trans_time"].dt.hour
    df["dayofweek"] = df["trans_date_trans_time"].dt.dayofweek
    df["month"] = df["trans_date_trans_time"].dt.month
    df["is_weekend"] = (df["dayofweek"] >= 5).astype(int)
    age_days = (df["trans_date_trans_time"] - df["dob"]).dt.days
    df["age"] = (age_days / 365.25).clip(lower=0)
    df["distance_km"] = haversine_np(df["lat"], df["long"], df["merch_lat"], df["merch_long"])
    df["amt_log"] = np.log1p(pd.to_numeric(df["amt"], errors="coerce"))
    return df


def add_advanced_features(df: pd.DataFrame, train_stats: dict | None = None) -> pd.DataFrame:
    df = df.copy()
    df["trans_date_trans_time"] = pd.to_datetime(df["trans_date_trans_time"], errors="coerce")
    existing_generated = [col for col in ADVANCED_FEATURE_COLUMNS if col in df.columns]
    if existing_generated:
        df = df.drop(columns=existing_generated, errors="ignore")

    df = df.sort_values(["cc_num", "trans_date_trans_time"]).reset_index(drop=True)
    df["trans_hour_bucket"] = df["trans_date_trans_time"].dt.floor("h")
    df["trans_day_bucket"] = df["trans_date_trans_time"].dt.floor("D")
    df["trans_count_hourly"] = df.groupby(["cc_num", "trans_hour_bucket"]).cumcount() + 1
    df["trans_count_daily"] = df.groupby(["cc_num", "trans_day_bucket"]).cumcount() + 1

    merchant_stats = (train_stats or {}).get("merchant_stats")
    if merchant_stats is not None and "merchant" in df.columns:
        df = df.merge(merchant_stats, on="merchant", how="left", validate="m:1")
    else:
        # Fallback to NaN if train stats unavailable in artifact.
        df["merchant_fraud_rate"] = np.nan
        df["merchant_trans_count"] = np.nan
        df["merchant_avg_amount"] = np.nan

    df["amt_x_distance"] = pd.to_numeric(df["amt"], errors="coerce") * pd.to_numeric(df["distance_km"], errors="coerce")
    df["age_group"] = pd.cut(
        pd.to_numeric(df["age"], errors="coerce"),
        bins=[0, 18, 25, 35, 45, 55, 65, 200],
        labels=["<18", "18-25", "26-35", "36-45", "46-55", "56-65", "65+"],
        include_lowest=True,
    )
    df["time_since_last_transaction_min"] = (
        df.groupby("cc_num")["trans_date_trans_time"].diff().dt.total_seconds().div(60).fillna(0)
    )
    df = df.drop(columns=["trans_hour_bucket", "trans_day_bucket"], errors="ignore")
    return df


def add_model_features(df: pd.DataFrame) -> pd.DataFrame:
    return df.drop(columns=IDENTIFIER_LIKE_COLS, errors="ignore").copy()


class PreprocessingTransformer(BaseEstimator, TransformerMixin):
    def __init__(self, train_stats):
        self.train_stats = train_stats

    def fit(self, X, y=None):
        return self

    def transform(self, X):
        df_out = add_eda_features(X)
        df_out = add_advanced_features(df_out, train_stats=self.train_stats)
        df_out = add_model_features(df_out)
        return df_out


class FeatureSelector(BaseEstimator, TransformerMixin):
    def __init__(self, feature_columns):
        self.feature_columns = list(feature_columns)

    def fit(self, X, y=None):
        return self

    def transform(self, X):
        missing = [col for col in self.feature_columns if col not in X.columns]
        if missing:
            raise ValueError(f"columns are missing: {set(missing)}")
        return X[self.feature_columns].copy()


class NumericFillna(BaseEstimator, TransformerMixin):
    def __init__(self, fill_values):
        self.fill_values = fill_values

    def fit(self, X, y=None):
        return self

    def transform(self, X):
        return X.fillna(self.fill_values)


def register_pipeline_compat_classes() -> None:
    class_map = {
        "PreprocessingTransformer": PreprocessingTransformer,
        "FeatureSelector": FeatureSelector,
        "NumericFillna": NumericFillna,
    }
    for mod_name in ("main", "__main__"):
        mod = sys.modules.get(mod_name)
        if mod is None:
            continue
        for cls_name, cls in class_map.items():
            if not hasattr(mod, cls_name):
                setattr(mod, cls_name, cls)


@st.cache_data(show_spinner=False)
def query_transactions_from_postgres(
    db_url: str,
    year: int,
    month: int | None = None,
) -> pd.DataFrame:
    datetime_col = "trans_date_trans_time"
    # Allow only simple identifiers to avoid SQL injection via table/column names.

    where_sql = f"""
        EXTRACT(YEAR FROM {datetime_col}::timestamp) = :year
    """
    params: dict[str, int] = {"year": year}
    if month is not None:
        where_sql += f" AND EXTRACT(MONTH FROM {datetime_col}::timestamp) = :month"
        params["month"] = month

    sql = text(f"""
        SELECT
            trans_num,
            trans_date_trans_time,
            cc_num,
            merchant,
            category,
            amt,
            first,
            last,
            gender,
            street,
            city,
            state,
            zip,
            lat,
            long,
            city_pop,
            job,
            dob,
            unix_time,
            merch_lat,
            merch_long,
            is_fraud,
            data_split
        FROM public.fraud_data
        WHERE {where_sql}
        ORDER BY {datetime_col}::timestamp ASC
    """)
    engine = create_engine(db_url)
    with engine.connect() as conn:
        return pd.read_sql(sql, conn, params=params)


@st.cache_resource(show_spinner=False)
def load_inference_pipeline(pipeline_path: str):
    register_pipeline_compat_classes()
    return load_with_stubbed_main_classes(pipeline_path)


def load_with_stubbed_main_classes(pipeline_path: str, max_retry: int = 8):
    """
    Handle joblib artifacts exported from notebook scope where custom classes
    were serialized under __main__/main module names.
    """
    pattern = re.compile(r"Can't get attribute '([^']+)' on <module '([^']+)'")
    stubbed_classes: list[str] = []

    for _ in range(max_retry):
        try:
            return joblib.load(pipeline_path)
        except Exception as exc:
            msg = str(exc)
            match = pattern.search(msg)
            if not match:
                raise

            missing_cls, target_module_name = match.group(1), match.group(2)
            target_module = sys.modules.get(target_module_name)
            if target_module is None:
                target_module = sys.modules.get("__main__")
            if target_module is None:
                raise

            if hasattr(target_module, missing_cls):
                raise

            # Minimal placeholder transformer so unpickling can continue.
            stub_cls = type(
                missing_cls,
                (),
                {
                    "__init__": lambda self, *args, **kwargs: self.__dict__.update(kwargs),
                    "fit": lambda self, X=None, y=None: self,
                    "transform": lambda self, X: X,
                },
            )
            setattr(target_module, missing_cls, stub_cls)
            stubbed_classes.append(missing_cls)

    raise RuntimeError(f"Failed to load pipeline after stubbing classes: {stubbed_classes}")


def render_prediction() -> None:
    with st.expander("Single Transaction Prediction", expanded=False):
        st.markdown(
            """
        <div class="section-card">
            <h2><i class="fa-solid fa-bolt" style="color:#4f46e5;margin-right:8px;"></i>Single Transaction Prediction</h2>
            <p>Enter transaction details to get real-time fraud probability prediction</p>
        </div>
        """,
            unsafe_allow_html=True,
        )
        models = load_models()
        col1, _ = st.columns(2)

        with col1:
            selected_model = st.selectbox("Select Model", ["All Models"] + (list(models.keys()) if models else ["Demo"]))
        # with col2:
        #     threshold = st.slider(
        #         "📊 Decision Threshold",
        #         min_value=0.0,
        #         max_value=1.0,
        #         value=0.5,
        #         step=0.05
        #     )
        
        st.markdown("---")
        st.markdown("### Transaction Features")

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

        display_features = [f for f in FEATURE_NAMES if f not in ["amt_log", "amt_x_distance", "is_weekend", "distance_km"]]
        col_count = 3
        for i in range(0, len(display_features), col_count):
            cols = st.columns(col_count)
            for j, feature in enumerate(display_features[i : i + col_count]):
                with cols[j]:
                    min_v, max_v, def_v = ranges.get(feature, (0, 100, 50))
                    step_v = steps.get(feature, 1.0)
                    help_text = field_descriptions.get(feature, "No description available.")

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
        dayofweek_value = int(feature_values.get("dayofweek", 0))
        feature_values["is_weekend"] = 1 if dayofweek_value >= 5 else 0
        feature_values["distance_km"] = float(
            haversine_np(
                feature_values["lat"],
                feature_values["long"],
                feature_values["merch_lat"],
                feature_values["merch_long"],
            )
        )
        feature_values["amt_x_distance"] = feature_values["amt"] * feature_values["distance_km"]

        st.markdown("---")
        if st.button("Predict Fraud", width="stretch"):
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
                        st.toast("Error predicting probability")
                        st.error("Error predicting probability. Please another model!")
                        return
                else:
                    st.toast("Error loading model")
                    st.error("Check your model folder! There is no model to load.")
                    return

                st.markdown("<br>", unsafe_allow_html=True)
                col1, col2, col3 = st.columns(3)
                with col1:
                    if label == 1:
                        st.markdown(
                            """
                        <div class="fraud-alert">
                            <h3>FRAUD ALERT</h3>
                            <p>High-risk transaction detected</p>
                        </div>
                        """,
                            unsafe_allow_html=True,
                        )
                    else:
                        st.markdown(
                            """
                        <div class="safe-alert">
                            <h3>LEGITIMATE</h3>
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


    with st.expander("Batch Transaction Prediction", expanded=False):
        st.markdown(
            """
        <div class="section-card">
            <h2><i class="fa-solid fa-database" style="color:#4f46e5;margin-right:8px;"></i>Batch Transaction Prediction</h2>
            <p>Query transaction in Database to get real-time fraud probability prediction</p>
        </div>
        """,
            unsafe_allow_html=True,
        )

        with st.expander("Configure connection to database", expanded=True):
            c1, c2, c3 = st.columns(3)
            with c1:
                db_user = st.text_input("DB User")
            with c2:
                db_password = st.text_input("DB Password",  type="password")
            with c3:
                db_host = st.text_input("DB Host", value="localhost")

            c4, c5, c6 = st.columns(3)
            with c4:
                db_port = st.number_input("DB Port", min_value=1, max_value=65535, value=5432, step=1)
            with c5:
                db_name = st.text_input("DB Name")
            with c6:
                st.text_input("Source Table", value="fraud_data", disabled=True)

        with st.expander("Query", expanded=True):
            c7, c8, c9 = st.columns(3)
            with c7:
                q_year = st.number_input("Year", min_value=2000, max_value=2100, value=2020, step=1)
            with c8:
                query_mode = st.selectbox("Query Mode", ["Year + Month", "Full Year"], index=0)
            with c9:
                if query_mode == "Year + Month":
                    q_month = st.selectbox("Month", list(range(1, 13)), index=0)
                else:
                    q_month = None
                    st.selectbox("Month", ["All months"], index=0, disabled=True)

            datetime_col = "trans_date_trans_time"

        db_url = f"postgresql+psycopg2://{db_user}:{db_password}@{db_host}:{int(db_port)}/{db_name}"

        pipeline_files = sorted([p.name for p in PIPELINE_DIR.glob("*.pkl")]) if PIPELINE_DIR.exists() else []
        selected_pipeline = st.selectbox(
            "Inference Pipeline (.pkl)",
            pipeline_files if pipeline_files else ["No pipeline found"],
        )

        if st.button("Predict Batch", width="stretch"):
            if not pipeline_files:
                st.error("No pipeline .pkl found. Please export one from notebook first.")
                return

            try:
                query_df = query_transactions_from_postgres(
                    db_url=db_url,
                    year=int(q_year),
                    month=int(q_month) if q_month is not None else None,
                )
            except Exception as exc:
                st.error(f"Query failed: {exc}")
                return

            if query_df.empty:
                st.warning("No data found for selected period.")
                return

            required_columns = [
                "trans_date_trans_time",
                "dob",
                "cc_num",
                "merchant",
                "amt",
                "lat",
                "long",
                "merch_lat",
                "merch_long",
                "city_pop",
            ]
            missing_cols = [c for c in required_columns if c not in query_df.columns]
            if missing_cols:
                st.error(f"Query thiếu cột đầu vào cho pipeline: {missing_cols}")
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

            if query_mode == "Full Year":
                result_df["time_bucket"] = result_df[datetime_col].dt.month
                grouped = (
                    result_df.groupby(["time_bucket", "pred_label"])
                    .size()
                    .unstack(fill_value=0)
                    .rename(columns={0: "Normal", 1: "Fraud"})
                )
                grouped = grouped.reindex(range(1, 13), fill_value=0)
                x_label = "Month"
                chart_title = "Normal vs Fraud predictions by month (full year)"
            else:
                result_df["time_bucket"] = result_df[datetime_col].dt.day
                grouped = (
                    result_df.groupby(["time_bucket", "pred_label"])
                    .size()
                    .unstack(fill_value=0)
                    .rename(columns={0: "Normal", 1: "Fraud"})
                )
                grouped = grouped.reindex(range(1, 31), fill_value=0)
                x_label = "Day of month"
                chart_title = "Normal vs Fraud predictions by day (month view)"

            st.success(f"Predicted {len(result_df):,} rows using `{selected_pipeline}`")
            st.markdown("#### Probability list")
            st.dataframe(
                result_df[[datetime_col, "pred_prob", "pred_label"]].sort_values("pred_prob", ascending=False).head(500),
                width="stretch",
            )

            st.markdown("#### Visualization Predictions")
            fig, ax = plt.subplots(figsize=(14, 5))
            x = np.arange(len(grouped.index))
            bar_w = 0.42
            normal_bars = ax.bar(x - bar_w / 2, grouped["Normal"].values, width=bar_w, label="Normal")
            fraud_bars = ax.bar(x + bar_w / 2, grouped["Fraud"].values, width=bar_w, label="Fraud")
            ax.set_xticks(x)
            ax.set_xticklabels(grouped.index)
            ax.set_xlabel(x_label)
            ax.set_ylabel("Transaction count")
            ax.set_title(chart_title)
            ax.legend()
            ax.grid(axis="y", alpha=0.3)

            # Add value labels on each bar so low-fraud counts are still visible.
            normal_labels = [f"{int(v):,}" if v > 0 else "" for v in grouped["Normal"].values]
            fraud_labels = [f"{int(v):,}" if v > 0 else "" for v in grouped["Fraud"].values]
            ax.bar_label(normal_bars, labels=normal_labels, padding=2, fontsize=8)
            ax.bar_label(fraud_bars, labels=fraud_labels, padding=2, fontsize=8)

            plt.tight_layout()
            st.pyplot(fig)
    