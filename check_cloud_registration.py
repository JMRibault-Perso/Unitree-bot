#!/usr/bin/env python3
"""
Check if robot is registered to Unitree cloud account
"""

import asyncio
import logging
import sys
from unitree_webrtc_connect.webrtc_driver import UnitreeWebRTCConnection, WebRTCConnectionMethod

logging.basicConfig(level=logging.INFO, format='%(message)s')

async def check_registration():
    print("=" * 70)
    print("G1 Cloud Registration Check")
    print("=" * 70)
    print()
    print("Checking if E21D1000PAHBMB06 is registered to your account...")
    print()
    
    try:
        # Try to connect - this will show us the exact error
        conn = UnitreeWebRTCConnection(
            WebRTCConnectionMethod.Remote,
            serialNumber="E21D1000PAHBMB06",
            username="sebastianribault1@gmail.com",
            password="Xlp142!?rz"
        )
        
        await conn.connect()
        
        print("✓ Robot IS registered and online!")
        print("\nYou should be able to control it now.")
        
    except ValueError as e:
        error_msg = str(e)
        print(f"✗ Connection Error: {error_msg}")
        print()
        
        if "Device not online" in error_msg:
            print("ISSUE: Robot not registered/paired to your cloud account")
            print()
            print("FIX: In your Android app:")
            print("─" * 70)
            print("1. Open Unitree app")
            print("2. Go to 'My Devices' or 'Device List'")
            print("3. Look for robot E21D1000PAHBMB06")
            print()
            print("If robot is NOT in the list:")
            print("  • Tap '+' or 'Add Device'")
            print("  • Select 'G1'")
            print("  • Follow pairing/binding process")
            print("  • Enter serial: E21D1000PAHBMB06")
            print()
            print("If robot IS in the list but shows offline:")
            print("  • Tap on the robot")
            print("  • Check 'Online Status'")
            print("  • If offline, tap 'Connect' or 'Wake Up'")
            print("  • Ensure robot has internet connection")
            print()
            print("Note: Just because the app can see/control the robot")
            print("      doesn't mean it's registered for cloud API access.")
            print("      The app may use direct WiFi connection.")
            print("─" * 70)
            
        elif "Authentication" in error_msg or "401" in error_msg:
            print("ISSUE: Account credentials incorrect")
            print()
            print("FIX: Verify your Unitree account:")
            print("  Email: sebastianribault1@gmail.com")
            print("  Password: Check if correct")
            
        else:
            print("ISSUE: Unknown connection error")
            print()
            print(f"Error details: {error_msg}")
            
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        logging.exception("Full trace:")

if __name__ == "__main__":
    try:
        asyncio.run(check_registration())
    except KeyboardInterrupt:
        print("\nCancelled")
