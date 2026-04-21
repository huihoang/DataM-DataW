import matplotlib.pyplot as plt
import numpy as np
import streamlit as st
from pathlib import Path

from shared import load_model_results


def render_evaluation_models() -> None:
    st.markdown(
        """
    <div class="section-card">
        <h2>📊 Evaluation Models</h2>
    </div>
    """,
        unsafe_allow_html=True,
    )

    threshold = st.selectbox("🎚️ Threshold", ["0.2", "0.5", "0.7"], index=0)
    results_df = load_model_results(threshold=threshold)
    if results_df is None:
        st.info(f"⚠️ Model results not available for threshold={threshold}.")

    col1, col2, col3 = st.columns(3)
    with col1:
        data_set = st.selectbox("🗂️ Dataset", ["All", "Validation", "Test"])
    with col2:
        metric_type = st.selectbox("🔍 Select Metric", ["All", "accuracy", "precision", "recall", "f1", "roc_auc", "pr_auc"])
    with col3:
        train_var = st.selectbox("🎯 Training Strategy", ["All", "imbalanced", "balanced_smote"])

    with st.expander("📋 Results & Filters", expanded=True):
        df_plot = results_df.copy()
        if train_var != "All":
            df_plot = df_plot[df_plot["train_variant"] == train_var]

        if df_plot.empty:
            st.warning("⚠️ No rows after filter.")
            return

        dataset_prefix = {"Validation": "valid_", "Test": "test_"}.get(data_set)
        metric_selected = metric_type != "All" and dataset_prefix is not None
        col_name = f"{dataset_prefix}{metric_type}" if metric_selected else None

        if metric_selected and col_name not in df_plot.columns:
            st.warning(f"⚠️ Column '{col_name}' not found in results")
            return

        st.markdown("### Detailed Metrics")
        if dataset_prefix is None:
            display_cols = ["model", "train_variant"] + [c for c in df_plot.columns if c.startswith(("valid_", "test_"))]
        else:
            display_cols = ["model", "train_variant"] + [c for c in df_plot.columns if c.startswith(dataset_prefix)]
        sort_col = col_name if col_name else None
        if sort_col:
            st.dataframe(df_plot[display_cols].sort_values(sort_col, ascending=False), width="stretch")
        else:
            st.dataframe(df_plot[display_cols], width="stretch")

        if not metric_selected:
            st.info("Select a specific Dataset and Metric to render comparison chart.")
        else:
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

    st.markdown("---")
    st.markdown("### 🖼️ Model Comparison")

    model_compare_dir = Path(__file__).resolve().parents[1] / "artifacts" / "modeling_results" / "figures" / "model_compare"
    if not model_compare_dir.exists():
        st.info(f"⚠️ Figure directory not found: `{model_compare_dir}`")
        return

    image_paths = sorted(model_compare_dir.glob("*.png"))
    if not image_paths:
        st.info("⚠️ No PNG figures found in model_compare directory.")
        return

    threshold_tag = f"threshold_{threshold}"
    threshold_images = [p for p in image_paths if threshold_tag in p.name]
    if threshold_images:
        image_paths = threshold_images
    else:
        st.info(f"ℹ️ No images matched `{threshold_tag}`, showing all available figures.")

    dataset_tag = {"Validation": "valid", "Test": "test"}.get(data_set)
    if dataset_tag is not None:
        dataset_images = [p for p in image_paths if f"_{dataset_tag}_" in p.name.lower()]
        if dataset_images:
            image_paths = dataset_images
        else:
            st.info(f"ℹ️ No images matched dataset `{data_set}`, keeping current figure set.")

    if train_var != "All":
        strategy_images = [p for p in image_paths if train_var in p.name.lower()]
        if strategy_images:
            image_paths = strategy_images
        else:
            st.info(f"ℹ️ No images matched strategy `{train_var}`, keeping current figure set.")

    grouped: dict[str, list[Path]] = {
        "Metrics Bars": [],
        "Confusion Matrices": [],
        "ROC Curves": [],
        "PR Curves": [],
        "Other Figures": [],
    }

    for img in image_paths:
        name = img.name.lower()
        if name.startswith("metrics_bar_"):
            grouped["Metrics Bars"].append(img)
        elif name.startswith("confusion_"):
            grouped["Confusion Matrices"].append(img)
        elif name.startswith("pr_"):
            grouped["PR Curves"].append(img)
        elif name.startswith("roc_"):
            grouped["ROC Curves"].append(img)
        else:
            grouped["Other Figures"].append(img)

    for section, paths in grouped.items():
        if not paths:
            continue
        with st.expander(f"{section} ({len(paths)})", expanded=False):
            if section == "Metrics Bars":
                for i in range(0, len(paths), 2):
                    cols = st.columns(2)
                    for j, img_path in enumerate(paths[i : i + 2]):
                        with cols[j]:
                            st.image(str(img_path), width="stretch")
            else:
                for img_path in paths:
                    st.image(str(img_path), width="stretch")
