#!/usr/bin/env python3
"""
Start SLAM Mapping
Quick command to begin SLAM mapping mode

Usage:
    python3 start_mapping.py
"""

import asyncio
import sys
sys.path.insert(0, '/root/G1/unitree_sdk2')
from robot_test_helpers import RobotTestConnection, SLAM_API, check_slam_response

async def main():
    async with RobotTestConnection() as robot:
        print("\n🗺️  Starting SLAM mapping mode...\n")
        
        response = await robot.send_slam_request(SLAM_API['START_MAPPING'], {})
        check_slam_response(response, "Start Mapping")
        
        print("\n✅ Mapping started!")
        print("\n📝 Next steps:")
        print("   1. Walk robot around area")
        print("   2. Run save_map.py when done")
        print("   3. Run stop_mapping.py to stop\n")

if __name__ == "__main__":
    asyncio.run(main())
