from pathlib import Path

import joblib
import pandas as pd
import streamlit as st

PROJECT_ROOT = Path(__file__).parent.parent
ARTIFACTS_PATH = PROJECT_ROOT / "artifacts"
MODELS_PATH = ARTIFACTS_PATH / "modeling_results" / "trained_models"

FEATURE_NAMES = [
    "amt",
    "amt_log",
    "trans_count_hourly",
    "amt_x_distance",
    "hour",
    "merchant_avg_amount",
    "merchant_fraud_rate",
    "is_weekend",
    "merchant_trans_count",
    "age",
    "trans_count_daily",
    "dayofweek",
    "time_since_last_transaction_min",
    "month",
    "city_pop",
    "lat",
    "long",
    "distance_km",
    "merch_long",
    "merch_lat",
]


@st.cache_resource
def load_models():
    models_dict = {}
    if not MODELS_PATH.exists():
        # st.toast("Error model_path not found", icon="❌")
        return None

    for model_file in MODELS_PATH.glob("*.pkl"):
        try:
            models_dict[model_file.stem] = joblib.load(str(model_file))
        except Exception:
            # st.toast("Error loading model", icon="❌")
            pass

    return models_dict if models_dict else None


@st.cache_data
def load_model_results(threshold: str = "0.2"):
    try:
        results_file = ARTIFACTS_PATH / "modeling_results" / f"model_comparison_threshold_{threshold}.csv"
        if results_file.exists():
            return pd.read_csv(results_file)
    except Exception:
        pass
    return None
