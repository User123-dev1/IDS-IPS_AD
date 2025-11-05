#!/usr/bin/env python3
"""
UNSW-NB15 Dataset Downloader

Downloads the UNSW-NB15 (University of New South Wales - Network Behavior 15) dataset.
This dataset contains network traffic with modern attack types.

Dataset Details:
- Source: University of New South Wales
- Size: ~2GB
- Records: 2.5M+ records
- Features: 49 features
- Attack Types: Exploits, Backdoors, DoS, Reconnaissance, Analysis, Fuzzers, Shellcode, Worms, Generic

Official Source: https://research.unsw.edu.au/projects/unsw-nb15-dataset
"""

import os
import sys
import requests
import csv
import gzip
from pathlib import Path
from tqdm import tqdm
import urllib.request

# UNSW-NB15 dataset URLs (official UNSW repository)
UNSW_NB15_URLS = {
    # Training and testing CSV files
    'UNSW-NB15_1.csv': 'https://cloudstor.aarnet.edu.au/plus/s/2DhnLGDdEECo4ys/download?path=%2F&files=UNSW-NB15_1.csv',
    'UNSW-NB15_2.csv': 'https://cloudstor.aarnet.edu.au/plus/s/2DhnLGDdEECo4ys/download?path=%2F&files=UNSW-NB15_2.csv',
    'UNSW-NB15_3.csv': 'https://cloudstor.aarnet.edu.au/plus/s/2DhnLGDdEECo4ys/download?path=%2F&files=UNSW-NB15_3.csv',
    'UNSW-NB15_4.csv': 'https://cloudstor.aarnet.edu.au/plus/s/2DhnLGDdEECo4ys/download?path=%2F&files=UNSW-NB15_4.csv',

    # Feature names
    'UNSW-NB15_features.csv': 'https://cloudstor.aarnet.edu.au/plus/s/2DhnLGDdEECo4ys/download?path=%2F&files=NUSW-NB15_features.csv',

    # Pre-split training and test sets
    'UNSW_NB15_training-set.csv': 'https://cloudstor.aarnet.edu.au/plus/s/2DhnLGDdEECo4ys/download?path=%2F&files=UNSW_NB15_training-set.csv',
    'UNSW_NB15_testing-set.csv': 'https://cloudstor.aarnet.edu.au/plus/s/2DhnLGDdEECo4ys/download?path=%2F&files=UNSW_NB15_testing-set.csv',
}

# Alternative URLs (Kaggle, GitHub)
KAGGLE_DATASET = 'mrwellsdavid/unsw-nb15'

GITHUB_MIRROR_URLS = {
    'UNSW_NB15_training-set.csv': 'https://github.com/abhisheksaxena1998/UNSW-NB15-Dataset/raw/main/UNSW_NB15_training-set.csv',
    'UNSW_NB15_testing-set.csv': 'https://github.com/abhisheksaxena1998/UNSW-NB15-Dataset/raw/main/UNSW_NB15_testing-set.csv',
}


class UNSWNB15Downloader:
    def __init__(self, output_dir='./unsw-nb15'):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.raw_dir = self.output_dir / 'raw'
        self.raw_dir.mkdir(parents=True, exist_ok=True)

    def download_file(self, url, filename, timeout=300):
        """Download a file with progress bar"""
        filepath = self.raw_dir / filename

        if filepath.exists():
            print(f"✓ {filename} already exists, skipping...")
            return filepath

        print(f"Downloading {filename}...")

        try:
            # Use requests with stream=True for progress tracking
            response = requests.get(url, stream=True, timeout=timeout, allow_redirects=True)
            response.raise_for_status()

            total_size = int(response.headers.get('content-length', 0))

            with open(filepath, 'wb') as f:
                if total_size > 0:
                    with tqdm(
                        total=total_size,
                        unit='B',
                        unit_scale=True,
                        unit_divisor=1024,
                    ) as pbar:
                        for chunk in response.iter_content(chunk_size=8192):
                            if chunk:
                                f.write(chunk)
                                pbar.update(len(chunk))
                else:
                    # No content-length header, download without progress
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)

            print(f"✓ Downloaded {filename}")
            return filepath

        except requests.exceptions.Timeout:
            print(f"✗ Timeout downloading {filename}")
            if filepath.exists():
                filepath.unlink()
            return None
        except requests.exceptions.RequestException as e:
            print(f"✗ Error downloading {filename}: {e}")
            if filepath.exists():
                filepath.unlink()
            return None
        except Exception as e:
            print(f"✗ Unexpected error downloading {filename}: {e}")
            if filepath.exists():
                filepath.unlink()
            return None

    def download_from_kaggle(self):
        """Download UNSW-NB15 from Kaggle using kaggle API"""
        try:
            import kaggle
            print("Downloading UNSW-NB15 from Kaggle...")

            # Check if kaggle is configured
            kaggle.api.authenticate()

            # Download the dataset
            kaggle.api.dataset_download_files(
                KAGGLE_DATASET,
                path=str(self.raw_dir),
                unzip=True
            )

            print("✓ Successfully downloaded from Kaggle")
            return True

        except ImportError:
            print("✗ Kaggle package not installed. Install with: pip install kaggle")
            return False
        except Exception as e:
            print(f"✗ Error downloading from Kaggle: {e}")
            return False

    def download_from_github_mirror(self):
        """Download UNSW-NB15 from GitHub mirror"""
        print("\nAttempting to download from GitHub mirror...")

        success = False
        for filename, url in GITHUB_MIRROR_URLS.items():
            result = self.download_file(url, filename)
            if result:
                success = True

        return success

    def download_from_official(self):
        """Download UNSW-NB15 from official UNSW repository"""
        print("\nAttempting to download from official UNSW repository...")

        # Download the pre-split training and test sets (most commonly used)
        essential_files = {
            'UNSW_NB15_training-set.csv': UNSW_NB15_URLS['UNSW_NB15_training-set.csv'],
            'UNSW_NB15_testing-set.csv': UNSW_NB15_URLS['UNSW_NB15_testing-set.csv'],
        }

        success = False
        for filename, url in essential_files.items():
            result = self.download_file(url, filename, timeout=600)
            if result:
                success = True

        return success

    def verify_download(self):
        """Verify that CSV files were downloaded"""
        csv_files = list(self.raw_dir.glob('*.csv'))

        if not csv_files:
            print("\n✗ No CSV files found!")
            return False

        print(f"\n✓ Found {len(csv_files)} CSV files:")
        total_size = 0
        for csv_file in csv_files:
            size = csv_file.stat().st_size
            total_size += size
            print(f"  - {csv_file.name} ({size / 1024 / 1024:.2f} MB)")

        print(f"\nTotal size: {total_size / 1024 / 1024:.2f} MB")

        # Verify file structure
        if csv_files:
            print("\nVerifying file structure...")
            sample_file = csv_files[0]
            try:
                import pandas as pd
                df = pd.read_csv(sample_file, nrows=5)
                print(f"  Columns: {len(df.columns)}")
                print(f"  Sample shape: {df.shape}")
                print("  ✓ File structure looks valid")
            except Exception as e:
                print(f"  ✗ Warning: Could not verify file structure: {e}")

        return True

    def run(self):
        """Main download process"""
        print("=" * 60)
        print("UNSW-NB15 Dataset Downloader")
        print("=" * 60)
        print()

        print("This downloader supports multiple methods:")
        print("1. GitHub Mirror (Fast, pre-split train/test)")
        print("2. Kaggle API (requires kaggle account)")
        print("3. Official UNSW Repository (may be slow)")
        print()

        # Try GitHub mirror first (fastest and most reliable)
        if self.download_from_github_mirror():
            if self.verify_download():
                return True

        # Try Kaggle
        print("\nGitHub download incomplete. Trying Kaggle...")
        if self.download_from_kaggle():
            if self.verify_download():
                return True

        # Try official repository
        print("\nKaggle download incomplete. Trying official UNSW repository...")
        if self.download_from_official():
            if self.verify_download():
                return True

        # If all methods fail, provide instructions
        print("\n" + "=" * 60)
        print("MANUAL DOWNLOAD INSTRUCTIONS")
        print("=" * 60)
        print()
        print("If automatic download failed, please manually download:")
        print()
        print("Option 1: Official Source")
        print("  1. Visit: https://research.unsw.edu.au/projects/unsw-nb15-dataset")
        print("  2. Download the CSV files:")
        print("     - UNSW_NB15_training-set.csv")
        print("     - UNSW_NB15_testing-set.csv")
        print(f"  3. Place them in: {self.raw_dir.absolute()}")
        print()
        print("Option 2: Kaggle")
        print("  1. Visit: https://www.kaggle.com/datasets/mrwellsdavid/unsw-nb15")
        print("  2. Click 'Download' (requires Kaggle account)")
        print(f"  3. Extract to: {self.raw_dir.absolute()}")
        print()
        print("Option 3: Alternative Research Repository")
        print("  1. Visit: https://cloudstor.aarnet.edu.au/plus/index.php/s/2DhnLGDdEECo4ys")
        print("  2. Download the training and testing CSV files")
        print(f"  3. Place them in: {self.raw_dir.absolute()}")
        print()
        print("After manual download, run the preprocessing script:")
        print("  python preprocess_unswnb15.py")
        print()

        return False


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description='Download UNSW-NB15 dataset',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python download_unswnb15.py
  python download_unswnb15.py --output-dir /path/to/output

Dataset Information:
  The UNSW-NB15 dataset contains modern network traffic with attack types:

  Attack Categories:
  - Exploits: Buffer overflow, code injection
  - Backdoors: Remote access trojans
  - DoS: Denial of Service attacks
  - Reconnaissance: Port scanning, network probing
  - Analysis: Spam, HTML exploits
  - Fuzzers: Fuzzing attacks
  - Shellcode: Exploit payloads
  - Worms: Self-replicating malware
  - Generic: Other attack types

  Features: 49 (including flow-based, content-based, time-based)
  Records: ~2.5M total (175K training, 82K testing in pre-split sets)
  Size: ~2GB
        """
    )

    parser.add_argument(
        '--output-dir',
        default='./unsw-nb15',
        help='Output directory for downloaded files (default: ./unsw-nb15)'
    )

    args = parser.parse_args()

    downloader = UNSWNB15Downloader(output_dir=args.output_dir)
    success = downloader.run()

    if success:
        print("\n✓ Download completed successfully!")
        print(f"  Files saved to: {downloader.raw_dir.absolute()}")
        print("\nNext steps:")
        print("  python preprocess_unswnb15.py")
        sys.exit(0)
    else:
        print("\n✗ Download incomplete. Please follow manual instructions above.")
        sys.exit(1)


if __name__ == '__main__':
    main()
