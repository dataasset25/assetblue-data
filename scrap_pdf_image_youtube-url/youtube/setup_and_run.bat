@echo off
echo Setting up YouTube Downloader with Oxylabs Proxy...
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH
    echo Please install Python from https://python.org
    pause
    exit /b 1
)

echo Python found. Installing required packages...
pip install -r requirements.txt

echo.
echo Setup complete!
echo.
echo IMPORTANT: Before running the downloader, please:
echo 1. Edit config.py and add your Oxylabs credentials
echo 2. Make sure you have the correct endpoint from Oxylabs
echo.
echo To run the downloader, use: python youtube_downloader.py
echo.
pause
