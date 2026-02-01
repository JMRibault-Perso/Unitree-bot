#!/usr/bin/env python3
"""
Check SLAM status via rt/slam_info and rt/slam_key_info to see why point clouds aren't publishing.
"""
import asyncio
import sys
import json
sys.path.insert(0, '/root/G1/go2_webrtc_connect')
from unitree_webrtc_connect.webrtc_driver import UnitreeWebRTCConnection, WebRTCConnectionMethod

slam_info_received = []
slam_key_info_received = []
points_received = 0

async def main():
    global points_received
    
    conn = UnitreeWebRTCConnection(WebRTCConnectionMethod.LocalSTA, ip="192.168.86.8")
    await conn.connect()
    print("✅ Connected\n")
    
    await conn.datachannel.disableTrafficSaving(True)
    
    def slam_info_cb(msg):
        print(f"\n📢 SLAM INFO:")
        if isinstance(msg, dict) and 'data' in msg:
            try:
                data = json.loads(msg['data']) if isinstance(msg['data'], str) else msg['data']
                print(json.dumps(data, indent=2))
                slam_info_received.append(data)
            except:
                print(f"   Raw: {msg['data']}")
                slam_info_received.append(msg)
    
    def slam_key_info_cb(msg):
        print(f"\n🔑 SLAM KEY INFO:")
        if isinstance(msg, dict) and 'data' in msg:
            try:
                data = json.loads(msg['data']) if isinstance(msg['data'], str) else msg['data']
                print(json.dumps(data, indent=2))
                slam_key_info_received.append(data)
            except:
                print(f"   Raw: {msg['data']}")
                slam_key_info_received.append(msg)
    
    def points_cb(msg):
        global points_received
        points_received += 1
        if points_received == 1:
            print(f"\n🎯 FIRST POINT CLOUD RECEIVED!")
            print(f"   Type: {type(msg)}")
            if isinstance(msg, dict):
                print(f"   Keys: {list(msg.keys())}")
    
    def response_cb(msg):
        print(f"\n📨 SLAM API Response: {msg}")
    
    # Subscribe to status topics FIRST
    print("📡 Subscribing to SLAM status topics...")
    conn.datachannel.pub_sub.subscribe("rt/slam_info", slam_info_cb)
    conn.datachannel.pub_sub.subscribe("rt/slam_key_info", slam_key_info_cb)
    conn.datachannel.pub_sub.subscribe("rt/api/slam_operate/response", response_cb)
    
    # Subscribe to point cloud
    conn.datachannel.pub_sub.subscribe("rt/unitree/slam_mapping/points", points_cb)
    
    print("✅ Subscribed to status topics\n")
    print("⏳ Waiting 5s to see current SLAM state...")
    await asyncio.sleep(5)
    
    # Now start SLAM
    print("\n🗺️  Starting SLAM mapping...")
    slam_request = {
        "header": {
            "identity": {
                "id": 0,
                "api_id": 1801  # START_MAPPING
            }
        }
    }
    
    conn.datachannel.pub_sub.publish_without_callback(
        "rt/api/slam_operate/request",
        json.dumps(slam_request)
    )
    
    print("✅ SLAM start command sent")
    print("⏳ Monitoring SLAM status for 30 seconds...\n")
    
    for i in range(30):
        await asyncio.sleep(1)
        if points_received > 0 and i % 5 == 0:
            print(f"   {points_received} point clouds received...")
    
    print("\n" + "="*70)
    print(f"📊 RESULTS:")
    print(f"   SLAM Info messages: {len(slam_info_received)}")
    print(f"   SLAM Key Info messages: {len(slam_key_info_received)}")
    print(f"   Point clouds: {points_received}")
    print("="*70)
    
    if len(slam_info_received) == 0 and len(slam_key_info_received) == 0:
        print("\n⚠️  NO SLAM status messages - topics may not be available via WebRTC")
    elif points_received == 0:
        print("\n⚠️  SLAM status received but NO point clouds")
        print("   This suggests a missing setup step or service requirement")

asyncio.run(main())
