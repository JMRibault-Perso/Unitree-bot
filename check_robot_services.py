#!/usr/bin/env python3
"""
Direct WebRTC query to list available services on the robot
Uses the robot controller's existing connection
"""

import asyncio
import sys
import json

sys.path.insert(0, '/root/G1/unitree_sdk2')
sys.path.insert(0, '/root/G1/go2_webrtc_connect')

from g1_app.core.robot_controller import RobotController
from g1_app.api.constants import RobotStateAPI, Service

async def list_services():
    """List all services available on the robot"""
    
    robot = RobotController(
        robot_ip="192.168.86.18",
        robot_sn="E21D1000PAHBMB06"
    )
    
    print("🔌 Connecting to robot...")
    await robot.connect()
    
    print("✅ Connected!\n")
    print("🔍 Querying service information...\n")
    
    # Method 1: Try to get service list (if API exists)
    print("📋 Attempting to get service list...")
    try:
        # Try API 5000 for service list
        payload = {
            "api_id": 5000,
            "parameter": "{}"
        }
        
        # Subscribe to response first
        responses = []
        def on_response(data):
            responses.append(data)
            print(f"   Response: {json.dumps(data, indent=2)}")
        
        robot.conn.datachannel.pub_sub.subscribe(
            f"rt/api/{Service.ROBOT_STATE}/response",
            on_response
        )
        
        await robot.conn.datachannel.pub_sub.publish_request_new(
            f"rt/api/{Service.ROBOT_STATE}/request",
            payload
        )
        
        await asyncio.sleep(2)
        
        if not responses:
            print("   ❌ No response for API 5000 (service list)")
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Method 2: Try querying specific known services
    print("\n📋 Checking known services...")
    from g1_app.api.constants import SystemService
    
    services_to_check = [
        "sport_mode",
        "ai_sport",  
        "advanced_sport",
        "lidar_driver",
        "unitree_slam",
        "slam_operate",
        "vui_service",
        "robot_state"
    ]
    
    for service_name in services_to_check:
        try:
            # Try SERVICE_SWITCH API (5001) to query status
            payload = {
                "api_id": RobotStateAPI.SERVICE_SWITCH,
                "parameter": json.dumps({"name": service_name, "switch": -1})  # -1 = query only
            }
            
            responses.clear()
            await robot.conn.datachannel.pub_sub.publish_request_new(
                f"rt/api/{Service.ROBOT_STATE}/request",
                payload
            )
            
            await asyncio.sleep(0.5)
            
            if responses:
                status_code = responses[0].get('data', {}).get('header', {}).get('status', {}).get('code')
                if status_code == 0:
                    print(f"   ✅ {service_name}: AVAILABLE")
                elif status_code == 3203:
                    print(f"   ❌ {service_name}: NOT IMPLEMENTED")
                else:
                    print(f"   ⚠️  {service_name}: status code {status_code}")
            else:
                print(f"   ⏱️  {service_name}: no response")
                
        except Exception as e:
            print(f"   ❌ {service_name}: error - {e}")
    
    print("\n✅ Service query complete")
    await robot.disconnect()

if __name__ == "__main__":
    asyncio.run(list_services())
