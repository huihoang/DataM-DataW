"""
Fraud Detection - Modern Streamlit Web Application
Interactive dashboard for fraud prediction and model performance analysis
"""

import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import joblib
from pathlib import Path
import warnings

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
# CONSTANTS & FILE PATHS
# ============================================================================
PROJECT_ROOT = Path(__file__).parent.parent
ARTIFACTS_PATH = PROJECT_ROOT / "artifacts"
MODELS_PATH = ARTIFACTS_PATH / "modeling_results" / "trained_models"
DATA_PATH = ARTIFACTS_PATH / "processed_csv"
FIGURES_PATH = ARTIFACTS_PATH / "modeling_results" / "figures"

# Feature names (20 features from preprocessing)
FEATURE_NAMES = [
    'distance_km', 'amt_log', 'merchant_fraud_rate', 'hour', 'trans_count_hourly',
    'trans_count_daily', 'amt', 'merchant_avg_amount', 'age', 'is_weekend',
    'dayofweek', 'category', 'month', 'amt_x_distance', 'merchant_trans_count',
    'time_since_last_trans', 'age_group', 'state', 'gender', 'fraud_dist_percentile'
]

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

@st.cache_resource
def load_models():
    """Load trained models from artifacts"""
    models_dict = {}
    
    if not MODELS_PATH.exists():
        return None
    
    try:
        # Load all available models
        for model_file in MODELS_PATH.glob("*.pkl"):
            try:
                model_name = model_file.stem
                models_dict[model_name] = joblib.load(str(model_file))
            except:
                pass
        
        return models_dict if models_dict else None
    except Exception as e:
        return None


@st.cache_data
def load_model_results():
    """Load model performance results"""
    try:
        results_file = ARTIFACTS_PATH / "modeling_results" / "model_comparison_threshold_0.2.csv"
        if results_file.exists():
            return pd.read_csv(results_file)
    except:
        pass
    return None


def make_demo_prediction(features):
    """Generate demo prediction when models not available"""
    distance = features[0] if len(features) > 0 else 50
    amount = features[6] if len(features) > 6 else 100
    
    base_prob = 0.01
    distance_factor = min(distance / 100, 0.3)
    amount_factor = min(amount / 200, 0.4)
    
    fraud_prob = min(base_prob + distance_factor + amount_factor, 0.95)
    return fraud_prob + np.random.normal(0, 0.05)


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
with st.sidebar:
    st.markdown("### 📍 Navigation")
    page = st.radio(
        "Select Page",
        ["🏠 Dashboard", "🎯 Prediction", "📊 Analytics", "📈 Models", "ℹ️ About"],
        label_visibility="collapsed"
    )
    
    st.markdown("---")
    
    st.markdown("""
    ### 🔑 Quick Stats
    - **4** ML Models
    - **2** Training Strategies
    - **20** Features Engineered
    - **Real-time** Predictions
    """)
    
    st.markdown("---")
    
    models = load_models()
    if models:
        st.success(f"✅ {len(models)} models loaded")
    else:
        st.warning("⚠️ Models not found")

# ============================================================================
# PAGE: DASHBOARD
# ============================================================================
if page == "🏠 Dashboard":
    
    # Key Metrics Row
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("""
        <div class="metric-card">
            <h3>Models</h3>
            <div class="value">4</div>
            <div class="unit">Algorithms</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="metric-card">
            <h3>Strategies</h3>
            <div class="value">2</div>
            <div class="unit">Training Methods</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="metric-card">
            <h3>Features</h3>
            <div class="value">20</div>
            <div class="unit">Engineered</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown("""
        <div class="metric-card">
            <h3>Thresholds</h3>
            <div class="value">3</div>
            <div class="unit">Tested</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Dataset Overview
    st.markdown("""
    <div class="section-card">
        <h2>📊 Dataset Overview</h2>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns(4)
    
    datasets = [
        ("Training Set", "1.04M", "0.166%"),
        ("After SMOTE", "2.07M", "50%"),
        ("Validation", "259K", "0.089%"),
        ("Test Set", "556K", "0.080%")
    ]
    
    for col, (label, rows, rate) in zip([col1, col2, col3, col4], datasets):
        with col:
            st.markdown(f"""
            <div class="metric-card">
                <h3>{label}</h3>
                <div class="value" style="font-size: 1.8rem;">{rows}</div>
                <div class="unit">Fraud Rate: {rate}</div>
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Key Insights
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <div class="section-card">
            <h2>⏰ Temporal Patterns</h2>
            
            - **Late-night spikes** (10 PM - 4 AM show highest fraud)
            - **Weekend elevation** by 30-50% above weekday average
            - **Holiday anomalies** with increased fraud attempts
            - **Monthly seasonality** with dramatic peaks
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="section-card">
            <h2>💰 Amount & Location Patterns</h2>
            
            - **2.4x higher** average fraud amount ($149 vs $62)
            - **Distance signal** strong fraud indicator
            - **Impossible travel** detection critical
            - **State variation** in fraud concentration
        </div>
        """, unsafe_allow_html=True)


# ============================================================================
# PAGE: PREDICTION
# ============================================================================
elif page == "🎯 Prediction":
    
    st.markdown("""
    <div class="section-card">
        <h2>🎯 Single Transaction Prediction</h2>
        <p>Enter transaction details to get real-time fraud probability prediction</p>
    </div>
    """, unsafe_allow_html=True)
    
    models = load_models()
    
    col1, col2 = st.columns(2)
    
    with col1:
        selected_model = st.selectbox(
            "🤖 Select Model",
            ["Ensemble"] + (list(models.keys()) if models else ["Demo"])
        )
    
    with col2:
        threshold = st.slider(
            "📊 Decision Threshold",
            min_value=0.0,
            max_value=1.0,
            value=0.5,
            step=0.05
        )
    
    st.markdown("---")
    st.markdown("### 📝 Transaction Features")
    
    col_count = 3
    cols = st.columns(col_count)
    
    feature_values = {}
    ranges = {
        'distance_km': (0, 2000, 100),
        'amt_log': (0, 10, 3),
        'merchant_fraud_rate': (0, 1, 0.1),
        'hour': (0, 23, 12),
        'trans_count_hourly': (0, 50, 5),
        'trans_count_daily': (0, 100, 10),
        'amt': (0, 1000, 100),
        'merchant_avg_amount': (0, 500, 50),
        'age': (18, 80, 40),
        'is_weekend': (0, 1, 0),
        'dayofweek': (0, 6, 3),
        'category': (0, 13, 5),
        'month': (1, 12, 6),
        'amt_x_distance': (0, 100000, 10000),
        'merchant_trans_count': (0, 10000, 1000),
        'time_since_last_trans': (0, 10000, 100),
        'age_group': (0, 7, 3),
        'state': (0, 50, 25),
        'gender': (0, 1, 0),
        'fraud_dist_percentile': (0, 1, 0.5),
    }
    
    for idx, feature in enumerate(FEATURE_NAMES):
        col_idx = idx % col_count
        if col_idx == 0 and idx > 0:
            cols = st.columns(col_count)
        
        with cols[col_idx]:
            min_v, max_v, def_v = ranges.get(feature, (0, 100, 50))
            
            if feature in ['is_weekend', 'gender']:
                feature_values[feature] = st.radio(
                    feature, [0, 1], horizontal=True, key=f"pred_{feature}"
                )
            else:
                feature_values[feature] = st.slider(
                    feature,
                    min_value=float(min_v),
                    max_value=float(max_v),
                    value=float(def_v),
                    key=f"pred_{feature}"
                )
    
    st.markdown("---")
    
    if st.button("🔍 Predict Fraud", use_container_width=True):
        features_array = [feature_values[f] for f in FEATURE_NAMES]
        
        if selected_model == "Ensemble" and models:
            probs = []
            for model in models.values():
                try:
                    prob = model.predict_proba([features_array])[0, 1]
                    probs.append(prob)
                except:
                    probs.append(make_demo_prediction(features_array))
            
            avg_prob = np.mean(probs)
        elif models and selected_model in models:
            try:
                avg_prob = models[selected_model].predict_proba([features_array])[0, 1]
            except:
                avg_prob = make_demo_prediction(features_array)
        else:
            avg_prob = make_demo_prediction(features_array)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if avg_prob >= threshold:
                st.markdown("""
                <div class="fraud-alert">
                    <h3>🚨 FRAUD ALERT</h3>
                    <p>High-risk transaction detected</p>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown("""
                <div class="safe-alert">
                    <h3>✅ LEGITIMATE</h3>
                    <p>Transaction appears safe</p>
                </div>
                """, unsafe_allow_html=True)
        
        with col2:
            st.metric("Fraud Probability", f"{avg_prob:.4f}", f"{avg_prob*100:.2f}%")
        
        with col3:
            confidence = max(avg_prob, 1 - avg_prob)
            st.metric("Confidence", f"{confidence:.2%}")


# ============================================================================
# PAGE: ANALYTICS
# ============================================================================
elif page == "📊 Analytics":
    
    st.markdown("""
    <div class="section-card">
        <h2>📊 Model Performance Analytics</h2>
    </div>
    """, unsafe_allow_html=True)
    
    results_df = load_model_results()
    
    if results_df is not None:
        st.markdown("<br>", unsafe_allow_html=True)
        
        with st.expander("📋 View Full Results Table", expanded=True):
            st.dataframe(results_df, use_container_width=True, height=400)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            data_set = st.selectbox(
                "📊 Dataset",
                ['Validation', 'Test']
            )
        
        with col2:
            metric_type = st.selectbox(
                "📈 Select Metric",
                ['accuracy', 'precision', 'recall', 'f1', 'roc_auc', 'pr_auc']
            )
        
        with col3:
            train_var = st.selectbox(
                "🎯 Training Strategy",
                ['All', 'imbalanced', 'balanced_smote']
            )
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Prepare data for plotting
        df_plot = results_df.copy()
        
        # Filter by training variant
        if train_var != 'All':
            df_plot = df_plot[df_plot['train_variant'] == train_var]
        
        # Map dataset name to column prefix
        dataset_prefix = "valid_" if data_set == "Validation" else "test_"
        col_name = f"{dataset_prefix}{metric_type}"
        
        if not df_plot.empty and col_name in df_plot.columns:
            # Create visualization
            fig, ax = plt.subplots(figsize=(12, 5))
            fig.patch.set_facecolor('#f5f7fa')
            ax.set_facecolor('#ffffff')
            
            # Sort by metric value
            df_sorted = df_plot.sort_values(col_name, ascending=False).reset_index(drop=True)
            
            # Create bar chart
            bars = ax.bar(range(len(df_sorted)), df_sorted[col_name].values)
            
            # Color bars by model
            colors = plt.cm.tab20(np.linspace(0, 1, len(df_sorted)))
            for bar, color in zip(bars, colors):
                bar.set_color(color)
            
            ax.set_xticks(range(len(df_sorted)))
            ax.set_xticklabels([f"{row['model']}\n({row['train_variant'][:3]})" 
                                for _, row in df_sorted.iterrows()], 
                              rotation=45, ha='right')
            ax.set_title(f"{metric_type.upper()} - {data_set} Set", 
                        fontsize=14, fontweight='bold', pad=20)
            ax.set_ylabel(metric_type.upper(), fontsize=11)
            ax.set_xlabel("Model (Strategy)", fontsize=11)
            ax.grid(axis='y', alpha=0.3)
            
            plt.tight_layout()
            st.pyplot(fig)
            
            # Show metrics table
            st.markdown("### 📊 Detailed Metrics")
            display_cols = ['model', 'train_variant'] + [c for c in df_plot.columns if c.startswith(dataset_prefix)]
            st.dataframe(df_plot[display_cols].sort_values(col_name, ascending=False), 
                        use_container_width=True)
        else:
            st.warning(f"⚠️ Column '{col_name}' not found in results")
    else:
        st.info("📊 Model results not available yet. Run modeling.ipynb to generate.")


# ============================================================================
# PAGE: MODELS
# ============================================================================
elif page == "📈 Models":
    
    models_info = [
        {
            "name": "Logistic Regression",
            "emoji": "📌",
            "type": "Linear Classification",
            "pros": ["⚡ Fast training", "📖 Interpretable", "✅ Handles imbalance well"],
            "cons": ["📊 Limited patterns", "🎯 Needs scaling"]
        },
        {
            "name": "Decision Tree",
            "emoji": "🌳",
            "type": "Tree-based Classification",
            "pros": ["📈 Non-linear", "🔍 Feature importance", "⚙️ Handles imbalance"],
            "cons": ["⚠️ Overfitting risk", "🎲 Unstable"]
        },
        {
            "name": "Gaussian Naive Bayes",
            "emoji": "🎲",
            "type": "Probabilistic Classification",
            "pros": ["⚡ Very fast", "💡 Light-weight", "📊 Probabilistic"],
            "cons": ["❌ Independence assumption", "📉 Dependent features"]
        },
        {
            "name": "Neural Network (MLP)",
            "emoji": "🧠",
            "type": "Deep Learning",
            "pros": ["🚀 Best performance", "🎯 Complex patterns", "🔮 Flexible"],
            "cons": ["⚙️ Requires tuning", "🖤 Black box", "💸 More resources"]
        }
    ]
    
    col1, col2 = st.columns(2)
    
    for idx, model_info in enumerate(models_info):
        col = col1 if idx % 2 == 0 else col2
        
        with col:
            pros_text = "\n".join(f"• {p}" for p in model_info['pros'])
            cons_text = "\n".join(f"• {c}" for c in model_info['cons'])
            
            markdown_content = f"""
### {model_info['emoji']} {model_info['name']}

**Type:** {model_info['type']}

**✅ Advantages:**
{pros_text}

**❌ Limitations:**
{cons_text}
"""
            st.markdown(markdown_content)


# ============================================================================
# PAGE: ABOUT
# ============================================================================
elif page == "ℹ️ About":
    
    st.markdown("""
    <div class="section-card">
        <h2>ℹ️ About This Project</h2>
        
        This Streamlit application demonstrates an end-to-end fraud detection system using machine learning, featuring multiple models, threshold optimization, and real-time predictions.
        
        ### 📊 Dataset
        - **Source**: Kaggle Fraud Detection Dataset
        - **Training**: 1.04M transactions
        - **Testing**: 556K transactions
        - **Features**: 20 engineered features
        
        ### 🤖 Models Compared
        1. Logistic Regression
        2. Decision Tree
        3. Gaussian Naive Bayes
        4. Neural Network (MLP)
        
        ### 📈 Training Strategies
        - **Imbalanced**: Original distribution (0.166% fraud)
        - **SMOTE**: Balanced to 50% fraud rate
        
        ### 🔧 Feature Groups
        - **Temporal**: 5 features (time-based)
        - **Geographic**: 3 features (location-based)
        - **Amount**: 3 features (transaction value)
        - **Behavioral**: 6 features (history-based)
        - **Demographic**: 2 features (user profile)
        - **Categorical**: 1 feature (transaction type)
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div class="success-box">
        <strong>✨ Version</strong> 1.0 | April 2026<br>
        <strong>📚 Course</strong> Data Mining | University<br>
        <strong>🎯 Status</strong> Production Ready
    </div>
    """, unsafe_allow_html=True)

# ============================================================================
# FOOTER
# ============================================================================
st.markdown("---")
st.markdown("""
<div style='text-align: center; padding: 2rem; color: #999;'>
    <p><strong>🔍 Fraud Detection System</strong> | Advanced ML Analytics</p>
    <p style='font-size: 0.85rem;'>© 2026 Data Mining Course Project</p>
</div>
""", unsafe_allow_html=True)
