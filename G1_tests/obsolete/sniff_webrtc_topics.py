#!/usr/bin/env python3
"""
Sniff WebRTC datachannel to find point cloud topic.
Listens to ALL messages and prints which topics arrive.
"""
import asyncio
import sys
import os
import json

# Setup WebRTC path
sys.path.insert(0, '/root/G1/go2_webrtc_connect')

from unitree_webrtc_connect.webrtc_driver import UnitreeWebRTCConnection
from unitree_webrtc_connect.constants import WebRTCConnectionMethod

# Track what topics we've seen
topics_seen = {}

async def main():
    robot_ip = sys.argv[1] if len(sys.argv) > 1 else "192.168.86.3"
    print(f"🎯 Connecting to {robot_ip}...")
    print("   This will print every topic that publishes data\n")
    
    conn = UnitreeWebRTCConnection(
        WebRTCConnectionMethod.LocalSTA,
        ip=robot_ip
    )
    
    try:
        await conn.connect()
        print("✅ Connected!\n")
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        print("   Is the robot online?")
        return
    
    await conn.datachannel.disableTrafficSaving(True)
    
    # Create a generic callback that tracks ALL topics
    def make_listener(topic_name):
        def callback(msg):
            if topic_name not in topics_seen:
                topics_seen[topic_name] = 0
                print(f"🎯 NEW TOPIC: {topic_name}")
                print(f"   Type: {type(msg).__name__}")
                if isinstance(msg, dict) and 'data' in msg:
                    data_size = len(msg['data']) if isinstance(msg['data'], (bytes, bytearray)) else "?"
                    print(f"   Data size: {data_size} bytes\n")
            
            topics_seen[topic_name] += 1
        
        return callback
    
    # List of topics to listen for (from your existing tests)
    candidate_topics = [
        # SLAM point cloud (from mapping)
        "rt/unitree/slam_mapping/points",
        "rt/unitree/slam_mapping/odom",
        "rt/unitree/slam_relocation/points",
        "rt/unitree/slam_relocation/odom",
        "rt/unitree/slam_relocation/global_map",
        
        # SLAM status
        "rt/slam_info",
        "rt/slam_key_info",
        
        # LiDAR raw
        "rt/utlidar/cloud_livox_mid360",
        "rt/utlidar/imu_livox_mid360",
        "rt/utlidar/voxel_map",
        "rt/utlidar/voxel_map_compressed",
        "rt/utlidar/lidar_state",
        "rt/utlidar/robot_pose",
        
        # Alternative names
        "rt/lidar/cloud",
        "rt/lf/utlidar/cloud_livox_mid360",
        "rt/hf/utlidar/cloud_livox_mid360",
        
        # Possible alternatives
        "rt/slam/pointcloud",
        "rt/slam/cloud",
        "rt/pointcloud",
        "rt/point_cloud",
        "rt/cloud",
        "rt/map",
        "rt/voxel",
        
        # State topics that might come with SLAM
        "rt/lowstate",
        "rt/lf/lowstate",
        "rt/hf/lowstate",
        "rt/sportmodestate",
    ]
    
    print(f"📡 Subscribing to {len(candidate_topics)} candidate topics...\n")
    
    for topic in candidate_topics:
        try:
            conn.datachannel.pub_sub.subscribe(topic, make_listener(topic))
        except Exception as e:
            pass  # Silent fail
    
    print("⏳ Listening for 30 seconds...")
    print("   (Move the robot around to generate data)\n")
    print("="*70)
    
    try:
        for i in range(30):
            await asyncio.sleep(1)
            if i % 10 == 0 and i > 0:
                active = sum(1 for v in topics_seen.values() if v > 0)
                print(f"   {i}s: {active} topics active so far")
    except KeyboardInterrupt:
        print("\n✋ Stopped by user")
    
    print("="*70)
    print("\n📊 RESULTS:\n")
    
    # Sort by activity
    sorted_topics = sorted(topics_seen.items(), key=lambda x: x[1], reverse=True)
    
    if any(count > 0 for _, count in sorted_topics):
        print("✅ ACTIVE TOPICS (received data):\n")
        for topic, count in sorted_topics:
            if count > 0:
                print(f"   {topic:<50} {count:>6} messages")
                
                # Highlight point cloud topics
                if 'point' in topic.lower() or 'cloud' in topic.lower() or 'slam' in topic.lower():
                    print(f"   {'>>> POINT CLOUD TOPIC <<<':<50}")
    else:
        print("❌ NO ACTIVE TOPICS!\n")
        print("   Possible issues:")
        print("   - Robot WebRTC not responding")
        print("   - Topics have different names")
        print("   - Need to enable SLAM first")
    
    print(f"\n   Total: {sum(1 for v in topics_seen.values() if v > 0)} active topics")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n✋ Interrupted")
