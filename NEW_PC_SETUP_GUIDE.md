# Setting Up IDS/IPS on a New PC - Complete Guide

## Problem

After moving the application to a different PC, you're getting reference errors because the required Python packages are not installed on the new machine.

**Missing dependencies:**
- PyQt6 (GUI framework)
- Scapy (packet capture)
- Pandas (data processing)
- NumPy (numerical operations)
- Scikit-learn (machine learning)
- Many others...

---

## Complete Setup Procedure

### Step 1: Install Python 3.10+

**Download and install Python 3.10 or higher:**
- https://www.python.org/downloads/

**During installation:**
- ✅ Check "Add Python to PATH"
- ✅ Check "Install pip"

**Verify installation:**
```powershell
python --version
# Should show: Python 3.10.x or higher
```

---

### Step 2: Install Npcap (Windows Packet Capture Driver)

**CRITICAL:** Required for packet capture to work!

**Download and install Npcap:**
1. Go to: https://npcap.com/#download
2. Download Npcap installer
3. Run installer **as Administrator**
4. ✅ Check "Install Npcap in WinPcap API-compatible Mode"
5. Complete installation
6. **Restart your computer**

**Verify installation:**
```powershell
Get-Service npcap
# Should show: Status = Running
```

---

### Step 3: Copy Project Files

**Option A: Use Git (Recommended)**

```powershell
# Open PowerShell
cd C:\Users\<YourUsername>\PycharmProjects

# Clone the repository
git clone <repository_url> IDS-IPS_AD

# Or if you already have it, pull latest:
cd IDS-IPS_AD
git pull origin claude/copy-dataset-to-repo-011CUptrG3Jgh2HjCHzGa8YY
```

**Option B: Manual Copy**

1. Copy entire `IDS-IPS_AD` folder from old PC to new PC
2. Place in: `C:\Users\<YourUsername>\PycharmProjects\IDS-IPS_AD`

---

### Step 4: Create Virtual Environment

```powershell
# Navigate to project folder
cd C:\Users\<YourUsername>\PycharmProjects\IDS-IPS_AD

# Create virtual environment
python -m venv .venv

# Activate virtual environment
.venv\Scripts\activate

# You should see (.venv) at start of prompt
```

---

### Step 5: Install All Dependencies

**Install from requirements file:**

```powershell
# Make sure virtual environment is activated (.venv)
pip install --upgrade pip

# Install all required packages
pip install PyQt6 scapy pandas numpy scikit-learn joblib

# Additional packages
pip install pyqtgraph matplotlib requests psutil

# If you have requirements.txt:
pip install -r requirements.txt
```

**Manual installation if needed:**
```powershell
pip install PyQt6==6.5.0
pip install scapy==2.5.0
pip install pandas==2.0.3
pip install numpy==1.24.3
pip install scikit-learn==1.3.0
pip install joblib==1.3.2
```

**Verify installations:**
```powershell
python -c "import PyQt6; print('PyQt6: OK')"
python -c "import scapy; print('Scapy: OK')"
python -c "import pandas; print('Pandas: OK')"
python -c "import sklearn; print('Scikit-learn: OK')"
```

All should print "OK" with no errors.

---

### Step 6: Verify ML Model Files Exist

**Check if model files are present:**

```powershell
# Navigate to project folder
cd C:\Users\<YourUsername>\PycharmProjects\IDS-IPS_AD

# Check for model files
dir models\
```

**Should see:**
- `improved_ml_detector.joblib` (the trained model)
- `improved_ml_detector_metadata.json` (model metadata)
- `improved_ml_detector_scaler.joblib` (feature scaler)

**If missing, copy from old PC or retrain:**
```powershell
# Option 1: Copy from old PC
# Copy entire "models" folder from old PC to new PC

# Option 2: Retrain the model (takes 5-10 minutes)
python train_improved.py
```

---

### Step 7: Verify Dataset Files (Optional)

**If you need to retrain the model, check for dataset:**

```powershell
dir data\datasets\
```

**Should see:**
- `unsw-nb15_train.csv`
- `unsw-nb15_test.csv`

**If missing, copy from old PC.**

---

### Step 8: Run the Application

**Run as Administrator (REQUIRED for packet capture):**

```powershell
# Right-click PowerShell → "Run as Administrator"
cd C:\Users\<YourUsername>\PycharmProjects\IDS-IPS_AD

# Activate virtual environment
.venv\Scripts\activate

# Run the application
python src/main.py
```

**Expected startup messages:**
```
INFO:scanner.network_monitor:✓ Improved ML detector enabled (Accuracy: 90.6%)
INFO:scanner.network_monitor:✓ Alert rules engine integrated with ML detector
INFO:scanner.network_monitor:NetworkMonitor initialized
```

**If you see errors, note them and check troubleshooting section below.**

---

### Step 9: Test Network Monitor

1. **Click " Network Monitor" tab**
2. **Click "🚨 Start Detection Mode"**
3. **Watch for status:** "🟢 DETECTION"
4. **Check console for:**
   ```
   INFO:scanner.network_monitor:Starting network monitor (learning_mode=False)
   INFO:scanner.secure_packet_capture:Packet capture started
   ```

---

### Step 10: Test Detection

**From a DIFFERENT PC on the network:**

```bash
# Ping test
ping <NEW_PC_IP> -t

# Port scan test
cd threat_simulations/
# Edit scripts: Set TARGET_IP to your new PC's IP
python threat_simulation_1_port_scan.py
```

**Expected on IDS/IPS PC:**
- Packets count increasing
- Devices appearing
- Threat detections for port scan

---

## Quick Setup Script

**Save this as `setup_new_pc.ps1` and run as Administrator:**

```powershell
# Setup IDS/IPS on New PC
Write-Host "=== IDS/IPS Setup Script ===" -ForegroundColor Cyan

# Check Python
Write-Host "`nChecking Python..." -ForegroundColor Yellow
python --version
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Python not found! Install Python 3.10+ first." -ForegroundColor Red
    exit 1
}

# Check Npcap
Write-Host "`nChecking Npcap..." -ForegroundColor Yellow
$npcap = Get-Service npcap -ErrorAction SilentlyContinue
if (-not $npcap) {
    Write-Host "ERROR: Npcap not installed! Download from: https://npcap.com/" -ForegroundColor Red
    exit 1
}
Write-Host "Npcap Status: $($npcap.Status)" -ForegroundColor Green

# Create virtual environment
Write-Host "`nCreating virtual environment..." -ForegroundColor Yellow
python -m venv .venv

# Activate and install
Write-Host "`nActivating virtual environment..." -ForegroundColor Yellow
& .\.venv\Scripts\Activate.ps1

Write-Host "`nUpgrading pip..." -ForegroundColor Yellow
python -m pip install --upgrade pip

Write-Host "`nInstalling dependencies..." -ForegroundColor Yellow
pip install PyQt6 scapy pandas numpy scikit-learn joblib pyqtgraph matplotlib requests psutil

# Verify installations
Write-Host "`nVerifying installations..." -ForegroundColor Yellow
python -c "import PyQt6; import scapy; import pandas; import sklearn; print('All packages installed successfully!')"

Write-Host "`n=== Setup Complete! ===" -ForegroundColor Green
Write-Host "`nTo run the application:" -ForegroundColor Cyan
Write-Host "  1. Right-click PowerShell -> Run as Administrator" -ForegroundColor White
Write-Host "  2. cd to project folder" -ForegroundColor White
Write-Host "  3. .venv\Scripts\activate" -ForegroundColor White
Write-Host "  4. python src\main.py" -ForegroundColor White
```

**Run it:**
```powershell
# As Administrator
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\setup_new_pc.ps1
```

---

## Troubleshooting Common Issues

### Issue 1: "No module named 'PyQt6'"

**Solution:**
```powershell
# Make sure virtual environment is activated
.venv\Scripts\activate

# Install PyQt6
pip install PyQt6
```

### Issue 2: "No module named 'scapy'"

**Solution:**
```powershell
pip install scapy

# Also make sure Npcap is installed!
Get-Service npcap
```

### Issue 3: "No module named 'pandas'" or "numpy" or "sklearn"

**Solution:**
```powershell
pip install pandas numpy scikit-learn
```

### Issue 4: "Permission denied" / "Access denied"

**Solution:**
- Close application
- Right-click PowerShell → "Run as Administrator"
- Run application again

### Issue 5: Model file not found

**Error:**
```
FileNotFoundError: [Errno 2] No such file or directory: 'models/improved_ml_detector.joblib'
```

**Solution:**

**Option A - Copy from old PC:**
```powershell
# Copy entire "models" folder from old PC to new PC
# Place in: IDS-IPS_AD\models\
```

**Option B - Retrain model:**
```powershell
# Make sure dataset files exist first
dir data\datasets\

# Train model (takes 5-10 minutes)
python train_improved.py
```

### Issue 6: Npcap not working

**Symptoms:**
- Packet capture fails
- "Scapy error" in console
- No packets captured

**Solution:**
1. Reinstall Npcap from https://npcap.com/
2. During install, check "WinPcap API-compatible Mode"
3. Restart computer
4. Verify service: `Get-Service npcap` shows "Running"

---

## Dependency Checklist

Before running the application, verify ALL of these are installed:

**System Requirements:**
- [ ] Python 3.10 or higher
- [ ] Npcap (Windows) - service running
- [ ] Administrator privileges

**Python Packages:**
- [ ] PyQt6 (GUI framework)
- [ ] scapy (packet capture)
- [ ] pandas (data processing)
- [ ] numpy (numerical operations)
- [ ] scikit-learn (machine learning)
- [ ] joblib (model serialization)

**Optional but Recommended:**
- [ ] pyqtgraph (graphing)
- [ ] matplotlib (plotting)
- [ ] requests (HTTP)
- [ ] psutil (system info)

**Project Files:**
- [ ] Virtual environment (.venv folder)
- [ ] Model files (models/ folder)
- [ ] Dataset files (data/datasets/ - only if retraining)
- [ ] Source code (src/ folder)

---

## Complete Requirements.txt

**Create this file in project root: `requirements.txt`**

```txt
PyQt6==6.5.0
scapy==2.5.0
pandas==2.0.3
numpy==1.24.3
scikit-learn==1.3.0
joblib==1.3.2
pyqtgraph==0.13.3
matplotlib==3.7.2
requests==2.31.0
psutil==5.9.5
```

**Install all at once:**
```powershell
pip install -r requirements.txt
```

---

## Quick Verification Commands

**After setup, run these to verify everything:**

```powershell
# Test imports
python -c "
import sys
print('Python version:', sys.version)

import PyQt6
print('PyQt6: OK')

import scapy
print('Scapy: OK')

import pandas
print('Pandas: OK')

import numpy
print('NumPy: OK')

import sklearn
print('Scikit-learn: OK')

import joblib
print('Joblib: OK')

print('\n✅ All dependencies installed successfully!')
"

# Test model loading
python -c "
import joblib
model = joblib.load('models/improved_ml_detector.joblib')
print('✅ ML model loaded successfully!')
"

# Test Npcap
Get-Service npcap
```

**All should complete without errors!**

---

## Summary

**Moving to new PC requires:**
1. ✅ Install Python 3.10+
2. ✅ Install Npcap
3. ✅ Copy project files
4. ✅ Create virtual environment
5. ✅ Install ALL dependencies (pip install)
6. ✅ Copy or retrain ML model
7. ✅ Run as Administrator
8. ✅ Test with Network Monitor

**Common mistake:** Forgetting to install dependencies on the new PC!

**Quick setup:**
```powershell
# As Administrator
python -m venv .venv
.venv\Scripts\activate
pip install PyQt6 scapy pandas numpy scikit-learn joblib
python src/main.py
```

The reference errors will disappear once all dependencies are properly installed! 🎯
