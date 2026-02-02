# Windows Quick Start - G1 Web UI

## ⚡ 5-Minute Setup

### 1. Install Python
Download from [python.org](https://www.python.org/downloads/) and install. **✓ Check "Add Python to PATH"**

### 2. Install Dependencies
```cmd
pip install fastapi uvicorn websockets
```

### 3. Run the Server
**Option A (Easiest):** Double-click `run_web_ui.bat`

**Option B (Command Prompt):**
```cmd
python -m g1_app.ui.web_server
```

**Option C (PowerShell):**
```powershell
.\run_web_ui.ps1
```

### 4. Open Web UI
Open browser to: **http://localhost:8000**

### 5. Connect to Robot
1. Enter robot IP and serial number
2. Click Connect
3. Control via web interface

## 📋 Pre-Requirements

- Windows 10/11
- Python 3.8+ (check: `python --version`)
- G1 robot on same WiFi network
- Robot powered on

## 🔍 Find Robot IP

**Option 1: Unitree App**
- Open Unitree app
- See robot IP in connection info

**Option 2: Router Admin Page**
- Log into router (usually 192.168.1.1)
- Check DHCP clients for "unitree" or "g1"

**Option 3: Command Prompt**
```cmd
arp -a | findstr unitree
```

## ⚠️ Troubleshooting

**"python is not recognized"**
- Python not in PATH
- Reinstall Python and check "Add Python to PATH"

**"Module not found"**
```cmd
pip install fastapi uvicorn websockets
```

**"Port 8000 in use"**
```cmd
netstat -ano | findstr :8000
taskkill /PID [PID] /F
```

## 📖 Full Documentation

- [WINDOWS_SETUP.md](WINDOWS_SETUP.md) - Detailed setup guide
- [WINDOWS_COMPATIBILITY.md](WINDOWS_COMPATIBILITY.md) - What was changed
- [WEB_UI_GUIDE.md](g1_app/ui/WEB_UI_GUIDE.md) - UI features

## 🎮 Web UI Controls

Once connected:

- **FSM States**: Click state buttons to transition
- **Movement**: Arrow keys or slider to move/rotate
- **Gestures**: Select from dropdown and execute
- **Status**: Real-time battery, mode, and state display

## 🚀 Advanced Options

```cmd
# Different port
python -m g1_app.ui.web_server --port 9000

# Verbose logging
python -m g1_app.ui.web_server --log-level debug

# Specific network interface
python -m g1_app.ui.web_server --host 192.168.1.100
```

## 💡 Tips

- Run in dedicated Command Prompt window (so you can see logs)
- Keep browser tab open while controlling
- Restart robot if connection drops
- Check firewall if can't connect

## 🆘 Get Help

1. Check error message in Command Prompt
2. Review [WINDOWS_SETUP.md](WINDOWS_SETUP.md) troubleshooting
3. Verify python: `python --version`
4. Verify packages: `pip list | findstr fastapi`

---

**Enjoy! 🤖**
