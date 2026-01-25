#!/usr/bin/env python3
"""
Test robot control using WebRTC-DDS bridge
Sends: go, zero torque, and damp commands
"""

import sys
sys.path.insert(0, '/root/G1/go2_webrtc_connect')

import asyncio
import json
from unitree_webrtc_connect.webrtc_driver import UnitreeWebRTCConnection
from unitree_webrtc_connect.webrtc_datachannel import WebRTCConnectionMethod

# Robot configuration
ROBOT_IP = "192.168.86.16"
ROBOT_SN = "E21D1000PAHBMB06"
EMAIL = "sebastianribault1@gmail.com"
PASSWORD = "Xlp142!?rz"

async def send_sport_command(conn, api_id, params=None):
    """Send sport mode command via DDS topic"""
    cmd = {"api_id": api_id}
    if params:
        cmd.update(params)
    
    topic = "rt/api/sport/request"
    print(f"Sending to {topic}: {cmd}")
    
    # Send via WebRTC data channel
    if hasattr(conn, 'pc') and conn.pc:
        for channel in conn.pc.getTransceivers():
            if hasattr(channel, 'send'):
                message = json.dumps({"topic": topic, "data": cmd})
                await channel.send(message)

async def test_local_connection():
    """Try local STA connection"""
    print("=" * 60)
    print("Testing LOCAL connection to robot")
    print("=" * 60)
    
    try:
        conn = UnitreeWebRTCConnection(
            WebRTCConnectionMethod.LocalSTA,
            ip=ROBOT_IP,
            serialNumber=ROBOT_SN
        )
        
        await conn.connect()
        print("✓ Connected locally!")
        return conn
    except Exception as e:
        print(f"✗ Local connection failed: {e}")
        return None

async def test_cloud_connection():
    """Try cloud connection"""
    print("=" * 60)
    print("Testing CLOUD connection to robot")
    print("=" * 60)
    
    try:
        conn = UnitreeWebRTCConnection(
            WebRTCConnectionMethod.Remote,
            serialNumber=ROBOT_SN,
            username=EMAIL,
            password=PASSWORD
        )
        
        await conn.connect()
        print("✓ Connected via cloud!")
        return conn
    except Exception as e:
        print(f"✗ Cloud connection failed: {e}")
        return None

async def main():
    # Try local first, then cloud
    conn = await test_local_connection()
    if not conn:
        conn = await test_cloud_connection()
    
    if not conn:
        print("\n❌ Could not connect to robot!")
        print("\nTroubleshooting:")
        print("1. Make sure robot is powered on")
        print("2. Check robot is at 192.168.86.16")
        print("3. Verify robot is registered to cloud (if using remote)")
        return
    
    print("\n" + "=" * 60)
    print("Sending commands to robot...")
    print("=" * 60)
    
    # Command sequence
    commands = [
        ("Stand Up", 1001, None),
        ("Zero Torque Mode", 1013, None),
        ("Damp Mode", 1008, None),
        ("Stand Up Again", 1001, None),
    ]
    
    for name, api_id, params in commands:
        print(f"\n→ {name} (api_id: {api_id})")
        await send_sport_command(conn, api_id, params)
        await asyncio.sleep(3)
    
    print("\n✓ Commands sent!")
    print("Keeping connection alive for 10 seconds...")
    await asyncio.sleep(10)
    
    await conn.disconnect()
    print("Disconnected")

if __name__ == '__main__':
    asyncio.run(main())

if __name__ == '__main__':
    main()
