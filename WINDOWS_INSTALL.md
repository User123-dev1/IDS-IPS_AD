# Windows Installation Guide

Quick guide for installing and running the OT/ICS Security System on Windows.

## Prerequisites

### 1. Install Python

1. Download Python from [python.org](https://www.python.org/downloads/)
2. **IMPORTANT**: During installation, CHECK the box "Add Python to PATH"
3. Click "Install Now"
4. Restart PowerShell/Command Prompt

### 2. Verify Python Installation

Open PowerShell and run:
```powershell
python --version
```

Should show: `Python 3.8.x` or higher

## Installation Steps

### Step 1: Navigate to Project Directory

```powershell
cd C:\Users\otlaptop\PycharmProjects\OTLAB_DEV
```

### Step 2: Install Dependencies

**Option A: Install ALL dependencies (Recommended)**
```powershell
python -m pip install -r requirements.txt
```

**Option B: Install ONLY ML dependencies (Minimal)**
```powershell
python -m pip install numpy pandas scikit-learn tensorflow xgboost PyQt6
```

### Step 3: Handle Common Errors

#### Error: "PyQt6-tools dependency not found"

**This is NORMAL and can be IGNORED!**

PyQt6-tools is optional (only for Qt Designer). The application will work fine without it.

#### Error: "Python was not found"

**Solution:**
1. Close PowerShell
2. Reinstall Python from [python.org](https://www.python.org/downloads/)
3. **CHECK "Add Python to PATH"** during installation
4. Restart PowerShell

#### Error: "pip is not recognized"

**Solution:**
```powershell
python -m ensurepip --upgrade
python -m pip install --upgrade pip
```

### Step 4: Verify ML System Installation

```powershell
python -c "import sys; sys.path.insert(0, 'src'); from ml.models.hybrid_security_models import HybridSecuritySystem; print('ML System is ready!')"
```

**Expected Output:** `ML System is ready!`

**If you see errors:**
- Missing numpy: `python -m pip install numpy`
- Missing sklearn: `python -m pip install scikit-learn`
- Missing tensorflow: `python -m pip install tensorflow`

## Running the Application

### Start the Application

```powershell
cd src
python main.py
```

**Note:** Some network features may require Administrator privileges.

### Run as Administrator (if needed)

1. Right-click PowerShell
2. Select "Run as Administrator"
3. Navigate to project directory
4. Run: `python src/main.py`

## First Time Setup

### 1. Install ML Dependencies
```powershell
python -m pip install numpy pandas scikit-learn tensorflow xgboost
```

### 2. Verify Installation
```powershell
python -c "import numpy; import pandas; import sklearn; import tensorflow; print('All ML libraries installed!')"
```

### 3. Run Application
```powershell
cd src
python main.py
```

### 4. Test ML System

1. Go to **OT Security Scanner** tab
2. Click **Start Scan**
3. After scan completes, click **Establish Security Baseline**
4. Should see: "Network baseline established" (no errors!)

## Troubleshooting

### Issue: "ML Security System is not available"

**Cause:** ML dependencies not installed

**Solution:**
```powershell
python -m pip install numpy pandas scikit-learn tensorflow xgboost
```

Then restart the application.

### Issue: TensorFlow installation is very slow

**This is normal!** TensorFlow is ~500MB and may take 5-15 minutes to download and install.

**Alternative:** Install TensorFlow separately with progress indicator:
```powershell
python -m pip install tensorflow --verbose
```

### Issue: "No module named 'PyQt6'"

**Solution:**
```powershell
python -m pip install PyQt6
```

### Issue: Out of memory during pip install

**Solution:** Install packages one at a time:
```powershell
python -m pip install numpy
python -m pip install pandas
python -m pip install scikit-learn
python -m pip install PyQt6
python -m pip install tensorflow
python -m pip install xgboost
```

### Issue: SSL Certificate errors

**Solution:**
```powershell
python -m pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org numpy pandas scikit-learn tensorflow
```

## Upgrade pip (Optional)

If you see "A new release of pip is available":

```powershell
python -m pip install --upgrade pip
```

## Virtual Environment (Recommended)

Using a virtual environment keeps dependencies isolated:

### Create Virtual Environment
```powershell
python -m venv venv
```

### Activate Virtual Environment
```powershell
.\venv\Scripts\Activate.ps1
```

**If you see "execution of scripts is disabled":**
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
.\venv\Scripts\Activate.ps1
```

### Install Dependencies in Virtual Environment
```powershell
python -m pip install -r requirements.txt
```

### Deactivate Virtual Environment
```powershell
deactivate
```

## Quick Command Reference

| Task | Command |
|------|---------|
| Install dependencies | `python -m pip install -r requirements.txt` |
| Install single package | `python -m pip install package_name` |
| Check Python version | `python --version` |
| Check pip version | `python -m pip --version` |
| Upgrade pip | `python -m pip install --upgrade pip` |
| Run application | `cd src && python main.py` |
| Verify ML system | `python -c "import sklearn; import tensorflow; print('OK')"` |

## System Requirements (Windows)

### Minimum
- Windows 10 or higher
- Python 3.8+
- 4GB RAM
- 2GB free disk space

### Recommended
- Windows 11
- Python 3.10+
- 8GB RAM
- 5GB free disk space
- SSD storage

## Next Steps

After successful installation:

1. ✅ ML dependencies installed
2. ✅ Application runs without errors
3. ✅ Read [ML_INSTALLATION.md](ML_INSTALLATION.md) for detailed ML setup
4. ✅ Read [README.md](README.md) for feature overview
5. ✅ Start scanning your network!

## Getting Help

If you continue to have issues:

1. Make sure Python is in PATH: `python --version`
2. Make sure pip works: `python -m pip --version`
3. Try installing dependencies one at a time
4. Check you're in the correct directory: `C:\Users\otlaptop\PycharmProjects\OTLAB_DEV`
5. Try running PowerShell as Administrator

## Common Windows-Specific Notes

- Use `python` not `python3`
- Use `\` for paths not `/`
- Use PowerShell (not CMD) for best compatibility
- Some features may require Administrator privileges
- Antivirus may flag network scanning tools - add exception if needed
