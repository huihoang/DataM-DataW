from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[1]
MODEL_RESULTS_DIR = PROJECT_ROOT / "artifacts" / "modeling_results"
FIGURES_DIR = MODEL_RESULTS_DIR / "figures"
METRICS_CSV = MODEL_RESULTS_DIR / "evaluate_ann_model_threshold_0.194.csv"

FIGURE_DESCRIPTIONS = {
    "ann_threshold_tuning_imbalanced_threshold_0.194.png": (
        "Threshold tuning",
        "Đường threshold giúp cân bằng giữa precision và recall. "
        "Ngưỡng 0.194 đang ưu tiên bắt được fraud tốt hơn so với dùng ngưỡng mặc định 0.5.",
    ),
    "ann_confusion_valid_imbalanced_threshold_0.194.png": (
        "Confusion matrix",
        "Ma trận nhầm lẫn cho thấy số lượng dự báo đúng/sai theo từng lớp. "
        "Đây là góc nhìn trực tiếp nhất để kiểm tra false positive và false negative.",
    ),
    "ann_roc_valid_imbalanced_threshold_0.194.png": (
        "ROC curve",
        "ROC-AUC cao thể hiện khả năng tách lớp mạnh trên toàn bộ ngưỡng quyết định.",
    ),
    "ann_pr_valid_imbalanced_threshold_0.194.png": (
        "Precision-Recall curve",
        "PR-AUC đặc biệt quan trọng với bài toán mất cân bằng lớp như fraud detection.",
    ),
    "ann_calibration_valid_imbalanced_threshold_0.194.png": (
        "Calibration",
        "Biểu đồ calibration kiểm tra mức độ khớp giữa xác suất dự báo và xác suất thực tế.",
    ),
    "ann_learning_curve_imbalanced_threshold_0.194.png": (
        "Learning curve",
        "Theo dõi hiệu năng theo kích thước dữ liệu để phát hiện underfit/overfit.",
    ),
    "ann_convergence_timeline_imbalanced_threshold_0.2.png": (
        "Convergence timeline",
        "Theo dõi độ hội tụ của mô hình trong quá trình học và kiểm tra độ ổn định.",
    ),
    "ann_loss_vs_time_imbalanced_threshold_0.2.png": (
        "Loss vs time",
        "Quan sát loss theo thời gian để đánh giá tốc độ học và nguy cơ dao động/không hội tụ.",
    ),
}


@st.cache_data(show_spinner=False)
def load_ann_metrics() -> pd.DataFrame:
    if not METRICS_CSV.exists():
        return pd.DataFrame()
    return pd.read_csv(METRICS_CSV)


def _render_metrics_table(df: pd.DataFrame) -> None:
    st.markdown("### Metrics Table")
    metrics = ["accuracy", "precision", "recall", "f1", "roc_auc", "pr_auc"]
    row_data: dict[str, list[float | str]] = {"Dataset": ["Validation", "Test"]}
    for metric in metrics:
        valid_key = f"valid_{metric}"
        test_key = f"test_{metric}"
        if valid_key in df.columns and test_key in df.columns:
            row_data[metric.upper()] = [float(df.iloc[0][valid_key]), float(df.iloc[0][test_key])]

    if len(row_data) <= 1:
        st.info("Không có dữ liệu metric để hiển thị.")
        return

    table_df = pd.DataFrame(row_data)
    st.dataframe(
        table_df.style.format({col: "{:.4f}" for col in table_df.columns if col != "Dataset"}),
        width="stretch",
        hide_index=True,
    )


def _metrics_plot_df(df: pd.DataFrame, prefix: str) -> pd.DataFrame:
    metrics = ["accuracy", "precision", "recall", "f1", "roc_auc", "pr_auc"]
    rows: list[dict[str, float | str]] = []
    for metric in metrics:
        key = f"{prefix}_{metric}"
        if key in df.columns:
            rows.append({"Metric": metric.upper(), "Score": float(df.iloc[0][key])})
    return pd.DataFrame(rows)


def _render_metric_charts(df: pd.DataFrame) -> None:
    valid_plot_df = _metrics_plot_df(df, "valid")
    test_plot_df = _metrics_plot_df(df, "test")

    st.markdown("#### Visualization Metrics")
    if valid_plot_df.empty or test_plot_df.empty:
        st.info("Không đủ dữ liệu để vẽ biểu đồ cột đôi.")
        return

    merged = valid_plot_df.merge(test_plot_df, on="Metric", suffixes=("_VALID", "_TEST"))
    compare_df = merged.set_index("Metric")[["Score_VALID", "Score_TEST"]]
    compare_df.columns = ["Validation", "Test"]
    chart_df = compare_df.reset_index().melt(id_vars="Metric", var_name="Dataset", value_name="Score")

    grouped_bar = (
        alt.Chart(chart_df)
        .mark_bar(size=60)
        .encode(
            x=alt.X("Metric:N", title="Metric", sort=list(compare_df.index)),
            xOffset=alt.XOffset("Dataset:N"),
            y=alt.Y("Score:Q", title="Score", scale=alt.Scale(domain=[0, 1])),
            color=alt.Color(
                "Dataset:N",
                scale=alt.Scale(domain=["Validation", "Test"], range=["#1f77b4", "#ff7f0e"]),
                legend=alt.Legend(title="Dataset"),
            ),
            tooltip=[
                alt.Tooltip("Metric:N"),
                alt.Tooltip("Dataset:N"),
                alt.Tooltip("Score:Q", format=".4f"),
            ],
        )
        .properties(height=260)
    )
    st.altair_chart(grouped_bar, width="stretch")


def _render_figure_gallery() -> None:
    figure_files = sorted([p for p in FIGURES_DIR.glob("ann_*.png") if p.is_file()])
    if not figure_files:
        st.info("Chưa tìm thấy ảnh đánh giá ANN trong thư mục artifacts.")
        return

    st.markdown("### Visualization Analysis ANN")
    for fig_path in figure_files:
        title, description = FIGURE_DESCRIPTIONS.get(
            fig_path.name, ("ANN chart", "Biểu đồ hỗ trợ đánh giá hiệu năng mô hình ANN.")
        )

        with st.expander(title, expanded=False):
            _, center_col, _ = st.columns([3, 4, 3])
            with center_col:
                st.image(str(fig_path), width="content")
                st.caption(description)


def render_analysis_ann_model() -> None:
    st.markdown(
        """
    <div class="section-card">
        <h2><i class="fa-solid fa-brain" style="color:#4f46e5;margin-right:8px;"></i>Analysis ANN Model</h2>
        <p>Trang phân tích chuyên sâu cho model chính là ANN với metrics, diễn giải và hình trực quan.</p>
    </div>
    """,
        unsafe_allow_html=True,
    )

    metrics_df = load_ann_metrics()
    if metrics_df.empty:
        st.error("Không đọc được file đánh giá ANN. Vui lòng kiểm tra đường dẫn artifacts.")
        return

    st.markdown("### Overview Configuration")
    info_col1, info_col2 = st.columns(2)
    with info_col1:
        st.write(f"- **Model:** `{metrics_df.iloc[0]['model']}`")
        st.write(f"- **Train variant:** `{metrics_df.iloc[0]['train_variant']}`")
    with info_col2:
        st.write("- **Threshold:** `0.194`")
        st.write("- **Nguồn dữ liệu:** `evaluate_ann_model_threshold_0.194.csv`")

    _render_metrics_table(metrics_df)
    _render_metric_charts(metrics_df)

    st.markdown("### Opinion Analysis")
    st.write(
        "- ROC-AUC và PR-AUC đều cao cho thấy ANN có khả năng phân biệt giao dịch fraud tốt trên dữ liệu mất cân bằng.\n"
        "- Precision/Recall ở mức gần nhau cho thấy mô hình đang cân bằng tương đối giữa việc bắt đúng fraud và hạn chế báo động giả.\n"
        "- F1 score ở mức ổn định giữa validation và test gợi ý khả năng tổng quát hóa tốt, chưa có dấu hiệu overfit mạnh.\n"
        "- Với bối cảnh fraud detection, nên theo dõi thêm calibration và đường threshold tuning để chọn ngưỡng tối ưu theo chi phí nghiệp vụ."
    )

    _render_figure_gallery()
