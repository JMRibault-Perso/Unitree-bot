#!/usr/bin/env python3
"""
Test script to verify LiDAR data is being published by the robot.
Based on the documentation: rt/utlidar/cloud_livox_mid360 topic at 10Hz.
"""

import asyncio
import sys
import time

# Add WebRTC library to path
sys.path.insert(0, '/root/G1/go2_webrtc_connect')
from unitree_webrtc_connect.webrtc_driver import UnitreeWebRTCConnection
from unitree_webrtc_connect.constants import WebRTCConnectionMethod

# Robot details
ROBOT_IP = "192.168.86.18"
ROBOT_SN = "E21D1000PAHBMB06"

LIDAR_TOPIC = "rt/utlidar/cloud_deskewed"  # Motion-compensated point cloud

message_count = 0
last_message_time = None

def lidar_callback(data: dict):
    """Handle LiDAR messages"""
    global message_count, last_message_time
    message_count += 1
    last_message_time = time.time()
    
    print(f"\n{'='*80}")
    print(f"📡 LIDAR MESSAGE #{message_count}")
    print(f"{'='*80}")
    print(f"Data type: {type(data)}")
    
    if isinstance(data, dict):
        print(f"\nTop-level keys: {list(data.keys())}")
        
        if 'data' in data:
            cloud_data = data['data']
            print(f"\nCloud data type: {type(cloud_data)}")
            if isinstance(cloud_data, dict):
                print(f"Cloud data keys (first 20): {list(cloud_data.keys())[:20]}")
                
                # Print important fields
                for key in ['width', 'height', 'point_step', 'row_step', 'is_dense', 'fields']:
                    if key in cloud_data:
                        value = cloud_data[key]
                        if isinstance(value, (list, bytes)) and len(value) > 100:
                            print(f"  {key}: {type(value).__name__} (length={len(value)})")
                        else:
                            print(f"  {key}: {value}")
                
                # Check data field
                if 'data' in cloud_data:
                    raw_data = cloud_data['data']
                    print(f"\n📊 Point cloud binary data:")
                    print(f"  Type: {type(raw_data)}")
                    print(f"  Length: {len(raw_data)} bytes")
                    
                    if len(raw_data) > 0:
                        # Calculate number of points
                        point_step = cloud_data.get('point_step', 16)
                        num_points = len(raw_data) // point_step
                        print(f"  Point step: {point_step} bytes")
                        print(f"  Estimated points: {num_points}")
                        
                        # Try parsing first point
                        if len(raw_data) >= point_step:
                            import struct
                            try:
                                # Common formats:
                                # - 16 bytes: x,y,z,intensity (4 floats)
                                # - 18 bytes: x,y,z,intensity,reflectivity,tag
                                if point_step == 16:
                                    x, y, z, i = struct.unpack('ffff', bytes(raw_data[0:16]))
                                    print(f"\n  First point (x,y,z,intensity):")
                                    print(f"    x={x:.3f}, y={y:.3f}, z={z:.3f}, intensity={i}")
                                else:
                                    print(f"\n  Point step is {point_step}, need custom parsing")
                            except Exception as e:
                                print(f"\n  Error parsing first point: {e}")
    else:
        print(f"Unexpected data structure: {data}")
    
    print(f"{'='*80}\n")


async def main():
    """Main test function"""
    print(f"🤖 Connecting to G1 at {ROBOT_IP}")
    print(f"   Serial: {ROBOT_SN}")
    print(f"   Topic: {LIDAR_TOPIC}")
    print(f"\n{'='*80}\n")
    
    try:
        # Connect to robot
        conn = UnitreeWebRTCConnection(
            WebRTCConnectionMethod.LocalSTA,
            ip=ROBOT_IP,
            serialNumber=ROBOT_SN
        )
        
        print("Establishing WebRTC connection...")
        await conn.connect()
        print("✅ Connected!\n")
        
        # G1 doesn't use rt/utlidar/switch - skip this
        # (LiDAR enabled via SLAM service instead)
        
        # Subscribe to LiDAR topic
        print(f"📡 Subscribing to {LIDAR_TOPIC}")
        conn.datachannel.pub_sub.subscribe(LIDAR_TOPIC, lidar_callback)
        print(f"✅ Subscribed!\n")
        
        print("Waiting for LiDAR messages...")
        print("(Press Ctrl+C to exit)\n")
        
        # Wait and report status
        start_time = time.time()
        while True:
            await asyncio.sleep(5)
            elapsed = time.time() - start_time
            
            if message_count == 0:
                print(f"⏳ Waiting... ({elapsed:.0f}s elapsed, no messages yet)")
                print(f"   Expected: 10 Hz (1 message every 100ms)")
                if elapsed > 30:
                    print(f"\n⚠️  WARNING: No LiDAR data after {elapsed:.0f}s")
                    print(f"   This may indicate:")
                    print(f"   - LiDAR sensor not installed on this G1 model")
                    print(f"   - Topic name is different")
                    print(f"   - LiDAR driver not running")
            else:
                since_last = time.time() - last_message_time
                rate = message_count / elapsed
                print(f"📊 Received {message_count} messages in {elapsed:.1f}s ({rate:.1f} Hz)")
                print(f"   Last message: {since_last:.1f}s ago")
    
    except KeyboardInterrupt:
        print("\n\n👋 Interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print(f"\n📊 Final stats: {message_count} messages received")
        if conn:
            await conn.disconnect()
            print("✅ Disconnected")


if __name__ == "__main__":
    asyncio.run(main())
