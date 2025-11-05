#!/usr/bin/env python3
"""
Quick Dataset Setup for UNSW-NB15

This script helps you quickly download and set up the UNSW-NB15 dataset
for use with OTLAB ML training.
"""

import os
import sys
from pathlib import Path

def check_existing_files():
    """Check if dataset files exist and are valid CSV files"""
    dataset_dir = Path('data/datasets')

    training_file = dataset_dir / 'UNSW_NB15_training-set.csv'
    testing_file = dataset_dir / 'UNSW_NB15_testing-set.csv'

    print("Checking existing dataset files...")
    print()

    issues = []

    # Check if files exist
    if not training_file.exists():
        issues.append(f"✗ Training file not found: {training_file}")
    else:
        # Check if it's a valid CSV (check first few bytes)
        with open(training_file, 'rb') as f:
            header = f.read(100)
            if b'TIFF' in header or header.startswith(b'II*') or header.startswith(b'MM\x00*'):
                issues.append(f"✗ Training file is a TIFF image, not a CSV file!")
            elif not (b',' in header or b'srcip' in header.lower()):
                issues.append(f"✗ Training file doesn't appear to be a valid CSV")
            else:
                print(f"✓ Training file exists and looks valid")

    if not testing_file.exists():
        issues.append(f"✗ Testing file not found: {testing_file}")
    else:
        with open(testing_file, 'rb') as f:
            header = f.read(100)
            if b'TIFF' in header or header.startswith(b'II*') or header.startswith(b'MM\x00*'):
                issues.append(f"✗ Testing file is a TIFF image, not a CSV file!")
            elif not (b',' in header or b'srcip' in header.lower()):
                issues.append(f"✗ Testing file doesn't appear to be a valid CSV")
            else:
                print(f"✓ Testing file exists and looks valid")

    if issues:
        print()
        for issue in issues:
            print(issue)
        return False

    return True

def print_download_instructions():
    """Print instructions for downloading the correct dataset"""
    print()
    print("=" * 70)
    print("UNSW-NB15 Dataset Download Instructions")
    print("=" * 70)
    print()
    print("The UNSW-NB15 dataset files need to be actual CSV files, not images.")
    print()
    print("Option 1: Use the automated download script")
    print("-" * 70)
    print("  cd data/datasets")
    print("  python download_unswnb15.py")
    print()
    print("Option 2: Download manually from GitHub")
    print("-" * 70)
    print("  Training set:")
    print("  https://github.com/abhisheksaxena1998/UNSW-NB15-Dataset/raw/main/UNSW_NB15_training-set.csv")
    print()
    print("  Testing set:")
    print("  https://github.com/abhisheksaxena1998/UNSW-NB15-Dataset/raw/main/UNSW_NB15_testing-set.csv")
    print()
    print("  Save both files to: data/datasets/")
    print()
    print("Option 3: Download from Kaggle")
    print("-" * 70)
    print("  1. Install kaggle: pip install kaggle")
    print("  2. Setup API key (kaggle.json in ~/.kaggle/)")
    print("  3. Run: kaggle datasets download -d mrwellsdavid/unsw-nb15")
    print("  4. Extract to data/datasets/")
    print()
    print("Option 4: Download from Official UNSW Repository")
    print("-" * 70)
    print("  Visit: https://research.unsw.edu.au/projects/unsw-nb15-dataset")
    print("  Or: https://cloudstor.aarnet.edu.au/plus/index.php/s/2DhnLGDdEECo4ys")
    print()
    print("=" * 70)
    print()
    print("After downloading, run the preprocessing script:")
    print("  python data/datasets/preprocess_unswnb15.py")
    print()

def offer_auto_download():
    """Offer to automatically download the dataset"""
    print("Would you like to automatically download the dataset now? (y/n): ", end='')
    response = input().strip().lower()

    if response == 'y':
        print()
        print("Attempting to download from GitHub mirror...")
        import subprocess
        try:
            result = subprocess.run(
                ['python', 'data/datasets/download_unswnb15.py'],
                capture_output=False
            )
            return result.returncode == 0
        except Exception as e:
            print(f"Error running download script: {e}")
            return False

    return False

def main():
    print("=" * 70)
    print("OTLAB UNSW-NB15 Dataset Setup")
    print("=" * 70)
    print()

    if check_existing_files():
        print()
        print("✓ Dataset files are ready!")
        print()
        print("Next steps:")
        print("  1. Preprocess the dataset:")
        print("     python data/datasets/preprocess_unswnb15.py")
        print()
        print("  2. Train the ML model:")
        print("     python src/ml/quick_start.py --dataset data/datasets/unsw-nb15_train.csv")
        return 0

    print()
    print_download_instructions()

    if sys.stdin.isatty():  # Only prompt if running interactively
        offer_auto_download()

    return 1

if __name__ == '__main__':
    sys.exit(main())
