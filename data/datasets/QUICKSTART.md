# UNSW-NB15 Dataset Quick Start Guide

## ⚠️ Important: Correct File Format

The UNSW-NB15 dataset must be in **CSV format**, not image files. If you have TIFF/image files, those are likely screenshots or documentation, not the actual dataset.

## Current Status

Your repository currently has image files (`.csv` files that are actually TIFF images). You need to replace them with actual CSV data files.

## Step-by-Step Setup

### Step 1: Remove Incorrect Files (if present)

```bash
cd data/datasets
# Remove the image files if they exist
rm -f UNSW_NB15_training-set.csv UNSW_NB15_testing-set.csv UNSW_NB15_features.csv
```

### Step 2: Download Real CSV Files

**Option A: Automated Download (Recommended)**
```bash
cd data/datasets
python download_unswnb15.py
```

**Option B: Manual Download from GitHub**

Download these files and save them to `data/datasets/`:

1. **Training Set** (175,341 records, ~43MB)
   ```
   wget https://raw.githubusercontent.com/abhisheksaxena1998/UNSW-NB15-Dataset/main/UNSW_NB15_training-set.csv
   ```

2. **Testing Set** (82,332 records, ~20MB)
   ```
   wget https://raw.githubusercontent.com/abhisheksaxena1998/UNSW-NB15-Dataset/main/UNSW_NB15_testing-set.csv
   ```

**Option C: Using curl (if wget not available)**

```bash
cd data/datasets

# Download training set
curl -L -o UNSW_NB15_training-set.csv \
  "https://raw.githubusercontent.com/abhisheksaxena1998/UNSW-NB15-Dataset/main/UNSW_NB15_training-set.csv"

# Download testing set
curl -L -o UNSW_NB15_testing-set.csv \
  "https://raw.githubusercontent.com/abhisheksaxena1998/UNSW-NB15-Dataset/main/UNSW_NB15_testing-set.csv"
```

**Option D: Using Python (cross-platform)**

```python
import requests
from pathlib import Path

base_url = "https://raw.githubusercontent.com/abhisheksaxena1998/UNSW-NB15-Dataset/main/"
files = [
    "UNSW_NB15_training-set.csv",
    "UNSW_NB15_testing-set.csv"
]

output_dir = Path("data/datasets")
output_dir.mkdir(parents=True, exist_ok=True)

for filename in files:
    url = base_url + filename
    print(f"Downloading {filename}...")

    response = requests.get(url)
    response.raise_for_status()

    filepath = output_dir / filename
    filepath.write_bytes(response.content)

    print(f"✓ Saved to {filepath}")

print("\n✓ Download complete!")
```

Save this as `download_manual.py` and run: `python download_manual.py`

### Step 3: Verify Files

```bash
cd data/datasets
python setup_dataset.py
```

This will check if your files are valid CSV files.

**Or manually check:**
```bash
# Should show CSV data, not binary/image data
head -3 data/datasets/UNSW_NB15_training-set.csv

# Should show file sizes around 43MB and 20MB
ls -lh data/datasets/UNSW_NB15*.csv
```

Expected output:
```
srcip,sport,dstip,dsport,proto,state,dur,sbytes,dbytes,sttl,dttl,...
175.45.176.0,22624,59.166.0.6,56976,tcp,FIN,0.121478,0,0,254,252,...
...
```

### Step 4: Preprocess the Dataset

```bash
cd data/datasets
python preprocess_unswnb15.py
```

This will:
- Load the raw CSV files
- Clean and validate data
- Engineer features for OTLAB ML pipeline
- Normalize features
- Create processed datasets:
  - `unsw-nb15_train.csv`
  - `unsw-nb15_test.csv`
  - `unsw-nb15_combined.csv`
  - `unsw-nb15_sample_10000.csv`

### Step 5: Train ML Model

```bash
# Quick test with sample data
python src/ml/quick_start.py --dataset data/datasets/unsw-nb15_sample_10000.csv

# Full training with complete dataset
python src/ml/quick_start.py --dataset data/datasets/unsw-nb15_train.csv
```

## Troubleshooting

### Issue: "File is a TIFF image, not CSV"

**Problem:** You downloaded image files instead of CSV data files.

**Solution:** Follow Step 1 and Step 2 above to download the correct CSV files.

### Issue: "No such file or directory"

**Problem:** Files are in the wrong location.

**Solution:** Ensure CSV files are in `data/datasets/` directory, not subdirectories.

### Issue: "pandas/numpy not installed"

**Problem:** Missing dependencies.

**Solution:**
```bash
pip install pandas numpy scikit-learn requests
```

### Issue: "Download fails with timeout"

**Problem:** Network issues or slow connection.

**Solution:**
- Try different download option (GitHub, Kaggle, Official)
- Download during off-peak hours
- Use manual download with browser
- Check firewall/proxy settings

### Issue: "CSV file is empty or corrupted"

**Problem:** Incomplete download.

**Solution:**
```bash
# Remove corrupt files
rm data/datasets/UNSW_NB15*.csv

# Re-download
python data/datasets/download_unswnb15.py
```

## Verification Checklist

Before preprocessing, verify:

- [ ] Files are in `data/datasets/` directory
- [ ] Files end with `.csv` extension
- [ ] Files are ~43MB (training) and ~20MB (testing)
- [ ] Opening files in text editor shows CSV data, not binary
- [ ] First line contains column names: `srcip,sport,dstip,dsport,...`
- [ ] Training file has ~175,000 rows
- [ ] Testing file has ~82,000 rows

## Quick Test Script

Save this as `test_dataset.py`:

```python
import pandas as pd
from pathlib import Path

def test_dataset():
    dataset_dir = Path("data/datasets")

    # Check training set
    train_file = dataset_dir / "UNSW_NB15_training-set.csv"
    if train_file.exists():
        print("Loading training set...")
        df_train = pd.read_csv(train_file, nrows=1000)
        print(f"✓ Training set: {df_train.shape}")
        print(f"  Columns: {len(df_train.columns)}")
        print(f"  Sample row:\n{df_train.iloc[0]}\n")
    else:
        print("✗ Training set not found")

    # Check testing set
    test_file = dataset_dir / "UNSW_NB15_testing-set.csv"
    if test_file.exists():
        print("Loading testing set...")
        df_test = pd.read_csv(test_file, nrows=1000)
        print(f"✓ Testing set: {df_test.shape}")
        print(f"  Columns: {len(df_test.columns)}")
        print(f"  Labels: {df_test['label'].value_counts().to_dict()}\n")
    else:
        print("✗ Testing set not found")

if __name__ == '__main__':
    test_dataset()
```

Run: `python test_dataset.py`

## Expected File Sizes

| File | Size | Rows | Format |
|------|------|------|--------|
| UNSW_NB15_training-set.csv | ~43 MB | 175,341 | CSV |
| UNSW_NB15_testing-set.csv | ~20 MB | 82,332 | CSV |
| UNSW_NB15_features.csv | ~50 KB | 49 | CSV |

## Next Steps After Setup

1. **Explore the data:**
   ```bash
   python -c "import pandas as pd; df = pd.read_csv('data/datasets/UNSW_NB15_training-set.csv', nrows=1000); print(df.info()); print(df.head())"
   ```

2. **Preprocess for OTLAB:**
   ```bash
   python data/datasets/preprocess_unswnb15.py
   ```

3. **Train models:**
   ```bash
   python src/ml/quick_start.py --dataset data/datasets/unsw-nb15_train.csv
   ```

4. **Evaluate results:**
   - Check training accuracy
   - Validate on test set
   - Compare with synthetic data performance

## Additional Resources

- **Official Dataset Page:** https://research.unsw.edu.au/projects/unsw-nb15-dataset
- **GitHub Mirror:** https://github.com/abhisheksaxena1998/UNSW-NB15-Dataset
- **Kaggle:** https://www.kaggle.com/datasets/mrwellsdavid/unsw-nb15
- **OTLAB ML Docs:** `/ML_INTEGRATION.md`
- **Dataset README:** `/data/datasets/README.md`

## Support

If you encounter issues:
1. Check the troubleshooting section above
2. Verify file integrity with checksums
3. Try alternative download sources
4. Review error messages carefully
5. Check dependencies are installed

**Common commands:**
```bash
# Check Python version
python --version

# Install dependencies
pip install pandas numpy scikit-learn requests tqdm

# Check file type
file data/datasets/UNSW_NB15_training-set.csv

# Count lines in CSV
wc -l data/datasets/UNSW_NB15_training-set.csv
```
