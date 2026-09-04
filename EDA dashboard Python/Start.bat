@echo off
cd /d "%~dp0"
echo ========================================
echo   EDA Dashboard Launcher
echo ========================================
echo.
echo Starting dashboard...
echo.
echo The dashboard will open in your default browser.
echo Press Ctrl+C to stop the server when done.
echo.
python -m streamlit run dashboard.py
pause
