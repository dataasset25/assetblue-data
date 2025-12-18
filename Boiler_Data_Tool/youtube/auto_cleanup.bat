@echo off
echo Starting Automatic Cleanup Monitor...
echo This will automatically remove .part files when downloads complete
echo Press Ctrl+C to stop the monitor
echo.

python auto_cleanup.py --monitor

pause
