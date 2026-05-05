import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

# ==============================
# CONFIG
# ==============================
TARGET = "is_fraud"

# ==============================
# 1. LOAD TRAIN DATA
# ==============================
base_dir = os.path.dirname(__file__)
train_path = os.path.join(base_dir, "archive", "fraudTrain.csv")

train_df = pd.read_csv(train_path)

print("Train shape:", train_df.shape)

# ==============================
# 2. SUMMARY
# ==============================
summary = {
    "rows": len(train_df),
    "columns": train_df.shape[1],
    "fraud_ratio": train_df[TARGET].mean(),
    "missing_values": train_df.isna().sum().sum()
}

print("\n=== TRAIN SUMMARY ===")
for k, v in summary.items():
    print(f"{k}: {v}")

# ==============================
# 3. PREVIEW
# ==============================
print("\n=== HEAD ===")
print(train_df.head())

print("\n=== INFO ===")
train_df.info()

# ==============================
# 4. LABEL DISTRIBUTION
# ==============================
counts = train_df[TARGET].value_counts().sort_index()

plot_df = pd.DataFrame({
    'label': ['Normal', 'Fraud'],
    'count': [counts.get(0, 0), counts.get(1, 0)]
})
plot_df['pct'] = plot_df['count'] / plot_df['count'].sum() * 100

plt.figure(figsize=(12,4))

# Count
plt.subplot(1,2,1)
sns.barplot(data=plot_df, x='label', y='count')
plt.title("Class Distribution (Count)")

# Percentage
plt.subplot(1,2,2)
sns.barplot(data=plot_df, x='label', y='pct')
plt.title("Class Distribution (%)")

plt.tight_layout()
plt.show()

# ==============================
# 5. DATA TYPES & MISSING
# ==============================
print("\n=== DATA TYPES ===")
print(train_df.dtypes.value_counts())

print("\n=== MISSING VALUES ===")
missing = train_df.isna().sum()
print(missing[missing > 0] if missing.sum() > 0 else "No missing values")

# ==============================
# 6. AMOUNT ANALYSIS
# ==============================
print("\n=== AMOUNT STATS ===")
print(train_df.groupby(TARGET)['amt'].describe())

# Distribution
plt.figure(figsize=(10,5))
sns.histplot(train_df['amt'], bins=50)
plt.title("Transaction Amount Distribution")
plt.show()

# Fraud vs Normal
plt.figure(figsize=(10,5))
sns.histplot(train_df[train_df[TARGET]==0]['amt'], label='Normal', kde=True)
sns.histplot(train_df[train_df[TARGET]==1]['amt'], label='Fraud', kde=True)
plt.legend()
plt.title("Fraud vs Normal Amount")
plt.show()

# Boxplot
plt.figure(figsize=(6,4))
sns.boxplot(x=TARGET, y='amt', data=train_df)
plt.title("Fraud vs Normal (Boxplot)")
plt.show()

# ==============================
# 7. CATEGORY ANALYSIS
# ==============================
fraud_by_category = (
    train_df.groupby('category')[TARGET]
    .mean()
    .sort_values(ascending=False)
)

print("\n=== FRAUD RATE BY CATEGORY ===")
print(fraud_by_category.head(10))

plt.figure(figsize=(10,5))
sns.barplot(x=fraud_by_category.head(10).index,
            y=fraud_by_category.head(10).values)
plt.xticks(rotation=45)
plt.title("Top Categories by Fraud Rate")
plt.show()

# ==============================
# 8. TIME ANALYSIS
# ==============================
train_df['trans_date_trans_time'] = pd.to_datetime(train_df['trans_date_trans_time'])
train_df['hour'] = train_df['trans_date_trans_time'].dt.hour

plt.figure(figsize=(10,5))
sns.countplot(x='hour', hue=TARGET, data=train_df)
plt.title("Fraud Distribution by Hour")
plt.show()

# ==============================
# DONE
# ==============================
print("\n=== TRAIN OVERVIEW COMPLETED ===")