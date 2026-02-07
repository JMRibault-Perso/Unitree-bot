#!/usr/bin/env python3
"""
Debug script - Listen to ALL robot data channels
"""

import asyncio
import sys
sys.path.insert(0, '/root/G1/go2_webrtc_connect')

from unitree_webrtc_connect.webrtc_driver import UnitreeWebRTCConnection
from unitree_webrtc_connect.constants import WebRTCConnectionMethod, RTC_TOPIC

ROBOT_IP = "192.168.86.16"
ROBOT_SN = "E21D1000PAHBMB06"

async def main():
    print(f"🔌 Connecting to robot at {ROBOT_IP}...")
    
    conn = UnitreeWebRTCConnection(
        WebRTCConnectionMethod.LocalSTA,
        ip=ROBOT_IP,
        serialNumber=ROBOT_SN
    )
    
    await conn.connect()
    print("✅ Connected!")
    
    # Subscribe to ALL available topics
    print("\n📡 Subscribing to all topics...")
    
    def make_callback(topic_name):
        def callback(data):
            print(f"📥 [{topic_name}]: {data}")
        return callback
    
    for key, topic in RTC_TOPIC.items():
        if 'response' in topic.lower() or 'state' in topic.lower():
            try:
                conn.datachannel.pub_sub.subscribe(topic, make_callback(topic))
                print(f"  ✓ {key}: {topic}")
            except Exception as e:
                print(f"  ✗ {key}: {e}")
    
    print("\n⏳ Listening for messages... (Ctrl+C to stop)")
    print("Try sending commands from the Android app now!\n")
    
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        print("\n\n🛑 Stopping...")
    finally:
        await conn.disconnect()
        print("Disconnected")

if __name__ == "__main__":
    asyncio.run(main())
