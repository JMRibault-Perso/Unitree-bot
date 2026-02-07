#!/usr/bin/env python3
"""
Simple SLAM map builder - build ONE reusable room map
Uses standard RobotTestConnection API pattern
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
from robot_test_helpers import RobotTestConnection, SLAM_API, check_slam_response

async def build_room_map():
    """Build one map of the room"""
    
    print("\n" + "="*60)
    print("BUILDING ROOM MAP")
    print("="*60)
    
    async with RobotTestConnection() as robot:
        # Start mapping
        print("\n1️⃣  START_MAPPING (API 1801)")
        response = await robot.send_slam_request(SLAM_API['START_MAPPING'], {"slam_type": "indoor"})
        check_slam_response(response, "Start Mapping")
        print("   ✅ Mapping active\n")
        
        # Wait for user to drive
        print("2️⃣  DRIVING PHASE (60 seconds)")
        print("   Drive the robot around the room")
        print("   Cover all areas - forward, backward, left, right, circles\n")
        
        for i in range(60, 0, -10):
            print(f"   ⏱️  {i} seconds remaining...", flush=True)
            await asyncio.sleep(10)
        
        print("   ✅ Mapping complete\n")
        
        # Save map
        print("3️⃣  SAVE_MAP (API 1802)")
        response = await robot.send_slam_request(SLAM_API['END_MAPPING'], {"address": "/home/unitree/room.pcd"})
        check_slam_response(response, "Save Map")
        print(f"   ✅ Map saved to: /home/unitree/room.pcd\n")
        
        # Load map to verify
        print("4️⃣  LOAD_MAP (API 1804) - Verify saved map")
        response = await robot.send_slam_request(
            SLAM_API['LOAD_MAP'],
            {
                "x": 0.0, "y": 0.0, "z": 0.0,
                "q_x": 0.0, "q_y": 0.0, "q_z": 0.0, "q_w": 1.0,
                "address": "/home/unitree/room.pcd"
            }
        )
        check_slam_response(response, "Load Map")
        print(f"   ✅ Map loaded and verified")
        
        print("\n✅ Map 'room.pcd' built and verified!")
        print("   Location: /home/unitree/room.pcd")
        print("   Ready for waypoint navigation tests")
        return True
        
    finally:
        # Disconnect
        print("\n🔌 Disconnecting...")
        await asyncio.sleep(0.2)
        await conn.disconnect()
        print("✅ Disconnected")

if __name__ == '__main__':
    success = asyncio.run(build_room_map())
    sys.exit(0 if success else 1)
