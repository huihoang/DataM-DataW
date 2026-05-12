"""
Fraud Detection - Modern Streamlit Web Application
Interactive dashboard for fraud prediction and model performance analysis
"""

import streamlit as st
import pandas as pd
import seaborn as sns
from pathlib import Path
import warnings
import base64

from page_about import render_about
from page_analysis_ann_model import render_analysis_ann_model
from page_dashboard import render_dashboard
from page_evaluation_models import render_evaluation_models
from page_prediction import render_prediction
from shared import load_models

warnings.filterwarnings('ignore')
FOOTER_LOGO_PATH = Path(__file__).resolve().parent / "LogoBK.png"
FOOTER_LOGO_BASE64 = (
    base64.b64encode(FOOTER_LOGO_PATH.read_bytes()).decode("utf-8") if FOOTER_LOGO_PATH.exists() else ""
)

# ============================================================================
# PAGE CONFIGURATION
# ============================================================================
st.set_page_config(
    page_title="Fraud Detection System",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================================
# MODERN CUSTOM STYLING
# ============================================================================
st.markdown("""
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.2/css/all.min.css">
<style>
    * {
        margin: 0;
        padding: 0;
        box-sizing: border-box;
        font-family: "Inter", sans-serif;
    }
    
    /* Main canvas — clean white; depth comes from card shadows */
    .main {
        background: #ffffff;
        padding: 0;
    }

    [data-testid="stAppViewContainer"] {
        background-color: #ffffff;
    }

    /* Push content below Streamlit top chrome (Deploy / menu) */
    .block-container {
        padding-top: 3rem !important;
        padding-bottom: 2rem;
        max-width: 1400px;
    }

    /* Page titles below our hero strip */
    .main [data-testid="stHeading"] h1,
    .main [data-testid="stMarkdownContainer"] h1 {
        margin-top: 0.85rem !important;
        letter-spacing: -0.025em;
        color: #0f172a;
        font-weight: 700;
    }

    .main [data-testid="stMarkdownContainer"] h2,
    .main [data-testid="stMarkdownContainer"] h3 {
        color: #1e293b;
        font-weight: 600;
    }

    .main [data-testid="stCaptionContainer"] p {
        color: #64748b !important;
        font-size: 0.9rem !important;
    }
    
    /* Header Section */
    .header-container {
        background: linear-gradient(135deg, #ffffff 0%, #fafbff 50%, #f8f7ff 100%);
        padding: 1.15rem 1.35rem;
        border-radius: 14px;
        color: #0f172a;
        margin-bottom: 1.35rem;
        margin-top: 0.25rem;
        box-shadow:
            0 12px 32px rgba(79, 70, 229, 0.07),
            0 4px 14px rgba(15, 23, 42, 0.06);
        border: 1px solid #e8e6ff;
    }
    
    .header-container h1 {
        font-size: 1.65rem;
        font-weight: 700;
        margin-bottom: 0;
        letter-spacing: -0.2px;
    }
    
    .header-container p {
        font-size: 0.9rem;
        color: #64748b;
        font-weight: 500;
    }

    .header-title {
        display: flex;
        align-items: center;
        gap: 0.75rem;
    }

    .header-title .fa-shield-halved {
        color: #7c6cff;
        font-size: 1.35rem;
    }

    .header-meta {
        display: flex;
        justify-content: space-between;
        align-items: center;
        gap: 1rem;
    }
    
    /* Metric Cards */
    .metric-card {
        background: rgba(255, 255, 255, 0.9);
        backdrop-filter: blur(6px);
        padding: 1.8rem;
        border-radius: 14px;
        text-align: center;
        box-shadow: 0 10px 28px rgba(15, 23, 42, 0.08);
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        border: 1px solid rgba(99, 102, 241, 0.12);
    }
    
    .metric-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 18px 36px rgba(79, 70, 229, 0.18);
        border: 1px solid rgba(99, 102, 241, 0.24);
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
        color: #4f46e5;
        margin-bottom: 0.5rem;
    }
    
    .metric-card .unit {
        color: #999;
        font-size: 0.9rem;
        font-weight: 500;
    }
    
    /* Section Cards */
    .section-card {
        background: rgba(255, 255, 255, 0.9);
        padding: 2rem;
        border-radius: 14px;
        margin: 1.5rem 0;
        box-shadow: 0 10px 28px rgba(15, 23, 42, 0.08);
        border-left: 5px solid #6366f1;
    }
    
    .section-card h2 {
        color: #333;
        margin-top: 0;
        margin-bottom: 1.5rem;
        font-size: 1.6rem;
        font-weight: 700;
    }

    /* Native Streamlit metric cards */
    [data-testid="stMetric"] {
        background: #ffffff;
        border: 1px solid #dfe5ee;
        border-radius: 14px;
        padding: 0.85rem 1rem;
        box-shadow: 0 10px 26px rgba(15, 23, 42, 0.08), 0 2px 8px rgba(15, 23, 42, 0.04);
    }

    [data-testid="stMetricLabel"] p {
        color: #475569;
        font-weight: 600;
    }

    [data-testid="stMetricValue"] {
        color: #111827;
    }

    /* Dashboard KPI strip (custom HTML — page_dashboard) */
    .kpi-strip {
        display: grid;
        grid-template-columns: repeat(4, minmax(0, 1fr));
        gap: 1rem;
        margin: 0 0 1.35rem 0;
    }

    @media (max-width: 1100px) {
        .kpi-strip {
            grid-template-columns: repeat(2, minmax(0, 1fr));
        }
    }

    @media (max-width: 560px) {
        .kpi-strip {
            grid-template-columns: 1fr;
        }
    }

    .kpi-card {
        display: flex;
        align-items: flex-start;
        gap: 0.85rem;
        padding: 1rem 1rem 1.05rem;
        border-radius: 14px;
        background: linear-gradient(145deg, #ffffff 0%, #fafbff 100%);
        border: 1px solid #e8eaf4;
        box-shadow:
            0 10px 28px rgba(79, 70, 229, 0.07),
            0 2px 10px rgba(15, 23, 42, 0.04);
        position: relative;
        overflow: hidden;
        min-height: 5.5rem;
    }

    .kpi-card::before {
        content: "";
        position: absolute;
        left: 0;
        top: 0;
        bottom: 0;
        width: 4px;
        border-radius: 14px 0 0 14px;
    }

    .kpi-card--indigo::before { background: linear-gradient(180deg, #6366f1, #4f46e5); }
    .kpi-card--rose::before { background: linear-gradient(180deg, #fb7185, #e11d48); }
    .kpi-card--amber::before { background: linear-gradient(180deg, #fbbf24, #d97706); }
    .kpi-card--violet::before { background: linear-gradient(180deg, #a78bfa, #7c3aed); }

    .kpi-card__icon {
        flex-shrink: 0;
        width: 2.5rem;
        height: 2.5rem;
        border-radius: 12px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.05rem;
    }

    .kpi-card--indigo .kpi-card__icon {
        background: rgba(99, 102, 241, 0.12);
        color: #4f46e5;
    }
    .kpi-card--rose .kpi-card__icon {
        background: rgba(244, 63, 94, 0.12);
        color: #e11d48;
    }
    .kpi-card--amber .kpi-card__icon {
        background: rgba(245, 158, 11, 0.14);
        color: #d97706;
    }
    .kpi-card--violet .kpi-card__icon {
        background: rgba(139, 92, 246, 0.14);
        color: #7c3aed;
    }

    .kpi-card__body {
        flex: 1;
        min-width: 0;
        display: flex;
        flex-direction: column;
        gap: 0.35rem;
    }

    .kpi-card__label {
        font-size: 0.72rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        color: #64748b;
        line-height: 1.25;
    }

    .kpi-card__value {
        font-size: clamp(1rem, 2.1vw, 1.45rem);
        font-weight: 800;
        color: #0f172a;
        letter-spacing: -0.02em;
        line-height: 1.25;
        word-break: break-word;
        overflow-wrap: anywhere;
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
        background: #7c6cff !important;
        color: white !important;
        border: none !important;
        border-radius: 10px !important;
        padding: 0.8rem 2rem !important;
        font-weight: 600 !important;
        font-size: 1rem !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 8px 18px rgba(124, 108, 255, 0.28) !important;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px) !important;
        background: #6a59ff !important;
        box-shadow: 0 10px 22px rgba(124, 108, 255, 0.34) !important;
    }

    .stButton > button:focus {
        outline: none !important;
        box-shadow: 0 0 0 3px rgba(129, 140, 248, 0.35), 0 12px 30px rgba(79, 70, 229, 0.28) !important;
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
        background: #ffffff;
        border-right: 1px solid #eef0f6;
    }

    [data-testid="stSidebar"] > div:first-child {
        padding-top: 1rem;
    }

    /* Sidebar System Status — themed panels (not Streamlit green/orange) */
    .sidebar-status {
        border-radius: 12px;
        padding: 12px 14px;
        font-size: 0.875rem;
        line-height: 1.55;
        border: 1px solid transparent;
        box-shadow: 0 8px 22px rgba(79, 70, 229, 0.12);
        margin-top: 4px;
    }

    .sidebar-status strong {
        display: block;
        font-weight: 700;
        margin-bottom: 6px;
        font-size: 0.92rem;
    }

    .sidebar-status ul {
        margin: 6px 0 0 1rem;
        padding: 0;
    }

    .sidebar-status--ok {
        background: linear-gradient(160deg, #f5f3ff 0%, #ede9fe 55%, #e8e4ff 100%);
        border-color: #c4b5fd;
        color: #3730a3;
    }

    .sidebar-status--ok strong {
        color: #4338ca;
    }

    .sidebar-status--warn {
        background: linear-gradient(160deg, #fffbeb 0%, #fef3c7 100%);
        border-color: #fcd34d;
        color: #92400e;
        box-shadow: 0 8px 22px rgba(217, 119, 6, 0.12);
    }

    .sidebar-status--warn strong {
        color: #b45309;
    }

    [data-testid="stSidebar"] [data-testid="stRadio"] > div {
        gap: 0.35rem;
        width: 100%;
    }

    [data-testid="stSidebar"] [data-testid="stRadio"] label {
        display: flex !important;
        align-items: center;
        width: 100% !important;
        background: transparent;
        border: 1px solid transparent;
        border-radius: 9px;
        padding: 8px 10px;
        transition: all 0.2s ease;
        margin: 0 !important;
    }

    [data-testid="stSidebar"] [data-testid="stRadio"] label > div:first-child {
        display: none !important;
    }

    [data-testid="stSidebar"] [data-testid="stRadio"] input[type="radio"] {
        display: none !important;
    }

    [data-testid="stSidebar"] [data-testid="stRadio"] label:hover {
        background: #f3f4f6;
        border-color: #e5e7eb;
    }

    [data-testid="stSidebar"] [data-testid="stRadio"] label:has(input:checked) {
        background: linear-gradient(135deg, #7c6cff 0%, #8b7bff 100%);
        border-color: #7c6cff;
        box-shadow: 0 8px 20px rgba(124, 108, 255, 0.28);
    }

    [data-testid="stSidebar"] [data-testid="stRadio"] label:has(input:checked) p {
        color: #ffffff !important;
        font-weight: 600;
    }
    
    /* Select boxes and inputs */
    .stSelectbox, .stSlider {
        background: transparent;
        padding: 0.5rem 0;
        border-radius: 10px;
    }

    div[data-baseweb="select"] > div,
    div[data-baseweb="input"] > div,
    div[data-baseweb="textarea"] > div {
        border-radius: 12px !important;
        border-color: #cbd5e1 !important;
        box-shadow: 0 2px 10px rgba(15, 23, 42, 0.04);
        background: rgba(255, 255, 255, 0.95);
    }

    div[data-baseweb="select"] > div:hover,
    div[data-baseweb="input"] > div:hover,
    div[data-baseweb="textarea"] > div:hover {
        border-color: #a5b4fc !important;
    }

    /* Expander polish */
    [data-testid="stExpander"] {
        border: 1px solid #dfe5ee !important;
        border-radius: 14px !important;
        background: #ffffff !important;
        box-shadow: 0 10px 26px rgba(15, 23, 42, 0.07), 0 2px 8px rgba(15, 23, 42, 0.04);
        overflow: hidden;
    }

    [data-testid="stExpander"] summary {
        background: linear-gradient(180deg, #ffffff 0%, #f8fafc 100%);
        border-radius: 14px;
        font-weight: 600;
    }

    /* Tabs and radio */
    [data-baseweb="tab-list"] {
        gap: 0.35rem;
        background: rgba(255, 255, 255, 0.8);
        padding: 0.35rem;
        border-radius: 12px;
        border: 1px solid #e2e8f0;
    }

    button[role="tab"] {
        border-radius: 10px !important;
    }

    [data-testid="stRadio"] label {
        font-weight: 500;
    }

    /* Dataframe container */
    [data-testid="stDataFrame"] {
        border: 1px solid #dfe5ee;
        border-radius: 12px;
        overflow: hidden;
        box-shadow: 0 8px 22px rgba(15, 23, 42, 0.06);
    }

    [data-testid="stVerticalBlockBorderWrapper"] {
        background: #ffffff;
        border: 1px solid #cfd8e8;
        border-radius: 14px;
        box-shadow:
            0 14px 36px rgba(15, 23, 42, 0.1),
            0 4px 12px rgba(15, 23, 42, 0.06);
        padding: 0.8rem 0.85rem 0.45rem;
        margin-bottom: 0.9rem;
    }

    /* Sidebar: hide any stray widget label above the nav radio */
    [data-testid="stSidebar"] [data-testid="stWidgetLabel"] {
        display: none !important;
    }

    /* Equal-height columns: bordered panels stretch to the taller sibling */
    [data-testid="stHorizontalBlock"],
    div.stHorizontalBlock,
    .stHorizontalBlock {
        display: flex !important;
        flex-direction: row !important;
        align-items: stretch !important;
        gap: 0.5rem;
    }

    [data-testid="stHorizontalBlock"] > [data-testid="column"],
    .stHorizontalBlock > [data-testid="column"] {
        display: flex !important;
        flex-direction: column !important;
        flex: 1 1 0 !important;
        min-width: 0 !important;
    }

    [data-testid="stHorizontalBlock"] > [data-testid="column"] > div,
    .stHorizontalBlock > [data-testid="column"] > div {
        flex: 1 1 auto !important;
        display: flex !important;
        flex-direction: column !important;
        min-height: 0 !important;
    }

    [data-testid="stHorizontalBlock"] [data-testid="stVerticalBlockBorderWrapper"],
    .stHorizontalBlock [data-testid="stVerticalBlockBorderWrapper"] {
        flex: 1 1 auto !important;
        display: flex !important;
        flex-direction: column !important;
        min-height: 0 !important;
        height: 100% !important;
        margin-bottom: 0 !important;
    }

    [data-testid="stHorizontalBlock"] [data-testid="stVerticalBlockBorderWrapper"] [data-testid="stPlotlyChart"],
    .stHorizontalBlock [data-testid="stVerticalBlockBorderWrapper"] [data-testid="stPlotlyChart"] {
        flex: 1 1 auto !important;
        min-height: 0 !important;
    }

    /* Streamlit 1.28.x fallback: horizontal row widget */
    div.row-widget.stHorizontal {
        display: flex !important;
        flex-direction: row !important;
        align-items: stretch !important;
        gap: 0.5rem;
    }

    div.row-widget.stHorizontal > [data-testid="column"] {
        display: flex !important;
        flex-direction: column !important;
        flex: 1 1 0 !important;
        min-width: 0 !important;
    }

    div.row-widget.stHorizontal > [data-testid="column"] > div {
        flex: 1 1 auto !important;
        display: flex !important;
        flex-direction: column !important;
        min-height: 0 !important;
    }

    div.row-widget.stHorizontal [data-testid="stVerticalBlockBorderWrapper"] {
        flex: 1 1 auto !important;
        display: flex !important;
        flex-direction: column !important;
        min-height: 0 !important;
        height: 100% !important;
        margin-bottom: 0 !important;
    }

    div.row-widget.stHorizontal [data-testid="stVerticalBlockBorderWrapper"] [data-testid="stPlotlyChart"] {
        flex: 1 1 auto !important;
        min-height: 0 !important;
    }

    [data-testid="stVerticalBlockBorderWrapper"] [data-testid="stPlotlyChart"] {
        background: #ffffff;
        border: 1px solid #eceff6;
        border-radius: 12px;
        padding: 0.2rem;
        overflow: hidden;
    }

    [data-testid="stVerticalBlockBorderWrapper"] [data-testid="stPlotlyChart"] > div,
    [data-testid="stVerticalBlockBorderWrapper"] .js-plotly-plot,
    [data-testid="stVerticalBlockBorderWrapper"] .plot-container,
    [data-testid="stVerticalBlockBorderWrapper"] .svg-container {
        width: 100% !important;
        max-width: 100% !important;
    }
    
    /* Footer */
    .sidebar-title {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        color: #0f172a;
        font-weight: 700;
        margin-bottom: 0.6rem;
    }

    .status-title {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        color: #0f172a;
        font-weight: 700;
        margin: 0.75rem 0 0.6rem;
    }

    .footer { text-align: center; padding: 1.25rem; color: #64748b; }
    .footer p { font-size: 0.85rem; margin: 4px 0; }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# HEADER SECTION
# ============================================================================
st.markdown("""
<div class="header-container">
    <div class="header-meta">
        <div>
            <div class="header-title">
                <i class="fa-solid fa-shield-halved"></i>
                <h1>Analytics Dashboard</h1>
            </div>
            <p>Fraud monitoring and model insights</p>
        </div>
        <i class="fa-solid fa-chart-simple" style="color:#7c6cff;font-size:1.15rem;"></i>
    </div>
</div>
""", unsafe_allow_html=True)

# ============================================================================
# SIDEBAR NAVIGATION
# ============================================================================
PAGES = {
    "Dashboard": render_dashboard,
    "Prediction": render_prediction,
    "Evaluation Models": render_evaluation_models,
    "Analysis ANN Model": render_analysis_ann_model,
    "About": render_about,
}

with st.sidebar:
    st.markdown(
        """
        <div class="sidebar-title">
            <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M3 5h18M3 12h18M3 19h18"/>
            </svg>
            <span>Navigation</span>
        </div>
        """,
        unsafe_allow_html=True,
    )
    page = st.radio(
        "page_nav",
        list(PAGES.keys()),
        label_visibility="hidden",
    )
    
    st.markdown("---")
    
    models = load_models()
    model_count = len(models) if models else 0
    model_status = "Ready" if model_count > 0 else "Unavailable"
    checked_at = pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")

    st.markdown(
        """
        <div class="status-title">
            <i class="fa-solid fa-signal"></i>
            <span>System Status</span>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if models:
        st.markdown(
            f"""
            <div class="sidebar-status sidebar-status--ok">
                <strong>Loaded models successfully</strong>
                <ul>
                    <li>Models loaded: {model_count}</li>
                    <li>Model registry: {model_status}</li>
                    <li>Inference mode: Real-time</li>
                </ul>
                <span style="display:block;margin-top:10px;font-size:0.8rem;opacity:0.92;">
                    Last health check: {checked_at}
                </span>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            """
            <div class="sidebar-status sidebar-status--warn">
                <strong>No models available</strong>
                <span style="display:block;margin-top:8px;font-size:0.82rem;">
                    Check your model artifacts folder and reload the app.
                </span>
            </div>
            """,
            unsafe_allow_html=True,
        )

PAGES[page]()

# ============================================================================
# FOOTER
# ============================================================================
st.markdown("---")
school_line = "Trường Đại học Bách Khoa ĐHQG-HCM"
if FOOTER_LOGO_BASE64:
    school_line = (
        f"<img src='data:image/png;base64,{FOOTER_LOGO_BASE64}' "
        "style='height:36px; width:auto; vertical-align:middle; margin-right:6px;'/>"
        f"{school_line}"
    )

st.markdown(f"""
<div class='footer'>
    <p class='footer-line'>{school_line}</p>
    <p class='footer-line'><strong>Fraud Detection System</strong> | Advanced ML Analytics</p>
    <p class='footer-line'>&copy; 2026 Data Warehouse + Data Mining Course Project | Developed by: Ng.H.Hoàng, Ng.T.Hoàng, Ng.D.Duy</p>
</div>
""", unsafe_allow_html=True)
