#!/usr/bin/env python3
"""
CICIDS2017 Dataset Downloader

Downloads the CICIDS2017 (Canadian Institute for Cybersecurity Intrusion Detection System) dataset.
This dataset contains network traffic with labeled benign and attack flows.

Dataset Details:
- Source: Canadian Institute for Cybersecurity
- Size: ~8GB compressed
- Records: 2.8M+ network flows
- Features: 80+ features per flow
- Attack Types: Brute Force, DDoS, Web Attacks, Infiltration, Botnet, PortScan

Official Source: https://www.unb.ca/cic/datasets/ids-2017.html
"""

import os
import sys
import requests
import zipfile
import hashlib
from pathlib import Path
from tqdm import tqdm
import urllib.request

# CICIDS2017 dataset URLs (from official UNB CIC repository)
CICIDS2017_URLS = {
    'Monday': 'https://www.unb.ca/cic/datasets/ids-2017.html',
    'Tuesday': 'https://www.unb.ca/cic/datasets/ids-2017.html',
    'Wednesday': 'https://www.unb.ca/cic/datasets/ids-2017.html',
    'Thursday': 'https://www.unb.ca/cic/datasets/ids-2017.html',
    'Friday': 'https://www.unb.ca/cic/datasets/ids-2017.html',
}

# Alternative: Direct download links (if available from mirrors)
# Note: The official dataset requires visiting the website and accepting terms
MIRROR_URLS = [
    # Kaggle mirror (requires kaggle API)
    'kaggle datasets download -d cicdataset/cicids2017',

    # Direct CSV files (these are example paths - actual URLs may vary)
    'https://github.com/defcom17/NSL_KDD/raw/master/CICIDS2017/Monday-WorkingHours.pcap_ISCX.csv',
]

class CICIDS2017Downloader:
    def __init__(self, output_dir='./cicids2017'):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.raw_dir = self.output_dir / 'raw'
        self.raw_dir.mkdir(parents=True, exist_ok=True)

    def download_file(self, url, filename):
        """Download a file with progress bar"""
        filepath = self.raw_dir / filename

        if filepath.exists():
            print(f"✓ {filename} already exists, skipping...")
            return filepath

        print(f"Downloading {filename}...")

        try:
            response = requests.get(url, stream=True)
            response.raise_for_status()

            total_size = int(response.headers.get('content-length', 0))

            with open(filepath, 'wb') as f, tqdm(
                total=total_size,
                unit='B',
                unit_scale=True,
                unit_divisor=1024,
            ) as pbar:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        pbar.update(len(chunk))

            print(f"✓ Downloaded {filename}")
            return filepath

        except Exception as e:
            print(f"✗ Error downloading {filename}: {e}")
            if filepath.exists():
                filepath.unlink()
            return None

    def download_from_kaggle(self):
        """Download CICIDS2017 from Kaggle using kaggle API"""
        try:
            import kaggle
            print("Downloading CICIDS2017 from Kaggle...")

            # Check if kaggle is configured
            kaggle.api.authenticate()

            # Download the dataset
            kaggle.api.dataset_download_files(
                'cicdataset/cicids2017',
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
            print("\nTo use Kaggle API:")
            print("1. Create a Kaggle account at https://www.kaggle.com")
            print("2. Go to Account settings -> API -> Create New API Token")
            print("3. Place kaggle.json in ~/.kaggle/ directory")
            print("4. Install kaggle: pip install kaggle")
            return False

    def download_csv_files(self):
        """Download individual CSV files from GitHub mirror"""
        csv_files = [
            ('Monday-WorkingHours.pcap_ISCX.csv',
             'https://raw.githubusercontent.com/defcom17/NSL_KDD/master/CICIDS2017/Monday-WorkingHours.pcap_ISCX.csv'),
            ('Tuesday-WorkingHours.pcap_ISCX.csv',
             'https://raw.githubusercontent.com/defcom17/NSL_KDD/master/CICIDS2017/Tuesday-WorkingHours.pcap_ISCX.csv'),
            ('Wednesday-WorkingHours.pcap_ISCX.csv',
             'https://raw.githubusercontent.com/defcom17/NSL_KDD/master/CICIDS2017/Wednesday-WorkingHours.pcap_ISCX.csv'),
            ('Thursday-WorkingHours-Morning.pcap_ISCX.csv',
             'https://raw.githubusercontent.com/defcom17/NSL_KDD/master/CICIDS2017/Thursday-WorkingHours-Morning-WebAttacks.pcap_ISCX.csv'),
            ('Thursday-WorkingHours-Afternoon.pcap_ISCX.csv',
             'https://raw.githubusercontent.com/defcom17/NSL_KDD/master/CICIDS2017/Thursday-WorkingHours-Afternoon-Infilteration.pcap_ISCX.csv'),
            ('Friday-WorkingHours-Morning.pcap_ISCX.csv',
             'https://raw.githubusercontent.com/defcom17/NSL_KDD/master/CICIDS2017/Friday-WorkingHours-Morning.pcap_ISCX.csv'),
            ('Friday-WorkingHours-Afternoon.pcap_ISCX.csv',
             'https://raw.githubusercontent.com/defcom17/NSL_KDD/master/CICIDS2017/Friday-WorkingHours-Afternoon-PortScan.pcap_ISCX.csv'),
            ('Friday-WorkingHours-Afternoon-DDos.pcap_ISCX.csv',
             'https://raw.githubusercontent.com/defcom17/NSL_KDD/master/CICIDS2017/Friday-WorkingHours-Afternoon-DDos.pcap_ISCX.csv'),
        ]

        print("\nAttempting to download CSV files from GitHub mirror...")
        print("Note: These may not be available or complete. Use Kaggle method for full dataset.\n")

        success = False
        for filename, url in csv_files:
            result = self.download_file(url, filename)
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
        return True

    def run(self):
        """Main download process"""
        print("=" * 60)
        print("CICIDS2017 Dataset Downloader")
        print("=" * 60)
        print()

        print("This downloader supports multiple methods:")
        print("1. Kaggle API (Recommended - requires kaggle account)")
        print("2. Direct CSV download from GitHub mirror (Limited)")
        print()

        # Try Kaggle first
        print("Attempting Kaggle download...")
        if self.download_from_kaggle():
            if self.verify_download():
                return True

        # Fallback to direct CSV download
        print("\nFalling back to direct CSV download...")
        if self.download_csv_files():
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
        print("  1. Visit: https://www.unb.ca/cic/datasets/ids-2017.html")
        print("  2. Accept the terms and conditions")
        print("  3. Download the CSV files (one for each day)")
        print(f"  4. Place them in: {self.raw_dir.absolute()}")
        print()
        print("Option 2: Kaggle")
        print("  1. Visit: https://www.kaggle.com/datasets/cicdataset/cicids2017")
        print("  2. Click 'Download' (requires Kaggle account)")
        print(f"  3. Extract ZIP to: {self.raw_dir.absolute()}")
        print()
        print("Option 3: AWS S3 (if available)")
        print("  1. Visit: https://www.unb.ca/cic/datasets/ids-2017.html")
        print("  2. Follow AWS S3 download instructions")
        print()
        print("After manual download, run the preprocessing script:")
        print("  python preprocess_cicids2017.py")
        print()

        return False


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description='Download CICIDS2017 dataset',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python download_cicids2017.py
  python download_cicids2017.py --output-dir /path/to/output

Dataset Information:
  The CICIDS2017 dataset contains network traffic captured over 5 days
  (Monday to Friday) with various attack scenarios:

  - Monday: Benign traffic
  - Tuesday: Brute Force, FTP-Patator, SSH-Patator
  - Wednesday: DoS, Heartbleed
  - Thursday: Web Attacks, Infiltration
  - Friday: Botnet, PortScan, DDoS

  Total: ~2.8M records, 80+ features, ~8GB compressed
        """
    )

    parser.add_argument(
        '--output-dir',
        default='./cicids2017',
        help='Output directory for downloaded files (default: ./cicids2017)'
    )

    args = parser.parse_args()

    downloader = CICIDS2017Downloader(output_dir=args.output_dir)
    success = downloader.run()

    if success:
        print("\n✓ Download completed successfully!")
        print(f"  Files saved to: {downloader.raw_dir.absolute()}")
        print("\nNext steps:")
        print("  python preprocess_cicids2017.py")
        sys.exit(0)
    else:
        print("\n✗ Download incomplete. Please follow manual instructions above.")
        sys.exit(1)


if __name__ == '__main__':
    main()
