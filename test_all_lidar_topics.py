#!/usr/bin/env python3
"""Test all possible LiDAR/point cloud topics"""
import asyncio
import sys
sys.path.insert(0, '/root/G1/go2_webrtc_connect')
from unitree_webrtc_connect.webrtc_driver import UnitreeWebRTCConnection, WebRTCConnectionMethod

topics_to_test = [
    # G1-specific (from G1 constants)
    "rt/utlidar/cloud_livox_mid360",
    "rt/utlidar/imu_livox_mid360",
    
    # SLAM point clouds (might only work during SLAM)
    "rt/uslam/frontend/cloud_world_ds",
    "rt/uslam/localization/cloud_world",
    
    # GO2 topics (might work on G1)
    "rt/utlidar/voxel_map",
    "rt/utlidar/voxel_map_compressed",
    "rt/utlidar/lidar_state",
    "rt/utlidar/robot_pose",
    
    # Other cloud topics
    "rt/pctoimage_local",
    "rt/uslam/cloud_map",
]

received = {}

async def main():
    conn = UnitreeWebRTCConnection(WebRTCConnectionMethod.LocalSTA, ip="192.168.86.18")
    await conn.connect()
    print("✅ Connected\n")
    
    # Subscribe to all topics
    for topic in topics_to_test:
        received[topic] = 0
        def make_callback(t):
            def cb(m):
                received[t] += 1
                if received[t] == 1:
                    print(f"🎯 FIRST MESSAGE on {t}!")
            return cb
        conn.datachannel.pub_sub.subscribe(topic, make_callback(topic))
        print(f"📡 Subscribed to {topic}")
    
    print(f"\n⏳ Listening for 15 seconds...\n")
    await asyncio.sleep(15)
    
    print("\n" + "="*70)
    print("📊 RESULTS:")
    print("="*70)
    for topic in topics_to_test:
        count = received[topic]
        status = "✅" if count > 0 else "❌"
        print(f"{status} {topic:<50} {count:>5} msgs")
    
    total = sum(received.values())
    print("="*70)
    print(f"Total: {total} messages across all topics")

asyncio.run(main())
