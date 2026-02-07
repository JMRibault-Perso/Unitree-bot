#!/usr/bin/env python3
"""
G1_6937 Connection with Retry Logic
Attempts multiple times and waits for robot to come online
"""

import asyncio
import logging
import time
from unitree_webrtc_connect.webrtc_driver import UnitreeWebRTCConnection, WebRTCConnectionMethod

logging.basicConfig(level=logging.WARNING)

async def try_connect(attempt_num, max_attempts):
    """Single connection attempt"""
    print(f"\n[Attempt {attempt_num}/{max_attempts}] Connecting to G1_6937...")
    
    try:
        conn = UnitreeWebRTCConnection(
            WebRTCConnectionMethod.Remote,
            serialNumber="G1_6937",
            username="sebastianribault1@gmail.com",
            password="Xlp142!?rz"
        )
        
        # This will raise an exception if it fails
        await conn.connect()
        return conn
        
    except ValueError as e:
        error_msg = str(e)
        if "Device not online" in error_msg:
            print(f"  ✗ Robot not online to cloud yet")
        elif "timeout" in error_msg.lower():
            print(f"  ✗ Connection timeout")
        else:
            print(f"  ✗ Error: {error_msg}")
        return None
    except Exception as e:
        print(f"  ✗ Unexpected error: {type(e).__name__}: {e}")
        return None

async def connect_with_retry():
    print("=" * 70)
    print("G1_6937 Connection with Retry")
    print("=" * 70)
    print("\nDevice: G1_6937")
    print("Account: sebastianribault1@gmail.com")
    print("\nThis will try multiple times and wait for robot to come online...")
    print("Press Ctrl+C to stop")
    print("-" * 70)
    
    max_attempts = 10
    wait_between = 10  # seconds
    
    for attempt in range(1, max_attempts + 1):
        conn = await try_connect(attempt, max_attempts)
        
        if conn:
            print("\n" + "=" * 70)
            print("✓✓✓ CONNECTION SUCCESSFUL! ✓✓✓")
            print("=" * 70)
            
            # Test control
            print("\nTesting robot control...")
            
            try:
                print("  → Sending wave gesture...")
                await conn.datachannel.pub_sub.publish_request_new(
                    "rt/api/arm/request",
                    {"api_id": 7106, "parameter": {"data": 26}}
                )
                
                await asyncio.sleep(5)
                
                print("  → Returning to neutral...")
                await conn.datachannel.pub_sub.publish_request_new(
                    "rt/api/arm/request",
                    {"api_id": 7106, "parameter": {"data": 99}}
                )
                
                await asyncio.sleep(2)
                
                print("\n✓ Robot control working!")
                print("\n" + "=" * 70)
                print("SUCCESS! Your G1 is ready for WebRTC control!")
                print("=" * 70)
                print("\nNext: Run full controller:")
                print("  python3 g1_webrtc_controller.py")
                print("\nRemember to:")
                print("  • Close Android app before connecting")
                print("  • Use device name: G1_6937")
                print("  • Use Remote connection mode")
                print("=" * 70)
                
                await asyncio.sleep(3)
                return True
                
            except Exception as e:
                print(f"\n✗ Control test failed: {e}")
                return False
        
        # Not connected, wait and retry
        if attempt < max_attempts:
            print(f"  ⏳ Waiting {wait_between}s before retry...")
            print(f"     (Make sure robot is awake and app is closed)")
            await asyncio.sleep(wait_between)
    
    print("\n" + "=" * 70)
    print("✗ Failed after", max_attempts, "attempts")
    print("=" * 70)
    print("\nTroubleshooting:")
    print("  1. Is robot powered on and standing?")
    print("  2. Is Android app completely closed?")
    print("  3. Does robot have internet connection?")
    print("  4. In app settings, enable 'Cloud Mode' or 'Remote Access'")
    print("  5. Try power cycling the robot")
    print("\nContact Unitree support if issue persists:")
    print("  support@unitree.com")
    print("=" * 70)
    return False

if __name__ == "__main__":
    try:
        result = asyncio.run(connect_with_retry())
        exit(0 if result else 1)
    except KeyboardInterrupt:
        print("\n\nConnection attempts cancelled.")
        print("You can try again anytime by running:")
        print("  python3 retry_connection.py")
        exit(1)
