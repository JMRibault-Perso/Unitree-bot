#!/usr/bin/env python3
"""
Test SLAM point cloud visualization with patched decoder
Verifies:
1. Decoder patch bypasses LibVoxel error
2. Binary point cloud data flows to LiDAR handler
3. Points parsed and available via API
"""

import asyncio
import sys
import os

sys.path.insert(0, '/root/G1/go2_webrtc_connect')
sys.path.insert(0, '/root/G1/unitree_sdk2')

# Import patches FIRST (before WebRTC classes)
from g1_app.patches import lidar_decoder_patch

from unitree_webrtc_connect.webrtc_driver import UnitreeWebRTCConnection
from unitree_webrtc_connect.constants import WebRTCConnectionMethod
from g1_app.core.lidar_handler import LiDARPointCloudHandler
import json
import struct

ROBOT_IP = "192.168.86.8"
ROBOT_SN = "E21D1000PAHBMB06"

async def test_point_cloud_flow():
    """Test end-to-end point cloud data flow"""
    print("🔧 Testing SLAM point cloud with patched decoder...")
    
    # Create LiDAR handler
    lidar_handler = LiDARPointCloudHandler()
    
    point_cloud_count = [0]
    total_points = [0]
    
    def on_point_cloud_update(binary_data: bytes, metadata: dict):
        """Callback when point cloud data arrives"""
        point_cloud_count[0] += 1
        
        # Parse points
        try:
            num_floats = len(binary_data) // 4
            if num_floats % 3 != 0:
                num_floats = (num_floats // 3) * 3
            
            points = []
            for i in range(0, num_floats, 3):
                offset = i * 4
                x, y, z = struct.unpack('<fff', binary_data[offset:offset+12])
                points.append([x, y, z])
            
            total_points[0] = len(points)
            
            if point_cloud_count[0] % 10 == 0:  # Log every 10th update
                print(f"📊 Point Cloud #{point_cloud_count[0]}: {len(points)} points, "
                      f"{len(binary_data)} bytes, metadata keys: {list(metadata.keys())}")
                
                # Show sample points
                if points:
                    sample = points[:3]
                    print(f"   Sample points: {sample}")
                    
        except Exception as e:
            print(f"❌ Error parsing point cloud: {e}")
    
    lidar_handler.subscribe(on_point_cloud_update)
    
    # Connect to robot
    conn = UnitreeWebRTCConnection(
        WebRTCConnectionMethod.LocalSTA,
        ip=ROBOT_IP,
        serialNumber=ROBOT_SN
    )
    
    try:
        print(f"🔌 Connecting to {ROBOT_IP}...")
        await conn.connect()
        print("✅ Connected!")
        
        # Enable LibVoxel decoder (with patch)
        conn.datachannel.set_decoder(decoder_type='libvoxel')
        print("✅ LibVoxel decoder enabled (patched)")
        
        # Subscribe to point cloud topic
        def on_slam_point_cloud(data: dict):
            """Handle patched point cloud data"""
            try:
                if isinstance(data, dict) and data.get('type') == 'lidar_pointcloud':
                    binary_data = data.get('binary_data')
                    metadata = data.get('metadata', {})
                    
                    if binary_data:
                        # Pass to handler
                        lidar_handler.set_raw_point_cloud(binary_data, metadata)
                else:
                    print(f"⚠️  Unexpected data format: {type(data)}")
                    if isinstance(data, dict):
                        print(f"   Keys: {list(data.keys())}")
            except Exception as e:
                print(f"❌ Error in callback: {e}")
                import traceback
                traceback.print_exc()
        
        conn.datachannel.pub_sub.subscribe("rt/unitree/slam_mapping/points", on_slam_point_cloud)
        print("📡 Subscribed to rt/unitree/slam_mapping/points")
        
        # Start SLAM mapping
        print("🗺️  Starting SLAM mapping...")
        slam_payload = {
            "api_id": 1801,
            "parameter": json.dumps({"data": {"slam_type": "indoor"}})
        }
        
        await conn.datachannel.pub_sub.publish_request_new(
            "rt/api/slam_operate/request",
            slam_payload
        )
        
        print("⏳ Waiting for point cloud data (20 seconds)...")
        print("   Decoder should NOT crash with KeyError...")
        
        await asyncio.sleep(20)
        
        # Report results
        print("\n" + "="*60)
        print("📊 TEST RESULTS:")
        print("="*60)
        print(f"✅ Point cloud messages received: {point_cloud_count[0]}")
        print(f"✅ Latest point count: {total_points[0]:,}")
        print(f"✅ LiDAR handler stats: {lidar_handler.get_stats()}")
        
        if point_cloud_count[0] > 0:
            print("\n🎉 SUCCESS: Point cloud data flowing without decoder crash!")
        else:
            print("\n⚠️  WARNING: No point cloud data received")
            print("   Make sure SLAM mapping started successfully")
        
        # Stop mapping
        print("\n🛑 Stopping SLAM mapping...")
        stop_payload = {
            "api_id": 1802,
            "parameter": json.dumps({"data": {"address": "/home/unitree/test_map.pcd"}})
        }
        await conn.datachannel.pub_sub.publish_request_new(
            "rt/api/slam_operate/request",
            stop_payload
        )
        
        await asyncio.sleep(2)
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("🔌 Disconnecting...")
        await conn.close()
        print("✅ Disconnected")


if __name__ == "__main__":
    asyncio.run(test_point_cloud_flow())
