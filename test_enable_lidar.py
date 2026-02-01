#!/usr/bin/env python3
"""Test enabling LiDAR driver service"""

import asyncio
import json
from unitree_webrtc_connect.webrtc_driver import UnitreeWebRTCConnection

async def test_enable_lidar():
    conn = UnitreeWebRTCConnection()
    await conn.connect("192.168.86.18")
    
    # Try different service names
    service_names = [
        "lidar_driver",
        "lidar_service",
        "mid360_driver",
        "unitree_lidar",
        "slam_service",
        "unitree_slam"
    ]
    
    for service in service_names:
        print(f"\n🔧 Trying to enable: {service}")
        
        # Method 1: Direct service enable via robot_state API
        payload = {
            "api_id": 5001,  # SERVICE_SWITCH
            "parameter": json.dumps({"name": service, "switch": 1})
        }
        
        conn.datachannel.pub_sub.publish("rt/api/robot_state/request", payload)
        await asyncio.sleep(0.5)
    
    # Wait a bit and check if LiDAR starts publishing
    print("\n⏳ Waiting 5 seconds to see if LiDAR activates...")
    
    lidar_received = False
    
    def lidar_callback(msg):
        nonlocal lidar_received
        if not lidar_received:
            print(f"✅ LiDAR DATA RECEIVED! Keys: {list(msg.keys())}")
            lidar_received = True
    
    conn.datachannel.pub_sub.subscribe("rt/utlidar/cloud_livox_mid360", lidar_callback)
    
    await asyncio.sleep(5)
    
    if not lidar_received:
        print("❌ No LiDAR data after service enable attempts")
        print("\n💡 The Android app may use a different activation method")
        print("   or LiDAR may require specific robot mode/state")
    
    await conn.disconnect()

if __name__ == "__main__":
    asyncio.run(test_enable_lidar())
