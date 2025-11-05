# IDS/IPS Enhancement Guide

Comprehensive guide to the new features added to improve ML-based intrusion detection performance.

## 🎯 Overview

This guide covers four major enhancements:

1. **Automated Hyperparameter Tuning** - Find optimal model parameters
2. **Enhanced Feature Engineering** - Improve detection of poor-performing attack categories
3. **HTML Report Generator** - Create professional performance reports
4. **GUI-Integrated Attack Simulations** - Test IDS/IPS directly from the interface

---

## 1. Automated Hyperparameter Tuning

### Purpose
Automatically search for optimal model parameters to maximize detection accuracy while minimizing false positives.

### Location
```
src/ml/tune_model.py
```

### What It Tunes
- **Contamination Factor** (0.6 - 1.0): Controls anomaly threshold
- **Sequence Length** (5 - 20): LSTM input window size
- **Epochs** (20 - 50): Training iterations
- **Batch Size** (16 - 64): Training batch size

### Usage

**Quick Search (12 configurations, ~30 minutes):**
```powershell
python src\ml\tune_model.py --quick
```

**Full Search (240 configurations, ~8-12 hours):**
```powershell
python src\ml\tune_model.py
```

**Custom dataset:**
```powershell
python src\ml\tune_model.py \
    --train-data data\datasets\unsw-nb15_train.csv \
    --test-data data\datasets\unsw-nb15_test.csv \
    --output my_tuning_results.json
```

### Output

**Results File** (`tuning_results.json`):
```json
{
  "timestamp": "2025-11-03T20:30:00",
  "best_config": {
    "contamination_factor": 0.8,
    "sequence_length": 15,
    "epochs": 40,
    "batch_size": 32,
    "accuracy": 0.682,
    "f1": 0.715,
    "fpr": 0.234,
    "composite_score": 0.698
  },
  "all_results": [...]
}
```

**Terminal Output:**
- Real-time progress for each configuration
- Performance metrics (Accuracy, Precision, Recall, F1, FPR)
- Top 5 best configurations
- Recommended training command

### Scoring System

Composite score prioritizes:
- **F1-Score (50%)** - Balance of precision and recall
- **Low FPR (30%)** - Minimize false positives
- **Accuracy (20%)** - Overall correctness

### Example Output

```
Testing Configuration 15/240
===============================================
  contamination_factor: 0.8
  sequence_length: 15
  epochs: 40
  batch_size: 32

  Training...
  Evaluating...

  Results:
    Accuracy:  68.2%
    Precision: 72.5%
    Recall:    71.8%
    F1:        71.5%
    FPR:       23.4%
    Score:     69.8%

  🏆 NEW BEST! Score: 69.8%
```

### Best Practices

1. **Start with Quick Search**
   - Fast results (~30 min)
   - Good enough for most cases
   - Identify promising parameter ranges

2. **Use Full Search for Production**
   - More thorough optimization
   - Run overnight
   - Better final performance

3. **Retrain with Best Parameters**
   ```powershell
   # Use the recommended command from tuning output
   python src\ml\train_unswnb15.py --epochs 40 --sequence-length 15
   ```

---

## 2. Enhanced Feature Engineering

### Purpose
Add specialized features to improve detection of poorly-performing attack categories.

### Location
```
data/datasets/preprocess_unswnb15.py
```

### Current Performance vs. Targets

| Category | Current | Target | Status |
|----------|---------|--------|--------|
| DoS | 34.9% | 70%+ | ⚠️ Needs improvement |
| Reconnaissance | 29.4% | 70%+ | ⚠️ Needs improvement |
| Backdoor | 18.4% | 60%+ | ❌ Poor |
| Shellcode | 18.0% | 55%+ | ❌ Poor |
| Analysis | 15.4% | 50%+ | ❌ Poor |

### New Features Added

#### DoS Detection Features (4 features)
```python
connection_rate       # Packets per second
syn_ack_ratio        # SYN/ACK packet ratio
packet_loss_rate     # Percentage of lost packets
flood_indicator      # High packets + short duration flag
```

#### Reconnaissance Features (5 features)
```python
port_scanning_indicator   # Multiple ports accessed
service_scan_indicator   # Service enumeration detected
host_scan_indicator      # Network-wide scanning
vertical_scan           # Same IP, many ports
horizontal_scan         # Many IPs, same port
```

#### Backdoor Detection Features (4 features)
```python
unusual_port           # High/low port numbers
persistent_connection  # Long-lived connections
beaconing_pattern     # Regular periodic traffic
c2_port_indicator     # Known C&C ports (4444, 8080, 443)
```

#### Shellcode Detection Features (4 features)
```python
small_payload_indicator  # Tiny payloads
exploit_pattern         # High RTT (exploitation delay)
nop_sled_indicator     # 400-600 byte payloads (NOP sleds)
shellcode_port         # Target ports 80/443/8080
```

#### Analysis Detection Features (3 features)
```python
analysis_pattern     # HTTP method analysis
fingerprinting      # Same source/dest IP+port
protocol_analysis   # Protocol depth > 1
```

#### General Improvements (9 features)
```python
byte_asymmetry          # Send/receive imbalance
packet_asymmetry        # Packet count imbalance
jitter_ratio            # Network jitter
ttl_difference          # TTL variations
connection_state        # Connection state tracking
time_to_live           # Packet TTL
session_duration       # Total session time
packet_interarrival    # Inter-packet timing
window_size_ratio      # TCP window size ratio
tcp_base_ratio         # TCP base sequence ratio
```

### Total New Features: 32

### Usage

**Preprocess with enhanced features:**
```powershell
cd data\datasets
python preprocess_unswnb15.py
```

**Training with enhanced features:**
```powershell
# The enhanced features are automatically included
python src\ml\train_unswnb15.py
```

### Expected Improvements

After retraining with enhanced features:

| Category | Before | After (Expected) | Improvement |
|----------|--------|------------------|-------------|
| DoS | 34.9% | 65-75% | +30-40% |
| Reconnaissance | 29.4% | 65-75% | +35-45% |
| Backdoor | 18.4% | 50-65% | +30-45% |
| Shellcode | 18.0% | 45-60% | +27-42% |
| Analysis | 15.4% | 40-55% | +25-40% |

### Feature Impact Analysis

**Most Impactful for DoS:**
- `flood_indicator` - Direct DoS detection
- `connection_rate` - Abnormal connection patterns

**Most Impactful for Reconnaissance:**
- `port_scanning_indicator` - Port sweep detection
- `vertical_scan` / `horizontal_scan` - Scan pattern recognition

**Most Impactful for Backdoor:**
- `beaconing_pattern` - Periodic C&C traffic
- `persistent_connection` - Long-lived connections

---

## 3. HTML Report Generator

### Purpose
Create professional, visually-appealing performance reports with charts and recommendations.

### Location
```
src/ml/generate_report.py
```

### Features

- **Visual Metrics Dashboard**
  - Color-coded performance indicators
  - Large, easy-to-read metric cards
  - Green/Orange/Red status indicators

- **Confusion Matrix Visualization**
  - TP, TN, FP, FN displayed clearly
  - Color-coded cells (green for correct, red for errors)

- **Per-Category Detection Rates**
  - Horizontal bar charts
  - Sortable by performance
  - Color-coded by detection rate

- **Automated Recommendations**
  - Identifies specific issues
  - Provides actionable solutions
  - Context-aware suggestions

### Usage

**Generate report from trained model:**
```powershell
python src\ml\generate_report.py \
    --model data\models\unsw_nb15_model \
    --output ml_performance_report.html
```

**Generate with JSON output:**
```powershell
python src\ml\generate_report.py \
    --model data\models\unsw_nb15_model \
    --output report.html \
    --json results.json
```

**Custom test data:**
```powershell
python src\ml\generate_report.py \
    --model data\models\unsw_nb15_model \
    --test-data data\datasets\unsw-nb15_test.csv \
    --output custom_report.html
```

### Report Sections

1. **Header**
   - Generated timestamp
   - Model path
   - Total samples tested

2. **Overall Performance Metrics**
   - Accuracy
   - Precision
   - Recall
   - F1-Score
   - False Positive Rate

3. **Confusion Matrix**
   - True Positives (attacks detected)
   - True Negatives (normal traffic)
   - False Positives (normal flagged as attack)
   - False Negatives (attacks missed)

4. **Detection Rate by Category**
   - Horizontal bar chart
   - All 9 attack categories
   - Color-coded performance

5. **Detailed Category Table**
   - Detected count
   - Total count
   - Detection rate percentage
   - Status indicator

6. **Recommendations**
   - Auto-generated based on results
   - Specific to identified issues
   - Actionable improvement steps

### Example Recommendations

```html
⚠ High False Positive Rate (68%)
Consider: Adjusting contamination parameter to 0.3-0.4,
establishing better baseline with more normal traffic samples,
or retraining with balanced dataset.

⚠ Poor Detection for: DoS, Reconnaissance, Backdoor
Consider: Enhanced feature engineering for these categories,
training separate specialized models, or collecting more
training samples for underrepresented attacks.
```

### Viewing Reports

Open the HTML file in any web browser:
```powershell
start ml_performance_report.html
```

Or from Python:
```python
import webbrowser
webbrowser.open('ml_performance_report.html')
```

---

## 4. GUI-Integrated Attack Simulations

### Purpose
Run attack simulations directly from the application GUI to test IDS/IPS detection capabilities.

### Location
```
src/gui/ml_anomaly_widget.py (lines 133-708)
```

### How It Works

1. **Button in ML Detection Tab**
   - Orange "🔥 Run Attack Simulations" button
   - Located next to "Train Models" button

2. **Attack Selection Dialog**
   - Checkboxes for each attack type
   - All selected by default
   - Warning about authorized use

3. **Background Execution**
   - Runs in separate thread
   - Doesn't block GUI
   - Real-time log updates

4. **Results Display**
   - Logs appear in Detection Log
   - Alerts appear in Live Alerts table
   - Completion notification

### Available Simulations

| Attack | Duration | Target | Description |
|--------|----------|--------|-------------|
| 🔍 Port Scanning | ~10s | Ports 20-100 | Reconnaissance |
| 💥 DoS Attack | 5s | Port 80 | SYN flood |
| 🔨 Service Fuzzing | ~8s | Port 80 | Malformed data |
| ⚡ Exploitation | ~5s | Port 80 | Exploit attempts |
| 🚪 Backdoor | ~20s | Port 4444 | C&C communication |
| 🌐 Reconnaissance | ~15s | Network | Host discovery |

### Usage from GUI

1. **Start the application**
   ```powershell
   cd src
   python main.py
   ```

2. **Go to ML Detection tab**

3. **Start Monitoring** (required)
   - Click "▶ Start Monitoring"
   - Wait for monitoring to activate

4. **Run Simulations**
   - Click "🔥 Run Attack Simulations"
   - Select desired attack types
   - Click "OK"

5. **Monitor Results**
   - Watch Detection Log for progress
   - Check Live Alerts table for detections
   - Wait for completion dialog

### Example Output

**Detection Log:**
```
==================================================
🔥 STARTING ATTACK SIMULATIONS
==================================================
Selected: portscan, dos, exploit
Target: 127.0.0.1 (localhost)

🔥 Running portscan simulation...
[2025-11-03 20:45:12] PORT_SCAN: Starting port scan: ports 20-100
[2025-11-03 20:45:13] PORT_OPEN: Port 80 is open
✓ portscan complete

🔥 Running dos simulation...
[2025-11-03 20:45:15] DOS_ATTACK: Starting SYN flood for 5 seconds
✓ dos complete

🔥 Running exploit simulation...
[2025-11-03 20:45:21] EXPLOIT: Starting exploitation simulation
✓ exploit complete

✓ Completed 3 attack simulations
⚠️  Check alerts table for detected threats!
```

**Live Alerts Table:**
```
Time           | Severity | Type           | Device IP   | Description
---------------|----------|----------------|-------------|------------------
20:45:13       | HIGH     | Reconnaissance | 127.0.0.1   | Port scanning detected
20:45:16       | CRITICAL | DoS            | 127.0.0.1   | SYN flood attack
20:45:22       | HIGH     | Exploits       | 127.0.0.1   | Exploitation attempt
```

### Safety Features

- **Localhost Only**: All simulations target 127.0.0.1
- **Authorization Warning**: Clear notice before execution
- **User Confirmation**: Must click OK to proceed
- **Supervised Execution**: Runs in controlled environment

### Validation Workflow

1. **Run simulations**
2. **Check detection rate**
3. **Compare against expected rates**
4. **Generate report** (src/ml/generate_report.py)
5. **Analyze false positives/negatives**
6. **Retrain if needed**

---

## Complete Workflow: Improving IDS/IPS Performance

### Step 1: Baseline Assessment

```powershell
# Evaluate current model
python src\ml\evaluate_unswnb15.py --model data\models\unsw_nb15_model

# Generate HTML report
python src\ml\generate_report.py --output baseline_report.html
```

### Step 2: Enhance Features

```powershell
# Reprocess with enhanced features
cd data\datasets
python preprocess_unswnb15.py
```

### Step 3: Tune Hyperparameters

```powershell
# Quick tuning
python src\ml\tune_model.py --quick --output tuning_quick.json

# Or full tuning (overnight)
python src\ml\tune_model.py --output tuning_full.json
```

### Step 4: Retrain with Optimal Parameters

```powershell
# Use recommended parameters from tuning
python src\ml\train_unswnb15.py --epochs 40 --sequence-length 15
```

### Step 5: Validate Improvements

```powershell
# Evaluate new model
python src\ml\evaluate_unswnb15.py --model data\models\unsw_nb15_model

# Generate comparison report
python src\ml\generate_report.py --output improved_report.html
```

### Step 6: Test with Simulations

1. Run application: `python src\main.py`
2. Go to ML Detection tab
3. Start Monitoring
4. Run Attack Simulations
5. Verify improved detection rates

### Step 7: Compare Results

| Metric | Baseline | After Tuning | After Features | Improvement |
|--------|----------|--------------|----------------|-------------|
| Accuracy | 43.7% | 55-65% | 65-75% | +20-30% |
| FPR | 68.0% | 40-50% | 25-35% | -30-45% |
| DoS Detection | 34.9% | 50-60% | 65-75% | +30-40% |
| Recon Detection | 29.4% | 45-55% | 65-75% | +35-45% |

---

## Troubleshooting

### Tuning Takes Too Long

**Solution**: Use `--quick` mode
```powershell
python src\ml\tune_model.py --quick
```

### Out of Memory During Tuning

**Solution**: Reduce sample size in evaluate_config():
```python
sample_size = min(5000, len(self.X_test))  # Reduce from 10000
```

### Features Not Improving Performance

**Possible causes**:
1. Need more training data
2. Need to retrain model
3. Features need adjustment

**Solution**:
```powershell
# Retrain from scratch
python src\ml\train_unswnb15.py --epochs 50
```

### Simulations Not Generating Alerts

**Possible causes**:
1. Monitoring not started
2. Baseline not established
3. Model not trained

**Solution**:
1. Click "Start Monitoring" first
2. Scan network and establish baseline
3. Train model if needed

---

## Performance Benchmarks

### Hardware Requirements

**Minimum**:
- CPU: 4 cores
- RAM: 8GB
- Disk: 5GB free

**Recommended**:
- CPU: 8+ cores
- RAM: 16GB
- Disk: 10GB free (SSD)

### Execution Times

| Task | Quick | Full |
|------|-------|------|
| Preprocessing | 2-3 min | 2-3 min |
| Training (30 epochs) | 5-10 min | 5-10 min |
| Hyperparameter Tuning | 30 min | 8-12 hrs |
| Evaluation | 1-2 min | 1-2 min |
| Report Generation | <10 sec | <10 sec |
| Attack Simulations | 1-2 min | 1-2 min |

---

## References

- **UNSW-NB15 Dataset**: https://research.unsw.edu.au/projects/unsw-nb15-dataset
- **Scikit-learn**: https://scikit-learn.org/stable/
- **TensorFlow**: https://www.tensorflow.org/
- **MITRE ATT&CK**: https://attack.mitre.org/

## Support

For issues or questions:
1. Check this guide
2. Review ML_INSTALLATION.md
3. Check MAIN_WINDOW_ANALYSIS.md
4. Review error logs

---

**Last Updated**: 2025-11-03
**Version**: 1.0
**Compatible With**: OTLAB_DEV v1.0+
