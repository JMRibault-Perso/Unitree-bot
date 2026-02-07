#!/usr/bin/env python3
"""Quick G1 connection and command test"""

import asyncio
import sys
sys.path.insert(0, '/root/G1/go2_webrtc_connect')

from unitree_webrtc_connect.webrtc_driver import UnitreeWebRTCConnection
from unitree_webrtc_connect.constants import WebRTCConnectionMethod

ROBOT_IP = "192.168.86.16"
ROBOT_SN = "E21D1000PAHBMB06"

async def main():
    print(f"Connecting to robot at {ROBOT_IP}...")
    
    conn = UnitreeWebRTCConnection(
        WebRTCConnectionMethod.LocalSTA,
        ip=ROBOT_IP,
        serialNumber=ROBOT_SN
    )
    
    try:
        await conn.connect()
        print("✓ Connected!")
        
        # Send stand command
        print("\nSending STAND command (api_id: 1001)...")
        await conn.datachannel.pub_sub.publish_request_new(
            "rt/api/sport/request",
            {"api_id": 1001}
        )
        await asyncio.sleep(2)
        
        print("✓ Stand command sent")
        print("\nConnected successfully! Keeping alive for 10s...")
        await asyncio.sleep(10)
        
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await conn.disconnect()
        print("Disconnected")

if __name__ == "__main__":
    asyncio.run(main())
