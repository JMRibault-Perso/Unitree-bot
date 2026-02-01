#!/usr/bin/env python3
"""
Just LISTEN for point clouds - don't try to control SLAM.
Start mapping from the Android app, then run this script.
"""
import asyncio
import sys
import json
sys.path.insert(0, '/root/G1/go2_webrtc_connect')
from unitree_webrtc_connect.webrtc_driver import UnitreeWebRTCConnection, WebRTCConnectionMethod

point_cloud_count = 0
odom_count = 0
slam_info_count = 0

async def main():
    global point_cloud_count, odom_count, slam_info_count
    
    conn = UnitreeWebRTCConnection(WebRTCConnectionMethod.LocalSTA, ip="192.168.86.8")
    await conn.connect()
    print("✅ Connected\n")
    
    await conn.datachannel.disableTrafficSaving(True)
    
    # Monitor point clouds with detailed info
    def points_cb(msg):
        global point_cloud_count
        point_cloud_count += 1
        if point_cloud_count == 1:
            print(f"\n🎯 FIRST POINT CLOUD RECEIVED!")
            print(f"   Message type: {type(msg)}")
            print(f"   Message keys: {msg.keys() if isinstance(msg, dict) else 'N/A'}")
            if isinstance(msg, dict) and 'data' in msg:
                data = msg['data']
                print(f"   Data type: {type(data)}")
                print(f"   Data length: {len(data) if hasattr(data, '__len__') else 'N/A'}")
        if point_cloud_count % 10 == 0:
            print(f"   {point_cloud_count} point clouds received...")
    
    # Monitor odometry
    def odom_cb(msg):
        global odom_count
        odom_count += 1
        if odom_count == 1:
            print(f"\n🎯 FIRST ODOMETRY RECEIVED!")
    
    # Monitor SLAM info
    def slam_info_cb(msg):
        global slam_info_count
        slam_info_count += 1
        if slam_info_count == 1:
            print(f"\n📊 FIRST SLAM INFO RECEIVED!")
    
    # Subscribe to point cloud topics
    print("📡 Subscribing to point cloud topics...")
    conn.datachannel.pub_sub.subscribe("rt/unitree/slam_mapping/points", points_cb)
    conn.datachannel.pub_sub.subscribe("rt/unitree/slam_mapping/odom", odom_cb)
    conn.datachannel.pub_sub.subscribe("rt/slam_info", slam_info_cb)
    print("✅ Subscribed!\n")
    
    print("=" * 70)
    print("⚠️  INSTRUCTIONS:")
    print("   1. Open the Unitree Android app")
    print("   2. Go to SLAM/Mapping section")
    print("   3. Press 'Start Mapping'")
    print("   4. Watch this script for point cloud data")
    print("   5. Waiting 60 seconds for data...")
    print("=" * 70 + "\n")
    
    # Wait and monitor
    for i in range(60):
        await asyncio.sleep(1)
        if i % 15 == 14:
            print(f"\n⏱️  {i+1}s elapsed:")
            print(f"   SLAM info:    {slam_info_count} messages")
            print(f"   Point clouds: {point_cloud_count} messages")
            print(f"   Odometry:     {odom_count} messages")
    
    print("\n" + "=" * 70)
    print("📊 FINAL RESULTS:")
    print("=" * 70)
    print(f"SLAM Info:     {slam_info_count} messages")
    print(f"Point Clouds:  {point_cloud_count} messages")
    print(f"Odometry:      {odom_count} messages")
    print("=" * 70)
    
    if point_cloud_count > 0:
        print("\n🎉 SUCCESS! Point clouds ARE being broadcast!")
        print(f"   Rate: ~{point_cloud_count/60:.1f} Hz")
    else:
        print("\n❌ No point clouds received")
        print("   Did you start mapping in the Android app?")

asyncio.run(main())
