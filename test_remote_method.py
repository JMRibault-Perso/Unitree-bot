#!/usr/bin/env python3
"""
Test connection using Remote (cloud) method like test_g1_6937.py
"""

import asyncio
import sys
sys.path.insert(0, 'C:/Unitree/G1/go2_webrtc_connect')

from unitree_webrtc_connect.webrtc_driver import UnitreeWebRTCConnection, WebRTCConnectionMethod

async def test():
    print("Testing WebRTC connection with Remote (cloud) method...")
    print("=" * 60)
    
    try:
        conn = UnitreeWebRTCConnection(
            WebRTCConnectionMethod.Remote,
            serialNumber="G1_6937",
            username="sebastianribault1@gmail.com",
            password="Xlp142!?rz"
        )
        
        print("Connecting...")
        await conn.connect()
        
        print("✅ SUCCESS! Connected to G1_6937!")
        print("Connection object:", conn)
        print("Datachannel:", conn.datachannel)
        
        await asyncio.sleep(2)
        
        await conn.disconnect()
        print("✅ Disconnected")
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test())
