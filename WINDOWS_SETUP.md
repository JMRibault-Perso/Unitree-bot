# G1 Web UI Server - Windows Setup Guide

## System Requirements

- **Windows 10/11** (64-bit recommended)
- **Python 3.8+** (3.10+ recommended)
- **Network connection** to G1 robot on same WiFi

## Installation

### 1. Install Python

1. Download Python from [python.org](https://www.python.org/downloads/)
2. Run the installer and **check "Add Python to PATH"** during installation
3. Verify installation:
   ```cmd
   python --version
   ```

### 2. Install Dependencies

Open Command Prompt in the project directory and run:

```cmd
pip install fastapi uvicorn websockets
```

Optional (for full functionality):
```cmd
pip install aiohttp pydantic
```

### 3. Verify Installation

```cmd
python -c "import fastapi; print('FastAPI OK')"
python -c "import uvicorn; print('Uvicorn OK')"
```

## Running the Web UI

### Method 1: Batch File (Easiest)

Double-click `run_web_ui.bat` in the project folder.

The server will start and open instructions in Command Prompt:
```
Starting G1 Web UI Server...

Open your browser to: http://localhost:8000

Press Ctrl+C to stop the server
```

### Method 2: Command Prompt

1. Open Command Prompt (`Win+R` → type `cmd` → press Enter)
2. Navigate to the project folder:
   ```cmd
   cd C:\path\to\Unitree-bot
   ```
3. Start the server:
   ```cmd
   python -m g1_app.ui.web_server
   ```

### Method 3: PowerShell

1. Open PowerShell
2. Navigate to project folder:
   ```powershell
   cd C:\path\to\Unitree-bot
   ```
3. Start the server:
   ```powershell
   python -m g1_app.ui.web_server
   ```

## Accessing the Web UI

Once the server is running:

1. **Local Access**: Open browser to `http://localhost:8000`
2. **Network Access**: From another computer on same WiFi:
   ```
   http://<your-pc-ip>:8000
   ```
   
   To find your PC's IP:
   - Command Prompt: `ipconfig`
   - Look for "IPv4 Address" (usually starts with 192.168.x.x)

## Connecting to Robot

1. Open web browser to `http://localhost:8000`
2. Enter robot details:
   - **IP Address**: Find in Unitree app or router (e.g., 192.168.86.3)
   - **Serial Number**: From robot label or Unitree app (e.g., E21D1000PAHBMB06)
3. Click **Connect**
4. Wait for "Successfully connected" message

## Troubleshooting

### Port 8000 Already in Use

If you get "Address already in use" error:

**Option 1**: Kill the existing process (PowerShell):
```powershell
Get-Process | Where-Object {$_.ProcessName -eq "python"} | Stop-Process -Force
```

**Option 2**: Use a different port. Edit `run_web_ui.bat`:
```batch
python -m g1_app.ui.web_server --port 8001
```

### Cannot Connect to Robot

1. Verify robot is on same WiFi network
2. Try pinging robot from Command Prompt:
   ```cmd
   ping 192.168.86.3
   ```
   (Replace with your robot's IP)
3. Check if robot is powered on
4. Restart robot and try again

### Python Not Found

If you get "python is not recognized":

1. Verify Python is installed: Check Programs and Features in Windows
2. Add Python to PATH:
   - Right-click "This PC" → Properties
   - Click "Advanced system settings"
   - Click "Environment Variables"
   - Under "User variables", click "New"
   - Variable name: `PATH`
   - Variable value: `C:\Users\[YourUsername]\AppData\Local\Programs\Python\Python311\` (adjust version)
   - Click OK and restart Command Prompt

### Dependencies Installation Fails

Try upgrading pip first:
```cmd
python -m pip install --upgrade pip
pip install fastapi uvicorn websockets
```

## Stopping the Server

Press `Ctrl+C` in the Command Prompt window where the server is running.

## Running as Windows Service (Advanced)

To run the server automatically at startup:

1. Install NSSM (Non-Sucking Service Manager):
   ```cmd
   # Download from: https://nssm.cc/download
   # Extract and add to PATH
   ```

2. Install as service:
   ```cmd
   nssm install G1WebUI python -m g1_app.ui.web_server
   ```

3. Start service:
   ```cmd
   nssm start G1WebUI
   ```

4. Stop service:
   ```cmd
   nssm stop G1WebUI
   ```

## File Paths on Windows

The application now uses **platform-independent paths**, so no configuration is needed:

- ✅ Works with Windows paths (`C:\Users\...`)
- ✅ Works with UNC paths (`\\server\share`)
- ✅ Handles spaces in paths
- ✅ Compatible with batch files

## Network Configuration

### Firewall

If Windows Firewall blocks the connection:

1. Open Windows Defender Firewall
2. Click "Allow an app through firewall"
3. Find Python and check both "Private" and "Public" boxes
4. Or use Command Prompt (as Administrator):
   ```cmd
   netsh advfirewall firewall add rule name="G1 Web UI" dir=in action=allow program="C:\path\to\python.exe" enable=yes
   ```

### Router

Ensure robot and PC are on same WiFi network:
- Robot: Check Unitree app for WiFi status
- PC: Settings → Network & Internet → WiFi

## Performance Tips

1. **Close unnecessary programs** to free up system resources
2. **Use 5GHz WiFi** if available (faster, more stable)
3. **Keep PC close to robot** for better signal
4. **Disable VPN** while controlling robot (may add latency)

## Security Considerations

⚠️ **WARNING**: The web server listens on 0.0.0.0 (all network interfaces)

For home use: This is fine
For networked environments:
- Run behind firewall
- Restrict network access
- Use SSH tunnel for remote access

## Command Line Options

Advanced users can customize the server:

```cmd
python -m g1_app.ui.web_server --help
```

Common options:
```cmd
# Use different port
python -m g1_app.ui.web_server --port 9000

# Verbose logging
python -m g1_app.ui.web_server --log-level debug

# Bind to specific IP only
python -m g1_app.ui.web_server --host 192.168.1.100
```

## Environment Setup

If you need to set environment variables for the server:

Create `run_web_ui_custom.bat`:
```batch
@echo off
set PYTHONUNBUFFERED=1
set G1_DEBUG=1
python -m g1_app.ui.web_server
pause
```

Then run `run_web_ui_custom.bat` instead.

## Logs and Debugging

Server logs are printed to Command Prompt. To save logs to file:

Create `run_web_ui_with_logs.bat`:
```batch
@echo off
python -m g1_app.ui.web_server > server.log 2>&1
pause
```

View logs with any text editor or Command Prompt:
```cmd
type server.log
```

## Getting Help

If you encounter issues:

1. Check server output for error messages
2. Verify Python and dependencies are installed
3. Ensure robot is powered on and on network
4. Try restarting both PC and robot
5. Check GitHub issues or documentation

## Next Steps

- Explore the web UI features
- Read [G1_AIR_CONTROL_GUIDE.md](G1_AIR_CONTROL_GUIDE.md) for detailed functionality
- Check [WEB_UI_GUIDE.md](g1_app/ui/WEB_UI_GUIDE.md) for UI controls

---

**Enjoy controlling your G1 robot from Windows! 🤖**
