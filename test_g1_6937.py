#!/usr/bin/env python3
"""
G1_6937 Cloud Connection Test
Using correct device name from Android app
"""

import asyncio
import logging
from unitree_webrtc_connect.webrtc_driver import UnitreeWebRTCConnection, WebRTCConnectionMethod

logging.basicConfig(level=logging.WARNING)

async def test_connection():
    print("=" * 60)
    print("G1 Cloud Connection Test")
    print("Device Name: G1_6937 (from Android app)")
    print("Serial: E21D1000PAHBMB06")
    print("=" * 60)
    
    try:
        print("\nConnecting via Unitree cloud...")
        print("(Using device name G1_6937)")
        
        conn = UnitreeWebRTCConnection(
            WebRTCConnectionMethod.Remote,
            serialNumber="G1_6937",  # Use device name, not serial!
            username="sebastianribault1@gmail.com",
            password="Xlp142!?rz"
        )
        
        await conn.connect()
        
        print("\n✓✓✓ SUCCESS! Connected to G1_6937! ✓✓✓")
        print("\nTesting robot control...")
        
        # Test 1: Wave gesture
        print("\n1. Sending wave gesture...")
        await conn.datachannel.pub_sub.publish_request_new(
            "rt/api/arm/request",
            {"api_id": 7106, "parameter": {"data": 26}}  # High wave
        )
        
        await asyncio.sleep(5)
        
        # Test 2: Return to neutral
        print("2. Returning arms to neutral...")
        await conn.datachannel.pub_sub.publish_request_new(
            "rt/api/arm/request",
            {"api_id": 7106, "parameter": {"data": 99}}  # Cancel
        )
        
        await asyncio.sleep(2)
        
        print("\n" + "=" * 60)
        print("✓ CONNECTION SUCCESSFUL!")
        print("=" * 60)
        print("\nYour G1 is ready for WebRTC control!")
        print("\nNext steps:")
        print("  1. Run full controller:")
        print("     python3 g1_webrtc_controller.py")
        print("\n  2. Use device name 'G1_6937' when connecting")
        print("\n  3. Enjoy controlling your robot!")
        print("=" * 60)
        
        await asyncio.sleep(3)
        return True
        
    except Exception as e:
        print(f"\n✗ Connection failed: {e}")
        logging.exception("Details:")
        return False

if __name__ == "__main__":
    try:
        result = asyncio.run(test_connection())
        exit(0 if result else 1)
    except KeyboardInterrupt:
        print("\n\nTest cancelled.")
        exit(1)
