@echo off
REM Simple server startup script for G1 Web Controller
REM Double-click this file to start the server

echo.
echo ================================================
echo   G1 Robot Web Controller - Starting Server
echo ================================================
echo.

cd /d %~dp0

REM Activate virtual environment
call .venv\Scripts\activate.bat

REM Set UTF-8 encoding for emoji support
set PYTHONIOENCODING=utf-8

REM Start server
echo Starting web server on http://127.0.0.1:8001
echo.
echo Press Ctrl+C to stop the server
echo.

python -m uvicorn g1_app.ui.web_server:app --host 127.0.0.1 --port 8001 --reload

pause
