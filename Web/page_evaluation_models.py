import matplotlib.pyplot as plt
import numpy as np
import streamlit as st
from pathlib import Path
import json
import pandas as pd
import re

from shared import load_model_results


@st.cache_data(show_spinner=False)
def load_model_parameter_report() -> dict:
    report_path = Path(__file__).resolve().parents[1] / "artifacts" / "modeling_results" / "parameter" / "model_comparison_artifact_report.json"
    if not report_path.exists():
        return {}
    try:
        with report_path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def extract_model_repr_table(model_repr: str) -> pd.DataFrame:
    rows: list[dict[str, str]] = []
    explanations = {
        "Pipeline": "Cho biết model có được đóng gói theo sklearn Pipeline hay không.",
        "Preprocessor": "Khối tiền xử lý đặc trưng trước khi đưa vào mô hình.",
        "Imputer strategy": "Cách xử lý giá trị thiếu trong dữ liệu đầu vào.",
        "Scaler": "Phương pháp chuẩn hóa/scale đặc trưng số.",
        "SVD n_components": "Số chiều giữ lại sau bước giảm chiều bằng TruncatedSVD.",
        "SVD random_state": "Seed cố định để tái lập kết quả của bước SVD.",
        "SVD": "Cho biết pipeline có dùng giảm chiều SVD hay không.",
        "Classifier": "Thuật toán phân loại ở bước cuối của pipeline.",
        "Classifier params": "Các siêu tham số chính của mô hình phân loại.",
    }

    def add_row(field: str, value: str) -> None:
        rows.append({"Field": field, "Value": value, "Explanation": explanations.get(field, "")})

    add_row("Pipeline", "Yes" if "Pipeline(" in model_repr else "No")
    add_row("Preprocessor", "ColumnTransformer" if "ColumnTransformer" in model_repr else "N/A")

    imputer_match = re.search(r"SimpleImputer\(strategy='([^']+)'\)", model_repr)
    add_row("Imputer strategy", imputer_match.group(1) if imputer_match else "N/A")

    scaler_match = re.search(r"(StandardScaler|MinMaxScaler|RobustScaler)\(\)", model_repr)
    add_row("Scaler", scaler_match.group(1) if scaler_match else "N/A")

    svd_match = re.search(r"TruncatedSVD\(n_components=(\d+),\s*random_state=(\d+)\)", model_repr)
    if svd_match:
        add_row("SVD n_components", svd_match.group(1))
        add_row("SVD random_state", svd_match.group(2))
    else:
        add_row("SVD", "Not used")

    clf_match = re.search(r"\('clf',\s*([A-Za-z_][A-Za-z0-9_]*)\((.*?)\)\)\]", model_repr, flags=re.DOTALL)
    if clf_match:
        clf_name = clf_match.group(1)
        clf_params_raw = " ".join(clf_match.group(2).split())
        add_row("Classifier", clf_name)
        add_row("Classifier params", clf_params_raw if clf_params_raw else "(default)")
    else:
        add_row("Classifier", "N/A")

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
        report = load_model_parameter_report()
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
                    model_repr = str(selected_item.get("model_repr", ""))
                    st.markdown("#### Model Representation (Structured Table)")
                    st.dataframe(extract_model_repr_table(model_repr), width="stretch", hide_index=True)

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
