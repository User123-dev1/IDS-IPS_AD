# ============================================================================
# IDS/IPS Application Launcher
# Run this script as Administrator to start the application
# ============================================================================

Write-Host "=== IDS/IPS Application Launcher ===" -ForegroundColor Cyan
Write-Host ""

# Check if running as Administrator
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Host "ERROR: This script must be run as Administrator!" -ForegroundColor Red
    Write-Host ""
    Write-Host "To fix:" -ForegroundColor Yellow
    Write-Host "  1. Right-click PowerShell" -ForegroundColor White
    Write-Host "  2. Select 'Run as Administrator'" -ForegroundColor White
    Write-Host "  3. Navigate to this folder" -ForegroundColor White
    Write-Host "  4. Run this script again" -ForegroundColor White
    Write-Host ""
    pause
    exit 1
}

Write-Host "✓ Running as Administrator" -ForegroundColor Green

# Check Python
Write-Host ""
Write-Host "Checking Python..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✓ $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "ERROR: Python not found!" -ForegroundColor Red
    Write-Host "Install Python 3.10+ from: https://www.python.org/downloads/" -ForegroundColor Yellow
    pause
    exit 1
}

# Check Npcap
Write-Host ""
Write-Host "Checking Npcap..." -ForegroundColor Yellow
$npcap = Get-Service npcap -ErrorAction SilentlyContinue
if ($npcap) {
    Write-Host "✓ Npcap Status: $($npcap.Status)" -ForegroundColor Green
    if ($npcap.Status -ne "Running") {
        Write-Host "  Starting Npcap service..." -ForegroundColor Yellow
        Start-Service npcap
    }
} else {
    Write-Host "WARNING: Npcap not installed!" -ForegroundColor Yellow
    Write-Host "  Packet capture may not work." -ForegroundColor Yellow
    Write-Host "  Download from: https://npcap.com/" -ForegroundColor Cyan
}

# Check virtual environment
Write-Host ""
Write-Host "Checking virtual environment..." -ForegroundColor Yellow
if (Test-Path ".venv\Scripts\python.exe") {
    Write-Host "✓ Virtual environment found" -ForegroundColor Green
} else {
    Write-Host "WARNING: Virtual environment not found!" -ForegroundColor Yellow
    Write-Host "  Creating virtual environment..." -ForegroundColor Cyan
    python -m venv .venv
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ Virtual environment created" -ForegroundColor Green
    } else {
        Write-Host "ERROR: Failed to create virtual environment!" -ForegroundColor Red
        pause
        exit 1
    }
}

# Activate virtual environment
Write-Host ""
Write-Host "Activating virtual environment..." -ForegroundColor Yellow
& .\.venv\Scripts\Activate.ps1

# Check dependencies
Write-Host ""
Write-Host "Checking dependencies..." -ForegroundColor Yellow
$missingPackages = @()

$requiredPackages = @("PyQt6", "scapy", "pandas", "numpy", "sklearn", "joblib")
foreach ($package in $requiredPackages) {
    python -c "import $package" 2>$null
    if ($LASTEXITCODE -ne 0) {
        $missingPackages += $package
    } else {
        Write-Host "  ✓ $package" -ForegroundColor Green
    }
}

if ($missingPackages.Count -gt 0) {
    Write-Host ""
    Write-Host "Missing packages detected!" -ForegroundColor Yellow
    Write-Host "Installing: $($missingPackages -join ', ')" -ForegroundColor Cyan
    Write-Host ""

    pip install --quiet --upgrade pip
    pip install PyQt6 scapy pandas numpy scikit-learn joblib matplotlib pyqtgraph requests psutil

    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ All dependencies installed" -ForegroundColor Green
    } else {
        Write-Host "ERROR: Failed to install dependencies!" -ForegroundColor Red
        pause
        exit 1
    }
}

# Check ML model
Write-Host ""
Write-Host "Checking ML model..." -ForegroundColor Yellow
if (Test-Path "models\improved_ml_detector.joblib") {
    Write-Host "✓ ML model found" -ForegroundColor Green
} else {
    Write-Host "WARNING: ML model not found!" -ForegroundColor Yellow
    Write-Host "  ML detection will not work without the model." -ForegroundColor Yellow
    Write-Host "  Train model with: python train_improved.py" -ForegroundColor Cyan
}

# All checks passed
Write-Host ""
Write-Host "=== All checks passed! ===" -ForegroundColor Green
Write-Host ""
Write-Host "Starting IDS/IPS Application..." -ForegroundColor Cyan
Write-Host ""

# Run the application
python src\main.py

# If we get here, application exited
Write-Host ""
Write-Host "Application closed." -ForegroundColor Yellow
pause
