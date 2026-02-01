#!/usr/bin/env python3
"""
Test SLAM point clouds during ACTIVE mapping.
Point clouds only publish while the robot is actually mapping, not just after START_MAPPING.
"""
import asyncio
import sys
import json

# Apply decoder patch FIRST (before importing WebRTC modules)
sys.path.insert(0, '/root/G1/unitree_sdk2')
from g1_app.patches import lidar_decoder_patch

sys.path.insert(0, '/root/G1/go2_webrtc_connect')
from unitree_webrtc_connect.webrtc_driver import UnitreeWebRTCConnection, WebRTCConnectionMethod

slam_info_count = 0
point_cloud_count = 0
odom_count = 0

async def main():
    global slam_info_count, point_cloud_count, odom_count
    
    conn = UnitreeWebRTCConnection(WebRTCConnectionMethod.LocalSTA, ip="192.168.86.8")
    await conn.connect()
    print("✅ Connected\n")
    
    await conn.datachannel.disableTrafficSaving(True)
    
    # Define callbacks first
    def slam_info_cb(msg):
        global slam_info_count
        slam_info_count += 1
        if isinstance(msg, dict) and 'data' in msg:
            try:
                data = json.loads(msg['data']) if isinstance(msg['data'], str) else msg['data']
                print(f"\n📊 SLAM INFO #{slam_info_count}: {data}")
            except:
                print(f"\n📊 SLAM INFO #{slam_info_count}: {msg['data']}")
    
    def points_cb(msg):
        global point_cloud_count
        point_cloud_count += 1
        if point_cloud_count == 1:
            print(f"\n🎯 FIRST POINT CLOUD RECEIVED!")
            print(f"   Message type: {type(msg)}")
        if point_cloud_count % 10 == 0:
            print(f"   {point_cloud_count} point clouds received...")
    
    def odom_cb(msg):
        global odom_count
        odom_count += 1
        if odom_count == 1:
            print(f"\n🎯 FIRST ODOMETRY RECEIVED!")
    
    def slam_response_cb(resp):
        print(f"📨 SLAM Response: {resp}\n")
    
    # Start SLAM mapping FIRST (using proper API request format)
    print("🗺️  Starting SLAM mapping...")
    
    map_name = "test_lidar_scan"
    
    # Subscribe to response BEFORE making request
    conn.datachannel.pub_sub.subscribe("rt/api/slam_operate/response", slam_response_cb)
    
    # Use publish_request_new() like the web controller does
    slam_payload = {
        "api_id": 1801,  # START_MAPPING
        "parameter": json.dumps({
            "data": {
                "slam_type": "indoor"
            }
        })
    }
    
    print(f"📝 Map will be saved as: /home/unitree/{map_name}.pcd\n")
    await conn.datachannel.pub_sub.publish_request_new(
        "rt/api/slam_operate/request",
        slam_payload
    )
    
    # Wait for SLAM to start
    print("⏳ Waiting for SLAM to start...")
    await asyncio.sleep(3)
    
    # NOW subscribe to point cloud topics AFTER mapping started
    print("📡 Subscribing to point cloud topics...")
    conn.datachannel.pub_sub.subscribe("rt/slam_info", slam_info_cb)
    conn.datachannel.pub_sub.subscribe("rt/unitree/slam_mapping/points", points_cb)
    conn.datachannel.pub_sub.subscribe("rt/unitree/slam_mapping/odom", odom_cb)
    print("✅ Subscribed to SLAM topics after mapping started!\n")
    
    print("\n" + "="*70)
    print("⚠️  Point clouds should now be streaming!")
    print("   - Robot can be stationary (you said voxels visible even when still)")
    print("   - Waiting 40 seconds for data...")
    print("="*70 + "\n")
    
    # Wait for point clouds
    for i in range(40):
        await asyncio.sleep(1)
        if i % 10 == 9:
            print(f"\n⏱️  {i+1}s elapsed:")
            print(f"   SLAM info: {slam_info_count} messages")
            print(f"   Point clouds: {point_cloud_count} messages")
            print(f"   Odometry: {odom_count} messages")
    
    print("\n" + "="*70)
    print("📊 FINAL RESULTS:")
    print("="*70)
    print(f"SLAM Info:     {slam_info_count} messages")
    print(f"Point Clouds:  {point_cloud_count} messages")
    print(f"Odometry:      {odom_count} messages")
    print("="*70)
    
    if point_cloud_count > 0:
        print("\n🎉 SUCCESS! Point clouds ARE available during mapping!")
        print(f"   Rate: ~{point_cloud_count/40:.1f} Hz")
    elif slam_info_count > 0:
        print("\n⚠️  SLAM is active but no point clouds yet")
        print("   Did you move the robot?")
    else:
        print("\n❌ No SLAM data received at all")
        print("   SLAM may not have started successfully")
    
    # Stop SLAM
    print("\n🛑 Stopping SLAM mapping and saving map...")
    end_mapping_request = {
        "header": {
            "identity": {
                "id": 0,
                "api_id": 1802  # END_MAPPING (saves the map)
            }
        },
        "data": {
            "address": f"/home/unitree/{map_name}.pcd"  # Full path as per API spec
        }
    }
    conn.datachannel.pub_sub.publish_without_callback(
        "rt/api/slam_operate/request",
        json.dumps(end_mapping_request)
    )
    await asyncio.sleep(2)
    print(f"✅ Map '{map_name}' saved!")
    
    # Close SLAM service
    print("🛑 Closing SLAM service...")
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
