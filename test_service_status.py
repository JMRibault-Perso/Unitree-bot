#!/usr/bin/env python3
"""
Query robot service status - replicate Android app Service Status screen
"""

import asyncio
import sys
import logging
import json

sys.path.insert(0, '/root/G1/go2_webrtc_connect')
from unitree_webrtc_connect.webrtc_driver import UnitreeWebRTCConnection, WebRTCConnectionMethod

logging.basicConfig(level=logging.WARNING)

async def main():
    try:
        print("🔌 Connecting to G1 Air robot...")
        conn = UnitreeWebRTCConnection(WebRTCConnectionMethod.LocalSTA, ip="192.168.86.18")
        await conn.connect()
        print("✅ Connected!\n")
        
        await conn.datachannel.disableTrafficSaving(True)
        
        print("📋 Subscribing to rt/servicestate topic...\n")
        
        received_data = []
        
        def service_callback(message):
            print(f"\n🎯 SERVICE STATE MESSAGE RECEIVED!")
            print(f"Type: {type(message)}")
            if isinstance(message, dict):
                print(f"Keys: {message.keys()}")
                if 'data' in message:
                    data = message['data']
                    print(f"\nData type: {type(data)}")
                    if isinstance(data, dict):
                        print(f"Data keys: {data.keys()}")
                        print(f"\n📊 SERVICE STATUS:")
                        print(json.dumps(data, indent=2))
                    elif isinstance(data, list):
                        print(f"Data length: {len(data)}")
                        print(f"\n📊 SERVICES ({len(data)} total):")
                        for item in data:
                            print(f"  - {item}")
                    else:
                        print(f"Data: {data}")
                received_data.append(message)
            else:
                print(f"Message: {message}")
        
        # Subscribe to service state topic
        conn.datachannel.pub_sub.subscribe("rt/servicestate", service_callback)
        
        print("⏳ Listening for 10 seconds...")
        await asyncio.sleep(10)
        
        if not received_data:
            print("\n⚠️ No service state messages received.")
            print("   This topic might require a request/response pattern instead of subscription.")
            print("   Trying robot_state service API request...")
            
            # Try sending a request to robot_state service
            # API 5001 = SERVICE_SWITCH (might also return status)
            request = {
                "header": {
                    "identity": {"id": 0, "api_id": 5001}  # ServiceSwitch API
                }
            }
            
            def response_callback(msg):
                print(f"\n🎯 ROBOT STATE RESPONSE:")
                print(json.dumps(msg, indent=2))
            
            conn.datachannel.pub_sub.publish("rt/api/robot_state/request", json.dumps(request), response_callback)
            await asyncio.sleep(5)
        
        print(f"\n✅ Test complete! Received {len(received_data)} messages")
        
    except Exception as e:
        logging.error(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⚠️ Interrupted by user")
        sys.exit(0)
