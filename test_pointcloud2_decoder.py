#!/usr/bin/env python3
"""
Test PointCloud2 decoder with saved binary data from /tmp/slam_raw.bin
"""

import sys
import struct
import json
import logging

sys.path.insert(0, '.')
from g1_app.patches.pointcloud2_decoder import PointCloud2Decoder

logging.basicConfig(level=logging.DEBUG, format='%(levelname)s: %(message)s')

# Load saved binary data
with open('/tmp/slam_raw.bin', 'rb') as f:
    data = f.read()

print("=" * 70)
print("Testing PointCloud2 Decoder with Saved G1 SLAM Data")
print("=" * 70)
print()

# Parse header
json_len = struct.unpack('<I', data[0:4])[0]
binary_len = struct.unpack('<I', data[4:8])[0]

print(f"File size: {len(data)} bytes")
print(f"JSON length: {json_len} bytes")
print(f"Binary length: {binary_len} bytes")
print()

# Parse JSON
json_str = data[8:8+json_len].decode('utf-8')
metadata = json.loads(json_str)

print("Metadata:")
print(json.dumps(metadata, indent=2))
print()

# Extract binary data
binary_data = data[8+json_len:]
print(f"Binary data size: {len(binary_data)} bytes")
print(f"First 64 bytes (hex): {binary_data[:64].hex()}")
print()

# Test decoder
print("-" * 70)
print("Testing PointCloud2 Decoder")
print("-" * 70)

decoder = PointCloud2Decoder()
result = decoder.decode(binary_data, metadata.get('data', {}))

print()
print("=" * 70)
print("DECODER RESULT:")
print("=" * 70)
print(f"Point count: {result.get('point_count', 0)}")
print(f"Format: {result.get('format', 'unknown')}")

if 'points' in result and len(result['points']) > 0:
    points = result['points']
    print(f"Points shape: {points.shape}")
    print(f"Point range:")
    print(f"  X: [{points[:,0].min():.3f}, {points[:,0].max():.3f}]")
    print(f"  Y: [{points[:,1].min():.3f}, {points[:,1].max():.3f}]")
    print(f"  Z: [{points[:,2].min():.3f}, {points[:,2].max():.3f}]")
    print()
    print(f"First 5 points:")
    for i in range(min(5, len(points))):
        print(f"  {i}: [{points[i,0]:.3f}, {points[i,1]:.3f}, {points[i,2]:.3f}]")
    
    if 'intensities' in result:
        intensities = result['intensities']
        print(f"\nIntensity range: [{intensities.min():.3f}, {intensities.max():.3f}]")

print()
print("=" * 70)
