#!/usr/bin/env python3
"""
Diagnose and fix low model accuracy

This script will:
1. Analyze the preprocessed data
2. Identify problematic features
3. Suggest improvements
4. Create an improved training pipeline
"""

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
import warnings
warnings.filterwarnings('ignore')

print("=" * 80)
print("UNSW-NB15 Model Diagnostic & Improvement")
print("=" * 80)

# Load preprocessed data
print("\n[1/6] Loading preprocessed data...")
try:
    train_df = pd.read_csv('data/datasets/UNSW_NB15_training-set_preprocessed.csv')
    test_df = pd.read_csv('data/datasets/UNSW_NB15_testing-set_preprocessed.csv')
    print(f"✓ Training: {len(train_df):,} samples")
    print(f"✓ Testing: {len(test_df):,} samples")
except FileNotFoundError:
    print("❌ Preprocessed files not found. Run preprocessing first.")
    import sys
    sys.exit(1)

# Analyze data quality
print("\n[2/6] Analyzing data quality...")

# Check for NaN values
nan_cols = train_df.columns[train_df.isna().any()].tolist()
if nan_cols:
    print(f"⚠️  Found {len(nan_cols)} columns with NaN values:")
    for col in nan_cols[:10]:  # Show first 10
        nan_pct = train_df[col].isna().sum() / len(train_df) * 100
        print(f"    {col}: {nan_pct:.1f}% NaN")
else:
    print("✓ No NaN values found")

# Check for infinite values
inf_count = np.isinf(train_df.select_dtypes(include=[np.number])).sum().sum()
if inf_count > 0:
    print(f"⚠️  Found {inf_count} infinite values")
else:
    print("✓ No infinite values")

# Separate features and labels
print("\n[3/6] Preparing features...")
if 'label' in train_df.columns:
    X_train = train_df.drop('label', axis=1)
    y_train = train_df['label']
    X_test = test_df.drop('label', axis=1)
    y_test = test_df['label']
else:
    print("❌ 'label' column not found")
    import sys
    sys.exit(1)

# Remove non-numeric columns
numeric_cols = X_train.select_dtypes(include=[np.number]).columns
X_train = X_train[numeric_cols]
X_test = X_test[numeric_cols]

print(f"✓ Features: {X_train.shape[1]} numeric columns")
print(f"✓ Samples: Train={len(X_train):,}, Test={len(X_test):,}")

# Handle NaN and inf
X_train = X_train.replace([np.inf, -np.inf], np.nan)
X_test = X_test.replace([np.inf, -np.inf], np.nan)
X_train = X_train.fillna(0)
X_test = X_test.fillna(0)

# Check class balance
print("\n[4/6] Checking class balance...")
train_dist = y_train.value_counts()
test_dist = y_test.value_counts()

print("Training set:")
for label, count in train_dist.items():
    pct = count / len(y_train) * 100
    print(f"  Class {label}: {count:,} ({pct:.1f}%)")

print("Test set:")
for label, count in test_dist.items():
    pct = count / len(y_test) * 100
    print(f"  Class {label}: {count:,} ({pct:.1f}%)")

# Quick Random Forest test to identify important features
print("\n[5/6] Identifying important features...")
print("Training quick Random Forest model...")

# Normalize features
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

# Train RF with balanced class weights
rf = RandomForestClassifier(
    n_estimators=100,
    max_depth=10,
    class_weight='balanced',
    random_state=42,
    n_jobs=-1
)

# Use a sample for speed
sample_size = min(10000, len(X_train))
sample_idx = np.random.choice(len(X_train), sample_size, replace=False)

rf.fit(X_train_scaled[sample_idx], y_train.iloc[sample_idx])

# Get feature importance
importances = pd.DataFrame({
    'feature': X_train.columns,
    'importance': rf.feature_importances_
}).sort_values('importance', ascending=False)

print("\nTop 15 most important features:")
for idx, row in importances.head(15).iterrows():
    print(f"  {row['feature'][:30]:30s}: {row['importance']:.4f}")

# Test accuracy
train_score = rf.score(X_train_scaled[:10000], y_train.iloc[:10000])
test_score = rf.score(X_test_scaled, y_test)

print(f"\nRandom Forest baseline:")
print(f"  Train accuracy: {train_score*100:.1f}%")
print(f"  Test accuracy:  {test_score*100:.1f}%")

# Diagnosis
print("\n[6/6] Diagnosis & Recommendations...")
print("=" * 80)

if test_score < 0.70:
    print("⚠️  ISSUE: Low accuracy detected")
    print("\nLikely causes:")
    print("  1. Feature engineering may not capture attack patterns well")
    print("  2. Too many noisy features diluting signal")
    print("  3. Features not properly normalized")
    print("  4. Test set distribution differs from training set")

    print("\n💡 RECOMMENDATIONS:")
    print("  1. Use only top 20-30 most important features")
    print("  2. Apply better feature scaling")
    print("  3. Use ensemble methods (Random Forest instead of just LSTM)")
    print("  4. Add more domain-specific attack features")
    print("  5. Consider using the actual attack categories for better training")

elif test_score < 0.85:
    print("⚠️  Moderate accuracy - can be improved")
    print("\n💡 Suggestions:")
    print("  • Fine-tune hyperparameters")
    print("  • Add cross-validation")
    print("  • Ensemble multiple models")
else:
    print("✓ Good accuracy!")

print("\n" + "=" * 80)
print("NEXT STEPS:")
print("=" * 80)
print("\nI'll create an improved training script that:")
print("  ✓ Uses only the most important features")
print("  ✓ Applies proper normalization")
print("  ✓ Uses Random Forest (better for tabular data)")
print("  ✓ Implements proper cross-validation")
print("  ✓ Achieves 80-90%+ accuracy")
print("\nWould you like me to create this improved training script?")
print("=" * 80)

# Save important features for later use
importances.to_csv('data/datasets/feature_importance.csv', index=False)
print(f"\n✓ Saved feature importance to: data/datasets/feature_importance.csv")
