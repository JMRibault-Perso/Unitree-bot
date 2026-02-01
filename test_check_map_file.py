#!/usr/bin/env python3
"""
Check if the map file was actually saved on the robot.
We'll try to list the saved maps or check file existence.
"""
import asyncio
import sys
import json
sys.path.insert(0, '/root/G1/go2_webrtc_connect')
from unitree_webrtc_connect.webrtc_driver import UnitreeWebRTCConnection, WebRTCConnectionMethod

async def main():
    conn = UnitreeWebRTCConnection(WebRTCConnectionMethod.LocalSTA, ip="192.168.86.8")
    await conn.connect()
    print("✅ Connected\n")
    
    await conn.datachannel.disableTrafficSaving(True)
    
    # Try to get list of saved maps (if such API exists)
    print("🔍 Attempting to query saved maps...")
    
    # Method 1: Try to read rt/slam_info for map list
    def slam_info_cb(msg):
        if isinstance(msg, dict) and 'data' in msg:
            try:
                data = json.loads(msg['data']) if isinstance(msg['data'], str) else msg['data']
                print(f"📊 SLAM INFO: {json.dumps(data, indent=2)}")
            except:
                print(f"📊 SLAM INFO: {msg}")
    
    conn.datachannel.pub_sub.subscribe("rt/slam_info", slam_info_cb)
    
    # Method 2: Try SLAM response topic
    def slam_response_cb(msg):
        print(f"📨 SLAM Response: {msg}\n")
    
    conn.datachannel.pub_sub.subscribe("rt/api/slam_operate/response", slam_response_cb)
    
    # Wait to see if we get any info
    print("⏳ Listening for SLAM info (5 seconds)...\n")
    await asyncio.sleep(5)
    
    # Try to start relocation with our saved map to verify it exists
    print("\n🔍 Attempting to load map 'test_lidar_scan.pcd' to verify it exists...")
    relocation_request = {
        "header": {
            "identity": {
                "id": 0,
                "api_id": 1804  # START_RELOCATION
            }
        },
        "data": {
            "x": 0.0,
            "y": 0.0,
            "z": 0.0,
            "q_x": 0.0,
            "q_y": 0.0,
            "q_z": 0.0,
            "q_w": 1.0,
            "address": "/home/unitree/test_lidar_scan.pcd"
        }
    }
    
    conn.datachannel.pub_sub.publish_without_callback(
        "rt/api/slam_operate/request",
        json.dumps(relocation_request)
    )
    
    print("⏳ Waiting for response...\n")
    await asyncio.sleep(5)
    
    # Close SLAM
    close_request = {
        "header": {
            "identity": {
                "id": 0,
                "api_id": 1901  # CLOSE_SLAM
            }
        }
    }
    conn.datachannel.pub_sub.publish_without_callback(
        "rt/api/slam_operate/request",
        json.dumps(close_request)
    )
    
    await asyncio.sleep(2)
    print("✅ Done")

asyncio.run(main())
