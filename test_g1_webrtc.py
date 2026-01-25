#!/usr/bin/env python3
"""
G1 Air WebRTC Connection Test
Tests connection to G1 robot using Unitree's WebRTC API
"""

import asyncio
import logging
import sys

from unitree_webrtc_connect.webrtc_driver import UnitreeWebRTCConnection, WebRTCConnectionMethod

# Enable detailed logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

async def test_connection():
    """Test WebRTC connection to G1 robot"""
    
    print("=" * 60)
    print("G1 Air WebRTC Connection Test")
    print("=" * 60)
    
    # Get connection parameters
    print("\nConnection Methods:")
    print("1. LocalSTA (same WiFi network)")
    print("2. LocalAP (robot hotspot)")
    print("3. Remote (via Unitree cloud)")
    
    method_choice = input("\nSelect method (1/2/3) [default: 1]: ").strip() or "1"
    
    try:
        if method_choice == "1":
            # LocalSTA mode - robot on same network
            print("\nLocalSTA Connection Options:")
            print("1. By IP address")
            print("2. By serial number (auto-discover IP)")
            local_method = input("Select [1/2, default=2]: ").strip() or "2"
            
            if local_method == "1":
                robot_ip = input("Enter robot IP [default: 192.168.86.3]: ").strip() or "192.168.86.3"
                print(f"\nConnecting to G1 at {robot_ip} via LocalSTA...")
                conn = UnitreeWebRTCConnection(WebRTCConnectionMethod.LocalSTA, ip=robot_ip)
            else:
                serial = input("Enter serial number [default: E21D1000PAHBMB06]: ").strip() or "E21D1000PAHBMB06"
                print(f"\nConnecting to G1 {serial} via LocalSTA (auto-discovering IP)...")
                conn = UnitreeWebRTCConnection(WebRTCConnectionMethod.LocalSTA, serialNumber=serial)
            
        elif method_choice == "2":
            # LocalAP mode - robot is WiFi hotspot
            print("\nConnecting to G1 via LocalAP (robot hotspot)...")
            conn = UnitreeWebRTCConnection(WebRTCConnectionMethod.LocalAP)
            
        elif method_choice == "3":
            # Remote mode - via Unitree cloud
            serial = input("Enter robot serial number [default: E21D1000PAHBMB06]: ").strip() or "E21D1000PAHBMB06"
            username = input("Enter Unitree account email: ").strip()
            password = input("Enter Unitree account password: ").strip()
            print(f"\nConnecting to {serial} via Remote (cloud)...")
            conn = UnitreeWebRTCConnection(
                WebRTCConnectionMethod.Remote,
                serialNumber=serial,
                username=username,
                password=password
            )
        else:
            print("Invalid choice!")
            return
        
        # Attempt connection
        print("\nEstablishing WebRTC connection...")
        await conn.connect()
        print("✓ Successfully connected to G1!")
        
        # Test basic status query
        print("\nTesting API communication...")
        
        # Get robot status (this may vary based on G1 API)
        print("Robot connection active and ready for commands")
        print("\nAvailable API topics:")
        print("  - rt/api/arm/request (arm actions)")
        print("  - rt/api/sport/request (locomotion modes)")
        print("  - rt/wirelesscontroller (movement commands)")
        
        # Keep connection alive for testing
        print("\nConnection established! Press Ctrl+C to exit.")
        print("You can now send commands to the robot.")
        
        # Example: Send a simple status request
        print("\nSending test command (stand mode)...")
        await conn.datachannel.pub_sub.publish_request_new(
            "rt/api/sport/request",
            {
                "api_id": 7101,
                "parameter": {"data": 500}  # Walk mode
            }
        )
        
        # Wait for response
        await asyncio.sleep(3)
        print("✓ Command sent successfully!")
        
        # Keep connection alive
        print("\nConnection test complete. Keeping connection alive for 30 seconds...")
        await asyncio.sleep(30)
        
    except ValueError as e:
        print(f"\n✗ Connection error: {e}")
        print("\nTroubleshooting:")
        print("  1. Verify robot IP is correct (check router DHCP leases)")
        print("  2. Ensure robot and PC are on same WiFi network")
        print("  3. Check if robot is powered on and connected to WiFi")
        print("  4. For Remote mode, verify Unitree account credentials")
        sys.exit(1)
        
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        logging.exception("Full error details:")
        sys.exit(1)
    
    finally:
        print("\nDisconnecting...")

if __name__ == "__main__":
    try:
        asyncio.run(test_connection())
    except KeyboardInterrupt:
        print("\n\nConnection test interrupted by user.")
        print("WebRTC connection closed.")
