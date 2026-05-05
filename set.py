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
# 4. LABEL DISTRIBUTION (UPDATED)
# ==============================
counts = train_df[TARGET].value_counts().sort_index()

plot_df = pd.DataFrame({
    'label': ['Normal', 'Fraud'],
    'count': [counts.get(0, 0), counts.get(1, 0)]
})
plot_df['pct'] = plot_df['count'] / plot_df['count'].sum() * 100

plt.figure(figsize=(12,4))

# Count
ax1 = plt.subplot(1,2,1)
sns.barplot(data=plot_df, x='label', y='count', ax=ax1)
plt.title("Class Distribution (Count)")

for i, row in plot_df.iterrows():
    ax1.text(i, row['count'], f"{int(row['count']):,}", 
             ha='center', va='bottom', fontsize=10)

# Percentage
ax2 = plt.subplot(1,2,2)
sns.barplot(data=plot_df, x='label', y='pct', ax=ax2)
plt.title("Class Distribution (%)")

for i, row in plot_df.iterrows():
    ax2.text(i, row['pct'], f"{row['pct']:.3f}%", 
             ha='center', va='bottom', fontsize=10)

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

# Boxplot (giữ cái quan trọng nhất)
plt.figure(figsize=(6,4))
sns.boxplot(x=TARGET, y='amt', data=train_df)
plt.title("Fraud vs Normal (Boxplot)")
plt.show()

# ==============================
# 7. CATEGORY ANALYSIS (UPDATED)
# ==============================
fraud_by_category = (
    train_df.groupby('category')
    .agg({TARGET: ['sum', 'count', 'mean']})
    .droplevel(0, axis=1)
    .rename(columns={'sum': 'fraud_count', 'count': 'total', 'mean': 'fraud_rate'})
    .sort_values('fraud_rate', ascending=False)
    .head(10)
)

print("\n=== FRAUD RATE BY CATEGORY ===")
print(fraud_by_category)

plt.figure(figsize=(12,6))
ax = sns.barplot(x=fraud_by_category.index,
                 y=fraud_by_category['fraud_rate'])

plt.xticks(rotation=45)
plt.title("Top Categories by Fraud Rate")

for i, v in enumerate(fraud_by_category['fraud_rate']):
    ax.text(i, v, f"{v:.3%}", ha='center', va='bottom')

plt.show()

# ==============================
# 8. TIME ANALYSIS (UPDATED)
# ==============================
train_df['trans_date_trans_time'] = pd.to_datetime(train_df['trans_date_trans_time'])
train_df['hour'] = train_df['trans_date_trans_time'].dt.hour

plt.figure(figsize=(12,5))
ax = sns.countplot(x='hour', hue=TARGET, data=train_df)

plt.title("Fraud Distribution by Hour")

# Annotate (tổng mỗi cột)
for p in ax.patches:
    height = p.get_height()
    if height > 0:
        ax.text(
            p.get_x() + p.get_width()/2,
            height,
            int(height),
            ha='center',
            va='bottom',
            fontsize=8
        )

plt.show()

# ==============================
# 9. CORRELATION MATRIX
# ==============================
print("\n=== CORRELATION MATRIX ===")

numeric_df = train_df.select_dtypes(include=['int64', 'float64'])
sample_df = numeric_df.sample(n=50000, random_state=42) if len(numeric_df) > 50000 else numeric_df

corr_matrix = sample_df.corr()

plt.figure(figsize=(12,8))
sns.heatmap(
    corr_matrix,
    cmap='coolwarm',
    center=0,
    linewidths=0.5
)

plt.title("Correlation Matrix (Numeric Features)")
plt.show()
# ==============================
# 9. FRAUD BY STATE (UPDATED)
# ==============================
fraud_by_state = (
    train_df.groupby('state')
    .agg({TARGET: ['sum', 'count', 'mean']})
    .droplevel(0, axis=1)
    .rename(columns={
        'sum': 'fraud_count',
        'count': 'total',
        'mean': 'fraud_rate'
    })
)

# Lọc >= 100 giao dịch + lấy top 10 cho dễ nhìn
fraud_by_state = fraud_by_state[fraud_by_state['total'] >= 100] \
    .sort_values('fraud_rate', ascending=False)

print("\n=== FRAUD RATE BY STATE ===")
print(fraud_by_state)

plt.figure(figsize=(18,6))
ax = sns.barplot(
    x=fraud_by_state.index,
    y=fraud_by_state['fraud_rate']
)

plt.title("Fraud Rate by State (All States)")
plt.xticks(rotation=90)





# chỉ annotate top 10 để tránh rối

for i, (state, row) in enumerate(fraud_by_state.iterrows()):
    if i < 10:
        ax.text(i, row['fraud_rate'], f"{row['fraud_rate']:.2%}",
                ha='center', va='bottom', fontsize=8)


plt.show()


# ==============================
# 10. FRAUD BY GENDER (UPDATED)
# ==============================


fraud_by_gender = (
    train_df.groupby('gender')
    .agg({TARGET: ['sum', 'count', 'mean']})
    .droplevel(0, axis=1)
    .rename(columns={
        'sum': 'fraud_count',
        'count': 'total',
        'mean': 'fraud_rate'
    })
)

print("\n=== FRAUD RATE BY GENDER ===")
print(fraud_by_gender)

plt.figure(figsize=(6,4))
ax = sns.barplot(
    x=fraud_by_gender.index,
    y=fraud_by_gender['fraud_rate']
)

plt.title("Fraud Rate by Gender")

# Add percentage label
for i, row in enumerate(fraud_by_gender['fraud_rate']):
    ax.text(i, row, f"{row:.3%}", ha='center', va='bottom')

plt.show()
# ==============================
# DONE
# ==============================
print("\n=== TRAIN OVERVIEW COMPLETED ===")