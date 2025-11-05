# Real-World IDS/IPS Datasets for OTLAB

This directory contains scripts to download and preprocess real-world network intrusion detection datasets for training the OTLAB machine learning models.

## Available Datasets

### 1. CICIDS2017 (Canadian Institute for Cybersecurity IDS)

**Overview:**
- **Source:** Canadian Institute for Cybersecurity, University of New Brunswick
- **Size:** ~8GB compressed, 2.8M+ network flows
- **Features:** 80+ flow-based features
- **Duration:** 5 days of network traffic (Monday-Friday)
- **Link:** https://www.unb.ca/cic/datasets/ids-2017.html

**Attack Types:**
- **Monday:** Benign traffic only
- **Tuesday:** Brute Force (FTP-Patator, SSH-Patator)
- **Wednesday:** DoS attacks (Hulk, Slowloris, SlowHTTPTest, GoldenEye), Heartbleed
- **Thursday:** Web attacks (Brute Force, XSS, SQL Injection), Infiltration
- **Friday:** Botnet (ARES), DDoS, Port Scan

**Key Features:**
- Realistic network traffic from enterprise environment
- Labeled with attack types and timestamps
- Comprehensive feature set including flow statistics, packet info, TCP flags
- Suitable for both binary and multi-class classification

**Best For:**
- Training models to detect diverse attack types
- Evaluating multi-class classification performance
- Time-series analysis of attack patterns
- Enterprise network security scenarios

---

### 2. UNSW-NB15 (University of New South Wales - Network Behavior 15)

**Overview:**
- **Source:** University of New South Wales, Australian Centre for Cyber Security
- **Size:** ~2GB, 2.5M+ records
- **Features:** 49 features (flow-based, content-based, time-based)
- **Link:** https://research.unsw.edu.au/projects/unsw-nb15-dataset

**Attack Types:**
1. **Exploits** - Buffer overflow, code injection
2. **Backdoors** - Remote access trojans
3. **DoS** - Denial of Service attacks
4. **Reconnaissance** - Port scanning, network probing
5. **Analysis** - Spam, HTML exploits
6. **Fuzzers** - Fuzzing attacks
7. **Shellcode** - Exploit payloads
8. **Worms** - Self-replicating malware
9. **Generic** - Other attack types

**Key Features:**
- Modern attack types (more recent than older datasets like KDD99)
- Balanced attack distribution
- Pre-split training/testing sets available
- Includes both normal and malicious traffic
- Detailed protocol analysis features

**Best For:**
- Training models for modern attack detection
- Binary classification (normal vs attack)
- Multi-class attack categorization
- Research and academic use

---

## Quick Start

### Step 1: Download Datasets

#### Download CICIDS2017:
```bash
cd data/datasets
python download_cicids2017.py
```

**Download Methods:**
1. **Kaggle API** (Recommended)
   - Requires: `pip install kaggle`
   - Setup: Place `kaggle.json` in `~/.kaggle/`
   - Fast and reliable

2. **Direct Download**
   - Downloads from GitHub mirror
   - Limited availability

3. **Manual Download**
   - Visit official website
   - Download CSV files manually
   - Place in `cicids2017/raw/` directory

#### Download UNSW-NB15:
```bash
cd data/datasets
python download_unswnb15.py
```

**Download Methods:**
1. **GitHub Mirror** (Fastest)
   - Pre-split train/test sets
   - Most reliable

2. **Kaggle API**
   - Requires kaggle setup
   - Alternative source

3. **Official UNSW Repository**
   - May be slower
   - Direct from source

---

### Step 2: Preprocess Datasets

#### Preprocess CICIDS2017:
```bash
cd data/datasets
python preprocess_cicids2017.py
```

**What it does:**
- Loads all CSV files from `cicids2017/raw/`
- Cleans data (removes duplicates, handles missing values)
- Engineers features compatible with OTLAB ML pipeline
- Normalizes features using StandardScaler
- Creates 80/20 train/test split
- Generates:
  - `cicids2017_train.csv` - Training set
  - `cicids2017_test.csv` - Testing set
  - `cicids2017_combined.csv` - Full dataset
  - `cicids2017_sample_10000.csv` - Small sample for quick testing

#### Preprocess UNSW-NB15:
```bash
cd data/datasets
python preprocess_unswnb15.py
```

**What it does:**
- Loads CSV files from `unsw-nb15/raw/`
- Handles pre-split train/test sets if available
- Cleans and normalizes data
- Encodes categorical features (protocol, service, state)
- Maps attack categories to numeric labels
- Generates:
  - `unsw-nb15_train.csv` - Training set
  - `unsw-nb15_test.csv` - Testing set
  - `unsw-nb15_combined.csv` - Full dataset
  - `unsw-nb15_sample_10000.csv` - Small sample for quick testing

---

### Step 3: Train ML Models

#### Using OTLAB Quick Start:
```bash
# Train with CICIDS2017
python src/ml/quick_start.py --dataset data/datasets/cicids2017_train.csv

# Train with UNSW-NB15
python src/ml/quick_start.py --dataset data/datasets/unsw-nb15_train.csv
```

#### Using Custom Training Script:
```python
import pandas as pd
from src.ml.models.hybrid_detector import HybridAnomalyDetector

# Load processed dataset
df_train = pd.read_csv('data/datasets/cicids2017_train.csv')
df_test = pd.read_csv('data/datasets/cicids2017_test.csv')

# Prepare features and labels
X_train = df_train.drop(['Label', 'is_attack', 'attack_category'], axis=1)
y_train = df_train['is_attack']

X_test = df_test.drop(['Label', 'is_attack', 'attack_category'], axis=1)
y_test = df_test['is_attack']

# Train model
detector = HybridAnomalyDetector()
detector.train(X_train.values, y_train.values)

# Evaluate
predictions = detector.predict(X_test.values)
accuracy = (predictions == y_test.values).mean()
print(f"Accuracy: {accuracy:.4f}")
```

---

## Dataset Comparison

| Feature | CICIDS2017 | UNSW-NB15 |
|---------|------------|-----------|
| **Size** | ~8GB | ~2GB |
| **Records** | 2.8M+ | 2.5M+ |
| **Features** | 80+ | 49 |
| **Attack Types** | 8 categories | 9 categories |
| **Time Period** | 5 days | Multiple days |
| **Format** | CSV | CSV |
| **Download Speed** | Slow (large) | Fast (smaller) |
| **Best For** | Diverse attacks, enterprise | Modern attacks, research |
| **Preprocessing Time** | ~10-20 min | ~5-10 min |

---

## Feature Mapping to OTLAB Pipeline

Both preprocessing scripts map dataset features to OTLAB's expected feature format:

### OTLAB ML Pipeline Features (10-11 dimensions):
1. `packet_size` - Average packet size
2. `packet_rate` - Packets per second
3. `flow_duration` - Connection duration
4. `dst_port` - Destination port
5. `src_port` - Source port (UNSW-NB15 only)
6. `bytes_sent` - Total bytes sent
7. `bytes_received` - Total bytes received
8. `packets_sent` - Total packets sent
9. `packets_received` - Total packets received
10. `tcp_flags` - TCP flag counts (CICIDS2017)
11. `load_ratio` - Load ratio (UNSW-NB15)

### Labels:
- `is_attack` - Binary label (0=benign, 1=attack)
- `attack_category` - Multi-class attack type (0-9)
- `Label` - Original attack name (preserved)

---

## Advanced Usage

### Custom Output Directory:
```bash
# Download to custom location
python download_cicids2017.py --output-dir /path/to/output

# Preprocess with custom input/output
python preprocess_cicids2017.py \
    --input-dir /path/to/raw \
    --output-dir /path/to/processed
```

### Custom Train/Test Split:
```bash
# Use 70/30 split instead of default 80/20
python preprocess_cicids2017.py --test-size 0.3
```

### Quick Testing with Sample Data:
```bash
# Use small sample (10k records) for quick experiments
python src/ml/quick_start.py --dataset data/datasets/cicids2017_sample_10000.csv
```

### Training with Hybrid Models:
```python
from src.ml.models.hybrid_security_models import (
    RandomForestSecurityClassifier,
    SVMSecurityClassifier,
    XGBoostSecurityClassifier
)

# Random Forest
rf_model = RandomForestSecurityClassifier()
rf_model.train(X_train, y_train)
rf_predictions = rf_model.predict(X_test)

# SVM
svm_model = SVMSecurityClassifier()
svm_model.train(X_train, y_train)
svm_predictions = svm_model.predict(X_test)

# XGBoost (if available)
xgb_model = XGBoostSecurityClassifier()
xgb_model.train(X_train, y_train)
xgb_predictions = xgb_model.predict(X_test)
```

---

## File Structure

```
data/datasets/
├── README.md                          # This file
├── download_cicids2017.py             # CICIDS2017 downloader
├── download_unswnb15.py               # UNSW-NB15 downloader
├── preprocess_cicids2017.py           # CICIDS2017 preprocessor
├── preprocess_unswnb15.py             # UNSW-NB15 preprocessor
│
├── cicids2017/                        # CICIDS2017 dataset
│   └── raw/                           # Raw downloaded CSV files
│       ├── Monday-WorkingHours.pcap_ISCX.csv
│       ├── Tuesday-WorkingHours.pcap_ISCX.csv
│       ├── Wednesday-WorkingHours.pcap_ISCX.csv
│       ├── Thursday-*.pcap_ISCX.csv
│       └── Friday-*.pcap_ISCX.csv
│
├── unsw-nb15/                         # UNSW-NB15 dataset
│   └── raw/                           # Raw downloaded CSV files
│       ├── UNSW_NB15_training-set.csv
│       └── UNSW_NB15_testing-set.csv
│
├── cicids2017_train.csv               # Processed training set
├── cicids2017_test.csv                # Processed testing set
├── cicids2017_combined.csv            # Full processed dataset
├── cicids2017_sample_10000.csv        # Sample for quick testing
│
├── unsw-nb15_train.csv                # Processed training set
├── unsw-nb15_test.csv                 # Processed testing set
├── unsw-nb15_combined.csv             # Full processed dataset
└── unsw-nb15_sample_10000.csv         # Sample for quick testing
```

---

## Troubleshooting

### Download Issues

**Problem:** Kaggle download fails
```
Solution:
1. Install kaggle: pip install kaggle
2. Create account at https://www.kaggle.com
3. Go to Account → API → Create New API Token
4. Place kaggle.json in ~/.kaggle/
5. Set permissions: chmod 600 ~/.kaggle/kaggle.json
```

**Problem:** Download timeout or slow
```
Solution:
- Use manual download from official sources
- Try different mirror (GitHub, Kaggle, Official)
- Download during off-peak hours
```

### Preprocessing Issues

**Problem:** Out of memory error
```
Solution:
1. Process datasets in chunks
2. Use sample datasets for testing
3. Increase system RAM or use swap
4. Process on machine with more memory
```

**Problem:** Missing columns error
```
Solution:
- Verify CSV files are complete
- Check column names (may have extra spaces)
- Re-download dataset if corrupted
```

**Problem:** sklearn not installed
```
Solution:
pip install scikit-learn pandas numpy
```

### Training Issues

**Problem:** Model training fails
```
Solution:
1. Verify processed datasets exist
2. Check feature dimensions match
3. Ensure labels are binary (0/1)
4. Use sample dataset first for testing
```

---

## Dependencies

Required Python packages:
```bash
pip install pandas numpy scikit-learn requests tqdm
```

Optional packages:
```bash
pip install kaggle          # For Kaggle downloads
pip install tensorflow      # For LSTM models
pip install xgboost        # For XGBoost models
```

---

## Citation

If you use these datasets in research, please cite:

**CICIDS2017:**
```
Sharafaldin, I., Lashkari, A.H., and Ghorbani, A.A. (2018)
"Toward Generating a New Intrusion Detection Dataset and Intrusion Traffic Characterization"
4th International Conference on Information Systems Security and Privacy (ICISSP), Portugal
```

**UNSW-NB15:**
```
Moustafa, N., and Slay, J. (2015)
"UNSW-NB15: a comprehensive data set for network intrusion detection systems"
Military Communications and Information Systems Conference (MilCIS), 2015
```

---

## Additional Resources

- **CICIDS2017 Paper:** https://www.unb.ca/cic/research/publications.html
- **UNSW-NB15 Paper:** https://ieeexplore.ieee.org/document/7348942
- **OTLAB ML Documentation:** `/ML_INTEGRATION.md`
- **Feature Extraction Guide:** `/src/ml/utils/feature_extraction.py`
- **Training Guide:** `/src/ml/quick_start.py`

---

## License

The datasets are provided by their respective institutions for research purposes.
Please review and comply with the license terms of each dataset:

- **CICIDS2017:** Canadian Institute for Cybersecurity
- **UNSW-NB15:** University of New South Wales

The download and preprocessing scripts in this repository are part of the OTLAB project
and follow the same license as the main project.

---

## Support

For issues with:
- **Download scripts:** Check download troubleshooting section above
- **Preprocessing:** Verify dependencies and input files
- **ML training:** See `/ML_INTEGRATION.md` for OTLAB ML documentation
- **OTLAB project:** Open an issue on the project repository

---

**Last Updated:** 2025-10-30
