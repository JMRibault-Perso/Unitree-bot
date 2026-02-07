#!/usr/bin/env python3
"""
Simple map builder - NO interactive prompts, NO hanging
Just: Start → Wait 60 sec for you to drive → Save → Verify → Done
"""
import asyncio
import sys
import os
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))
from robot_test_helpers import RobotTestConnection, SLAM_API, check_slam_response

MAP_NAME = "room"
MAP_PATH = f"/home/unitree/{MAP_NAME}.pcd"

async def main():
    print("\n" + "="*60)
    print("BUILDING ROOM MAP (60 second mapping window)")
    print("="*60)
    
    async with RobotTestConnection() as robot:
        # Phase 1: START MAPPING
        print("\n1️⃣  START_MAPPING...")
        response = await robot.send_slam_request(SLAM_API['START_MAPPING'], {"slam_type": "indoor"})
        check_slam_response(response, "Start Mapping")
        print("   ✅ Mapping active - LiDAR capturing\n")
        
        # Phase 2: DRIVE (60 second window)
        print("2️⃣  DRIVING WINDOW (60 seconds)")
        print("   📍 Drive the robot around the room now!")
        print("   • Move in patterns: forward/back, left/right, circles")
        print("   • Cover as much area as possible")
        print("   • Return to starting position before timer ends\n")
        
        for i in range(60, 0, -10):
            print(f"   ⏱️  {i} seconds remaining...", flush=True)
            await asyncio.sleep(10)
        
        print("   ✅ Driving window complete\n")
        
        # Phase 3: SAVE MAP
        print("3️⃣  SAVE_MAP...")
        response = await robot.send_slam_request(
            SLAM_API['END_MAPPING'], 
            {'address': MAP_PATH}
        )
        check_slam_response(response, "Save Map")
        print(f"   ✅ Map saved to: {MAP_PATH}\n")
        
        # Phase 4: LOAD MAP (verify)
        print("4️⃣  LOAD_MAP (verify)...")
        response = await robot.send_slam_request(
            SLAM_API['LOAD_MAP'],
            {
                'x': 0.0, 'y': 0.0, 'z': 0.0,
                'q_x': 0.0, 'q_y': 0.0, 'q_z': 0.0, 'q_w': 1.0,
                'address': MAP_PATH
            }
        )
        check_slam_response(response, "Load Map")
        print(f"   ✅ Map loaded and verified\n")
        
        print("="*60)
        print("✅ ROOM MAP BUILT AND READY")
        print("="*60)
        print(f"\nMap location: {MAP_PATH}")
        print(f"Ready for waypoint navigation tests\n")

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⚠️  Interrupted")
        sys.exit(1)
