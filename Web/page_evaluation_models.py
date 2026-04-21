import matplotlib.pyplot as plt
import numpy as np
import streamlit as st

from shared import load_model_results


def render_evaluation_models() -> None:
    st.markdown(
        """
    <div class="section-card">
        <h2>📊 Models Performance Evaluation</h2>
    </div>
    """,
        unsafe_allow_html=True,
    )

    results_df = load_model_results()
    if results_df is None:
        st.info("⚠️ Model results not available yet. Run modeling.ipynb to generate.")
        return

    st.markdown("<br>", unsafe_allow_html=True)
    with st.expander("📋 View Full Results Table", expanded=True):
        st.dataframe(results_df, width="stretch", height=400)

    col1, col2, col3 = st.columns(3)
    with col1:
        data_set = st.selectbox("🗂️ Dataset", ["Validation", "Test"])
    with col2:
        metric_type = st.selectbox("🔍 Select Metric", ["accuracy", "precision", "recall", "f1", "roc_auc", "pr_auc"])
    with col3:
        train_var = st.selectbox("🎯 Training Strategy", ["All", "imbalanced", "balanced_smote"])

    st.markdown("<br>", unsafe_allow_html=True)
    df_plot = results_df.copy()
    if train_var != "All":
        df_plot = df_plot[df_plot["train_variant"] == train_var]

    dataset_prefix = "valid_" if data_set == "Validation" else "test_"
    col_name = f"{dataset_prefix}{metric_type}"

    if df_plot.empty or col_name not in df_plot.columns:
        st.warning(f"⚠️ Column '{col_name}' not found in results")
        return

    st.markdown("### 📊 Detailed Metrics")
    display_cols = ["model", "train_variant"] + [c for c in df_plot.columns if c.startswith(dataset_prefix)]
    st.dataframe(df_plot[display_cols].sort_values(col_name, ascending=False), width="stretch")

    fig, ax = plt.subplots(figsize=(12, 5))
    fig.patch.set_facecolor("#f5f7fa")
    ax.set_facecolor("#ffffff")
    df_sorted = df_plot.sort_values(col_name, ascending=False).reset_index(drop=True)

    bars = ax.bar(range(len(df_sorted)), df_sorted[col_name].values)
    colors = plt.cm.tab20(np.linspace(0, 1, len(df_sorted)))
    for bar, color in zip(bars, colors):
        bar.set_color(color)

    ax.set_xticks(range(len(df_sorted)))
    ax.set_xticklabels([f"{row['model']}\n({row['train_variant'][:3]})" for _, row in df_sorted.iterrows()], rotation=45, ha="right")
    ax.set_title(f"{metric_type.upper()} - {data_set} Set", fontsize=14, fontweight="bold", pad=20)
    ax.set_ylabel(metric_type.upper(), fontsize=11)
    ax.set_xlabel("Model (Strategy)", fontsize=11)
    ax.grid(axis="y", alpha=0.3)
    plt.tight_layout()
    st.pyplot(fig)
