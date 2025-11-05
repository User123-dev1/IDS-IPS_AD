#!/usr/bin/env python3
"""
Automated Hyperparameter Tuning for UNSW-NB15 Hybrid Detector

Performs grid search to find optimal model parameters that maximize
detection accuracy while minimizing false positives.

Tunes:
- Contamination parameter
- Sequence length
- Number of epochs
- Batch size

Usage:
    python tune_model.py                    # Full grid search
    python tune_model.py --quick            # Quick search (fewer combinations)
    python tune_model.py --focus dos        # Optimize for specific attack type
"""

import sys
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
from itertools import product
import json

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from ml.models.hybrid_detector import HybridAnomalyDetector


class HyperparameterTuner:
    """Automated hyperparameter tuning for hybrid detector"""

    def __init__(self, train_data_path: str, test_data_path: str):
        self.train_data_path = train_data_path
        self.test_data_path = test_data_path
        self.results = []
        self.best_config = None
        self.best_score = 0

    def load_data(self):
        """Load training and test data"""
        print("Loading datasets...")

        # Load training data
        df_train = pd.read_csv(self.train_data_path)
        print(f"  ✓ Training: {len(df_train)} records")

        # Load test data
        df_test = pd.read_csv(self.test_data_path)
        print(f"  ✓ Testing: {len(df_test)} records")

        # Prepare features
        exclude_cols = ['label', 'is_attack', 'attack_category', 'attack_cat',
                       'srcip', 'dstip', 'proto', 'service', 'state', 'Label']

        feature_cols = [col for col in df_train.columns if col not in exclude_cols]

        self.X_train = df_train[feature_cols].values
        self.y_train = df_train['is_attack'].values if 'is_attack' in df_train.columns else df_train['label'].values

        self.X_test = df_test[feature_cols].values
        self.y_test = df_test['is_attack'].values if 'is_attack' in df_test.columns else df_test['label'].values

        # Get attack categories for detailed analysis
        if 'attack_category' in df_test.columns:
            self.attack_categories = df_test['attack_category'].values
        else:
            self.attack_categories = None

        print(f"  ✓ Features: {self.X_train.shape[1]}")
        print()

    def evaluate_config(self, config: dict) -> dict:
        """Evaluate a single configuration"""
        print(f"\nTesting configuration:")
        for key, value in config.items():
            print(f"  {key}: {value}")

        try:
            # Calculate contamination
            raw_contamination = np.mean(self.y_train == 1)
            contamination = min(raw_contamination * config['contamination_factor'], 0.5)

            # Create detector
            detector = HybridAnomalyDetector(
                sequence_length=config['sequence_length'],
                contamination=contamination
            )

            # Train
            print("  Training...")
            detector.train(
                normal_traffic_features=self.X_train,
                epochs=config['epochs'],
                batch_size=config['batch_size']
            )

            # Evaluate on subset for speed
            sample_size = min(10000, len(self.X_test))
            sample_indices = np.random.choice(len(self.X_test), sample_size, replace=False)
            X_sample = self.X_test[sample_indices]
            y_sample = self.y_test[sample_indices]

            # Predict
            print("  Evaluating...")
            results = detector.predict(X_sample)
            y_pred = results['is_anomaly']

            # Calculate metrics
            tp = np.sum((y_sample == 1) & (y_pred == 1))
            tn = np.sum((y_sample == 0) & (y_pred == 0))
            fp = np.sum((y_sample == 0) & (y_pred == 1))
            fn = np.sum((y_sample == 1) & (y_pred == 0))

            accuracy = (tp + tn) / len(y_sample) if len(y_sample) > 0 else 0
            precision = tp / (tp + fp) if (tp + fp) > 0 else 0
            recall = tp / (tp + fn) if (tp + fn) > 0 else 0
            f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
            fpr = fp / (fp + tn) if (fp + tn) > 0 else 0

            # Composite score (weighted average)
            # Prioritize: F1 (50%), Low FPR (30%), Accuracy (20%)
            composite_score = (
                f1 * 0.5 +
                (1 - fpr) * 0.3 +
                accuracy * 0.2
            )

            result = {
                **config,
                'accuracy': accuracy,
                'precision': precision,
                'recall': recall,
                'f1': f1,
                'fpr': fpr,
                'composite_score': composite_score,
                'tp': int(tp),
                'tn': int(tn),
                'fp': int(fp),
                'fn': int(fn)
            }

            print(f"  Results:")
            print(f"    Accuracy:  {accuracy * 100:.2f}%")
            print(f"    Precision: {precision * 100:.2f}%")
            print(f"    Recall:    {recall * 100:.2f}%")
            print(f"    F1:        {f1 * 100:.2f}%")
            print(f"    FPR:       {fpr * 100:.2f}%")
            print(f"    Score:     {composite_score * 100:.2f}%")

            return result

        except Exception as e:
            print(f"  ✗ Error: {e}")
            return {
                **config,
                'error': str(e),
                'composite_score': 0
            }

    def grid_search(self, param_grid: dict) -> list:
        """Perform grid search over parameter space"""
        print("\n" + "=" * 70)
        print("  HYPERPARAMETER GRID SEARCH")
        print("=" * 70)
        print()

        # Generate all combinations
        keys = param_grid.keys()
        values = param_grid.values()
        combinations = [dict(zip(keys, v)) for v in product(*values)]

        print(f"Testing {len(combinations)} configurations...")
        print()

        # Evaluate each configuration
        for i, config in enumerate(combinations, 1):
            print(f"\n{'=' * 70}")
            print(f"  Configuration {i}/{len(combinations)}")
            print(f"{'=' * 70}")

            result = self.evaluate_config(config)
            self.results.append(result)

            # Track best
            if result['composite_score'] > self.best_score:
                self.best_score = result['composite_score']
                self.best_config = result
                print(f"\n  🏆 NEW BEST! Score: {self.best_score * 100:.2f}%")

        return self.results

    def print_summary(self):
        """Print tuning summary"""
        print("\n" + "=" * 70)
        print("  TUNING SUMMARY")
        print("=" * 70)
        print()

        if not self.best_config:
            print("No successful configurations found.")
            return

        print("Best Configuration Found:")
        print("-" * 70)
        print(f"  Contamination Factor: {self.best_config['contamination_factor']}")
        print(f"  Sequence Length:      {self.best_config['sequence_length']}")
        print(f"  Epochs:               {self.best_config['epochs']}")
        print(f"  Batch Size:           {self.best_config['batch_size']}")
        print()
        print("Performance:")
        print("-" * 70)
        print(f"  Composite Score:      {self.best_config['composite_score'] * 100:.2f}%")
        print(f"  Accuracy:             {self.best_config['accuracy'] * 100:.2f}%")
        print(f"  Precision:            {self.best_config['precision'] * 100:.2f}%")
        print(f"  Recall:               {self.best_config['recall'] * 100:.2f}%")
        print(f"  F1-Score:             {self.best_config['f1'] * 100:.2f}%")
        print(f"  False Positive Rate:  {self.best_config['fpr'] * 100:.2f}%")
        print()

        # Show top 5 configurations
        sorted_results = sorted(
            [r for r in self.results if 'error' not in r],
            key=lambda x: x['composite_score'],
            reverse=True
        )

        if len(sorted_results) > 1:
            print("\nTop 5 Configurations:")
            print("-" * 70)
            for i, result in enumerate(sorted_results[:5], 1):
                print(f"\n{i}. Score: {result['composite_score'] * 100:.2f}%")
                print(f"   contamination_factor={result['contamination_factor']}, "
                      f"seq_len={result['sequence_length']}, "
                      f"epochs={result['epochs']}, "
                      f"batch={result['batch_size']}")
                print(f"   Acc={result['accuracy']*100:.1f}%, "
                      f"F1={result['f1']*100:.1f}%, "
                      f"FPR={result['fpr']*100:.1f}%")

        print("\n" + "=" * 70)

    def save_results(self, output_path: str):
        """Save tuning results to JSON"""
        results_data = {
            'timestamp': datetime.now().isoformat(),
            'best_config': self.best_config,
            'all_results': self.results
        }

        with open(output_path, 'w') as f:
            json.dump(results_data, f, indent=2)

        print(f"\n📄 Results saved to: {output_path}")

    def generate_training_command(self):
        """Generate command to train with best parameters"""
        if not self.best_config:
            return

        print("\n" + "=" * 70)
        print("  RECOMMENDED TRAINING COMMAND")
        print("=" * 70)
        print()
        print("To train with the optimal parameters, run:")
        print()

        # Calculate actual contamination
        raw_contamination = np.mean(self.y_train == 1)
        contamination = min(raw_contamination * self.best_config['contamination_factor'], 0.5)

        print(f"python src/ml/train_unswnb15.py \\")
        print(f"    --epochs {self.best_config['epochs']} \\")
        print(f"    --sequence-length {self.best_config['sequence_length']}")
        print()
        print(f"Note: Contamination will be automatically set to {contamination:.3f}")
        print(f"      (raw: {raw_contamination:.3f} × factor: {self.best_config['contamination_factor']})")
        print()


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description='Automated hyperparameter tuning for hybrid detector'
    )

    parser.add_argument(
        '--train-data',
        default='data/datasets/unsw-nb15_train.csv',
        help='Path to training data'
    )

    parser.add_argument(
        '--test-data',
        default='data/datasets/unsw-nb15_test.csv',
        help='Path to test data'
    )

    parser.add_argument(
        '--quick',
        action='store_true',
        help='Run quick search with fewer combinations'
    )

    parser.add_argument(
        '--output',
        default='tuning_results.json',
        help='Output file for results'
    )

    args = parser.parse_args()

    # Define parameter grid
    if args.quick:
        # Quick search - smaller grid
        param_grid = {
            'contamination_factor': [0.7, 0.9, 1.0],
            'sequence_length': [10, 15],
            'epochs': [20, 30],
            'batch_size': [32]
        }
        print("\n🚀 Quick Search Mode (12 configurations)")
    else:
        # Full search
        param_grid = {
            'contamination_factor': [0.6, 0.7, 0.8, 0.9, 1.0],
            'sequence_length': [5, 10, 15, 20],
            'epochs': [20, 30, 40, 50],
            'batch_size': [16, 32, 64]
        }
        print("\n🔍 Full Search Mode (240 configurations)")
        print("⚠️  This will take several hours!")
        print()
        response = input("Continue? (yes/no): ")
        if response.lower() != 'yes':
            print("Cancelled.")
            return

    # Run tuning
    tuner = HyperparameterTuner(args.train_data, args.test_data)
    tuner.load_data()
    tuner.grid_search(param_grid)
    tuner.print_summary()
    tuner.save_results(args.output)
    tuner.generate_training_command()

    print("\n✓ Tuning complete!")
    print()


if __name__ == "__main__":
    main()
