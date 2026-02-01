#!/usr/bin/env python3
"""
Test with LibVoxel decoder explicitly enabled + height_map_array
Based on documentation: need to close mobile app first
"""
import asyncio
import sys
sys.path.insert(0, '/root/G1/go2_webrtc_connect')
from unitree_webrtc_connect.webrtc_driver import UnitreeWebRTCConnection, WebRTCConnectionMethod

msg_count = 0

async def main():
    global msg_count
    conn = UnitreeWebRTCConnection(WebRTCConnectionMethod.LocalSTA, ip="192.168.86.18")
    await conn.connect()
    print("✅ Connected")
    
    # Disable traffic saving (enables high-bandwidth data)
    await conn.datachannel.disableTrafficSaving(True)
    print("✅ Traffic saving disabled")
    
    # Set LibVoxel decoder for voxel data
    conn.datachannel.set_decoder(decoder_type='libvoxel')
    print("✅ LibVoxel decoder enabled")
    
    def cb(m):
        global msg_count
        msg_count += 1
        print(f"\n🎯 VOXEL DATA #{msg_count}")
        print(f"   Type: {type(m).__name__}")
        if isinstance(m, dict):
            print(f"   Keys: {list(m.keys())}")
            if 'data' in m:
                data = m['data']
                print(f"   Data type: {type(data).__name__}")
                if hasattr(data, '__len__'):
                    print(f"   Data size: {len(data)}")
                if isinstance(data, dict):
                    print(f"   Data keys: {list(data.keys())}")
    
    # Try all possible voxel topics
    topics = [
        "rt/utlidar/height_map_array",
        "rt/utlidar/voxel_map_compressed",
        "rt/utlidar/voxel_map",
    ]
    
    for topic in topics:
        print(f"\n📡 Subscribing to {topic}...")
        conn.datachannel.pub_sub.subscribe(topic, cb)
    
    print("\n⏳ Waiting 20 seconds for voxel data...")
    print("   (Make sure Unitree Explorer App is CLOSED!)\n")
    
    await asyncio.sleep(20)
    print(f"\n📊 Final Result: {msg_count} voxel messages received")
    
    if msg_count == 0:
        print("\n⚠️  No voxel data received. Possible causes:")
        print("   1. Mobile app still connected (close it completely)")
        print("   2. G1 Air doesn't bridge LiDAR to WebRTC datachannel")
        print("   3. Need to start SLAM first to enable LiDAR publishing")

asyncio.run(main())
