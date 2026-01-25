#!/usr/bin/env python3
"""
Test WebRTC connection to discover robot info
"""
import sys
sys.path.insert(0, '/root/G1/go2_webrtc_connect')
sys.path.insert(0, '/root/G1/unitree_sdk2')

import asyncio
from unitree_webrtc_connect import WebRTCConnection

async def test_discovery():
    print("Attempting to connect to robot at 192.168.86.2...")
    
    try:
        conn = WebRTCConnection("LocalSTA", "192.168.86.2")
        await conn.connect()
        
        print(f"✅ Connected!")
        print(f"   Serial: {conn.serial_number}")
        print(f"   IP: 192.168.86.2")
        
        await conn.disconnect()
        
        return {
            "serial_number": conn.serial_number,
            "ip": "192.168.86.2",
            "name": f"G1_{conn.serial_number[-4:]}" if conn.serial_number else "G1"
        }
        
    except Exception as e:
        print(f"❌ Failed: {e}")
        return None

if __name__ == '__main__':
    result = asyncio.run(test_discovery())
    if result:
        print(f"\nRobot Info: {result}")
