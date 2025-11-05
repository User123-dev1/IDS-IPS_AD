#!/usr/bin/env python3
"""
Fix UNSW-NB15 Dataset Files

This script detects if you have image files instead of CSV files,
and automatically downloads the correct CSV files from GitHub.
"""

import os
import sys
import requests
from pathlib import Path
from tqdm import tqdm

# GitHub mirror URLs (most reliable)
GITHUB_URLS = {
    'UNSW_NB15_training-set.csv': 'https://raw.githubusercontent.com/abhisheksaxena1998/UNSW-NB15-Dataset/main/UNSW_NB15_training-set.csv',
    'UNSW_NB15_testing-set.csv': 'https://raw.githubusercontent.com/abhisheksaxena1998/UNSW-NB15-Dataset/main/UNSW_NB15_testing-set.csv',
}

def check_file_is_csv(filepath):
    """Check if file is a valid CSV (not an image)"""
    if not filepath.exists():
        return False

    try:
        with open(filepath, 'rb') as f:
            header = f.read(512)

            # Check for image signatures
            if (b'TIFF' in header or
                header.startswith(b'II*') or
                header.startswith(b'MM\x00*') or
                header.startswith(b'\x89PNG') or
                header.startswith(b'\xff\xd8\xff')):
                return False

            # Check for CSV-like content
            if b',' in header or b'srcip' in header.lower():
                return True

        return False
    except Exception as e:
        print(f"Error checking file {filepath}: {e}")
        return False

def download_file(url, filepath, description):
    """Download a file with progress bar"""
    try:
        print(f"\nDownloading {description}...")
        print(f"  URL: {url}")
        print(f"  Destination: {filepath}")

        response = requests.get(url, stream=True, timeout=60)
        response.raise_for_status()

        total_size = int(response.headers.get('content-length', 0))

        with open(filepath, 'wb') as f:
            if total_size > 0:
                with tqdm(
                    total=total_size,
                    unit='B',
                    unit_scale=True,
                    unit_divisor=1024,
                    desc=filepath.name
                ) as pbar:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            pbar.update(len(chunk))
            else:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)

        # Verify download
        if check_file_is_csv(filepath):
            file_size = filepath.stat().st_size / (1024 * 1024)
            print(f"  ✓ Downloaded successfully ({file_size:.2f} MB)")
            return True
        else:
            print(f"  ✗ Downloaded file is not a valid CSV")
            return False

    except requests.exceptions.RequestException as e:
        print(f"  ✗ Download failed: {e}")
        return False
    except Exception as e:
        print(f"  ✗ Unexpected error: {e}")
        return False

def main():
    print("=" * 70)
    print("UNSW-NB15 Dataset File Fixer")
    print("=" * 70)
    print()

    dataset_dir = Path('data/datasets')
    dataset_dir.mkdir(parents=True, exist_ok=True)

    files_to_fix = []

    # Check each file
    for filename in GITHUB_URLS.keys():
        filepath = dataset_dir / filename

        if not filepath.exists():
            print(f"✗ {filename}: Not found")
            files_to_fix.append(filename)
        elif not check_file_is_csv(filepath):
            print(f"✗ {filename}: Invalid format (appears to be an image file)")
            files_to_fix.append(filename)
        else:
            file_size = filepath.stat().st_size / (1024 * 1024)
            print(f"✓ {filename}: Valid CSV ({file_size:.2f} MB)")

    if not files_to_fix:
        print()
        print("=" * 70)
        print("✓ All dataset files are valid!")
        print("=" * 70)
        print()
        print("Next steps:")
        print("  1. python data/datasets/preprocess_unswnb15.py")
        print("  2. python src/ml/quick_start.py --dataset data/datasets/unsw-nb15_train.csv")
        return 0

    print()
    print("=" * 70)
    print(f"Found {len(files_to_fix)} file(s) that need to be fixed")
    print("=" * 70)

    # Confirm with user
    if sys.stdin.isatty():
        print()
        print("This will:")
        for filename in files_to_fix:
            filepath = dataset_dir / filename
            if filepath.exists():
                print(f"  - Replace: {filename}")
            else:
                print(f"  - Download: {filename}")
        print()
        response = input("Continue? (y/n): ").strip().lower()
        if response != 'y':
            print("Cancelled.")
            return 1

    # Backup and download
    success_count = 0
    for filename in files_to_fix:
        filepath = dataset_dir / filename

        # Backup existing file if it exists
        if filepath.exists():
            backup_path = filepath.with_suffix('.csv.backup')
            print(f"\nBacking up existing file to: {backup_path}")
            filepath.rename(backup_path)

        # Download new file
        url = GITHUB_URLS[filename]
        if download_file(url, filepath, filename):
            success_count += 1

            # Remove backup if download successful
            backup_path = filepath.with_suffix('.csv.backup')
            if backup_path.exists():
                backup_path.unlink()
                print(f"  Removed backup file")
        else:
            # Restore backup if download failed
            backup_path = filepath.with_suffix('.csv.backup')
            if backup_path.exists():
                backup_path.rename(filepath)
                print(f"  Restored backup file")

    print()
    print("=" * 70)
    print(f"Downloaded {success_count}/{len(files_to_fix)} file(s)")
    print("=" * 70)

    if success_count == len(files_to_fix):
        print()
        print("✓ All files downloaded successfully!")
        print()
        print("Next steps:")
        print("  1. Preprocess the dataset:")
        print("     python data/datasets/preprocess_unswnb15.py")
        print()
        print("  2. Train the ML model:")
        print("     python src/ml/quick_start.py --dataset data/datasets/unsw-nb15_train.csv")
        return 0
    else:
        print()
        print("✗ Some files failed to download")
        print()
        print("Please try:")
        print("  1. Check your internet connection")
        print("  2. Run this script again")
        print("  3. See QUICKSTART.md for manual download instructions")
        return 1

if __name__ == '__main__':
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\nCancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nUnexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
