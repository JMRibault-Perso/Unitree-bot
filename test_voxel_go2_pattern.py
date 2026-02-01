#!/usr/bin/env python3
"""
Test LiDAR voxel reception using exact GO2 pattern.
Based on: go2_webrtc_connect/examples/go2/data_channel/lidar/lidar_stream.py
"""

import asyncio
import logging
import sys

sys.path.insert(0, '/root/G1/go2_webrtc_connect')
from unitree_webrtc_connect.webrtc_driver import UnitreeWebRTCConnection, WebRTCConnectionMethod

logging.basicConfig(level=logging.INFO)

message_count = 0

async def main():
    try:
        # Connect to G1 Air robot
        conn = UnitreeWebRTCConnection(WebRTCConnectionMethod.LocalSTA, ip="192.168.86.18")
        
        print("[1/6] Connecting to robot...")
        await conn.connect()
        print("✅ Connected!")
        
        print("[2/6] Disabling traffic saving...")
        await conn.datachannel.disableTrafficSaving(True)
        print("✅ Traffic saving disabled!")
        
        print("[3/6] Setting LibVoxel decoder...")
        conn.datachannel.set_decoder(decoder_type='libvoxel')
        print("✅ LibVoxel decoder set!")
        
        print("[4/6] G1 doesn't need LiDAR switch - it's always ready")
        print("✅ Ready!")
        
        def lidar_callback(message):
            global message_count
            message_count += 1
            print(f"\n🎯 LIDAR MESSAGE #{message_count}")
            print(f"   Type: {type(message)}")
            print(f"   Keys: {message.keys() if isinstance(message, dict) else 'N/A'}")
            if isinstance(message, dict) and "data" in message:
                data = message["data"]
                print(f"   Data type: {type(data)}")
                print(f"   Data length: {len(data) if hasattr(data, '__len__') else 'N/A'}")
                if hasattr(data, 'keys'):
                    print(f"   Data keys: {data.keys()}")
                else:
                    # Try to show first 100 bytes if binary
                    try:
                        print(f"   Data preview: {str(data)[:200]}")
                    except:
                        pass
        
        print("[5/6] Subscribing to rt/utlidar/cloud_livox_mid360 (G1-specific)...")
        conn.datachannel.pub_sub.subscribe("rt/utlidar/cloud_livox_mid360", lidar_callback)
        print("✅ Subscribed!")
        
        print("[6/6] Listening for point cloud data (30s)...")
        await asyncio.sleep(30)
        
        print(f"\n📊 FINAL RESULT: {message_count} point cloud messages received")
        
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
