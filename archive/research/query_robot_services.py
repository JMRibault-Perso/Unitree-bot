#!/usr/bin/env python3
"""Query robot service status via RobotStateClient API"""

import asyncio
import json
from unitree_webrtc_connect.webrtc_driver import UnitreeWebRTCConnection
from unitree_webrtc_connect.constants import WebRTCConnectionMethod

async def query_services():
    conn = UnitreeWebRTCConnection(
        WebRTCConnectionMethod.LocalSTA,
        ip="192.168.86.18"
    )
    
    await conn.connect()
    
    print("🔍 Querying robot services...")
    
    # Subscribe to response topic
    responses = []
    
    def response_callback(msg):
        print(f"📬 Response received: {msg}")
        responses.append(msg)
    
    conn.datachannel.pub_sub.subscribe("rt/api/robot_state/response", response_callback)
    
    # Try querying service list (if such API exists)
    # API IDs we know: 5001 = SERVICE_SWITCH
    # Try API ID 5000 for SERVICE_LIST or SERVICE_STATUS
    
    for api_id in [5000, 5001, 5002, 5003, 5010]:
        print(f"\n🔧 Trying API ID {api_id}...")
        payload = {
            "api_id": api_id,
            "parameter": "{}"
        }
        
        conn.datachannel.pub_sub.publish("rt/api/robot_state/request", payload)
        await asyncio.sleep(0.5)
    
    # Try querying specific service status
    print(f"\n🔧 Querying lidar_driver status...")
    payload = {
        "api_id": 5001,  # SERVICE_SWITCH
        "parameter": json.dumps({"name": "lidar_driver"})  # No "switch" param - maybe returns status?
    }
    conn.datachannel.pub_sub.publish("rt/api/robot_state/request", payload)
    await asyncio.sleep(1)
    
    print(f"\n📊 Total responses received: {len(responses)}")
    if not responses:
        print("❌ No responses from robot_state service")
        print("💡 RobotStateClient API may not be available on G1 Air")
    
    await conn.disconnect()

if __name__ == "__main__":
    asyncio.run(query_services())
