#!/bin/bash
# G1 Robot Information
# Serial: E21D1000PAHBMB06

cat << 'EOF'
╔══════════════════════════════════════════════════════════════════╗
║           G1 Robot Status & Connection Guide                      ║
║           Serial: E21D1000PAHBMB06                                ║
╚══════════════════════════════════════════════════════════════════╝

CONNECTION STATUS:
  Robot IP: 192.168.86.3 ✓ (pingable)
  WebRTC Ports: ✗ (connection refused on 8081, 9991)
  
DIAGNOSIS:
  The robot is online but not accepting WebRTC connections.
  This typically means the robot is not in the correct mode.

SOLUTION: Use Remote/Cloud Connection
──────────────────────────────────────────────────────────────────

The Android app works because it uses Unitree's cloud relay.
You can do the same!

STEPS:

1. Ensure you have a Unitree account
   - The same account you use in the Android app
   - Email/password login

2. Run the controller with Remote mode:
   
   python3 g1_webrtc_controller.py
   
   Then select:
   - Connection Method: 3 (Remote)
   - Serial: E21D1000PAHBMB06 (default)
   - Enter your Unitree account email
   - Enter your password

3. This connects via Unitree's cloud server:
   
   [Your PC] ←→ [global-robot-api.unitree.com] ←→ [G1 Robot]
   
   Same as Android app, no local network setup needed!

ALTERNATIVE: Enable Local WebRTC Access
──────────────────────────────────────────────────────────────────

If you want direct local control (no cloud), the robot needs to be
in the right mode:

Option A: Via Android App
  1. Open Unitree app
  2. Connect to robot
  3. Look for "Developer Mode" or "SDK Mode" in settings
  4. Enable it
  5. Restart robot if prompted

Option B: Via R3-1 Remote Control
  1. Power on robot with R3-1
  2. Check if there's a button combination for SDK mode
  3. Consult Unitree manual for R3-1 mode switching

Option C: Contact Unitree Support
  - Email: support@unitree.com
  - Ask: "How to enable WebRTC/SDK mode for G1 serial E21D1000PAHBMB06"
  - Mention: Android app works, but local WebRTC connections fail

QUICK TEST COMMANDS:
──────────────────────────────────────────────────────────────────

# Check robot is online
ping -c 2 192.168.86.3

# Test WebRTC ports (should connect if SDK mode enabled)
nc -zv 192.168.86.3 8081
nc -zv 192.168.86.3 9991

# Run interactive controller
python3 g1_webrtc_controller.py

# Run simple test
python3 test_g1_webrtc.py

WHY THIS HAPPENS:
──────────────────────────────────────────────────────────────────

The G1 has two communication modes:

1. Cloud Mode (ALWAYS WORKS)
   - Used by Android app
   - Goes through Unitree's servers
   - Requires account login
   - Works from anywhere

2. Local WebRTC Mode (REQUIRES ENABLING)
   - Direct connection over WiFi
   - Faster, lower latency
   - No internet needed once connected
   - Must be explicitly enabled

Your robot is currently in Cloud-only mode.

RECOMMENDED: Try Remote/Cloud Connection First
──────────────────────────────────────────────────────────────────

This is the fastest way to get started since it works immediately:

python3 -c "
import asyncio
from unitree_webrtc_connect.webrtc_driver import (
    UnitreeWebRTCConnection, WebRTCConnectionMethod
)

async def test():
    # Replace with your Unitree account
    username = input('Unitree email: ')
    password = input('Password: ')
    
    conn = UnitreeWebRTCConnection(
        WebRTCConnectionMethod.Remote,
        serialNumber='E21D1000PAHBMB06',
        username=username,
        password=password
    )
    
    await conn.connect()
    print('✓ Connected! Waving hello...')
    
    # Wave gesture
    await conn.datachannel.pub_sub.publish_request_new(
        'rt/api/arm/request',
        {'api_id': 7106, 'parameter': {'data': 26}}
    )
    
    await asyncio.sleep(10)

asyncio.run(test())
"

EOF
