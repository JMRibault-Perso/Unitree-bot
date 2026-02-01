#!/usr/bin/env python3
"""
Test SLAM-specific point cloud topics that only publish during mapping/relocation.
Based on official Unitree SLAM documentation.
"""
import asyncio
import sys
import json
sys.path.insert(0, '/root/G1/go2_webrtc_connect')
from unitree_webrtc_connect.webrtc_driver import UnitreeWebRTCConnection, WebRTCConnectionMethod

topics_received = {
    "rt/unitree/slam_mapping/points": 0,
    "rt/unitree/slam_mapping/odom": 0,
    "rt/unitree/slam_relocation/points": 0,
    "rt/unitree/slam_relocation/odom": 0,
    "rt/unitree/slam_relocation/global_map": 0,
}

async def main():
    conn = UnitreeWebRTCConnection(WebRTCConnectionMethod.LocalSTA, ip="192.168.86.8")
    await conn.connect()
    print("✅ Connected\n")
    
    await conn.datachannel.disableTrafficSaving(True)
    
    # Subscribe to all SLAM topics
    for topic in topics_received.keys():
        def make_callback(t):
            def cb(m):
                topics_received[t] += 1
                if topics_received[t] == 1:
                    print(f"\n🎯 FIRST DATA on {t}!")
                    print(f"   Type: {type(m).__name__}")
                    if isinstance(m, dict) and 'data' in m:
                        data = m['data']
                        print(f"   Data type: {type(data).__name__}")
                        if hasattr(data, '__len__'):
                            print(f"   Data size: {len(data)} bytes")
            return cb
        conn.datachannel.pub_sub.subscribe(topic, make_callback(topic))
        print(f"📡 Subscribed to {topic}")
    
    # Start SLAM mapping to trigger point cloud publishing
    print("\n🗺️  Starting SLAM mapping...")
    
    def slam_response_cb(resp):
        print(f"\n📨 SLAM Response: {resp}")
    
    conn.datachannel.pub_sub.subscribe("rt/api/slam_operate/response", slam_response_cb)
    
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
    print("✅ SLAM start command sent!\n")
    
    print("⏳ Waiting 25 seconds for point cloud data...\n")
    
    for i in range(25):
        await asyncio.sleep(1)
        total = sum(topics_received.values())
        if total > 0 and i % 5 == 0:
            print(f"   {total} messages received so far...")
    
    # Stop SLAM
    print("\n🛑 Stopping SLAM...")
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
    
    print("\n" + "="*70)
    print("📊 FINAL RESULTS:")
    print("="*70)
    for topic, count in topics_received.items():
        status = "✅" if count > 0 else "❌"
        short_name = topic.replace("rt/unitree/slam_", "")
        print(f"{status} {short_name:<40} {count:>5} msgs")
    
    total = sum(topics_received.values())
    print("="*70)
    print(f"Total: {total} point cloud messages")
    
    if total > 0:
        print("\n🎉 SUCCESS! SLAM point clouds ARE available!")
    else:
        print("\n❌ No SLAM point clouds received")

asyncio.run(main())
