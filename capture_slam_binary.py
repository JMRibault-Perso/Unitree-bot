#!/usr/bin/env python3
"""
Capture raw SLAM binary by intercepting at WebRTC message level
"""

import asyncio
import sys
import struct

sys.path.insert(0, '/root/G1/go2_webrtc_connect')

from unitree_webrtc_connect.webrtc_driver import UnitreeWebRTCConnection
from unitree_webrtc_connect.constants import WebRTCConnectionMethod
import json

ROBOT_IP = "192.168.86.8"
ROBOT_SN = "E21D1000PAHBMB06"

captured_buffers = []

async def capture_raw_lidar():
    """Capture raw binary at WebRTC datachannel level"""
    
    conn = UnitreeWebRTCConnection(
        WebRTCConnectionMethod.LocalSTA,
        ip=ROBOT_IP,
        serialNumber=ROBOT_SN
    )
    
    try:
        print(f"🔌 Connecting to {ROBOT_IP}...")
        await conn.connect()
        print("✅ Connected!")
        
        # NOW monkey patch the datachannel on_message to capture raw buffers
        original_on_message = conn.datachannel.on_message
        
        def capturing_on_message(message):
            """Intercept messages before they reach the decoder"""
            if isinstance(message, bytes):
                # Check if it's a lidar message (header [2, 0])
                if len(message) >= 8:
                    header = list(message[:8])
                    if header[:2] == [2, 0]:  # LiDAR binary header
                        # Save the buffer (skip 4-byte header)
                        buffer = message[4:]
                        captured_buffers.append(buffer)
                        print(f"✅ Captured LiDAR buffer: {len(buffer)} bytes")
                        
                        if len(captured_buffers) == 1:
                            # Analyze first buffer immediately
                            print(f"\n📊 First buffer analysis:")
                            print(f"   Total bytes: {len(buffer)}")
                            print(f"   First 100 bytes (hex): {buffer[:100].hex()[:160]}")
                            
                            # Try parsing as float32 array
                            num_floats = len(buffer) // 4
                            num_points = num_floats // 3
                            print(f"   Possible points (as float32 XYZ): {num_points}")
                            
                            # Parse first 10 points
                            for i in range(min(10, num_points)):
                                offset = i * 12
                                try:
                                    x, y, z = struct.unpack('<fff', buffer[offset:offset+12])
                                    print(f"      Point {i}: [{x:8.3f}, {y:8.3f}, {z:8.3f}]")
                                except:
                                    print(f"      Point {i}: Parse error")
                                    break
                            
                            # Save to file
                            with open('/tmp/slam_raw.bin', 'wb') as f:
                                f.write(buffer)
                            print(f"\n💾 Saved to /tmp/slam_raw.bin")
            
            # Call original handler
            return original_on_message(message)
        
        conn.datachannel.on_message = capturing_on_message
        
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
        
        print("⏳ Capturing for 10 seconds...")
        await asyncio.sleep(10)
        
        print(f"\n{'='*60}")
        print(f"📊 CAPTURE COMPLETE")
        print(f"{'='*60}")
        print(f"Total buffers captured: {len(captured_buffers)}")
        
        if captured_buffers:
            # Detailed analysis of first buffer
            buf = captured_buffers[0]
            num_floats = len(buf) // 4
            num_points = num_floats // 3
            
            # Parse all points
            points = []
            for i in range(num_points):
                offset = i * 12
                try:
                    x, y, z = struct.unpack('<fff', buf[offset:offset+12])
                    points.append([x, y, z])
                except:
                    break
            
            print(f"\n✅ Successfully parsed: {len(points)} points from {len(buf)} bytes")
            
            if points:
                xs = [p[0] for p in points]
                ys = [p[1] for p in points]
                zs = [p[2] for p in points]
                
                print(f"\n📐 Point cloud bounds:")
                print(f"   X: [{min(xs):7.3f} to {max(xs):7.3f}] (range: {max(xs)-min(xs):.2f}m)")
                print(f"   Y: [{min(ys):7.3f} to {max(ys):7.3f}] (range: {max(ys)-min(ys):.2f}m)")
                print(f"   Z: [{min(zs):7.3f} to {max(zs):7.3f}] (range: {max(zs)-min(zs):.2f}m)")
                
                # Validate
                if abs(max(xs)) < 50 and abs(max(ys)) < 50 and abs(max(zs)) < 50:
                    print(f"\n🎉 SUCCESS! Data looks like valid 3D point cloud coordinates!")
                    print(f"   Point cloud volume: {max(xs)-min(xs):.2f}m × {max(ys)-min(ys):.2f}m × {max(zs)-min(zs):.2f}m")
                else:
                    print(f"\n⚠️  Values seem unusually large - may need different parsing")
        
        # Stop SLAM
        print(f"\n🛑 Stopping SLAM...")
        stop_payload = {
            "api_id": 1802,
            "parameter": json.dumps({"data": {"address": "/home/unitree/test.pcd"}})
        }
        await conn.datachannel.pub_sub.publish_request_new(
            "rt/api/slam_operate/request",
            stop_payload
        )
        
        await asyncio.sleep(1)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(capture_raw_lidar())
