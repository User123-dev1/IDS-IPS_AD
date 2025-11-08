@echo off
REM ============================================================================
REM IDS/IPS Application - Quick Launcher
REM Double-click this file to run the application
REM ============================================================================

echo.
echo ============================================
echo    IDS/IPS Application Launcher
echo ============================================
echo.

REM Check for Administrator privileges
net session >nul 2>&1
if %errorLevel% == 0 (
    echo [OK] Running as Administrator
    echo.

    REM Run the PowerShell script
    powershell.exe -ExecutionPolicy Bypass -File "%~dp0run_app.ps1"

) else (
    echo [ERROR] This application requires Administrator privileges!
    echo.
    echo To fix:
    echo   1. Right-click this file (RUN_AS_ADMIN.bat)
    echo   2. Select "Run as administrator"
    echo.
    pause
    exit /b 1
)
