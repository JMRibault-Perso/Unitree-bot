#!/usr/bin/env python3
"""
Load SLAM Map
Load a previously saved map for navigation

Usage:
    python3 load_map.py --name my_room
    python3 load_map.py --name my_room --x 0.0 --y 0.0 --yaw 0.0
"""

import asyncio
import argparse
import math
import sys
from pathlib import Path

repo_root = Path(__file__).resolve().parents[2]
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))
from robot_test_helpers import RobotTestConnection, SLAM_API, check_slam_response

def yaw_to_quaternion(yaw_deg):
    """Convert yaw angle to quaternion"""
    yaw_rad = math.radians(yaw_deg)
    return {
        'x': 0.0,
        'y': 0.0,
        'z': math.sin(yaw_rad / 2),
        'w': math.cos(yaw_rad / 2)
    }

async def main():
    parser = argparse.ArgumentParser(description='Load SLAM map')
    parser.add_argument('--name', required=True,
                       help='Map name to load')
    parser.add_argument('--x', type=float, default=0.0,
                       help='Initial X position (meters)')
    parser.add_argument('--y', type=float, default=0.0,
                       help='Initial Y position (meters)')
    parser.add_argument('--yaw', type=float, default=0.0,
                       help='Initial yaw angle (degrees)')
    args = parser.parse_args()
    
    async with RobotTestConnection() as robot:
        print(f"\n🗺️  Loading map: {args.name}")
        print(f"   Initial pose: x={args.x}, y={args.y}, yaw={args.yaw}°\n")
        
        # Convert yaw to quaternion
        quat = yaw_to_quaternion(args.yaw)
        
        parameters = {
            'x': args.x,
            'y': args.y,
            'z': 0.0,
            'q_x': 0.0,
            'q_y': 0.0,
            'q_z': quat['z'],
            'q_w': quat['w'],
            'address': f'/home/unitree/{args.name}.pcd'
        }
        
        response = await robot.send_slam_request(SLAM_API['LOAD_MAP'], parameters)
        check_slam_response(response, "Load Map")
        
        print("\n✅ Map loaded successfully!")
        print("\n📝 Next steps:")
        print("   1. Navigate: python3 test_navigation_v2.py --target-x X --target-y Y")
        print("   2. Monitor position: python3 ../utilities/monitor_telemetry.py\n")

if __name__ == "__main__":
    asyncio.run(main())
