#!/usr/bin/env python3
"""
Test playing a teaching action via API 7108
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
ROBOT_SN = "E21D1000PAHBMB06"

async def test_play_action(action_name: str):
    print("="*70)
    print("TESTING API 7108 - EXECUTE_CUSTOM_ACTION")
    print("="*70)
    print(f"Robot: {ROBOT_IP} ({ROBOT_SN})")
    print(f"Action: {action_name}")
    print()
    
    robot = RobotController(ROBOT_IP, ROBOT_SN)
    
    try:
        print("1. Connecting to robot...")
        await robot.connect()
        print("   ✓ Connected")
        
        await asyncio.sleep(2)
        
        print(f"\n2. Executing action '{action_name}' via API 7108...")
        result = await robot.executor.execute_custom_action(action_name)
        
        print(f"\n3. Response:")
        print(f"   {result}")
        
        # Wait a bit to see if action executes
        print("\n4. Waiting 5 seconds for action to complete...")
        await asyncio.sleep(5)
        
        print("\n5. Disconnecting...")
        await robot.disconnect()
        print("   ✓ Disconnected")
        
    except Exception as e:
        logger.error(f"Test failed: {e}", exc_info=True)
        if robot.connected:
            await robot.disconnect()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 test_play_teaching_action.py <action_name>")
        print("\nExample action names from PCAP analysis:")
        print("  - waist_drum_dance")
        print("  - spin_disks")
        print("  - test")
        print("\nOr try any action name saved in your robot")
        sys.exit(1)
    
    action_name = sys.argv[1]
    
    try:
        asyncio.run(test_play_action(action_name))
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
