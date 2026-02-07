#!/usr/bin/env python3
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
    
    def cb(m):
        global msg_count
        msg_count += 1
        print(f"🎯 HEIGHT_MAP #{msg_count}: {type(m)}, keys: {m.keys() if isinstance(m, dict) else 'N/A'}")
        if isinstance(m, dict) and 'data' in m:
            data = m['data']
            print(f"   Data type: {type(data).__name__}, len: {len(data) if hasattr(data, '__len__') else '?'}")
    
    print("🗺️  Subscribing to rt/utlidar/height_map_array (voxelized stream)...")
    conn.datachannel.pub_sub.subscribe("rt/utlidar/height_map_array", cb)
    
    print("⏳ Waiting 20s...")
    await asyncio.sleep(20)
    print(f"\n📊 Result: {msg_count} messages")

asyncio.run(main())
