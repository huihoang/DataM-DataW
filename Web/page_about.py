import streamlit as st


def render_about() -> None:
    st.markdown(
        """
    <div class="section-card">
        <h2><i class="fa-solid fa-circle-info" style="color:#4f46e5;margin-right:8px;"></i>About This Project</h2>
    </div>
    """,
        unsafe_allow_html=True,
    )

    st.markdown("### Project Objective")
    st.write(
        "Xây dựng hệ thống phát hiện gian lận giao dịch theo hướng end-to-end: "
        "từ mô hình hóa, đánh giá nhiều ngưỡng quyết định, đến triển khai dự đoán real-time trên giao diện vận hành."
    )

    st.markdown("### Scope and Data")
    st.markdown(
        """
    - **Bài toán:** Binary classification (`fraud` vs `normal`) trên dữ liệu mất cân bằng mạnh.
    - **Nguồn dữ liệu:** [Kaggle Fraud Detection Dataset](https://www.kaggle.com/datasets/kartik2112/fraud-detection).
    - **Quy mô tham chiếu:** ~1.04M train, ~556K test.
    - **Feature engineering:** 20 đặc trưng đã chuẩn hóa cho pipeline suy luận.
    - **Nhóm đặc trưng chính:** temporal, geographic, amount, behavioral, demographic.
    """
    )

    st.markdown("### Modeling Strategy")
    st.markdown(
        """
    - **Mô hình so sánh:** Logistic Regression, Decision Tree, Gaussian Naive Bayes, ANN (MLP).
    - **Chiến lược train:** `imbalanced` (giữ phân phối gốc) và `balanced_smote` (cân bằng lớp).
    - **Đánh giá:** cả Validation và Test, theo nhiều metric: Accuracy, Precision, Recall, F1, ROC-AUC, PR-AUC.
    """
    )

    st.markdown("### Threshold Governance")
    threshold_table = [
        {
            "Threshold": "0.2",
            "Ưu điểm": "Bắt fraud tốt hơn (recall cao), giảm nguy cơ bỏ sót giao dịch gian lận.",
            "Nhược điểm": "Tăng false positive, đội vận hành cần review nhiều cảnh báo hơn.",
        },
        {
            "Threshold": "0.5",
            "Ưu điểm": "Cân bằng tương đối giữa precision và recall, dễ dùng làm baseline.",
            "Nhược điểm": "Có thể vẫn bỏ sót một phần fraud trong bối cảnh dữ liệu lệch lớp mạnh.",
        },
        {
            "Threshold": "0.7",
            "Ưu điểm": "Giảm báo động giả, giúp tập trung xử lý các case có độ tin cậy cao.",
            "Nhược điểm": "Recall giảm đáng kể, rủi ro bỏ lọt fraud tăng.",
        },
    ]
    st.dataframe(threshold_table, width="stretch", hide_index=True)

    st.markdown("### Enterprise and Research Readiness")
    st.markdown(
        """
    - **Theo hướng doanh nghiệp:** có so sánh đa mô hình, quản trị threshold, và dashboard phục vụ quyết định.
    - **Theo hướng nghiên cứu:** tách validation/test rõ ràng, dùng nhiều chỉ số đánh giá phù hợp dữ liệu lệch lớp.
    - **Tái lập kết quả:** artifact hóa mô hình/pipeline và báo cáo tham số để truy vết thực nghiệm.
    - **Khuyến nghị triển khai:** thêm monitoring theo thời gian (data drift, performance drift, alert volume, cost of false positives).
    """
    )

    st.markdown(
        """
    <div class="success-box">
        <strong>Version</strong> 1.0 | April 2026<br>
        <strong>Context</strong> Data Mining + Data Warehouse Project<br>
        <strong>Delivery State</strong> Research Prototype with Business-oriented Evaluation
    </div>
    """,
        unsafe_allow_html=True,
    )
