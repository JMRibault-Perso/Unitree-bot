#!/usr/bin/env python3
"""
Test if starting SLAM mapping enables LiDAR point cloud streaming.
Theory: lidar_driver is functional but only publishes when SLAM is active.
"""

import asyncio
import sys
import logging
import json

sys.path.insert(0, '/root/G1/go2_webrtc_connect')
from unitree_webrtc_connect.webrtc_driver import UnitreeWebRTCConnection, WebRTCConnectionMethod

logging.basicConfig(level=logging.WARNING)

point_cloud_count = 0

async def main():
    global point_cloud_count
    
    try:
        print("🔌 Connecting to G1 Air robot...")
        conn = UnitreeWebRTCConnection(WebRTCConnectionMethod.LocalSTA, ip="192.168.86.18")
        await conn.connect()
        print("✅ Connected!\n")
        
        await conn.datachannel.disableTrafficSaving(True)
        
        # Step 1: Subscribe to LiDAR topic BEFORE starting SLAM
        print("📡 [1/4] Subscribing to rt/utlidar/cloud_livox_mid360...")
        
        def lidar_callback(message):
            global point_cloud_count
            point_cloud_count += 1
            print(f"\n🎯 POINT CLOUD #{point_cloud_count} RECEIVED!")
            if isinstance(message, dict):
                print(f"   Keys: {list(message.keys())}")
                if 'data' in message:
                    data = message['data']
                    print(f"   Data type: {type(data).__name__}")
                    if isinstance(data, (bytes, bytearray)):
                        print(f"   Data size: {len(data)} bytes")
                    elif isinstance(data, dict):
                        print(f"   Data keys: {list(data.keys())}")
                    elif isinstance(data, str):
                        print(f"   Data length: {len(data)} chars")
        
        conn.datachannel.pub_sub.subscribe("rt/utlidar/cloud_livox_mid360", lidar_callback)
        print("✅ Subscribed!\n")
        
        # Step 2: Wait a bit to see if any data comes without SLAM
        print("⏳ [2/4] Waiting 5s to check if LiDAR publishes without SLAM...")
        await asyncio.sleep(5)
        
        if point_cloud_count > 0:
            print(f"✅ LiDAR already publishing! ({point_cloud_count} messages)")
        else:
            print("❌ No LiDAR data yet (expected - SLAM not started)\n")
        
        # Step 3: Start SLAM mapping
        print("🗺️  [3/4] Starting SLAM mapping (should enable LiDAR)...")
        
        slam_response_received = False
        
        def slam_response_callback(response):
            nonlocal slam_response_received
            slam_response_received = True
            print(f"\n📨 SLAM Response:")
            print(json.dumps(response, indent=2))
        
        # Send START_MAPPING request (API 1801)
        slam_request = {
            "header": {
                "identity": {
                    "id": 0,
                    "api_id": 1801  # START_MAPPING
                }
            }
        }
        
        # Subscribe to response topic
        conn.datachannel.pub_sub.subscribe("rt/api/slam_operate/response", slam_response_callback)
        
        # Send request without callback
        conn.datachannel.pub_sub.publish_without_callback(
            "rt/api/slam_operate/request",
            json.dumps(slam_request)
        )
        
        print("✅ SLAM start command sent!\n")
        
        # Step 4: Wait for LiDAR data
        print("⏳ [4/4] Waiting 20 seconds for LiDAR point cloud data...")
        
        for i in range(20):
            await asyncio.sleep(1)
            if point_cloud_count > 0:
                print(f"   ✅ {point_cloud_count} point clouds received so far...")
        
        # Results
        print(f"\n" + "="*60)
        print(f"📊 FINAL RESULTS:")
        print(f"   SLAM Response: {'✅ Received' if slam_response_received else '❌ Not received'}")
        print(f"   Point Clouds: {point_cloud_count} messages")
        
        if point_cloud_count > 0:
            print(f"\n🎉 SUCCESS! LiDAR data IS available via WebRTC!")
            print(f"   Topic: rt/utlidar/cloud_livox_mid360")
            print(f"   Rate: ~{point_cloud_count/20:.1f} Hz")
        else:
            print(f"\n❌ FAILED: No LiDAR data received even with SLAM active")
            print(f"   Possible causes:")
            print(f"   - G1 Air doesn't expose LiDAR via WebRTC datachannel")
            print(f"   - LiDAR data on separate video stream (not topic)")
            print(f"   - Need different decoder or topic subscription method")
        
        # Cleanup: Stop SLAM
        print(f"\n🛑 Stopping SLAM...")
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
        
        print("="*60)
        
    except Exception as e:
        logging.error(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⚠️ Interrupted by user")
        sys.exit(0)
