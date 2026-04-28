# 💳 Credit Card Fraud Detection using Data Mining

## Overview
This project aims to detect fraudulent credit card transactions using machine learning techniques. The dataset is highly imbalanced, making fraud detection a challenging task that requires proper preprocessing, model selection, and evaluation.

---

## Objectives
- Analyze and understand transaction data
- Handle class imbalance problem
- Build and compare multiple machine learning models
- Optimize decision threshold for better fraud detection

---

## Dataset
- File: `fraudTrain.csv`
- Real-world transaction dataset
- Highly imbalanced (fraud cases are rare)

---

## Methodology

### Data Processing
- Data cleaning and preprocessing
- Feature scaling
- Dimensionality reduction (TruncatedSVD)
- Handling imbalance:
  - Imbalanced dataset (original)
  - Balanced dataset (SMOTE)

### Models
- Logistic Regression (baseline)
- Decision Tree
- Gaussian Naive Bayes
- Artificial Neural Network (MLP)

### Threshold Tuning
- `0.7` → higher precision
- `0.5` → default
- `0.2` → higher recall (detect more fraud cases)

---

## Evaluation Metrics
- Accuracy
- Precision
- Recall
- F1-score
- ROC-AUC
- PR-AUC (important for imbalanced data)

---

## Results

- ANN (imbalanced) → best overall performance
- Decision Tree → highest recall (detects most fraud)
- SMOTE → improves recall but reduces precision
- Threshold = 0.2 → increases recall, decreases precision

Final choice:
> **ANN (imbalanced + threshold = 0.2)**

---

## Visualizations
Figures include:
- Confusion Matrix
- Metric Comparison
- Precision-Recall Curve
- ROC Curve


---

## Conclusion
- Decision Tree is suitable when maximizing fraud detection (Recall)
- ANN provides better balance between Precision and Recall

Recommended model:
> **ANN with threshold = 0.2**

---

## Limitations
- Only basic ML models used
- No advanced models (XGBoost, LightGBM)
- Limited hyperparameter tuning

---

## Future Work
- Apply advanced models (XGBoost, LightGBM)
- Improve feature engineering
- Optimize hyperparameters
- Deploy real-time system

---

## Technologies
- Python
- Scikit-learn
- Pandas, NumPy
- Matplotlib
- Imbalanced-learn (SMOTE)

## Contribute:
| Họ tên              | MSSV     |
|---------------------|----------|
| Nguyễn Huy Hoàng    | 2211093  |
| Nguyễn Thanh Hoàng  | 2211101  |
| Nguyễn Đức Duy      | 2210510  |