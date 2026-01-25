# G1 Air WebRTC Control Guide

## Discovery: Your G1 Uses WebRTC, Not Local DDS!

Your G1 Air communicates via **WebRTC through Unitree's cloud API** (`global-robot-api.unitree.com`), not local DDS. This is why local SDK attempts failed.

## Quick Start

### 1. Test Connection
```bash
cd /root/G1/unitree_sdk2
python3 test_g1_webrtc.py
```

**Connection Methods:**
- **LocalSTA**: Robot and PC on same WiFi (recommended, no account needed)
  - Use robot IP: `192.168.86.3` (or current IP from router)
- **LocalAP**: Connect to robot's WiFi hotspot
- **Remote**: Control over internet (requires Unitree account)

### 2. Full Controller
```bash
python3 g1_webrtc_controller.py
```

**Interactive Mode Commands:**
```
ARM ACTIONS:
  wave, handshake, high_five, hug, clap, hands_up
  face_wave, left_kiss, arm_heart, xray, reject
  reset (return arms to neutral)

MODES:
  walk       - Standard walking mode
  run        - Running mode

MOVEMENT:
  forward    - Walk forward
  back       - Walk backward
  left       - Strafe left
  right      - Strafe right
  turn_left  - Rotate left
  turn_right - Rotate right
  stop       - Emergency stop

CONTROL:
  quit       - Exit program
```

## Architecture

```
┌─────────────┐          ┌──────────────────────┐          ┌──────────┐
│   Your PC   │  WebRTC  │  Unitree Cloud API   │  WebRTC  │ G1 Robot │
│  (Python)   │◄────────►│ global-robot-api.com │◄────────►│  (WiFi)  │
└─────────────┘          └──────────────────────┘          └──────────┘
                             DTLSv1.2 encrypted
```

**Key Points:**
- No firmware modification needed
- No local SDK required (G1 Air doesn't have Jetson NX)
- Same API used by Android app
- Works with G1 AIR/EDU models

## API Topics

### Arm Control: `rt/api/arm/request`
```python
{
    "api_id": 7106,
    "parameter": {"data": <action_id>}
}
```

**Action IDs:**
- 27 = Handshake, 18 = High Five, 19 = Hug
- 26 = High Wave, 17 = Clap, 25 = Face Wave
- 12 = Left Kiss, 20 = Arm Heart, 21 = Right Heart
- 15 = Hands Up, 24 = X-Ray, 23 = Right Hand Up
- 22 = Reject, 99 = Cancel (return to neutral)

### Sport Mode: `rt/api/sport/request`
```python
{
    "api_id": 7101,
    "parameter": {"data": <mode_id>}
}
```

**Mode IDs:**
- 500 = Walk
- 501 = Walk (with waist control)
- 801 = Run

### Movement: `rt/wirelesscontroller`
```python
{
    "lx": 0.0,  # Strafe left/right (-1.0 to 1.0)
    "ly": 0.0,  # Forward/back (-1.0 to 1.0)
    "rx": 0.0,  # Turn left/right (-1.0 to 1.0)
    "ry": 0.0,  # Pitch control (-1.0 to 1.0)
    "keys": 0
}
```

## Troubleshooting

### Connection Fails
1. **Verify robot IP**: Check router DHCP leases or Unitree app
2. **Same network**: Both PC and robot must be on same WiFi
3. **Robot powered on**: Check if robot responds to remote control
4. **Firewall**: WSL2 may need Windows Firewall rules for WebRTC

### Find Robot IP
```bash
# Scan your network (adjust subnet)
nmap -sn 192.168.86.0/24 | grep -B 2 "Unitree"

# Check router admin page for DHCP leases
# Look for device named "G1_6937" or similar
```

### Test Basic Connectivity
```bash
# Ping test
ping 192.168.86.3

# Port check (WebRTC uses random UDP ports)
nc -zv 192.168.86.3 8080
```

## Why Local DDS Didn't Work

Your G1 Air is a **Basic model** without:
- ❌ Jetson Orin NX development computer
- ❌ Local DDS services
- ❌ SSH access to robot

The Android app uses **WebRTC**, which you can now replicate!

## Community Resources

- **unitree_webrtc_connect**: `/root/G1/go2_webrtc_connect/`
  - Python library for WebRTC control
  - Examples: `/root/G1/go2_webrtc_connect/examples/g1/`
  
- **GitHub**: https://github.com/legion1581/unitree_webrtc_connect
  - Supports G1 firmware 1.4.0+
  - No jailbreak/firmware mod needed

- **Unitree Docs**: https://support.unitree.com/home/en/G1_developer

## Next Steps

1. **Test connection**: `python3 test_g1_webrtc.py`
2. **Try demo**: `python3 g1_webrtc_controller.py` → select mode 2
3. **Interactive control**: `python3 g1_webrtc_controller.py` → select mode 1
4. **Build custom app**: Use `unitree_webrtc_connect` library

## Example: Custom Script

```python
import asyncio
from unitree_webrtc_connect.webrtc_driver import (
    UnitreeWebRTCConnection, WebRTCConnectionMethod
)

async def main():
    # Connect to robot
    conn = UnitreeWebRTCConnection(
        WebRTCConnectionMethod.LocalSTA, 
        ip="192.168.86.3"
    )
    await conn.connect()
    
    # Wave hello
    await conn.datachannel.pub_sub.publish_request_new(
        "rt/api/arm/request",
        {"api_id": 7106, "parameter": {"data": 26}}  # High wave
    )
    
    await asyncio.sleep(10)

asyncio.run(main())
```

## Success! 🎉

You can now control your G1 Air using WebRTC - the same protocol the Android app uses!
