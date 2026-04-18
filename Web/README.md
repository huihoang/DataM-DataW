# 🔍 Fraud Detection - Streamlit Web Application

Interactive web application for fraud detection using machine learning models trained on transaction data.

## 📋 Features

- **📊 Dashboard** - Overview of dataset and fraud patterns
- **🎯 Single Prediction** - Real-time fraud prediction for individual transactions
- **📈 Model Performance** - Compare 4 models across different strategies and thresholds
- **📉 Visualization** - ROC curves, confusion matrices, and feature importance
- **ℹ️ About** - Documentation and project information

## 🚀 Installation & Setup

### Prerequisites
- Python 3.8+
- pip or conda

### Step 1: Create Virtual Environment (Optional but Recommended)
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate
```

### Step 2: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 3: Run the Application
```bash
streamlit run app.py
```

The app will open in your default browser at `http://localhost:8501`

## 📊 Data Requirements

The app expects processed data and trained models in the following structure:

```
notebooks/artifacts/
├── processed_csv/
│   ├── X_train.csv           # Training features (imbalanced)
│   ├── y_train.csv           # Training labels
│   ├── X_train_balanced.csv  # Training features (SMOTE)
│   ├── y_train_balanced.csv  # Training labels (SMOTE)
│   ├── X_test.csv            # Test features
│   └── y_test.csv            # Test labels
├── modeling_results/
│   ├── trained_models/
│   │   ├── logistic_regression_imbalanced.pkl
│   │   ├── logistic_regression_smote.pkl
│   │   ├── decision_tree_imbalanced.pkl
│   │   ├── decision_tree_smote.pkl
│   │   ├── gaussian_nb_imbalanced.pkl
│   │   ├── gaussian_nb_smote.pkl
│   │   ├── mlp_imbalanced.pkl
│   │   └── mlp_smote.pkl
│   ├── figures/
│   │   ├── roc_curve_*.png
│   │   ├── confusion_matrix_*.png
│   │   └── feature_importance_*.png
│   └── model_results.csv      # Results table
```

### Generate Data & Models

Run the preprocessing and modeling notebooks first:

```bash
# In project root directory
jupyter notebook notebooks/fraud_detection_btl.ipynb
jupyter notebook notebooks/modeling.ipynb
```

## 🎯 Usage Guide

### Dashboard
- Overview of dataset statistics
- Key fraud pattern summary
- Quick metrics

### Single Prediction
1. Select a machine learning model
2. Adjust the decision threshold (0.0 - 1.0)
3. Enter transaction details using sliders
4. Click "Predict" to get fraud probability

**Threshold Interpretation:**
- **Threshold = 0.2** → Maximize recall (catch more fraud, but more false alarms)
- **Threshold = 0.5** → Balanced approach (default)
- **Threshold = 0.7** → Maximize precision (fewer false alarms, but miss some fraud)

### Model Performance
- Compare prediction metrics across models
- Analyze different training strategies (Imbalanced vs SMOTE)
- Evaluate impact of different thresholds

### Visualization
- ROC curves for each model
- Confusion matrices
- Feature importance rankings
- Precision-Recall curves

## 🤖 Models Included

1. **Logistic Regression** - Linear baseline model
2. **Decision Tree** - Non-linear decision boundaries
3. **Gaussian Naive Bayes** - Probabilistic classifier
4. **Neural Network (MLP)** - Deep learning approach

Each model is trained on:
- **Imbalanced data** - Original distribution (0.166% fraud)
- **SMOTE-balanced data** - Synthetic oversampling (50% fraud)

## 📊 Evaluation Metrics

The application displays:
- **Accuracy** - Overall correctness rate
- **Precision** - False positive rate
- **Recall** - Fraud detection rate (True positive rate)
- **F1-Score** - Harmonic mean
- **ROC-AUC** - Threshold-independent metric
- **PR-AUC** - Precision-Recall area under curve

## 🛠️ Configuration

Edit `app.py` to customize:

```python
# Feature names (line ~85)
FEATURE_NAMES = [...]

# Model paths (line ~99)
MODELS_PATH = ARTIFACTS_PATH / "modeling_results" / "trained_models"

# Feature ranges (line ~253)
feature_ranges = {...}
```

## 📝 Notes

- **Demo Mode**: If trained models are not found, the app runs in demo mode with synthetic predictions
- **Caching**: Streamlit caches models and data for faster loading
- **Browser**: Best viewed on Chrome, Firefox, or Safari

## 🔗 Related Files

- `modeling.ipynb` - Model training and evaluation
- `fraud_detection_btl.ipynb` - Data preprocessing
- `../docs/` - Full project report (LaTeX)

## 📚 References

- Dataset: [Kaggle - Fraud Detection](https://www.kaggle.com/datasets/kartik2112/fraud-detection)
- Streamlit Docs: [streamlit.io](https://streamlit.io/)
- Scikit-learn: [scikit-learn.org](https://scikit-learn.org/)

## 🐛 Troubleshooting

### Port Already in Use
```bash
streamlit run app.py --logger.level=debug --server.port=8502
```

### Models Not Loading
- Run `modeling.ipynb` to generate trained models
- Check `notebooks/artifacts/modeling_results/trained_models/` exists
- Check individual `.pkl` files are present

### Data Not Found
- Run `fraud_detection_btl.ipynb` first
- Verify `notebooks/artifacts/processed_csv/` folder exists
- Check `.csv` files are named correctly

## 📧 Support

For issues or questions, refer to the project documentation in `../docs/main.pdf`

---
**Version:** 1.0 | **Last Updated:** April 2026
