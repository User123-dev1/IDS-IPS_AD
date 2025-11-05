#!/usr/bin/env python3
"""
Train Hybrid Detector on UNSW-NB15 Dataset

Trains the hybrid anomaly detector (LSTM + Isolation Forest)
on real-world UNSW-NB15 network attack data.
"""

import sys
import pandas as pd
import numpy as np
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from ml.models.hybrid_detector import HybridAnomalyDetector

def train_on_unswnb15(train_data_path, model_save_path, epochs=30, sequence_length=10):
    """Train hybrid detector on UNSW-NB15 training data"""

    print("=" * 70)
    print("  UNSW-NB15 Hybrid Detector Training")
    print("=" * 70)
    print()

    # Load training data
    print(f"[1/5] Loading training data from {train_data_path}...")
    df_train = pd.read_csv(train_data_path)
    print(f"  [OK] Loaded {len(df_train)} records")
    print()

    # Prepare features and labels
    print("[2/5] Preparing features...")

    # Exclude label columns
    exclude_cols = ['label', 'is_attack', 'attack_category', 'attack_cat',
                   'srcip', 'dstip', 'proto', 'service', 'state', 'Label']

    feature_cols = [col for col in df_train.columns if col not in exclude_cols]

    # Get features and labels
    X_train = df_train[feature_cols].values

    # Get true labels (is_attack column: 0=normal, 1=attack)
    if 'is_attack' in df_train.columns:
        y_train = df_train['is_attack'].values
    elif 'label' in df_train.columns:
        y_train = df_train['label'].values
    else:
        print("  [ERROR] No label column found!")
        return False

    print(f"  [OK] Features: {X_train.shape}")
    print(f"  [OK] Labels: {y_train.shape}")
    print(f"       Feature names: {len(feature_cols)} features")
    print(f"       Normal: {np.sum(y_train == 0)} ({np.mean(y_train == 0) * 100:.1f}%)")
    print(f"       Attack: {np.sum(y_train == 1)} ({np.mean(y_train == 1) * 100:.1f}%)")
    print()

    # Calculate contamination (proportion of attacks)
    # Note: IsolationForest requires contamination <= 0.5
    raw_contamination = np.mean(y_train == 1)
    contamination = min(raw_contamination, 0.5)

    print(f"  Attack proportion in data: {raw_contamination:.3f} ({raw_contamination*100:.1f}%)")
    print(f"  Using contamination: {contamination:.3f} (capped at 0.5 for IsolationForest)")
    print()

    # Initialize detector
    print("[3/5] Initializing Hybrid Anomaly Detector...")
    detector = HybridAnomalyDetector(
        sequence_length=sequence_length,
        contamination=contamination
    )
    print("  [OK] Detector initialized")
    print(f"  Using LSTM: {detector.use_lstm}")
    print()

    # Train model
    print("[4/5] Training model...")
    print()
    print("=" * 70)
    print("  Training Hybrid Anomaly Detector")
    print("=" * 70)
    print()

    # Train with specified epochs (validation_split is hardcoded to 0.2 in the model)
    detector.train(X_train, epochs=epochs)

    print()
    print("=" * 70)
    print("  [SUCCESS] Training Complete!")
    print("=" * 70)
    print()

    # Save model
    print(f"[5/5] Saving model to {model_save_path}...")
    Path(model_save_path).parent.mkdir(parents=True, exist_ok=True)
    detector.save(model_save_path)
    print("  [OK] Model saved")
    print()

    # Quick evaluation on training data (sanity check)
    print("Quick Training Data Evaluation (sanity check):")
    print("-" * 70)

    # Test on a sample
    sample_size = min(10000, len(X_train))
    sample_indices = np.random.choice(len(X_train), sample_size, replace=False)
    X_sample = X_train[sample_indices]
    y_sample = y_train[sample_indices]

    results = detector.predict(X_sample)
    y_pred = results['is_anomaly']

    # Calculate metrics
    tp = np.sum((y_sample == 1) & (y_pred == 1))
    tn = np.sum((y_sample == 0) & (y_pred == 0))
    fp = np.sum((y_sample == 0) & (y_pred == 1))
    fn = np.sum((y_sample == 1) & (y_pred == 0))

    accuracy = (tp + tn) / len(y_sample)
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0

    print(f"  Samples tested: {sample_size}")
    print(f"  Accuracy:  {accuracy * 100:.1f}%")
    print(f"  Precision: {precision * 100:.1f}%")
    print(f"  Recall:    {recall * 100:.1f}%")
    print()

    print("=" * 70)
    print("  [SUCCESS] Training Complete!")
    print("=" * 70)
    print()
    print("Next steps:")
    print(f"  1. Evaluate on test data:")
    print(f"     python src/ml/evaluate_unswnb15.py --model {model_save_path}")
    print()
    print(f"  2. Use in real-time detection:")
    print(f"     python src/ml/monitoring/realtime_monitor.py")
    print()

    return True


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description='Train Hybrid Detector on UNSW-NB15 dataset'
    )

    parser.add_argument(
        '--train-data',
        default='data/datasets/unsw-nb15_train.csv',
        help='Path to training dataset (default: data/datasets/unsw-nb15_train.csv)'
    )

    parser.add_argument(
        '--model-output',
        default='data/models/unsw_nb15_model',
        help='Path to save trained model (default: data/models/unsw_nb15_model)'
    )

    parser.add_argument(
        '--epochs',
        type=int,
        default=30,
        help='Number of training epochs (default: 30)'
    )

    parser.add_argument(
        '--sequence-length',
        type=int,
        default=10,
        help='LSTM sequence length (default: 10)'
    )

    args = parser.parse_args()

    # Check if training data exists
    if not Path(args.train_data).exists():
        print(f"ERROR: Training data not found: {args.train_data}")
        print()
        print("Please ensure you have preprocessed the UNSW-NB15 dataset:")
        print("  cd data/datasets")
        print("  python preprocess_unswnb15.py")
        sys.exit(1)

    # Train
    success = train_on_unswnb15(
        args.train_data,
        args.model_output,
        epochs=args.epochs,
        sequence_length=args.sequence_length
    )

    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
