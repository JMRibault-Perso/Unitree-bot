#!/usr/bin/env python3
"""
Quick G1 Cloud Connection Test
Connects to E21D1000PAHBMB06 via Unitree cloud
"""

import asyncio
import logging
from unitree_webrtc_connect.webrtc_driver import UnitreeWebRTCConnection, WebRTCConnectionMethod

# Reduce logging noise
logging.basicConfig(level=logging.WARNING)

async def test_cloud_connection():
    print("=" * 60)
    print("G1 Cloud Connection Test")
    print("Serial: E21D1000PAHBMB06")
    print("=" * 60)
    
    try:
        print("\nConnecting to G1 via Unitree cloud...")
        print("(This may take 10-15 seconds)")
        
        conn = UnitreeWebRTCConnection(
            WebRTCConnectionMethod.Remote,
            serialNumber="E21D1000PAHBMB06",
            username="sebastianribault1@gmail.com",
            password="Xlp142!?rz"
        )
        
        await conn.connect()
        
        print("\n✓ SUCCESS! Connected to your G1 robot!")
        print("\nTesting arm control...")
        
        # Wave hello
        print("  - Sending wave gesture...")
        await conn.datachannel.pub_sub.publish_request_new(
            "rt/api/arm/request",
            {"api_id": 7106, "parameter": {"data": 26}}  # High wave
        )
        
        await asyncio.sleep(5)
        
        # Return to neutral
        print("  - Returning arms to neutral...")
        await conn.datachannel.pub_sub.publish_request_new(
            "rt/api/arm/request",
            {"api_id": 7106, "parameter": {"data": 99}}  # Cancel
        )
        
        await asyncio.sleep(2)
        
        print("\n✓ Test complete!")
        print("\nYour G1 is ready for control!")
        print("\nNext: Run full controller:")
        print("  python3 g1_webrtc_controller.py")
        
        # Keep connection alive briefly
        await asyncio.sleep(3)
        
    except Exception as e:
        print(f"\n✗ Connection failed: {e}")
        print("\nTroubleshooting:")
        print("  1. Verify robot is powered on")
        print("  2. Check robot is connected to internet (via WiFi)")
        print("  3. Verify credentials are correct")
        print("  4. Check robot status in Android app")
        return False
    
    return True

if __name__ == "__main__":
    try:
        result = asyncio.run(test_cloud_connection())
        exit(0 if result else 1)
    except KeyboardInterrupt:
        print("\n\nTest interrupted.")
        exit(1)
