import streamlit as st


def render_about() -> None:
    st.markdown(
        """
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
    """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
    <div class="success-box">
        <strong>✨ Version</strong> 1.0 | April 2026<br>
        <strong>📚 Course</strong> Data Mining | University<br>
        <strong>🎯 Status</strong> Production Ready
    </div>
    """,
        unsafe_allow_html=True,
    )
