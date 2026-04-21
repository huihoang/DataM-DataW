import streamlit as st


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

    col1, col2, col3, col4 = st.columns(4)
    datasets = [
        ("Training Set", "1.04M", "0.166%"),
        ("After SMOTE", "2.07M", "50%"),
        ("Validation", "259K", "0.089%"),
        ("Test Set", "556K", "0.080%"),
    ]

    for col, (label, rows, rate) in zip([col1, col2, col3, col4], datasets):
        with col:
            st.markdown(
                f"""
            <div class="metric-card">
                <h3>{label}</h3>
                <div class="value" style="font-size: 1.8rem;">{rows}</div>
                <div class="unit">Fraud Rate: {rate}</div>
            </div>
            """,
                unsafe_allow_html=True,
            )

    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)

    with col1:
        st.markdown(
            """
        <div class="section-card">
            <h2>⏰ Temporal Patterns</h2>
            - **Late-night spikes** (10 PM - 4 AM show highest fraud)
            - **Weekend elevation** by 30-50% above weekday average
            - **Holiday anomalies** with increased fraud attempts
            - **Monthly seasonality** with dramatic peaks
        </div>
        """,
            unsafe_allow_html=True,
        )

    with col2:
        st.markdown(
            """
        <div class="section-card">
            <h2>💰 Amount & Location Patterns</h2>
            - **2.4x higher** average fraud amount ($149 vs $62)
            - **Distance signal** strong fraud indicator
            - **Impossible travel** detection critical
            - **State variation** in fraud concentration
        </div>
        """,
            unsafe_allow_html=True,
        )
