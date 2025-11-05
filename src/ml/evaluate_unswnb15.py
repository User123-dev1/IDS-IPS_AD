#!/usr/bin/env python3
"""
Evaluate Trained Model on UNSW-NB15 Dataset

Tests the hybrid anomaly detector on real-world UNSW-NB15 attack data.
"""

import sys
import pandas as pd
import numpy as np
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from ml.models.hybrid_detector import HybridAnomalyDetector

def evaluate_model(model_path, test_data_path):
    """Evaluate model on UNSW-NB15 test data"""

    print("=" * 70)
    print("  UNSW-NB15 Model Evaluation")
    print("=" * 70)
    print()

    # Load test data
    print(f"[1/4] Loading test data from {test_data_path}...")
    df_test = pd.read_csv(test_data_path)
    print(f"  [OK] Loaded {len(df_test)} records")
    print()

    # Prepare features and labels
    print("[2/4] Preparing features...")

    # Exclude label columns
    exclude_cols = ['label', 'is_attack', 'attack_category', 'attack_cat',
                   'srcip', 'dstip', 'proto', 'service', 'state', 'Label']

    feature_cols = [col for col in df_test.columns if col not in exclude_cols]

    # Get features and labels
    X_test = df_test[feature_cols].values

    # Get true labels (is_attack column: 0=normal, 1=attack)
    if 'is_attack' in df_test.columns:
        y_true = df_test['is_attack'].values
    elif 'label' in df_test.columns:
        y_true = df_test['label'].values
    else:
        print("  [ERROR] No label column found!")
        return

    print(f"  [OK] Features: {X_test.shape}")
    print(f"  [OK] Labels: {y_true.shape}")
    print(f"       Normal: {np.sum(y_true == 0)} ({np.mean(y_true == 0) * 100:.1f}%)")
    print(f"       Attack: {np.sum(y_true == 1)} ({np.mean(y_true == 1) * 100:.1f}%)")
    print()

    # Load model
    print(f"[3/4] Loading model from {model_path}...")
    detector = HybridAnomalyDetector()
    detector.load(model_path)
    print("  [OK] Model loaded")
    print()

    # Make predictions
    print("[4/4] Making predictions...")
    results = detector.predict(X_test)
    y_pred = results['is_anomaly']
    scores = results['anomaly_score']

    print("  [OK] Predictions complete")
    print()

    # Calculate metrics
    print("=" * 70)
    print("  EVALUATION RESULTS")
    print("=" * 70)
    print()

    # Confusion matrix
    tp = np.sum((y_true == 1) & (y_pred == 1))
    tn = np.sum((y_true == 0) & (y_pred == 0))
    fp = np.sum((y_true == 0) & (y_pred == 1))
    fn = np.sum((y_true == 1) & (y_pred == 0))

    # Metrics
    accuracy = (tp + tn) / len(y_true)
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0

    # False positive rate
    fpr = fp / (fp + tn) if (fp + tn) > 0 else 0

    print("Overall Performance:")
    print(f"  Accuracy:  {accuracy * 100:6.2f}%")
    print(f"  Precision: {precision * 100:6.2f}%")
    print(f"  Recall:    {recall * 100:6.2f}%")
    print(f"  F1-Score:  {f1 * 100:6.2f}%")
    print(f"  FPR:       {fpr * 100:6.2f}%")
    print()

    print("Confusion Matrix:")
    print(f"  True Positives  (TP): {tp:6d}  (Attacks correctly detected)")
    print(f"  True Negatives  (TN): {tn:6d}  (Normal correctly identified)")
    print(f"  False Positives (FP): {fp:6d}  (Normal flagged as attack)")
    print(f"  False Negatives (FN): {fn:6d}  (Attacks missed)")
    print()

    # Attack category performance (if available)
    if 'attack_cat' in df_test.columns:
        print("Performance by Attack Category:")
        print("-" * 70)

        attack_cats = df_test['attack_cat'].unique()
        for cat in sorted(attack_cats):
            if cat == 'Normal' or pd.isna(cat):
                continue

            mask = df_test['attack_cat'] == cat
            cat_true = y_true[mask]
            cat_pred = y_pred[mask]

            cat_detected = np.sum(cat_pred == 1)
            cat_total = len(cat_true)
            cat_recall = cat_detected / cat_total if cat_total > 0 else 0

            print(f"  {cat:20s}: {cat_detected:5d}/{cat_total:5d} detected ({cat_recall * 100:5.1f}%)")
        print()

    # Anomaly score distribution
    print("Anomaly Score Distribution:")
    print(f"  Mean:   {np.mean(scores):.4f}")
    print(f"  Median: {np.median(scores):.4f}")
    print(f"  Min:    {np.min(scores):.4f}")
    print(f"  Max:    {np.max(scores):.4f}")
    print()

    print("=" * 70)
    print("  [SUCCESS] Evaluation Complete!")
    print("=" * 70)
    print()

    # Return metrics
    return {
        'accuracy': accuracy,
        'precision': precision,
        'recall': recall,
        'f1': f1,
        'fpr': fpr,
        'tp': tp,
        'tn': tn,
        'fp': fp,
        'fn': fn
    }


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description='Evaluate trained model on UNSW-NB15 dataset'
    )

    parser.add_argument(
        '--model',
        default='data/models/unsw_nb15_model',
        help='Path to trained model (default: data/models/unsw_nb15_model)'
    )

    parser.add_argument(
        '--test-data',
        default='data/datasets/unsw-nb15_test.csv',
        help='Path to test dataset (default: data/datasets/unsw-nb15_test.csv)'
    )

    args = parser.parse_args()

    # Check if files exist
    if not Path(args.test_data).exists():
        print(f"ERROR: Test data not found: {args.test_data}")
        print()
        print("Please ensure you have preprocessed the UNSW-NB15 dataset:")
        print("  cd data/datasets")
        print("  python preprocess_unswnb15.py")
        sys.exit(1)

    if not Path(f"{args.model}_meta.json").exists():
        print(f"ERROR: Model not found: {args.model}")
        print()
        print("Please train a model first:")
        print("  python src/quick_start.py --dataset data/datasets/unsw-nb15_train.csv")
        sys.exit(1)

    # Evaluate
    metrics = evaluate_model(args.model, args.test_data)

    # Exit with success
    sys.exit(0)


if __name__ == '__main__':
    main()
