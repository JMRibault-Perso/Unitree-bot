#!/usr/bin/env python3
"""
Test API 7107 (GetActionList) to retrieve taught actions from robot
"""

import asyncio
import logging
import sys
sys.path.insert(0, '/root/G1/unitree_sdk2')

from g1_app.core.robot_controller import RobotController

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

ROBOT_IP = "192.168.86.3"
ROBOT_SN = "E21D1000PAHBMB06"  # G1_6937

async def test_get_action_list():
    print("="*70)
    print("TESTING API 7107 - GET_ACTION_LIST")
    print("="*70)
    print(f"Robot: {ROBOT_IP} ({ROBOT_SN})")
    print()
    
    robot = RobotController(ROBOT_IP, ROBOT_SN)
    
    try:
        print("1. Connecting to robot...")
        await robot.connect()
        print("   ✓ Connected")
        
        # Wait for connection to stabilize
        await asyncio.sleep(2)
        
        print("\n2. Requesting action list via API 7107...")
        result = await robot.get_custom_action_list()
        
        print(f"\n3. Response:")
        print(f"   Success: {result.get('success')}")
        
        if result.get('success'):
            print(f"   Data: {result.get('data')}")
            
            # Try to parse action names
            data = result.get('data', {})
            if isinstance(data, dict):
                actions = data.get('actions', data.get('action_list', data.get('data', [])))
                if actions:
                    print(f"\n4. Found {len(actions)} actions:")
                    for idx, action in enumerate(actions):
                        print(f"   [{idx}] {action}")
                else:
                    print("\n4. No actions found in response")
                    print(f"   Raw data keys: {list(data.keys())}")
            else:
                print(f"\n4. Unexpected data format: {type(data)}")
        else:
            print(f"   Error: {result.get('error')}")
        
        print("\n5. Disconnecting...")
        await robot.disconnect()
        print("   ✓ Disconnected")
        
    except Exception as e:
        logger.error(f"Test failed: {e}", exc_info=True)
        if robot.connected:
            await robot.disconnect()

if __name__ == "__main__":
    try:
        asyncio.run(test_get_action_list())
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
