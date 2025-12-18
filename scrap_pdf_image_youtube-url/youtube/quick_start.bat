@echo off
echo YouTube Downloader with Oxylabs Proxy - Quick Start
echo ==================================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH
    echo Please install Python from https://python.org
    pause
    exit /b 1
)

echo Step 1: Installing required packages...
pip install -r requirements.txt
echo.

echo Step 2: Testing setup...
python test_setup.py
echo.

echo Step 3: If tests passed, you can now run the downloader:
echo    python youtube_downloader.py
echo.

echo IMPORTANT: Make sure to edit config.py with your Oxylabs credentials first!
echo.

pause
