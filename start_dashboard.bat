@echo off
echo ===============================================================================
echo     PROJECT REVIEW 3: INTERACTIVE LIVE DEMONSTRATION LAUNCHER
echo     P8: Managed vs Self-Hosted Cloud Database Services Under Bursty Load
echo     Students: Swayam Pani (23BCE1526) · Anamitra Shrivastava (23BCE5012)
echo     Guide: Dr. Indra Priyadarshini S
echo ===============================================================================
echo.
echo [1/2] Starting Local Interactive Benchmark Server on http://localhost:8000 ...
start /b python web_dashboard\server.py
echo [2/2] Waiting 2 seconds for server initialization...
timeout /t 2 >nul
echo [3/3] Opening Web Browser Dashboard...
start "" http://localhost:8000
echo.
echo Server is running! Press Ctrl+C in this terminal when you want to stop the server.
echo.
pause
