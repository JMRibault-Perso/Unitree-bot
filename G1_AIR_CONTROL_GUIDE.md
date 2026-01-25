# G1 Air Robot Control via WebRTC - Complete Guide

## 🎯 Critical Discovery

**G1 Air (without Jetson NX) CANNOT use direct DDS** - it only responds via **WebRTC**, same as the Android app.

## 📋 Key Findings

### 1. G1 Uses LocoClient API (Not SportClient)

Unlike GO2 which uses SportClient with individual command API IDs (Damp=1001, StandUp=1004, etc.), **G1 uses LocoClient** which controls the robot through a **Finite State Machine (FSM)** via a single API:

```python
ROBOT_API_ID_LOCO_SET_FSM_ID = 7101  # The only API you need!
```

### 2. Command Structure

**Correct payload format for G1:**
```python
{
    "api_id": 7101,
    "parameter": json.dumps({"data": <fsm_id>})
}
```

**WRONG (GO2 style - doesn't work on G1):**
```python
{
    "api_id": 1001  # This is GO2's Damp command - G1 ignores it!
}
```

### 3. FSM State IDs

From the official SDK (`unitree_sdk2py/g1/loco/g1_loco_client.py`):

| FSM ID | State Name | Description | LED Color |
|--------|------------|-------------|-----------|
| 0 | ZeroTorque | Motors off, no resistance | Purple |
| 1 | Damp | Motors damped, safe state | Orange |
| 200 | Start/Ready | Ready for motion | - |
| 3 | Sit | Sitting position | - |
| 706 | Squat2StandUp | Stand up from squat | - |
| 707 | StandUp2Squat | Squat down | - |
| 702 | Lie2StandUp | Stand up from lying (use carefully!) | - |

### 4. Proper State Transition Sequence

Based on official Unitree documentation:

```
Zero Torque (0) → Damp (1) → Start/Ready (200) → Motion Commands
```

**Start your robot:**
1. Press `d` - Damp mode (FSM 1) - Robot LED turns **orange**
2. Press `s` - Start/Ready mode (FSM 200) - Robot prepares for motion
3. Now you can use other commands like stand up

## 🚀 Quick Start

### Prerequisites

```bash
cd /root/G1/go2_webrtc_connect
# Make sure go2_webrtc_connect is installed
```

### Run the Controller

```bash
cd /root/G1/unitree_sdk2
python3 g1_controller.py
```

**Make sure the Android app is CLOSED** - only one WebRTC client can connect at a time.

### Commands

```
z = ZERO TORQUE (FSM 0)
d = DAMP mode (FSM 1) - START HERE
s = START/READY mode (FSM 200) - Then this
u = SQUAT TO STAND (FSM 706)
q = quit
```

## 💻 Code Reference

### Minimal Working Example

```python
import asyncio
import json
import sys
sys.path.insert(0, '/root/G1/go2_webrtc_connect')

from unitree_webrtc_connect.webrtc_driver import UnitreeWebRTCConnection
from unitree_webrtc_connect.constants import WebRTCConnectionMethod

ROBOT_IP = "192.168.86.16"
ROBOT_SN = "E21D1000PAHBMB06"
LOCO_API_SET_FSM_ID = 7101

async def send_damp():
    # Connect
    conn = UnitreeWebRTCConnection(
        WebRTCConnectionMethod.LocalSTA,
        ip=ROBOT_IP,
        serialNumber=ROBOT_SN
    )
    await conn.connect()
    
    # Send Damp command (FSM ID 1)
    payload = {
        "api_id": LOCO_API_SET_FSM_ID,
        "parameter": json.dumps({"data": 1})
    }
    
    await conn.datachannel.pub_sub.publish_request_new(
        "rt/api/sport/request",
        payload
    )
    
    await asyncio.sleep(1)
    await conn.disconnect()

asyncio.run(send_damp())
```

## 🔍 How We Discovered This

### The Problem
Initial attempts using GO2's SportClient commands (api_id: 1001, 1002, etc.) failed silently - robot didn't respond.

### The Investigation
1. **Checked official SDK**: Found `unitree_sdk2_python` on GitHub
2. **Discovered G1 uses LocoClient**: Unlike GO2's SportClient
3. **Found the API**: `ROBOT_API_ID_LOCO_SET_FSM_ID = 7101`
4. **Tested FSM states**: Confirmed FSM ID 1 (Damp) works!

### Key Code Reference
From `unitree_sdk2_python/unitree_sdk2py/g1/loco/g1_loco_client.py`:

```python
def Damp(self):
    self.SetFsmId(1)  # Calls API 7101 with data=1

def Start(self):
    self.SetFsmId(200)  # Calls API 7101 with data=200
```

## 📚 Official SDK Reference

### Service Information
- **Service Name**: `"sport"` (NOT "loco" - confusing but true!)
- **API Version**: `"1.0.0.0"`
- **Request Topic**: `"rt/api/sport/request"`
- **State Topic**: `"rt/lf/sportmodestate"`

### From g1_loco_api.py:
```python
LOCO_SERVICE_NAME = "sport"  # G1 uses "sport" service
LOCO_API_VERSION = "1.0.0.0"

# API IDs
ROBOT_API_ID_LOCO_SET_FSM_ID = 7101
ROBOT_API_ID_LOCO_SET_BALANCE_MODE = 7102
ROBOT_API_ID_LOCO_SET_STAND_HEIGHT = 7104
ROBOT_API_ID_LOCO_SET_VELOCITY = 7105
ROBOT_API_ID_LOCO_SET_ARM_TASK = 7106
```

## 🐛 Troubleshooting

### "Go2 is connected by another WebRTC client"
**Solution**: Close the Android app completely before running the Python controller.

### Robot doesn't respond to commands
**Checklist**:
1. ✅ Robot powered on and connected to WiFi
2. ✅ Android app is CLOSED
3. ✅ Using correct API ID (7101, not 1001)
4. ✅ Parameter format: `json.dumps({"data": fsm_id})`
5. ✅ Starting with Damp (FSM 1) before other commands

### MediaStreamError messages
**Ignore these** - they're from the video/audio streams which we don't use. Commands still work!

### Connection timeout
- Check robot IP is correct (`192.168.86.16` in this example)
- Verify robot is on same network
- Try pinging: `ping 192.168.86.16`

## 🔧 Technical Details

### WebRTC vs DDS

| Feature | G1 Air (no NX) | G1 EDU (with NX) |
|---------|----------------|------------------|
| Direct DDS | ❌ Not available | ✅ Available |
| WebRTC Control | ✅ Works | ✅ Works |
| SDK Examples | ❌ Won't work | ✅ Work directly |
| Android App | ✅ Works | ✅ Works |

### Why WebRTC for G1 Air?

G1 Air models without Jetson Orin NX don't run DDS services directly. Instead:
1. Robot has a WebRTC server (like a web interface)
2. Android app connects via WebRTC
3. WebRTC server forwards commands to internal DDS
4. Our Python code mimics the Android app's WebRTC connection

### Network Setup

```
[Your PC] --WiFi--> [Router] --WiFi--> [G1 Robot]
              (192.168.86.x network)

PC IP: 192.168.86.x (assigned by router)
G1 IP: 192.168.86.16 (assigned by router)
```

## 📁 File Structure

```
/root/G1/
├── unitree_sdk2/
│   ├── g1_controller.py          # Main controller (WORKING)
│   └── G1_AIR_CONTROL_GUIDE.md   # This file
│
├── go2_webrtc_connect/            # WebRTC library
│   └── unitree_webrtc_connect/
│       ├── webrtc_driver.py
│       └── constants.py
│
└── unitree_sdk2_python/           # Official SDK (for reference)
    └── unitree_sdk2py/g1/loco/
        ├── g1_loco_api.py         # API definitions
        └── g1_loco_client.py      # Client implementation
```

## 🎓 Learning Resources

### Official Unitree Documentation
- Architecture: https://support.unitree.com/home/en/G1_developer/architecture_description
- Remote Control: https://support.unitree.com/home/en/G1_developer/remote_control
- SDK GitHub: https://github.com/unitreerobotics/unitree_sdk2_python

### Key Insights from Documentation
- Remote control uses L2+B for Damp mode
- Boot sequence: Zero Torque → Damp → Ready → Motion
- LED colors indicate robot state (Orange = Damp, Purple = Zero Torque)

## ✅ Success Criteria

You know it's working when:
1. ✅ Controller connects (shows "✅ Connected!")
2. ✅ Press 'd' command
3. ✅ Robot LED turns **ORANGE**
4. ✅ You hear/feel motors engage with damping
5. ✅ Terminal shows "✅ damp sent!"

## 🚀 Next Steps

Now that basic control works, you can:

1. **Add more FSM states**: Movement (FSM 7105 for SetVelocity)
2. **Arm control**: Using ROBOT_API_ID_LOCO_SET_ARM_TASK (7106)
3. **Create GUI**: Build a simple UI for easier control
4. **Video streaming**: Add camera feed display
5. **Autonomous behavior**: Combine with vision/AI

## 🙏 Credits

- **Unitree Robotics**: For G1 robot and official SDK
- **go2_webrtc_connect**: Community library for WebRTC control
- **Discovery**: Through reverse-engineering official SDK structure

---

**Last Updated**: January 23, 2026  
**Robot**: G1 Air (SN: E21D1000PAHBMB06)  
**Status**: ✅ **WORKING**
