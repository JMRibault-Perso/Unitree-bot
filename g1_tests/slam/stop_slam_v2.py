#!/usr/bin/env python3
"""Stop SLAM completely - exit navigation mode"""

import asyncio
import logging
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from robot_test_helpers import RobotTestConnection, SLAM_API, check_slam_response

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

async def main():
    async with RobotTestConnection() as robot:
        print("\n🛑 Closing SLAM system...")
        data = await robot.send_slam_request(SLAM_API['CLOSE_SLAM'], {})
        check_slam_response(data, "Close SLAM")
        # Context manager will wait before disconnecting

if __name__ == '__main__':
    asyncio.run(main())
