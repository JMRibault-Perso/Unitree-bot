#!/usr/bin/env python3
"""Quick test to verify if resolution=0.05 fix works"""
import sys
import asyncio
import json
import logging

# Apply decoder patch BEFORE any other imports
sys.path.insert(0, '.')
from g1_app.patches import lidar_decoder_patch

# Now import WebRTC
sys.path.insert(0, '/root/G1/go2_webrtc_connect')
from unitree_webrtc_connect.webrtc_driver import UnitreeWebRTCConnection, WebRTCConnectionMethod

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

async def main():
    print("=" * 60)
    print("Testing LibVoxel decoder with resolution=0.05 fix")
    print("=" * 60)
    
    conn = UnitreeWebRTCConnection(
        WebRTCConnectionMethod.LocalSTA,
        ip='192.168.86.8'
    )
    
    await conn.connect()
    print("✅ Connected to robot\n")
    
    # Start SLAM mapping
    result = await conn.datachannel.pub_sub.publish_request_new(
        'rt/api/slam_operate/request',
        {'api_id': 1801, 'parameter': json.dumps({'data': {'slam_type': 'indoor'}})}
    )
    print(f"📡 Started SLAM mapping: {result}\n")
    
    # Wait for point cloud data
    print("⏳ Waiting 15 seconds for point clouds to flow...")
    print("   Watch for '🎯 LibVoxel RESULT' messages below:")
    print("-" * 60)
    
    await asyncio.sleep(15)
    
    print("\n" + "=" * 60)
    print("Test complete. Check logs above for decoder results.")
    print("=" * 60)

if __name__ == '__main__':
    asyncio.run(main())
