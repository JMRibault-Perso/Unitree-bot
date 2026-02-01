#!/usr/bin/env python3
"""
Debug the LibVoxel decoder to see what's happening with G1 SLAM point clouds.
"""
import asyncio
import sys
import time
import struct
import json
import math

sys.path.insert(0, '/root/G1/unitree_sdk2')
from g1_app.patches import lidar_decoder_patch

sys.path.insert(0, '/root/G1/go2_webrtc_connect')
from unitree_webrtc_connect.webrtc_driver import UnitreeWebRTCConnection, WebRTCConnectionMethod

robot_ip = "192.168.86.8"
message_count = 0
conn = None

async def main():
    global message_count, conn
    
    print("🔌 Connecting to robot...")
    conn = UnitreeWebRTCConnection(WebRTCConnectionMethod.LocalSTA, ip=robot_ip)
    await conn.connect()
    await asyncio.sleep(2)
    
    print("🗺️  Starting SLAM mapping...")
    await conn.datachannel.pub_sub.publish_request_new(
        "rt/api/slam_operate/request",
        {
            "api_id": 1801,
            "parameter": json.dumps({"data": {"slam_type": "indoor"}})
        }
    )
    await asyncio.sleep(2)
    
    def on_point_cloud(data):
        global message_count
        message_count += 1
        
        if data['topic'] != 'rt/unitree/slam_mapping/points':
            return
        
        if message_count > 3:  # Only process first 3 messages
            return
            
        buffer = bytes(data['data'])
        
        # Parse header
        json_len = struct.unpack('<I', buffer[0:4])[0]
        binary_len = struct.unpack('<I', buffer[4:8])[0]
        
        # Extract JSON metadata
        json_str = buffer[8:8+json_len].decode('utf-8')
        metadata = json.loads(json_str)
        
        # Extract binary
        binary_data = buffer[8+json_len:]
        
        print(f"\n{'='*60}")
        print(f"MESSAGE #{message_count}")
        print(f"{'='*60}")
        print(f"Total size: {len(buffer)} bytes")
        print(f"JSON length: {json_len}")
        print(f"Binary length: {binary_len}")
        print(f"\nG1 Complete Message:")
        print(json.dumps(metadata, indent=2))
        
        data_dict = metadata.get('data', {})
        
        # Check if there's ALREADY origin/resolution in the metadata
        if 'origin' in data_dict and 'resolution' in data_dict:
            print(f"\n🎯 FOUND DIRECT origin/resolution in G1 metadata!")
            print(f"   origin: {data_dict['origin']}")
            print(f"   resolution: {data_dict['resolution']}")
            go2_metadata = {
                'origin': data_dict['origin'],
                'resolution': data_dict['resolution'],
                'frame_id': data_dict.get('header', {}).get('frame_id', 'map')
            }
        else:
            print(f"\n🔧 Converting bounding box to origin/resolution...")
        
        # Convert to GO2 format (like our patch does)
        origin_x = data_dict.get('xmin', 0.0)
        origin_y = data_dict.get('ymin', 0.0)
        origin_z = data_dict.get('zmin', 0.0)
        
        range_x = data_dict.get('xmax', 0.0) - origin_x
        range_y = data_dict.get('ymax', 0.0) - origin_y
        range_z = data_dict.get('zmax', 0.0) - origin_z
        
        resolution = max(range_x, range_y, range_z) / 128.0
        
        go2_metadata = {
            'origin': [origin_x, origin_y, origin_z],
            'resolution': resolution,
            'frame_id': data_dict.get('header', {}).get('frame_id', 'map')
        }
        
        print(f"\nConverted GO2 Metadata:")
        print(json.dumps(go2_metadata, indent=2))
        
        # Calculate the Z-parameter that LibVoxel uses
        z_param = math.floor(origin_z / resolution) if resolution > 0 else 0
        print(f"\nLibVoxel Z-parameter: {z_param}")
        print(f"  origin[2] = {origin_z:.6f}")
        print(f"  resolution = {resolution:.6f}")
        print(f"  origin[2]/resolution = {origin_z/resolution if resolution > 0 else 'DIV_BY_ZERO'}")
        
        # Try to decode
        print(f"\n🔧 Calling LibVoxel decoder...")
        try:
            from unitree_webrtc_connect.lidar.lidar_decoder_libvoxel import LidarDecoder
            decoder = LidarDecoder()
            result = decoder.decode(binary_data, go2_metadata)
            
            print(f"✅ SUCCESS!")
            print(f"  point_count: {result.get('point_count', 0)}")
            print(f"  face_count: {result.get('face_count', 0)}")
            print(f"  positions shape: {result.get('positions', []).shape if hasattr(result.get('positions', []), 'shape') else 'N/A'}")
            print(f"  uvs shape: {result.get('uvs', []).shape if hasattr(result.get('uvs', []), 'shape') else 'N/A'}")
            print(f"  indices shape: {result.get('indices', []).shape if hasattr(result.get('indices', []), 'shape') else 'N/A'}")
            
            if message_count >= 3:
                print(f"\n✅ Processed 3 messages successfully!")
                import sys
                sys.exit(0)
                
        except Exception as e:
            print(f"❌ DECODER ERROR: {e}")
            import traceback
            traceback.print_exc()
    
    print("📡 Subscribing to point cloud topic...")
    conn.datachannel.pub_sub.subscribe(
        'rt/unitree/slam_mapping/points',
        on_point_cloud
    )
    
    print("⏳ Waiting for point cloud data (20 seconds)...")
    await asyncio.sleep(20)
    
    if message_count == 0:
        print("❌ No messages received!")
    else:
        print(f"\n✅ Received {message_count} messages total")

if __name__ == "__main__":
    asyncio.run(main())
