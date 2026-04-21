"""
Fraud Detection - Modern Streamlit Web Application
Interactive dashboard for fraud prediction and model performance analysis
"""

import streamlit as st
import pandas as pd
import seaborn as sns
from pathlib import Path
import warnings

from page_about import render_about
from page_analysis_ann_model import render_analysis_ann_model
from page_dashboard import render_dashboard
from page_evaluation_models import render_evaluation_models
from page_prediction import render_prediction
from shared import load_models

warnings.filterwarnings('ignore')

# ============================================================================
# PAGE CONFIGURATION
# ============================================================================
st.set_page_config(
    page_title="Fraud Detection System",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================================
# MODERN CUSTOM STYLING
# ============================================================================
st.markdown("""
<style>
    * {
        margin: 0;
        padding: 0;
        box-sizing: border-box;
    }
    
    /* Main background */
    .main {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        padding: 0;
    }
    
    .block-container {
        padding-top: 1.5rem;
    }
    
    /* Header Section */
    .header-container {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 3rem 2rem;
        border-radius: 15px;
        color: white;
        margin-bottom: 2rem;
        box-shadow: 0 20px 60px rgba(102, 126, 234, 0.4);
    }
    
    .header-container h1 {
        font-size: 2.8rem;
        font-weight: 800;
        margin-bottom: 0.5rem;
        letter-spacing: -1px;
    }
    
    .header-container p {
        font-size: 1.1rem;
        opacity: 0.95;
        font-weight: 500;
    }
    
    /* Metric Cards */
    .metric-card {
        background: white;
        padding: 1.8rem;
        border-radius: 12px;
        text-align: center;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.08);
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        border: 1px solid rgba(102, 126, 234, 0.1);
    }
    
    .metric-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 20px 40px rgba(102, 126, 234, 0.2);
        border: 1px solid rgba(102, 126, 234, 0.3);
    }
    
    .metric-card h3 {
        color: #333;
        font-size: 1rem;
        margin-bottom: 0.8rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    .metric-card .value {
        font-size: 2.5rem;
        font-weight: 700;
        color: #667eea;
        margin-bottom: 0.5rem;
    }
    
    .metric-card .unit {
        color: #999;
        font-size: 0.9rem;
        font-weight: 500;
    }
    
    /* Section Cards */
    .section-card {
        background: white;
        padding: 2rem;
        border-radius: 12px;
        margin: 1.5rem 0;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.08);
        border-left: 5px solid #667eea;
    }
    
    .section-card h2 {
        color: #333;
        margin-top: 0;
        margin-bottom: 1.5rem;
        font-size: 1.6rem;
        font-weight: 700;
    }
    
    /* Alert Boxes */
    .fraud-alert {
        background: linear-gradient(135deg, #ff6b6b 0%, #ee5a6f 100%);
        color: white;
        padding: 2rem;
        border-radius: 12px;
        margin: 1rem 0;
        box-shadow: 0 10px 30px rgba(255, 107, 107, 0.3);
        border-left: 5px solid #c92a2a;
    }
    
    .fraud-alert h3 {
        margin: 0 0 0.5rem 0;
        font-size: 1.4rem;
    }
    
    .safe-alert {
        background: linear-gradient(135deg, #51cf66 0%, #37b24d 100%);
        color: white;
        padding: 2rem;
        border-radius: 12px;
        margin: 1rem 0;
        box-shadow: 0 10px 30px rgba(81, 207, 102, 0.3);
        border-left: 5px solid #2f9e44;
    }
    
    .safe-alert h3 {
        margin: 0 0 0.5rem 0;
        font-size: 1.4rem;
    }
    
    /* Info/Warning/Success boxes */
    .info-box {
        background: linear-gradient(135deg, #4c6ef5 0%, #5c7cfa 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 5px solid #364fc7;
        margin: 1rem 0;
    }
    
    .warning-box {
        background: linear-gradient(135deg, #ffa94d 0%, #fd7e14 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 5px solid #e67700;
        margin: 1rem 0;
    }
    
    .success-box {
        background: linear-gradient(135deg, #69db7c 0%, #51cf66 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 5px solid #2f9e44;
        margin: 1rem 0;
    }
    
    /* Buttons */
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 10px !important;
        padding: 0.8rem 2rem !important;
        font-weight: 600 !important;
        font-size: 1rem !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 10px 30px rgba(102, 126, 234, 0.3) !important;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 15px 40px rgba(102, 126, 234, 0.4) !important;
    }
    
    /* Sliders */
    .stSlider {
        padding: 1rem 0;
    }
    
    /* Tables */
    table {
        border-collapse: collapse;
        font-size: 0.95rem;
    }
    
    table thead {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
    }
    
    table th {
        padding: 1rem;
        text-align: left;
        font-weight: 600;
    }
    
    table td {
        padding: 0.8rem 1rem;
        border-bottom: 1px solid #eee;
    }
    
    table tr:hover {
        background: #f9f9f9;
    }
    
    /* Sidebar */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #ffffff 0%, #f8f9ff 100%);
        border-right: 2px solid #e8eaf6;
    }
    
    /* Select boxes and inputs */
    .stSelectbox, .stSlider {
        background: white;
        padding: 1rem;
        border-radius: 10px;
    }
    
    /* Footer */
    .footer {
        text-align: center;
        padding: 2rem;
        color: #999;
        font-size: 0.9rem;
        border-top: 1px solid #eee;
        margin-top: 3rem;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# HEADER SECTION
# ============================================================================
st.markdown("""
<div class="header-container">
    <h1>🔍 Fraud Detection System</h1>
    <p>Advanced Machine Learning Analytics for Transaction Risk Assessment</p>
</div>
""", unsafe_allow_html=True)

# ============================================================================
# SIDEBAR NAVIGATION
# ============================================================================
PAGES = {
    "🏠 Dashboard": render_dashboard,
    "🎯 Prediction": render_prediction,
    "📊 Evaluation Models": render_evaluation_models,
    "📈 Analysis ANN Model": render_analysis_ann_model,
    "ℹ️ About": render_about,
}

with st.sidebar:
    st.markdown("### 📍 Navigation")
    page = st.radio(
        "Select Page",
        list(PAGES.keys()),
        label_visibility="collapsed"
    )
    
    st.markdown("---")
    
    models = load_models()
    model_count = len(models) if models else 0
    model_status = "Ready" if model_count > 0 else "Unavailable"
    checked_at = pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")

    st.markdown("### 🛰️ System Status")
    if models:
        st.success(f"""✅ Loaded models successfully\n
💠Models loaded: {model_count}\n
💠Model registry: {model_status}\n
💠Inference mode: Real-time\n
Last health check: {checked_at}""")
    else:
        st.warning("⚠️ No models available")

PAGES[page]()

# ============================================================================
# FOOTER
# ============================================================================
st.markdown("---")
st.markdown("""
<div style='text-align: center; padding: 2rem; color: #999;'>
    <p><strong>🔍 Fraud Detection System</strong> | Advanced ML Analytics</p>
    <p style='font-size: 0.85rem;'>© 2026 Data Warehouse + Data Mining Course Project</p>
</div>
""", unsafe_allow_html=True)
