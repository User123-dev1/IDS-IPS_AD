#!/usr/bin/env python3
"""
UNSW-NB15 Dataset Preprocessor

Preprocesses the UNSW-NB15 dataset to make it compatible with the OTLAB ML pipeline.
Performs cleaning, feature engineering, normalization, and train/test splitting.

Input: Raw UNSW-NB15 CSV files from data/datasets/unsw-nb15/raw/
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

class UNSWNB15Preprocessor:
    def __init__(self, input_dir='./unsw-nb15/raw', output_dir='./'):
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # UNSW-NB15 feature columns (49 features)
        self.feature_columns = [
            'srcip', 'sport', 'dstip', 'dsport', 'proto', 'state', 'dur',
            'sbytes', 'dbytes', 'sttl', 'dttl', 'sloss', 'dloss', 'service',
            'Sload', 'Dload', 'Spkts', 'Dpkts', 'swin', 'dwin', 'stcpb',
            'dtcpb', 'smeansz', 'dmeansz', 'trans_depth', 'res_bdy_len',
            'Sjit', 'Djit', 'Stime', 'Ltime', 'Sintpkt', 'Dintpkt',
            'tcprtt', 'synack', 'ackdat', 'is_sm_ips_ports', 'ct_state_ttl',
            'ct_flw_http_mthd', 'is_ftp_login', 'ct_ftp_cmd', 'ct_srv_src',
            'ct_srv_dst', 'ct_dst_ltm', 'ct_src_ltm', 'ct_src_dport_ltm',
            'ct_dst_sport_ltm', 'ct_dst_src_ltm', 'attack_cat', 'label'
        ]

        # Numeric features
        self.numeric_features = [
            'dur', 'sbytes', 'dbytes', 'sttl', 'dttl', 'sloss', 'dloss',
            'Sload', 'Dload', 'Spkts', 'Dpkts', 'swin', 'dwin', 'stcpb',
            'dtcpb', 'smeansz', 'dmeansz', 'trans_depth', 'res_bdy_len',
            'Sjit', 'Djit', 'Stime', 'Ltime', 'Sintpkt', 'Dintpkt',
            'tcprtt', 'synack', 'ackdat', 'is_sm_ips_ports', 'ct_state_ttl',
            'ct_flw_http_mthd', 'is_ftp_login', 'ct_ftp_cmd', 'ct_srv_src',
            'ct_srv_dst', 'ct_dst_ltm', 'ct_src_ltm', 'ct_src_dport_ltm',
            'ct_dst_sport_ltm', 'ct_dst_src_ltm'
        ]

        # Categorical features
        self.categorical_features = ['proto', 'service', 'state']

        # Attack categories
        self.attack_categories = {
            'Normal': 0,
            'Generic': 1,
            'Exploits': 2,
            'Fuzzers': 3,
            'DoS': 4,
            'Reconnaissance': 5,
            'Analysis': 6,
            'Backdoor': 7,
            'Shellcode': 8,
            'Worms': 9,
        }

    def load_csv_files(self):
        """Load UNSW-NB15 CSV files"""
        # Try to load pre-split train/test sets from input_dir
        train_file = self.input_dir / 'UNSW_NB15_training-set.csv'
        test_file = self.input_dir / 'UNSW_NB15_testing-set.csv'

        # Also check parent directory (data/datasets/) if input_dir is subdirectory
        parent_train_file = self.input_dir.parent / 'UNSW_NB15_training-set.csv'
        parent_test_file = self.input_dir.parent / 'UNSW_NB15_testing-set.csv'

        # Also check current directory if running from datasets folder
        current_train_file = Path('UNSW_NB15_training-set.csv')
        current_test_file = Path('UNSW_NB15_testing-set.csv')

        # Priority: input_dir -> parent dir -> current dir
        if train_file.exists() and test_file.exists():
            print(f"Found pre-split train/test sets in {self.input_dir}")
            print(f"  - {train_file.name}")
            print(f"  - {test_file.name}")
            return self._load_presplit_sets(train_file, test_file)
        elif parent_train_file.exists() and parent_test_file.exists():
            print(f"Found pre-split train/test sets in parent directory")
            print(f"  - {parent_train_file.name}")
            print(f"  - {parent_test_file.name}")
            return self._load_presplit_sets(parent_train_file, parent_test_file)
        elif current_train_file.exists() and current_test_file.exists():
            print(f"Found pre-split train/test sets in current directory")
            print(f"  - {current_train_file.name}")
            print(f"  - {current_test_file.name}")
            return self._load_presplit_sets(current_train_file, current_test_file)

        # Otherwise, load all CSV files and combine
        csv_files = list(self.input_dir.glob('UNSW-NB15_*.csv'))

        if not csv_files:
            print(f"✗ No CSV files found in {self.input_dir}")
            print("\nPlease download the dataset first using one of these methods:")
            print("  1. python download_unswnb15.py")
            print("  2. python fix_dataset_files.py")
            print("  3. See QUICKSTART.md for manual download")
            return None, None, False

        print(f"Found {len(csv_files)} CSV files:")
        for f in csv_files:
            print(f"  - {f.name}")

        return self._load_and_combine_files(csv_files)

    def _load_presplit_sets(self, train_file, test_file):
        """Load pre-split training and testing sets"""
        print("\nLoading pre-split datasets...")

        # First, check if files are actually CSV files
        print("Checking file types...")
        for file_path in [train_file, test_file]:
            with open(file_path, 'rb') as f:
                header = f.read(512)
                if b'TIFF' in header or header.startswith(b'II*') or header.startswith(b'MM\x00*'):
                    print(f"\n✗ ERROR: {file_path.name} is a TIFF image file, not a CSV!")
                    print("The file you have is not the actual dataset.")
                    print("\nPlease download the correct CSV files:")
                    print("  1. Run: python download_unswnb15.py")
                    print("  2. Or run: python fix_dataset_files.py")
                    print("  3. Or see QUICKSTART.md for manual download")
                    return None, None, False

        # Try multiple encoding options
        encodings = ['utf-8', 'latin-1', 'iso-8859-1', 'cp1252']

        for encoding in encodings:
            try:
                print(f"Trying encoding: {encoding}...")
                # Load with error handling for malformed rows
                train_df = pd.read_csv(
                    train_file,
                    encoding=encoding,
                    on_bad_lines='skip',  # Skip malformed rows
                    engine='python'
                )
                print(f"  ✓ Loaded training set: {len(train_df)} records")

                test_df = pd.read_csv(
                    test_file,
                    encoding=encoding,
                    on_bad_lines='skip',  # Skip malformed rows
                    engine='python'
                )
                print(f"  ✓ Loaded testing set: {len(test_df)} records")

                return train_df, test_df, True

            except UnicodeDecodeError:
                print(f"  ✗ Encoding {encoding} failed, trying next...")
                continue
            except Exception as e:
                if 'Buffer overflow' in str(e):
                    print(f"\n✗ Buffer overflow error detected!")
                    print("This usually means the file is corrupted or not a valid CSV.")
                    print("\nPlease re-download the dataset:")
                    print("  python download_unswnb15.py")
                    return None, None, False
                print(f"  ✗ Error with {encoding}: {e}")
                continue

        # If all encodings failed, try with C engine
        print("\nTrying with default C engine...")
        for encoding in encodings:
            try:
                train_df = pd.read_csv(
                    train_file,
                    encoding=encoding,
                    on_bad_lines='skip'
                )
                test_df = pd.read_csv(
                    test_file,
                    encoding=encoding,
                    on_bad_lines='skip'
                )
                print(f"  ✓ Successfully loaded with {encoding} encoding")
                return train_df, test_df, True
            except:
                continue

        print("\n✗ All loading methods failed.")
        print("\nPossible issues:")
        print("  1. Files are corrupted")
        print("  2. Files are not actual CSV files")
        print("  3. Files have incompatible encoding")
        print("\nRecommended action:")
        print("  python download_unswnb15.py")
        return None, None, False

    def _load_and_combine_files(self, csv_files):
        """Load and combine multiple CSV files"""
        print("\nLoading CSV files...")

        dfs = []
        for csv_file in csv_files:
            try:
                print(f"  Loading {csv_file.name}...")
                df = pd.read_csv(csv_file, encoding='utf-8', low_memory=False)

                # Clean column names
                df.columns = df.columns.str.strip()

                dfs.append(df)
                print(f"    ✓ Loaded {len(df)} records")
            except Exception as e:
                print(f"    ✗ Error loading {csv_file.name}: {e}")
                continue

        if not dfs:
            print("✗ Failed to load any CSV files")
            return None, None, False

        # Concatenate all dataframes
        print("\nCombining all datasets...")
        df_combined = pd.concat(dfs, ignore_index=True)
        print(f"✓ Total records: {len(df_combined)}")

        return df_combined, None, False

    def clean_data(self, df):
        """Clean the dataset"""
        print("\nCleaning data...")

        initial_rows = len(df)

        # Clean column names
        df.columns = df.columns.str.strip()

        # Handle different column name formats
        if 'Label' in df.columns and 'label' not in df.columns:
            df = df.rename(columns={'Label': 'label'})
        if 'Attack_cat' in df.columns and 'attack_cat' not in df.columns:
            df = df.rename(columns={'Attack_cat': 'attack_cat'})

        # Remove rows with missing labels
        if 'label' in df.columns:
            df = df[df['label'].notna()]

        # Handle infinite values
        df = df.replace([np.inf, -np.inf], np.nan)

        # Handle missing values in numeric columns
        for col in self.numeric_features:
            if col in df.columns:
                if df[col].isna().any():
                    df[col] = df[col].fillna(df[col].median())

        # Handle missing values in categorical columns
        for col in self.categorical_features:
            if col in df.columns:
                if df[col].isna().any():
                    df[col] = df[col].fillna('unknown')

        # Handle missing attack_cat
        if 'attack_cat' in df.columns:
            df['attack_cat'] = df['attack_cat'].fillna('Normal')

        # Remove duplicate rows
        df = df.drop_duplicates()

        final_rows = len(df)
        print(f"  Removed {initial_rows - final_rows} rows")
        print(f"  ✓ Cleaned dataset: {final_rows} records")

        return df

    def feature_engineering(self, df):
        """Engineer features to match OTLAB ML pipeline"""
        print("\nEngineering features...")

        # Ensure label column exists and is binary
        if 'label' not in df.columns:
            print("✗ Error: 'label' column not found")
            return None

        # Create binary attack indicator (0 = normal, 1 = attack)
        df['is_attack'] = df['label'].astype(int)

        # Map attack categories to numeric values
        if 'attack_cat' in df.columns:
            df['attack_category'] = df['attack_cat'].map(
                lambda x: self.attack_categories.get(str(x).strip(), 0)
            )
        else:
            df['attack_category'] = df['is_attack']

        # Encode categorical features
        le_proto = LabelEncoder()
        le_service = LabelEncoder()
        le_state = LabelEncoder()

        if 'proto' in df.columns:
            df['proto_encoded'] = le_proto.fit_transform(df['proto'].astype(str))

        if 'service' in df.columns:
            df['service_encoded'] = le_service.fit_transform(df['service'].astype(str))

        if 'state' in df.columns:
            df['state_encoded'] = le_state.fit_transform(df['state'].astype(str))

        # Extract key features that align with OTLAB feature extraction
        # (matching the 10-11 features used in the ML pipeline)
        df['packet_size'] = df.get('smeansz', 0)
        df['packet_rate'] = df.get('Spkts', 0) / (df.get('dur', 1) + 1e-10)
        df['flow_duration'] = df.get('dur', 0)
        df['dst_port'] = df.get('dsport', 0)
        df['src_port'] = df.get('sport', 0)
        df['bytes_sent'] = df.get('sbytes', 0)
        df['bytes_received'] = df.get('dbytes', 0)
        df['packets_sent'] = df.get('Spkts', 0)
        df['packets_received'] = df.get('Dpkts', 0)
        df['load_ratio'] = df.get('Sload', 0) / (df.get('Dload', 1) + 1e-10)

        # === ENHANCED FEATURES FOR POOR-PERFORMING CATEGORIES ===

        # Helper function to safely get column as Series
        def get_col(col_name, default_val=0):
            """Get column as Series, or return Series of default values if missing"""
            if col_name in df.columns:
                return df[col_name]
            else:
                return pd.Series(default_val, index=df.index)

        # DoS Detection Features (currently 34.9% -> target 70%+)
        df['connection_rate'] = get_col('Spkts', 0) / (get_col('dur', 1) + 1e-10)
        df['syn_ack_ratio'] = get_col('synack', 0) / (get_col('ackdat', 1) + 1e-10)
        df['packet_loss_rate'] = (get_col('sloss', 0) + get_col('dloss', 0)) / (get_col('Spkts', 1) + get_col('Dpkts', 1) + 1e-10)
        df['flood_indicator'] = ((get_col('Spkts', 0) > 100).astype(int)) * ((get_col('dur', 1) < 1).astype(int))

        # Reconnaissance Detection Features (currently 29.4% -> target 70%+)
        df['port_scanning_indicator'] = (get_col('ct_state_ttl', 0) > 5).astype(int)
        df['service_scan_indicator'] = (get_col('ct_srv_src', 0) > 10).astype(int)
        df['host_scan_indicator'] = (get_col('ct_dst_ltm', 0) > 20).astype(int)
        df['vertical_scan'] = (get_col('ct_src_dport_ltm', 0) > 5).astype(int)  # Same IP, many ports
        df['horizontal_scan'] = (get_col('ct_dst_sport_ltm', 0) > 5).astype(int)  # Many IPs, same port

        # Backdoor Detection Features (currently 18.4% -> target 60%+)
        df['unusual_port'] = ((get_col('dsport', 0) > 49152) | (get_col('dsport', 0) < 1024)).astype(int)
        df['persistent_connection'] = (get_col('dur', 0) > 60).astype(int)  # Long-lived connection
        df['beaconing_pattern'] = ((get_col('Sintpkt', 0) > 0).astype(int)) * ((get_col('Sintpkt', 0) < 10).astype(int))  # Regular intervals
        df['c2_port_indicator'] = ((get_col('dsport', 0) == 4444) | (get_col('dsport', 0) == 8080) | (get_col('dsport', 0) == 443)).astype(int)

        # Shellcode Detection Features (currently 18.0% -> target 55%+)
        df['small_payload_indicator'] = ((get_col('res_bdy_len', 0) < 100).astype(int)) * ((get_col('res_bdy_len', 0) > 0).astype(int))
        df['exploit_pattern'] = (get_col('tcprtt', 0) > 1).astype(int)  # High RTT may indicate exploitation
        df['nop_sled_indicator'] = ((get_col('smeansz', 0) > 400).astype(int)) * ((get_col('smeansz', 0) < 600).astype(int))
        df['shellcode_port'] = ((get_col('dsport', 0) == 80) | (get_col('dsport', 0) == 443) | (get_col('dsport', 0) == 8080)).astype(int)

        # Analysis Detection Features (currently 15.4% -> target 50%+)
        df['analysis_pattern'] = (get_col('ct_flw_http_mthd', 0) > 0).astype(int)
        df['fingerprinting'] = (get_col('is_sm_ips_ports', 0) == 1).astype(int)
        df['protocol_analysis'] = (get_col('trans_depth', 0) > 1).astype(int)

        # General Improvement Features
        df['byte_asymmetry'] = abs(get_col('sbytes', 0) - get_col('dbytes', 0)) / (get_col('sbytes', 1) + get_col('dbytes', 1) + 1e-10)
        df['packet_asymmetry'] = abs(get_col('Spkts', 0) - get_col('Dpkts', 0)) / (get_col('Spkts', 1) + get_col('Dpkts', 1) + 1e-10)
        df['jitter_ratio'] = get_col('Sjit', 0) / (get_col('Djit', 1) + 1e-10)
        df['ttl_difference'] = abs(get_col('sttl', 0) - get_col('dttl', 0))
        df['connection_state'] = get_col('ct_state_ttl', 0)

        # Time-based features
        df['time_to_live'] = get_col('sttl', 0)
        df['session_duration'] = get_col('Ltime', 0) - get_col('Stime', 0)
        df['packet_interarrival'] = (get_col('Sintpkt', 0) + get_col('Dintpkt', 0)) / 2

        # Advanced ratios
        df['window_size_ratio'] = df.get('swin', 0) / (df.get('dwin', 1) + 1e-10)
        df['tcp_base_ratio'] = df.get('stcpb', 0) / (df.get('dtcpb', 1) + 1e-10)

        print("  ✓ Feature engineering complete (with enhanced attack detection features)")

        return df

    def normalize_features(self, df, fit_scaler=True):
        """Normalize features"""
        print("\nNormalizing features...")

        # Select numeric features (exclude labels and IPs)
        exclude_cols = ['label', 'is_attack', 'attack_category', 'attack_cat',
                       'srcip', 'dstip', 'proto', 'service', 'state']

        feature_cols = [col for col in df.columns if col not in exclude_cols]
        feature_cols = [col for col in feature_cols
                       if df[col].dtype in [np.int64, np.float64]]

        if fit_scaler:
            self.scaler = StandardScaler()
            df[feature_cols] = self.scaler.fit_transform(df[feature_cols])
        else:
            df[feature_cols] = self.scaler.transform(df[feature_cols])

        print(f"  ✓ Normalized {len(feature_cols)} features")

        return df

    def create_train_test_split(self, df, test_size=0.2):
        """Create train/test split"""
        print(f"\nCreating train/test split (test_size={test_size})...")

        train_df, test_df = train_test_split(
            df,
            test_size=test_size,
            random_state=42,
            stratify=df['is_attack']
        )

        print(f"  Training set: {len(train_df)} records")
        print(f"  Testing set: {len(test_df)} records")

        return train_df, test_df

    def save_datasets(self, train_df, test_df, prefix='unsw-nb15'):
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

        print("\nBinary Classification:")
        if 'is_attack' in df.columns:
            attack_counts = df['is_attack'].value_counts()
            print(f"  Normal: {attack_counts.get(0, 0):8d} ({(attack_counts.get(0, 0) / len(df)) * 100:5.2f}%)")
            print(f"  Attack: {attack_counts.get(1, 0):8d} ({(attack_counts.get(1, 0) / len(df)) * 100:5.2f}%)")

        print("\nAttack Categories:")
        if 'attack_cat' in df.columns:
            cat_counts = df['attack_cat'].value_counts()
            for cat_name, count in cat_counts.items():
                percentage = (count / len(df)) * 100
                print(f"  {str(cat_name):20s}: {count:8d} ({percentage:5.2f}%)")

    def run(self):
        """Main preprocessing pipeline"""
        print("=" * 60)
        print("UNSW-NB15 Dataset Preprocessor")
        print("=" * 60)
        print()

        # Load raw CSV files
        train_df, test_df, has_presplit = self.load_csv_files()

        if train_df is None:
            return False

        # If pre-split sets were loaded, process them separately
        if has_presplit:
            # Clean both sets
            train_df = self.clean_data(train_df)
            test_df = self.clean_data(test_df)

            if train_df is None or test_df is None:
                return False

            # Feature engineering on both sets
            train_df = self.feature_engineering(train_df)
            test_df = self.feature_engineering(test_df)

            # Print statistics (on training set)
            self.print_statistics(train_df)

            # Normalize features (fit on training data)
            train_df = self.normalize_features(train_df, fit_scaler=True)
            test_df = self.normalize_features(test_df, fit_scaler=False)

        else:
            # Process combined dataset
            df = train_df  # train_df contains combined data in this case

            # Clean data
            df = self.clean_data(df)
            if df is None:
                return False

            # Feature engineering
            df = self.feature_engineering(df)

            # Print statistics
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
        print("  1. Use unsw-nb15_train.csv for training")
        print("  2. Use unsw-nb15_test.csv for evaluation")
        print("  3. Use unsw-nb15_sample_10000.csv for quick testing")
        print()
        print("Example ML training:")
        print("  python src/ml/quick_start.py --dataset data/datasets/unsw-nb15_train.csv")

        return True


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description='Preprocess UNSW-NB15 dataset for OTLAB ML pipeline',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        '--input-dir',
        default='./unsw-nb15/raw',
        help='Input directory containing raw CSV files (default: ./unsw-nb15/raw)'
    )

    parser.add_argument(
        '--output-dir',
        default='./',
        help='Output directory for processed files (default: ./)'
    )

    args = parser.parse_args()

    preprocessor = UNSWNB15Preprocessor(
        input_dir=args.input_dir,
        output_dir=args.output_dir
    )

    success = preprocessor.run()

    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
