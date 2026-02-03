@echo off
REM Quick Start - G1 Robot Controller for Windows
REM Just double-click this file to start!

echo.
echo ============================================
echo   G1 Robot Controller - Quick Start
echo ============================================
echo.
echo Starting web server...
echo.

REM Start the server in the background
start "G1 Web Server" /MIN .venv\Scripts\python.exe -m g1_app.ui.web_server

REM Wait for server to start
echo Waiting for server to start...
timeout /t 3 /nobreak >nul

REM Open browser
echo Opening browser to http://localhost:3000
start http://localhost:3000

echo.
echo ============================================
echo Server is running in a separate window
echo.
echo To stop the server:
echo   1. Find the "G1 Web Server" window
echo   2. Press Ctrl+C
echo   3. Or close the window
echo ============================================
echo.

pause

pause
