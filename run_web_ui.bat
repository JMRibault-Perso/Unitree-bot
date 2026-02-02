@echo off
REM Run the G1 Web UI Server on Windows
REM This is the Windows equivalent of run_web_ui.sh

setlocal enabledelayedexpansion

REM Get the directory where this script is located
set SCRIPT_DIR=%~dp0

REM Navigate to script directory
cd /d "%SCRIPT_DIR%"

echo.
echo ============================================================
echo G1 Web UI Server - Windows
echo ============================================================
echo.

REM Install dependencies if needed
echo Installing dependencies (if needed)...
pip install -q fastapi uvicorn websockets 2>nul || echo Warning: Could not auto-install dependencies

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo ERROR: Python not found in PATH
    echo Please install Python 3.8+ and add it to your PATH
    echo See: https://www.python.org/downloads/
    pause
    exit /b 1
)

REM Run the server
echo.
echo Starting G1 Web UI Server...
echo.
echo Open your browser to: http://localhost:8000
echo.
echo Press Ctrl+C to stop the server
echo.

python -m g1_app.ui.web_server

pause
