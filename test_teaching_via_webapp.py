#!/usr/bin/env python3
"""
Test teaching mode commands via the running web app
Uses the existing WebRTC connection that's already established
"""

import asyncio
import sys
import logging

sys.path.insert(0, '/root/G1/unitree_sdk2')

from g1_app import RobotController
from g1_app.utils import setup_app_logging

setup_app_logging(verbose=True)
logger = logging.getLogger(__name__)


async def test_teaching_commands():
    """Test teaching mode commands via WebRTC datachannel"""
    
    robot = RobotController(
        robot_ip="192.168.86.2",
        robot_sn="G1_6937"
    )
    
    try:
        # Connect to robot
        logger.info("=" * 80)
        logger.info("CONNECTING TO ROBOT")
        logger.info("=" * 80)
        await robot.connect()
        
        await asyncio.sleep(2)
        
        # Test 1: List teaching actions
        logger.info("\n" + "=" * 80)
        logger.info("TEST 1: LIST TEACHING ACTIONS")
        logger.info("=" * 80)
        result = await robot.executor.list_teaching_actions()
        logger.info(f"Result: {result}")
        
        await asyncio.sleep(2)
        
        logger.info("\n✅ Teaching commands test complete")
        
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
    finally:
        if robot.executor:
            await robot.executor.stop_motion()
        if robot.conn:
            await robot.conn.disconnect()


if __name__ == "__main__":
    asyncio.run(test_teaching_commands())
