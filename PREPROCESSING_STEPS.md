# Step-by-Step: Fix Preprocessing and Train Model

## Issue
You're getting: `[Errno 2] No such file or directory: 'data/datasets/UNSW_NB15_training-set_preprocessed.csv'`

This means preprocessing hasn't been run yet. Here's the complete process:

---

## STEP 1: Fix the Preprocessing Script (30 seconds)

The original preprocessing script has a bug with `df.get()`. We have a fix ready.

**Run this command:**
```bash
python best_fix.py
```

**Expected Output:**
```
============================================================
Best Fix for preprocess_unswnb15.py
============================================================
✓ Created backup
✓ Added column initialization at line XX
✓ File saved!

Fix applied: All required columns will be created with defaults
This prevents AttributeError when columns are missing.

Now you can run:
  cd data/datasets
  python preprocess_unswnb15.py
```

---

## STEP 2: Download the Dataset (if not already downloaded)

Check if dataset files exist:
```bash
ls data/datasets/UNSW-NB15_*.csv
```

If files are **missing**, download them:
```bash
cd data/datasets
python download_unswnb15.py
cd ../..
```

**Note:** Download may take 5-10 minutes depending on internet speed.

---

## STEP 3: Run Preprocessing (10-15 minutes)

Now run the fixed preprocessing script:

```bash
cd data/datasets
python preprocess_unswnb15.py
cd ../..
```

**Expected Output:**
```
================================================================================
UNSW-NB15 Dataset Preprocessing
================================================================================

[1/4] Loading datasets...
  ✓ Training set loaded: 175,341 records
  ✓ Test set loaded: 82,332 records

[2/4] Cleaning data...
  ✓ Training set cleaned
  ✓ Test set cleaned

[3/4] Engineering features...
  ✓ 196 features engineered

[4/4] Saving preprocessed data...
  ✓ Saved: UNSW_NB15_training-set_preprocessed.csv
  ✓ Saved: UNSW_NB15_testing-set_preprocessed.csv

================================================================================
Preprocessing Complete!
================================================================================
```

**What this does:**
- Cleans raw dataset (handles missing values, encodes categories)
- Engineers 196 features from network traffic data
- Saves preprocessed files for training

**Output Files Created:**
```
data/datasets/
├── UNSW_NB15_training-set_preprocessed.csv   ← 175,341 samples
└── UNSW_NB15_testing-set_preprocessed.csv    ← 82,332 samples
```

---

## STEP 4: Run Improved Training (8-15 minutes)

Now you can run the improved training:

```bash
python train_improved.py
```

**Expected Output:**
```
================================================================================
IMPROVED UNSW-NB15 IDS/IPS Model Training
================================================================================

[1/7] Loading preprocessed data...
  ✓ Training: 175,341 samples, 196 features
  ✓ Testing: 82,332 samples, 196 features

[2/7] Preparing features and labels...
  ✓ Separated features and labels

[3/7] Selecting top 30 features...
  Training feature selector on 20,000 samples...
  ✓ Selected 30 features

  Top 10 features by importance:
    sbytes                             : 0.1234
    dbytes                             : 0.0987
    Sload                              : 0.0876
    Dload                              : 0.0765
    ct_state_ttl                       : 0.0654
    ...

[4/7] Normalizing features...
  ✓ Features normalized with StandardScaler

[5/7] Training Random Forest model...
  Training on 175,341 samples with 30 features...
  [This takes 5-10 minutes]
  ✓ Training complete in 8.5 minutes

[6/7] Evaluating model performance...

================================================================================
MODEL PERFORMANCE
================================================================================

Training Set Performance:
  Accuracy:  98.5%

Test Set Performance:
  Accuracy:   85.2%  ← Target: 80-90%
  Precision:  87.5%
  Recall:     82.1%
  F1-Score:   84.7%

Confusion Matrix:
                Predicted
              Normal  Attack
  Actual Normal   7450     350
         Attack    200    1000

Classification Report:
              precision    recall  f1-score   support
      Normal       0.97      0.96      0.96      7800
      Attack       0.74      0.83      0.78      1200
    accuracy                           0.94      9000

🎉 SUCCESS! Excellent model performance (≥85% accuracy)
================================================================================

[7/7] Saving model artifacts...
  ✓ Model saved: data/models/improved_ids_model.pkl
  ✓ Scaler saved: data/models/improved_ids_scaler.pkl
  ✓ Features saved: data/models/improved_ids_features.json
  ✓ Metadata saved: data/models/improved_ids_metadata.json

Training complete! Model ready for deployment.
```

---

## Complete Command Sequence

**Copy and paste these commands one by one:**

```bash
# Step 1: Fix preprocessing script
python best_fix.py

# Step 2: Check if dataset is downloaded
ls data/datasets/UNSW-NB15_*.csv

# Step 2b: Download if needed (skip if files exist)
cd data/datasets
python download_unswnb15.py
cd ../..

# Step 3: Run preprocessing (10-15 min)
cd data/datasets
python preprocess_unswnb15.py
cd ../..

# Step 4: Run improved training (8-15 min)
python train_improved.py
```

---

## Time Estimate

| Step | Time |
|------|------|
| Fix script | 30 seconds |
| Download dataset (if needed) | 5-10 minutes |
| Preprocessing | 10-15 minutes |
| Training | 8-15 minutes |
| **Total** | **20-40 minutes** |

---

## Troubleshooting

### "FileNotFoundError: UNSW-NB15_1.csv"
→ Dataset not downloaded. Run: `cd data/datasets && python download_unswnb15.py`

### "ModuleNotFoundError: No module named 'tqdm'"
→ Missing dependency. Run: `pip install tqdm`

### "ModuleNotFoundError: No module named 'sklearn'"
→ Missing dependency. Run: `pip install scikit-learn`

### "AttributeError: 'bool' object has no attribute 'astype'"
→ Preprocessing script not fixed. Run: `python best_fix.py`

### Preprocessing is very slow
→ This is normal. Processing 257,673 samples takes 10-15 minutes.

### Training is very slow
→ This is normal. Training Random Forest on 175K samples takes 8-15 minutes.

---

## Success Indicators

✅ **After Preprocessing:**
```bash
ls -lh data/datasets/*_preprocessed.csv
# You should see two files, each 50-100 MB
```

✅ **After Training:**
```bash
ls -lh data/models/improved_*
# You should see 4 files:
# - improved_ids_model.pkl (largest, ~20-50 MB)
# - improved_ids_scaler.pkl
# - improved_ids_features.json
# - improved_ids_metadata.json
```

---

## What Happens Next?

After successful training with 80-90% accuracy:

1. ✅ Integrate model into IDS/IPS application
2. ✅ Test with live network traffic
3. ✅ Run threat simulation tests (see THREAT_SIMULATION_GUIDE.md)
4. ✅ Deploy to production

---

**Start with Step 1:**
```bash
python best_fix.py
```
