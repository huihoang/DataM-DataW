import matplotlib.pyplot as plt
import numpy as np
import streamlit as st
from pathlib import Path
import json
import pandas as pd

from shared import load_model_results


@st.cache_data(show_spinner=False)
def load_model_parameter_report(report_mtime_ns: int) -> dict:
    report_path = Path(__file__).resolve().parents[1] / "artifacts" / "modeling_results" / "parameter" / "model_comparison_artifact_report.json"
    if not report_path.exists():
        return {}
    try:
        with report_path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def params_to_table(params: dict) -> pd.DataFrame:
    if not isinstance(params, dict) or not params:
        return pd.DataFrame(columns=["parameter", "value"])
    rows = [{"parameter": str(k), "value": str(v)} for k, v in sorted(params.items(), key=lambda x: x[0])]
    return pd.DataFrame(rows)


def render_evaluation_models() -> None:
    st.markdown(
        """
    <div class="section-card">
        <h2>📊 Evaluation Models</h2>
        <p>Trang đánh giá số liệu của các mô hình với các ngưỡng khác nhau và các thống kê metrics.</p>
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

    with st.expander("📋 Detailed Metrics", expanded=True):
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

        st.markdown("### Metrics Table")
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

    with st.expander("🧩 Detailed Parameters", expanded=False):
        report_path = Path(__file__).resolve().parents[1] / "artifacts" / "modeling_results" / "parameter" / "model_comparison_artifact_report.json"
        report_mtime_ns = report_path.stat().st_mtime_ns if report_path.exists() else 0
        report = load_model_parameter_report(report_mtime_ns)
        pickles = report.get("pickles", []) if isinstance(report, dict) else []

        if not pickles:
            st.info("⚠️ Parameter report not found or empty.")
        else:
            rows = []
            for item in pickles:
                artifact_name = item.get("artifact_name", "")
                if "__" in artifact_name:
                    strategy, model_name_with_ext = artifact_name.split("__", 1)
                    model_name = model_name_with_ext.replace(".pkl", "")
                else:
                    strategy = "unknown"
                    model_name = artifact_name.replace(".pkl", "")

                rows.append(
                    {
                        "artifact_name": artifact_name,
                        "train_variant": strategy,
                        "model": model_name,
                        "final_estimator_type": item.get("final_estimator_type", "N/A"),
                        "pipeline_steps": " -> ".join(item.get("pipeline_steps", [])),
                    }
                )

            params_df = pd.DataFrame(rows)

            if train_var != "All":
                params_df = params_df[params_df["train_variant"] == train_var]

            if params_df.empty:
                st.info(f"ℹ️ No parameter rows for strategy `{train_var}`.")
            else:
                selected_artifact = st.selectbox("Select artifact", params_df["artifact_name"].tolist())
                selected_item = next((x for x in pickles if x.get("artifact_name") == selected_artifact), None)

                if selected_item:
                    st.markdown("#### Core Model Information")
                    core_explanations = {
                        "clf_class": "Tên thuật toán classifier ở bước cuối pipeline.",
                        "clf_module": "Module Python của classifier (thư viện/namespace).",
                        "classes_": "Danh sách nhãn lớp mà model học được.",
                        "pipeline_steps": "Thứ tự các bước xử lý trong pipeline.",
                    }
                    core_rows = [
                        {
                            "field": "clf_class",
                            "value": str(selected_item.get("clf_class", "N/A")),
                            "explanation": core_explanations["clf_class"],
                        },
                        {
                            "field": "clf_module",
                            "value": str(selected_item.get("clf_module", "N/A")),
                            "explanation": core_explanations["clf_module"],
                        },
                        {
                            "field": "classes_",
                            "value": str(selected_item.get("classes_", "N/A")),
                            "explanation": core_explanations["classes_"],
                        },
                        {
                            "field": "pipeline_steps",
                            "value": " -> ".join(selected_item.get("pipeline_steps", [])) or "N/A",
                            "explanation": core_explanations["pipeline_steps"],
                        },
                    ]
                    st.dataframe(pd.DataFrame(core_rows), width="stretch", hide_index=True)

                    st.markdown("#### Classifier Parameters")
                    # Backward compatibility: some old reports used clf_params_non_default.
                    clf_params = selected_item.get("clf_params", selected_item.get("clf_params_non_default", {}))
                    if not isinstance(clf_params, dict):
                        clf_params = {}
                    clf_param_rows = []
                    for param_name, param_value in sorted(clf_params.items(), key=lambda x: x[0]):
                        clf_param_rows.append(
                            {
                                "parameter": str(param_name),
                                "value": str(param_value),
                                # "explanation": "Hyperparameter của classifier đọc từ pkl (get_params deep=True).",
                            }
                        )
                    if not clf_param_rows:
                        st.info("No classifier parameters found.")
                    else:
                        st.dataframe(pd.DataFrame(clf_param_rows), width="stretch", hide_index=True)

    st.markdown("---")
    st.markdown("### 🖼️ Models Comparison")

    model_compare_dir = Path(__file__).resolve().parents[1] / "artifacts" / "modeling_results" / "figures" / "model_compare"
    if not model_compare_dir.exists():
        st.info(f"⚠️ Figure directory not found: `{model_compare_dir}`")
        return

    image_paths = sorted(model_compare_dir.glob("*.png"))
    if not image_paths:
        st.info("⚠️ No PNG figures found in model_compare directory.")
        return

    image_paths = sorted(image_paths, key=lambda p: p.name.lower())

    threshold_tag = f"threshold_{threshold}"
    threshold_images = [p for p in image_paths if threshold_tag in p.name.lower()]
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

    # File naming in model_compare:
    # - confusion_* includes train strategy explicitly (imbalanced OR balanced_smote)
    # - metrics_bar/pr/roc include both strategies in one figure (imbalanced_balanced)
    # => apply strategy filter only for confusion files.
    if train_var != "All":
        strategy_images = []
        for p in image_paths:
            name = p.name.lower()
            if name.startswith("confusion_"):
                if f"_{train_var}_" in name:
                    strategy_images.append(p)
            else:
                strategy_images.append(p)
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
