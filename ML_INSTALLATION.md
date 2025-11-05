# ML System Installation Guide

This guide will help you install the required dependencies for the ML-based IDS/IPS system.

## 🪟 Windows Users - Important Notes

**Use `python` instead of `python3`:**
```powershell
# On Windows, use:
python -m pip install -r requirements.txt

# NOT python3 (unless you specifically installed Python 3 with that command)
```

**If you see "Python was not found":**
1. Install Python from [python.org](https://www.python.org/downloads/)
2. During installation, CHECK "Add Python to PATH"
3. Restart PowerShell/Command Prompt after installation

**PyQt6-tools error is normal and can be ignored** - it's optional (only for Qt Designer)

## Error: "ML Security System is not available"

If you see this error when trying to establish a security baseline, it means the required ML dependencies are not installed.

## Quick Fix

**Windows:**
```powershell
python -m pip install -r requirements.txt
```

**Linux/Mac:**
```bash
pip install -r requirements.txt
```

Or install ML dependencies specifically:

**Windows:**
```powershell
python -m pip install numpy pandas scikit-learn tensorflow xgboost
```

**Linux/Mac:**
```bash
pip install numpy pandas scikit-learn tensorflow xgboost
```

## Step-by-Step Installation

### 1. Basic ML Dependencies (Required)

```bash
# Core data processing
pip install numpy>=1.24.0
pip install pandas>=2.0.0

# Machine learning framework
pip install scikit-learn>=1.3.0
```

### 2. Deep Learning Dependencies (Required for LSTM models)

```bash
# TensorFlow for deep learning models
pip install tensorflow>=2.13.0
```

**Note**: TensorFlow installation may take several minutes and requires ~500MB of disk space.

### 3. Advanced ML Dependencies (Optional but Recommended)

```bash
# XGBoost for advanced classification
pip install xgboost>=1.7.0
```

### 4. Verify Installation

Test if the ML system is available:

**Windows:**
```powershell
python -c "import sys; sys.path.insert(0, 'src'); from ml.models.hybrid_security_models import HybridSecuritySystem; print('ML System is ready!')"
```

**Linux/Mac:**
```bash
python3 -c "
import sys
sys.path.insert(0, 'src')
from ml.models.hybrid_security_models import HybridSecuritySystem
print('✓ ML System is ready!')
"
```

If you see "✓ ML System is ready!" then installation was successful.

## System Requirements

### Minimum Requirements
- Python 3.8 or higher
- 4GB RAM
- 2GB free disk space

### Recommended Requirements
- Python 3.10 or higher
- 8GB RAM
- 5GB free disk space
- CUDA-capable GPU (optional, for faster training)

## GPU Acceleration (Optional)

For faster ML training, you can install TensorFlow with GPU support:

```bash
# NVIDIA GPU with CUDA support
pip install tensorflow[and-cuda]
```

**Requirements**:
- NVIDIA GPU with CUDA Compute Capability 3.5+
- CUDA Toolkit 11.8 or higher
- cuDNN 8.6 or higher

## Troubleshooting

### Issue: "No module named 'numpy'"

**Solution**: Install numpy
```bash
pip install numpy
```

### Issue: "No module named 'sklearn'"

**Solution**: Install scikit-learn (note: package name is scikit-learn, import name is sklearn)
```bash
pip install scikit-learn
```

### Issue: "No module named 'tensorflow'"

**Solution**: Install TensorFlow
```bash
pip install tensorflow
```

### Issue: TensorFlow installation fails

**Solution 1**: Try installing an older stable version
```bash
pip install tensorflow==2.13.0
```

**Solution 2**: On some systems, you may need to install dependencies first
```bash
pip install --upgrade pip setuptools wheel
pip install tensorflow
```

### Issue: "Could not load dynamic library 'cudart64'"

This is a warning (not an error) when TensorFlow tries to use GPU but CUDA is not installed. The system will automatically fall back to CPU mode. You can safely ignore this warning.

### Issue: Memory errors during training

**Solution**: Reduce batch size in training scripts
- Edit `src/ml/train_unswnb15.py`
- Change `batch_size=32` to `batch_size=16` or `batch_size=8`

## Virtual Environment (Recommended)

It's recommended to use a virtual environment:

```bash
# Create virtual environment
python3 -m venv venv

# Activate (Linux/Mac)
source venv/bin/activate

# Activate (Windows)
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Docker Installation (Alternative)

If you prefer using Docker:

```bash
# Build the container
docker build -t otlab-ml .

# Run the application
docker run -p 8000:8000 otlab-ml
```

## Verify ML System After Installation

1. Start the application
2. Go to the **OT Security Scanner** tab
3. Click **Start Scan** to discover network devices
4. After scan completes, click **Establish Security Baseline**
5. If you see a success message, the ML system is working correctly!

## Expected Behavior

After successful installation:

✅ **ML Detection tab** - Shows real-time monitoring controls
✅ **ML Performance tab** - Displays model metrics and performance
✅ **Establish Baseline** - Creates security baseline from scanned devices
✅ **Anomaly Detection** - Detects unusual network behavior
✅ **Threat Classification** - Identifies attack types

## Getting Help

If you continue to experience issues:

1. Check Python version: `python3 --version` (should be 3.8+)
2. Check pip version: `pip --version`
3. Verify installation: Run the verification script above
4. Check logs for detailed error messages

## Performance Notes

- **First run**: May be slower as TensorFlow initializes
- **Training**: Takes 5-15 minutes on UNSW-NB15 dataset (82K records)
- **Inference**: Real-time detection takes <100ms per device
- **Memory usage**: ~2GB during training, ~500MB during monitoring

## Next Steps

After successful installation:

1. Review [QUICKSTART.md](data/datasets/QUICKSTART.md) for dataset setup
2. Read [ML_PERFORMANCE_REPORT.md](ML_PERFORMANCE_REPORT.md) for model details
3. Check [MAIN_WINDOW_ANALYSIS.md](MAIN_WINDOW_ANALYSIS.md) for workflow guide
