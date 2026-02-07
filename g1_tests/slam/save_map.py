#!/usr/bin/env python3
"""
Save SLAM Map
Save current map to file

Usage:
    python3 save_map.py
    python3 save_map.py --name my_room
"""

import asyncio
import argparse
import sys
from datetime import datetime
from pathlib import Path

repo_root = Path(__file__).resolve().parents[2]
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))
from robot_test_helpers import RobotTestConnection, SLAM_API, check_slam_response

async def main():
    parser = argparse.ArgumentParser(description='Save SLAM map')
    parser.add_argument('--name', default=None,
                       help='Map name (default: auto-generated timestamp)')
    args = parser.parse_args()
    
    # Generate map name
    if args.name:
        map_name = args.name
    else:
        map_name = f"map_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    async with RobotTestConnection() as robot:
        print(f"\n💾 Saving map as: {map_name}\n")
        
        parameters = {
            'address': f"/home/unitree/{map_name}.pcd"
        }
        
        response = await robot.send_slam_request(SLAM_API['SAVE_MAP'], parameters)
        check_slam_response(response, "Save Map")
        
        print(f"\n✅ Map saved successfully!")
        print(f"\n📁 Map file: /data/maps/{map_name}.pcd")
        print("\n📝 Next steps:")
        print(f"   1. Load map: python3 load_map.py --name {map_name}")
        print("   2. View map: python3 ../slam_map_viewer.py")
        print("   3. Navigate: python3 test_navigation_v2.py --map-path /data/maps/{map_name}.pcd\n")

if __name__ == "__main__":
    asyncio.run(main())
