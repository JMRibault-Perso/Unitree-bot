#!/usr/bin/env python3
"""Quick script to cancel/pause navigation"""

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
        print("\n🛑 Pausing navigation...")
        data = await robot.send_slam_request(SLAM_API['PAUSE_NAV'], {})
        check_slam_response(data, "Pause navigation")

if __name__ == '__main__':
    asyncio.run(main())
