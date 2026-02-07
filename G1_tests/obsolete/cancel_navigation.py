#!/usr/bin/env python3
"""Quick script to cancel/pause navigation"""

import sys
import asyncio
import json
sys.path.insert(0, '.')
from g1_app.utils.arp_discovery import discover_robot_ip
sys.path.insert(0, '/root/G1/go2_webrtc_connect')
from unitree_webrtc_connect.webrtc_driver import UnitreeWebRTCConnection, WebRTCConnectionMethod

async def main():
    # Discover robot
    robot_ip = discover_robot_ip()
    if not robot_ip:
        print("❌ Robot not found")
        return
    
    print(f"🔌 Connecting to {robot_ip}...")
    conn = UnitreeWebRTCConnection(WebRTCConnectionMethod.LocalSTA, ip=robot_ip)
    await conn.connect()
    print("✅ Connected!")
    await asyncio.sleep(2)
    
    # Send pause navigation command (API 1201)
    print("\n🛑 Pausing navigation...")
    payload = {
        'api_id': 1201,
        'parameter': json.dumps({'data': {}})
    }
    
    response = await conn.datachannel.pub_sub.publish_request_new(
        'rt/api/slam_operate/request',
        payload
    )
    
    print(f"✅ Response: {response}")
    
    await asyncio.sleep(1)
    await conn.disconnect()
    print("🔌 Disconnected")

if __name__ == '__main__':
    asyncio.run(main())
