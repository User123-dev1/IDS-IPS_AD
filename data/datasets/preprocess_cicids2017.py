#!/usr/bin/env python3
"""
CICIDS2017 Dataset Preprocessor

Preprocesses the CICIDS2017 dataset to make it compatible with the OTLAB ML pipeline.
Performs cleaning, feature engineering, normalization, and train/test splitting.

Input: Raw CICIDS2017 CSV files from data/datasets/cicids2017/raw/
Output: Processed datasets in data/datasets/ ready for ML training
"""

import os
import sys
import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, LabelEncoder
import warnings
warnings.filterwarnings('ignore')

class CICIDS2017Preprocessor:
    def __init__(self, input_dir='./cicids2017/raw', output_dir='./'):
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # CICIDS2017 feature columns (80+ features)
        self.numeric_features = [
            'Destination Port', 'Flow Duration', 'Total Fwd Packets',
            'Total Backward Packets', 'Total Length of Fwd Packets',
            'Total Length of Bwd Packets', 'Fwd Packet Length Max',
            'Fwd Packet Length Min', 'Fwd Packet Length Mean',
            'Fwd Packet Length Std', 'Bwd Packet Length Max',
            'Bwd Packet Length Min', 'Bwd Packet Length Mean',
            'Bwd Packet Length Std', 'Flow Bytes/s', 'Flow Packets/s',
            'Flow IAT Mean', 'Flow IAT Std', 'Flow IAT Max', 'Flow IAT Min',
            'Fwd IAT Total', 'Fwd IAT Mean', 'Fwd IAT Std', 'Fwd IAT Max',
            'Fwd IAT Min', 'Bwd IAT Total', 'Bwd IAT Mean', 'Bwd IAT Std',
            'Bwd IAT Max', 'Bwd IAT Min', 'Fwd PSH Flags', 'Bwd PSH Flags',
            'Fwd URG Flags', 'Bwd URG Flags', 'Fwd Header Length',
            'Bwd Header Length', 'Fwd Packets/s', 'Bwd Packets/s',
            'Min Packet Length', 'Max Packet Length', 'Packet Length Mean',
            'Packet Length Std', 'Packet Length Variance', 'FIN Flag Count',
            'SYN Flag Count', 'RST Flag Count', 'PSH Flag Count',
            'ACK Flag Count', 'URG Flag Count', 'CWE Flag Count',
            'ECE Flag Count', 'Down/Up Ratio', 'Average Packet Size',
            'Avg Fwd Segment Size', 'Avg Bwd Segment Size',
            'Fwd Header Length.1', 'Fwd Avg Bytes/Bulk', 'Fwd Avg Packets/Bulk',
            'Fwd Avg Bulk Rate', 'Bwd Avg Bytes/Bulk', 'Bwd Avg Packets/Bulk',
            'Bwd Avg Bulk Rate', 'Subflow Fwd Packets', 'Subflow Fwd Bytes',
            'Subflow Bwd Packets', 'Subflow Bwd Bytes', 'Init_Win_bytes_forward',
            'Init_Win_bytes_backward', 'act_data_pkt_fwd', 'min_seg_size_forward',
            'Active Mean', 'Active Std', 'Active Max', 'Active Min',
            'Idle Mean', 'Idle Std', 'Idle Max', 'Idle Min'
        ]

        self.categorical_features = []

        # Attack type mapping for binary and multi-class classification
        self.attack_types = {
            'BENIGN': 0,
            'DoS Hulk': 1,
            'PortScan': 2,
            'DDoS': 3,
            'DoS GoldenEye': 1,
            'FTP-Patator': 4,
            'SSH-Patator': 4,
            'DoS slowloris': 1,
            'DoS Slowhttptest': 1,
            'Bot': 5,
            'Web Attack – Brute Force': 6,
            'Web Attack – XSS': 6,
            'Web Attack – Sql Injection': 6,
            'Infiltration': 7,
            'Heartbleed': 8,
        }

        # Map to general attack categories
        self.attack_categories = {
            0: 'Benign',
            1: 'DoS',
            2: 'PortScan',
            3: 'DDoS',
            4: 'Brute Force',
            5: 'Botnet',
            6: 'Web Attack',
            7: 'Infiltration',
            8: 'Heartbleed'
        }

    def load_csv_files(self):
        """Load all CSV files from the raw directory"""
        csv_files = list(self.input_dir.glob('*.csv'))

        if not csv_files:
            print(f"✗ No CSV files found in {self.input_dir}")
            print("Please run download_cicids2017.py first")
            return None

        print(f"Found {len(csv_files)} CSV files:")
        for f in csv_files:
            print(f"  - {f.name}")

        print("\nLoading CSV files...")
        dfs = []
        for csv_file in csv_files:
            try:
                print(f"  Loading {csv_file.name}...")
                df = pd.read_csv(csv_file, encoding='utf-8', low_memory=False)

                # Clean column names (remove extra spaces)
                df.columns = df.columns.str.strip()

                dfs.append(df)
                print(f"    ✓ Loaded {len(df)} records")
            except Exception as e:
                print(f"    ✗ Error loading {csv_file.name}: {e}")
                continue

        if not dfs:
            print("✗ Failed to load any CSV files")
            return None

        # Concatenate all dataframes
        print("\nCombining all datasets...")
        df_combined = pd.concat(dfs, ignore_index=True)
        print(f"✓ Total records: {len(df_combined)}")

        return df_combined

    def clean_data(self, df):
        """Clean the dataset"""
        print("\nCleaning data...")

        initial_rows = len(df)

        # Handle label column (different possible names)
        label_columns = ['Label', ' Label', 'label', ' label']
        label_col = None
        for col in label_columns:
            if col in df.columns:
                label_col = col
                break

        if label_col is None:
            print("✗ Error: Could not find label column")
            return None

        # Rename label column to standard name
        if label_col != 'Label':
            df = df.rename(columns={label_col: 'Label'})

        # Remove rows with missing labels
        df = df[df['Label'].notna()]

        # Handle infinite values
        df = df.replace([np.inf, -np.inf], np.nan)

        # Handle missing values
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        for col in numeric_cols:
            if df[col].isna().any():
                df[col] = df[col].fillna(df[col].median())

        # Remove duplicate rows
        df = df.drop_duplicates()

        final_rows = len(df)
        print(f"  Removed {initial_rows - final_rows} rows")
        print(f"  ✓ Cleaned dataset: {final_rows} records")

        return df

    def feature_engineering(self, df):
        """Engineer features to match OTLAB ML pipeline"""
        print("\nEngineering features...")

        # Ensure numeric columns are properly typed
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        for col in numeric_cols:
            if col != 'Label':
                df[col] = pd.to_numeric(df[col], errors='coerce')

        # Create binary attack indicator
        df['is_attack'] = (df['Label'] != 'BENIGN').astype(int)

        # Map attack types to categories
        df['attack_category'] = df['Label'].map(
            lambda x: self.attack_types.get(x, 0)
        )

        # Extract key features that align with OTLAB feature extraction
        # (matching the 10-11 features used in the ML pipeline)
        df['packet_size'] = df.get('Packet Length Mean', 0)
        df['packet_rate'] = df.get('Flow Packets/s', 0)
        df['flow_duration'] = df.get('Flow Duration', 0)
        df['dst_port'] = df.get('Destination Port', 0)
        df['fwd_packets'] = df.get('Total Fwd Packets', 0)
        df['bwd_packets'] = df.get('Total Backward Packets', 0)
        df['fin_flag'] = df.get('FIN Flag Count', 0)
        df['syn_flag'] = df.get('SYN Flag Count', 0)
        df['rst_flag'] = df.get('RST Flag Count', 0)
        df['psh_flag'] = df.get('PSH Flag Count', 0)
        df['ack_flag'] = df.get('ACK Flag Count', 0)

        print("  ✓ Feature engineering complete")

        return df

    def normalize_features(self, df, fit_scaler=True):
        """Normalize features"""
        print("\nNormalizing features...")

        # Select numeric features (exclude labels)
        feature_cols = [col for col in df.columns
                       if col not in ['Label', 'is_attack', 'attack_category']]
        feature_cols = [col for col in feature_cols
                       if df[col].dtype in [np.int64, np.float64]]

        if fit_scaler:
            self.scaler = StandardScaler()
            df[feature_cols] = self.scaler.fit_transform(df[feature_cols])
        else:
            df[feature_cols] = self.scaler.transform(df[feature_cols])

        print(f"  ✓ Normalized {len(feature_cols)} features")

        return df

    def create_train_test_split(self, df, test_size=0.2, stratify=True):
        """Create train/test split"""
        print(f"\nCreating train/test split (test_size={test_size})...")

        stratify_col = df['is_attack'] if stratify else None

        train_df, test_df = train_test_split(
            df,
            test_size=test_size,
            random_state=42,
            stratify=stratify_col
        )

        print(f"  Training set: {len(train_df)} records")
        print(f"  Testing set: {len(test_df)} records")

        return train_df, test_df

    def save_datasets(self, train_df, test_df, prefix='cicids2017'):
        """Save processed datasets"""
        print("\nSaving processed datasets...")

        # Save full datasets
        train_path = self.output_dir / f'{prefix}_train.csv'
        test_path = self.output_dir / f'{prefix}_test.csv'

        train_df.to_csv(train_path, index=False)
        test_df.to_csv(test_path, index=False)

        print(f"  ✓ Saved: {train_path.name} ({len(train_df)} records)")
        print(f"  ✓ Saved: {test_path.name} ({len(test_df)} records)")

        # Save combined dataset
        combined_path = self.output_dir / f'{prefix}_combined.csv'
        combined_df = pd.concat([train_df, test_df], ignore_index=True)
        combined_df.to_csv(combined_path, index=False)
        print(f"  ✓ Saved: {combined_path.name} ({len(combined_df)} records)")

        # Save a smaller sample for quick testing
        sample_size = min(10000, len(combined_df))
        sample_df = combined_df.sample(n=sample_size, random_state=42)
        sample_path = self.output_dir / f'{prefix}_sample_{sample_size}.csv'
        sample_df.to_csv(sample_path, index=False)
        print(f"  ✓ Saved: {sample_path.name} ({len(sample_df)} records)")

        return {
            'train': train_path,
            'test': test_path,
            'combined': combined_path,
            'sample': sample_path
        }

    def print_statistics(self, df):
        """Print dataset statistics"""
        print("\nDataset Statistics:")
        print("=" * 60)

        print(f"Total records: {len(df)}")
        print(f"Total features: {len(df.columns) - 3}")  # Exclude label columns

        print("\nAttack Distribution:")
        label_counts = df['Label'].value_counts()
        for label, count in label_counts.items():
            percentage = (count / len(df)) * 100
            print(f"  {label:30s}: {count:8d} ({percentage:5.2f}%)")

        print("\nBinary Classification:")
        attack_counts = df['is_attack'].value_counts()
        print(f"  Benign: {attack_counts.get(0, 0):8d} ({(attack_counts.get(0, 0) / len(df)) * 100:5.2f}%)")
        print(f"  Attack: {attack_counts.get(1, 0):8d} ({(attack_counts.get(1, 0) / len(df)) * 100:5.2f}%)")

        print("\nAttack Categories:")
        cat_counts = df['attack_category'].value_counts()
        for cat_id in sorted(cat_counts.index):
            cat_name = self.attack_categories.get(cat_id, 'Unknown')
            count = cat_counts[cat_id]
            percentage = (count / len(df)) * 100
            print(f"  {cat_name:20s}: {count:8d} ({percentage:5.2f}%)")

    def run(self):
        """Main preprocessing pipeline"""
        print("=" * 60)
        print("CICIDS2017 Dataset Preprocessor")
        print("=" * 60)
        print()

        # Load raw CSV files
        df = self.load_csv_files()
        if df is None:
            return False

        # Clean data
        df = self.clean_data(df)
        if df is None:
            return False

        # Feature engineering
        df = self.feature_engineering(df)

        # Print statistics before normalization
        self.print_statistics(df)

        # Create train/test split
        train_df, test_df = self.create_train_test_split(df)

        # Normalize features (fit on training data)
        train_df = self.normalize_features(train_df, fit_scaler=True)
        test_df = self.normalize_features(test_df, fit_scaler=False)

        # Save datasets
        saved_files = self.save_datasets(train_df, test_df)

        print("\n" + "=" * 60)
        print("✓ Preprocessing completed successfully!")
        print("=" * 60)
        print("\nOutput files:")
        for name, path in saved_files.items():
            print(f"  {name:10s}: {path}")

        print("\nNext steps:")
        print("  1. Use cicids2017_train.csv for training")
        print("  2. Use cicids2017_test.csv for evaluation")
        print("  3. Use cicids2017_sample_10000.csv for quick testing")
        print()
        print("Example ML training:")
        print("  python src/ml/quick_start.py --dataset data/datasets/cicids2017_train.csv")

        return True


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description='Preprocess CICIDS2017 dataset for OTLAB ML pipeline',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        '--input-dir',
        default='./cicids2017/raw',
        help='Input directory containing raw CSV files (default: ./cicids2017/raw)'
    )

    parser.add_argument(
        '--output-dir',
        default='./',
        help='Output directory for processed files (default: ./)'
    )

    parser.add_argument(
        '--test-size',
        type=float,
        default=0.2,
        help='Test set size as fraction (default: 0.2)'
    )

    args = parser.parse_args()

    preprocessor = CICIDS2017Preprocessor(
        input_dir=args.input_dir,
        output_dir=args.output_dir
    )

    success = preprocessor.run()

    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
