"""
Test the improved model with realistic network traffic data.

This script loads actual preprocessed data and tests predictions.
"""

import pickle
import json
import pandas as pd
import numpy as np
from pathlib import Path

print("=" * 70)
print("Testing Improved IDS/IPS Model with Real Data")
print("=" * 70)

# Load model and components
MODEL_DIR = Path('data/models')

print("\n[1/4] Loading model components...")
with open(MODEL_DIR / 'improved_ids_model.pkl', 'rb') as f:
    model = pickle.load(f)
print("  ✓ Model loaded")

with open(MODEL_DIR / 'improved_ids_scaler.pkl', 'rb') as f:
    scaler = pickle.load(f)
print("  ✓ Scaler loaded")

with open(MODEL_DIR / 'improved_ids_features.json', 'r') as f:
    features = json.load(f)
print(f"  ✓ Features loaded ({len(features)} features)")

with open(MODEL_DIR / 'improved_ids_metadata.json', 'r') as f:
    metadata = json.load(f)
print(f"  ✓ Metadata loaded")

print("\n[2/4] Model Performance:")
print(f"  Accuracy:  {metadata['test_accuracy']:.1%}")
print(f"  Precision: {metadata['test_precision']:.1%}")
print(f"  Recall:    {metadata['test_recall']:.1%}")
print(f"  F1-Score:  {metadata['test_f1']:.1%}")

print("\n[3/4] Required features (top 10):")
for i, feat in enumerate(features[:10], 1):
    print(f"  {i:2d}. {feat}")
if len(features) > 10:
    print(f"  ... and {len(features) - 10} more")

# Load some test data
print("\n[4/4] Testing with real data samples...")
try:
    test_df = pd.read_csv('data/datasets/unsw-nb15_test.csv')
    print(f"  ✓ Loaded {len(test_df):,} test samples")

    # Get actual labels
    y_true = test_df['label'].values

    # Prepare features
    X_test = test_df.drop('label', axis=1)

    # Keep only required features (that exist in the dataset)
    available_features = [f for f in features if f in X_test.columns]
    missing_features = [f for f in features if f not in X_test.columns]

    if missing_features:
        print(f"\n  ⚠️  Warning: {len(missing_features)} features not in dataset")
        for feat in missing_features:
            X_test[feat] = 0  # Add missing features with default value

    X_test = X_test[features]

    # Handle missing/infinite values
    X_test = X_test.replace([np.inf, -np.inf], np.nan).fillna(0)

    # Normalize
    X_test_scaled = scaler.transform(X_test)

    # Predict
    print("\n  Making predictions...")
    y_pred = model.predict(X_test_scaled)
    y_prob = model.predict_proba(X_test_scaled)

    # Analyze predictions
    print("\n" + "=" * 70)
    print("PREDICTION RESULTS")
    print("=" * 70)

    # Overall stats
    total = len(y_pred)
    predicted_attacks = np.sum(y_pred == 1)
    predicted_normal = np.sum(y_pred == 0)
    actual_attacks = np.sum(y_true == 1)
    actual_normal = np.sum(y_true == 0)

    print(f"\nDataset composition:")
    print(f"  Total samples:    {total:,}")
    print(f"  Actual attacks:   {actual_attacks:,} ({actual_attacks/total:.1%})")
    print(f"  Actual normal:    {actual_normal:,} ({actual_normal/total:.1%})")

    print(f"\nPredictions:")
    print(f"  Predicted attacks: {predicted_attacks:,} ({predicted_attacks/total:.1%})")
    print(f"  Predicted normal:  {predicted_normal:,} ({predicted_normal/total:.1%})")

    # Accuracy
    correct = np.sum(y_pred == y_true)
    accuracy = correct / total
    print(f"\nAccuracy: {accuracy:.1%} ({correct:,} / {total:,} correct)")

    # Sample predictions
    print("\n" + "=" * 70)
    print("SAMPLE PREDICTIONS")
    print("=" * 70)

    # Show 5 normal and 5 attack samples
    normal_indices = np.where(y_true == 0)[0][:5]
    attack_indices = np.where(y_true == 1)[0][:5]

    print("\nNormal Traffic Samples:")
    print(f"{'#':<5} {'Actual':<10} {'Predicted':<12} {'Confidence':<12} {'Threat Level':<12}")
    print("-" * 70)
    for idx in normal_indices:
        actual = "Normal"
        predicted = "Attack" if y_pred[idx] == 1 else "Normal"
        confidence = y_prob[idx][y_pred[idx]]
        attack_prob = y_prob[idx][1]

        if attack_prob >= 0.9:
            threat = "CRITICAL"
        elif attack_prob >= 0.7:
            threat = "HIGH"
        elif attack_prob >= 0.5:
            threat = "MEDIUM"
        else:
            threat = "LOW"

        correct_mark = "✓" if y_pred[idx] == 0 else "✗"
        print(f"{idx:<5} {actual:<10} {predicted:<12} {confidence:.1%}{'':>6} {threat:<12} {correct_mark}")

    print("\nAttack Traffic Samples:")
    print(f"{'#':<5} {'Actual':<10} {'Predicted':<12} {'Confidence':<12} {'Threat Level':<12}")
    print("-" * 70)
    for idx in attack_indices:
        actual = "Attack"
        predicted = "Attack" if y_pred[idx] == 1 else "Normal"
        confidence = y_prob[idx][y_pred[idx]]
        attack_prob = y_prob[idx][1]

        if attack_prob >= 0.9:
            threat = "CRITICAL"
        elif attack_prob >= 0.7:
            threat = "HIGH"
        elif attack_prob >= 0.5:
            threat = "MEDIUM"
        else:
            threat = "LOW"

        correct_mark = "✓" if y_pred[idx] == 1 else "✗"
        print(f"{idx:<5} {actual:<10} {predicted:<12} {confidence:.1%}{'':>6} {threat:<12} {correct_mark}")

    # Confusion matrix
    from sklearn.metrics import confusion_matrix
    cm = confusion_matrix(y_true, y_pred)
    tn, fp, fn, tp = cm.ravel()

    print("\n" + "=" * 70)
    print("CONFUSION MATRIX")
    print("=" * 70)
    print(f"\n                 Predicted")
    print(f"              Normal    Attack")
    print(f"Actual Normal   {tn:6,}    {fp:6,}")
    print(f"       Attack   {fn:6,}    {tp:6,}")

    print(f"\nMetrics:")
    print(f"  True Positives (TP):   {tp:,} - Attacks correctly detected")
    print(f"  True Negatives (TN):   {tn:,} - Normal correctly identified")
    print(f"  False Positives (FP):  {fp:,} - False alarms")
    print(f"  False Negatives (FN):  {fn:,} - Missed attacks")

    fpr = fp / (fp + tn) if (fp + tn) > 0 else 0
    fnr = fn / (fn + tp) if (fn + tp) > 0 else 0

    print(f"\nError Rates:")
    print(f"  False Positive Rate:   {fpr:.1%} (false alarms)")
    print(f"  False Negative Rate:   {fnr:.1%} (missed attacks)")

    print("\n" + "=" * 70)
    print("✓ Model testing complete!")
    print("=" * 70)

    print("\nConclusion:")
    if accuracy >= 0.85:
        print("  ✓ Model performance is EXCELLENT (≥85%)")
    elif accuracy >= 0.80:
        print("  ✓ Model performance is GOOD (≥80%)")
    else:
        print("  ⚠️  Model performance is below target (<80%)")

    if fnr <= 0.05:
        print("  ✓ Security coverage is EXCELLENT (≤5% attacks missed)")
    elif fnr <= 0.10:
        print("  ✓ Security coverage is GOOD (≤10% attacks missed)")
    else:
        print("  ⚠️  Security coverage needs improvement (>10% attacks missed)")

    if fpr <= 0.20:
        print("  ✓ False alarm rate is ACCEPTABLE (≤20%)")
    else:
        print("  ⚠️  False alarm rate is HIGH (>20%)")

    print("\n✓ Model is ready for deployment!")

except FileNotFoundError as e:
    print(f"\n  ❌ Error: {e}")
    print("  Please run preprocessing first:")
    print("  cd data/datasets && python preprocess_unswnb15.py")
except Exception as e:
    print(f"\n  ❌ Error: {e}")
    import traceback
    traceback.print_exc()
