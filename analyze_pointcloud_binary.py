#!/usr/bin/env python3
"""
Analyze raw SLAM point cloud binary data - skip JSON parsing
"""

import asyncio
import sys
import struct

sys.path.insert(0, '/root/G1/go2_webrtc_connect')
sys.path.insert(0, '/root/G1/unitree_sdk2')

from unitree_webrtc_connect.webrtc_driver import UnitreeWebRTCConnection
from unitree_webrtc_connect.constants import WebRTCConnectionMethod
import json

ROBOT_IP = "192.168.86.8"
ROBOT_SN = "E21D1000PAHBMB06"

captured_samples = []

async def analyze_raw_binary():
    """Capture raw binary and analyze structure"""
    print("🔍 Analyzing SLAM point cloud binary format...")
    
    conn = UnitreeWebRTCConnection(
        WebRTCConnectionMethod.LocalSTA,
        ip=ROBOT_IP,
        serialNumber=ROBOT_SN
    )
    
    try:
        print(f"🔌 Connecting to {ROBOT_IP}...")
        await conn.connect()
        print("✅ Connected!")
        
        def on_raw_binary(msg):
            """Capture raw binary messages"""
            if isinstance(msg, bytes):
                captured_samples.append(msg)
                print(f"📦 Captured binary: {len(msg)} bytes")
                
                if len(captured_samples) <= 3:
                    # Show first 100 bytes as hex
                    hex_preview = msg[:100].hex()
                    print(f"   First 100 bytes: {hex_preview[:80]}...")
                    
                    # Try parsing as float32 array
                    num_floats = len(msg) // 4
                    print(f"   Could contain {num_floats} floats ({num_floats // 3} XYZ points)")
                    
                    # Parse first 10 points
                    try:
                        points = []
                        for i in range(min(10, num_floats // 3)):
                            offset = i * 12
                            x, y, z = struct.unpack('<fff', msg[offset:offset+12])
                            points.append([x, y, z])
                        
                        print(f"   First 10 points (as float32 XYZ):")
                        for idx, (x, y, z) in enumerate(points):
                            print(f"      {idx}: [{x:8.3f}, {y:8.3f}, {z:8.3f}]")
                    except Exception as e:
                        print(f"   Could not parse as XYZ: {e}")
        
        # Subscribe to point cloud topic
        conn.datachannel.pub_sub.subscribe("rt/unitree/slam_mapping/points", on_raw_binary)
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
        
        print("⏳ Collecting 5 samples (10 seconds)...")
        await asyncio.sleep(10)
        
        # Analysis
        print("\n" + "="*60)
        print("📊 ANALYSIS RESULTS:")
        print("="*60)
        print(f"Total samples captured: {len(captured_samples)}")
        
        if captured_samples:
            sizes = [len(s) for s in captured_samples]
            print(f"Message sizes: min={min(sizes)}, max={max(sizes)}, avg={sum(sizes)//len(sizes)}")
            
            # Analyze first sample in detail
            sample = captured_samples[0]
            print(f"\n🔬 Detailed analysis of first sample ({len(sample)} bytes):")
            
            # Try as pure float32 array
            num_floats = len(sample) // 4
            num_points = num_floats // 3
            print(f"   Total floats: {num_floats}")
            print(f"   Total XYZ points: {num_points}")
            
            # Parse all points
            all_points = []
            for i in range(num_points):
                offset = i * 12
                try:
                    x, y, z = struct.unpack('<fff', sample[offset:offset+12])
                    all_points.append([x, y, z])
                except:
                    break
            
            print(f"   Successfully parsed: {len(all_points)} points")
            
            # Statistics
            if all_points:
                xs = [p[0] for p in all_points]
                ys = [p[1] for p in all_points]
                zs = [p[2] for p in all_points]
                
                print(f"\n   Point cloud bounds:")
                print(f"      X: [{min(xs):7.3f} to {max(xs):7.3f}]")
                print(f"      Y: [{min(ys):7.3f} to {max(ys):7.3f}]")
                print(f"      Z: [{min(zs):7.3f} to {max(zs):7.3f}]")
                
                # Check if reasonable point cloud data
                if abs(max(xs)) < 100 and abs(max(ys)) < 100 and abs(max(zs)) < 100:
                    print(f"\n   ✅ Data looks like valid 3D coordinates!")
                    print(f"   📐 Point cloud spans:")
                    print(f"      {max(xs)-min(xs):.2f}m × {max(ys)-min(ys):.2f}m × {max(zs)-min(zs):.2f}m")
                else:
                    print(f"\n   ⚠️  Values seem too large - may not be XYZ coordinates")
            
            # Save first sample to file
            with open('/tmp/slam_pointcloud_sample.bin', 'wb') as f:
                f.write(sample)
            print(f"\n💾 Saved first sample to /tmp/slam_pointcloud_sample.bin")
        
        # Stop mapping
        print("\n🛑 Stopping SLAM...")
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
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("🔌 Disconnecting...")


if __name__ == "__main__":
    asyncio.run(analyze_raw_binary())
