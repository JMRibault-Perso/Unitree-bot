# AP Mode Implementation Summary

## Overview
Added support for connecting to the G1 robot via **AP mode** (robot hotspot) in addition to the existing **STA mode** (WiFi network). This allows users to connect when the robot is not on an existing WiFi network.

## What Changed

### Backend Changes

#### 1. `g1_app/core/robot_controller.py`
- Added `connection_mode` parameter to `RobotController.__init__()` (default: "sta")
- Modified `connect()` method to support three modes:
  - **"sta"**: Robot on existing WiFi network (requires IP + serial number)
  - **"ap"**: Robot creates hotspot (requires only serial number)
  - **"remote"**: Cloud connection (not yet implemented)

**Key Code:**
```python
def __init__(self, ..., connection_mode: str = "sta"):
    self.connection_mode = connection_mode

async def connect(self, ip: str = None, serial_number: str = None):
    if self.connection_mode == "ap":
        # AP mode: robot creates hotspot, no IP needed
        self.webrtc_conn = UnitreeWebRTCConnection(WebRTCConnectionMethod.LocalAP)
    elif self.connection_mode == "sta":
        # STA mode: robot on network, needs IP or serial
        self.webrtc_conn = UnitreeWebRTCConnection(
            WebRTCConnectionMethod.LocalSTA,
            ip=ip,
            serialNumber=serial_number
        )
```

#### 2. `g1_app/ui/web_server.py`
- Updated `/api/connect` endpoint to accept `mode` query parameter
- Skip ping check in AP mode (robot not yet on network)
- Pass mode to RobotController

**Key Code:**
```python
@app.post("/api/connect")
async def connect_robot(ip: str = None, serial_number: str = None, mode: str = "sta"):
    # Validate mode
    if mode not in ["sta", "ap", "remote"]:
        return {"success": False, "error": f"Invalid mode: {mode}"}
    
    # Skip ping in AP mode (robot creates hotspot, not on network yet)
    if mode != "ap":
        # Existing ping logic for STA mode
        ...
    
    # Create controller with specified mode
    global robot_controller
    robot_controller = RobotController(..., connection_mode=mode)
```

### Frontend Changes

#### 3. `g1_app/ui/index.html`

**Added Connection Mode Selector:**
```html
<select id="connectionMode">
    <option value="sta">🌐 WiFi Network (STA Mode)</option>
    <option value="ap">📡 Robot Hotspot (AP Mode)</option>
</select>
```

**Updated JavaScript `connectToSelectedRobot()` function:**
- Reads selected mode from dropdown
- Skips IP requirement for AP mode
- Adds `mode` parameter to `/api/connect` call
- Shows mode-specific help text

**Mode-Specific Help Text:**
- **STA Mode**: "Robot connects to your existing WiFi network. Requires robot and PC on same network."
- **AP Mode**: "Robot creates its own WiFi hotspot. Connect your PC to the robot's WiFi network before clicking Connect."

## How to Use

### STA Mode (WiFi Network) - Existing Behavior
1. Ensure robot and PC are on the same WiFi network
2. Select "🌐 WiFi Network (STA Mode)" (default)
3. Wait for robot to appear in discovered list
4. Click "Connect"

### AP Mode (Robot Hotspot) - **NEW**
1. Power on robot (it will create WiFi hotspot named like "G1_XXXX")
2. Connect your PC's WiFi to the robot's hotspot network
3. In the web UI, select "📡 Robot Hotspot (AP Mode)"
4. Click "Connect" (no IP needed, robot will be discovered via WebRTC)

## Technical Details

### WebRTC Connection Methods
From `unitree_webrtc_connect.constants`:
- **`WebRTCConnectionMethod.LocalAP`**: Robot creates hotspot, client connects directly
  - No parameters needed (robot advertises itself)
  - Slower but works without existing WiFi infrastructure
  
- **`WebRTCConnectionMethod.LocalSTA`**: Robot joins existing WiFi network
  - Requires `ip=` or `serialNumber=` parameter
  - Faster, requires network infrastructure

### SDK Reference
Based on `g1_webrtc_controller.py` examples:
```python
# AP Mode Example (Line 260)
conn = UnitreeWebRTCConnection(WebRTCConnectionMethod.LocalAP)
await conn.connect()

# STA Mode Example (Lines 239-256)
conn = UnitreeWebRTCConnection(
    WebRTCConnectionMethod.LocalSTA,
    ip="192.168.86.3",
    serialNumber="your_serial"
)
await conn.connect()
```

## Testing Recommendations

### Test AP Mode:
1. Power on robot without connecting to WiFi
2. Look for robot's WiFi network on your PC
3. Connect to robot's hotspot
4. Open web UI: `http://127.0.0.1:9000`
5. Select "AP Mode" and click Connect

### Test STA Mode (existing):
1. Ensure robot is on your network (check app)
2. Open web UI
3. Select "STA Mode" (default)
4. Wait for discovery, click Connect

## Files Modified
1. ✅ `g1_app/core/robot_controller.py` - Backend connection logic
2. ✅ `g1_app/ui/web_server.py` - API endpoint handling
3. ✅ `g1_app/ui/index.html` - UI mode selector and help text

## Documentation Updates Needed
- [ ] Update `WINDOWS_SETUP.md` with AP mode instructions
- [ ] Update `QUICK_START.md` with mode selection guide
- [ ] Add troubleshooting for AP mode connection issues
