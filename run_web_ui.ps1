#!/usr/bin/env pwsh
# Run the G1 Web UI Server on Windows using PowerShell
# This is an alternative to run_web_ui.bat with better error handling

param(
    [int]$Port = 8000,
    [string]$LogLevel = "info"
)

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "G1 Web UI Server - Windows (PowerShell)" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# Check if Python is available
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✓ Found Python: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "✗ Python not found in PATH" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please install Python 3.8+ from: https://www.python.org/downloads/" -ForegroundColor Yellow
    Write-Host "Make sure to check 'Add Python to PATH' during installation" -ForegroundColor Yellow
    exit 1
}

# Check if required packages are installed
Write-Host ""
Write-Host "Checking dependencies..." -ForegroundColor Cyan

$packages = @("fastapi", "uvicorn", "websockets")
$missing = @()

foreach ($package in $packages) {
    try {
        python -c "import $package" 2>$null
        Write-Host "✓ $package installed" -ForegroundColor Green
    } catch {
        Write-Host "✗ $package not found" -ForegroundColor Yellow
        $missing += $package
    }
}

# Install missing packages
if ($missing.Count -gt 0) {
    Write-Host ""
    Write-Host "Installing missing packages: $($missing -join ', ')" -ForegroundColor Yellow
    
    try {
        pip install -q @missing
        Write-Host "✓ Dependencies installed successfully" -ForegroundColor Green
    } catch {
        Write-Host "✗ Failed to install dependencies" -ForegroundColor Red
        Write-Host "Try running: pip install fastapi uvicorn websockets" -ForegroundColor Yellow
        exit 1
    }
}

# Start the server
Write-Host ""
Write-Host "Starting G1 Web UI Server..." -ForegroundColor Green
Write-Host ""
Write-Host "Web UI URL: http://localhost:$Port" -ForegroundColor Cyan
Write-Host "Network Access: http://<your-pc-ip>:$Port" -ForegroundColor Cyan
Write-Host ""
Write-Host "To stop the server, press Ctrl+C" -ForegroundColor Yellow
Write-Host ""

# Run the server
python -m g1_app.ui.web_server --port $Port --log-level $LogLevel

Write-Host ""
Write-Host "Server stopped" -ForegroundColor Yellow
