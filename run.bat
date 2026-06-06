@echo off
cd /d "%~dp0"
echo ====================================
echo   TriLingua Bridge - PWA Launcher
echo ====================================
echo.

call .venv\Scripts\activate.bat 2>nul
if errorlevel 1 (
    echo [INFO] No virtual env found, using system Python
)

python run.py %*
if errorlevel 1 (
    echo.
    echo [ERROR] Failed to start. Ensure dependencies are installed:
    echo   pip install -r requirements.txt
    pause
)
