#!/usr/bin/env python3
"""
SLAM Mapping Test - Standardized API calling pattern
Uses RobotTestConnection with consistent SLAM API wrapper
"""

import asyncio
import json
import sys
import os
import math

# Add parent directories to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))  # /root/G1/unitree_sdk2
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))      # /root/G1/unitree_sdk2/g1_tests
from robot_test_helpers import RobotTestConnection, SLAM_API, check_slam_response


async def main():
    print("=" * 70)
    print("SLAM MAPPING TEST")
    print("=" * 70)
    
    async with RobotTestConnection() as robot:
        # Phase 1: Start mapping
        print("\n" + "=" * 70)
        print("PHASE 1: START MAPPING")
        print("=" * 70)
        
        print("Starting SLAM mapping...")
        response = await robot.send_slam_request(SLAM_API['START_MAPPING'], {"slam_type": "indoor"})
        check_slam_response(response, "Start Mapping")
        print("✅ Mapping started\n")
        
        # Phase 2: Auto-timer for mapping
        print("PHASE 2: MAPPING WINDOW (60 seconds)")
        print("Walk the robot around the room to map the area.\n")
        
        for i in range(60, 0, -10):
            print(f"⏱️  {i} seconds remaining...", flush=True)
            await asyncio.sleep(10)
        
        print("✅ Mapping complete\n")
        
        # Phase 3: Save map
        print("=" * 70)
        print("PHASE 3: SAVE MAP")
        print("=" * 70)
        
        map_name = "test_simple"
        print(f"\nSaving map as '{map_name}'...")
        
        response = await robot.send_slam_request(SLAM_API['END_MAPPING'], {"address": f"/home/unitree/{map_name}.pcd"})
        check_slam_response(response, "Save Map")
        print(f"✅ Map saved\n")
        
        # Phase 4: Load map
        print("=" * 70)
        print("PHASE 4: LOAD MAP FOR NAVIGATION")
        print("=" * 70)
        
        print(f"\nLoading map '{map_name}'...")
        
        response = await robot.send_slam_request(
            SLAM_API['LOAD_MAP'],
            {
                "x": 0.0,
                "y": 0.0,
                "z": 0.0,
                "q_x": 0.0,
                "q_y": 0.0,
                "q_z": 0.0,
                "q_w": 1.0,
                "address": f"/home/unitree/{map_name}.pcd"
            }
        )
        check_slam_response(response, "Load Map")
        print(f"✅ Map loaded\n")
        
        # Phase 5: Subscribe to odometry
        print("=" * 70)
        print("PHASE 5: MONITORING ROBOT POSE")
        print("=" * 70)
        print("\nListening for pose updates (15 seconds)...")
        print("Move the robot manually and observe coordinates...\n")
        
        pose_count = [0]  # Use list to modify in nested function
        
        def on_odom(data: dict):
            """Handle odometry messages"""
            try:
                if isinstance(data, dict) and 'data' in data:
                    msg_data = data['data']
                    
                    # Parse JSON if it's a string
                    if isinstance(msg_data, str):
                        msg_data = json.loads(msg_data)
                    
                    if isinstance(msg_data, dict):
                        pose_info = msg_data.get('data', {})
                        
                        if 'currentPose' in pose_info:
                            pose = pose_info['currentPose']
                            pose_count[0] += 1
                            
                            x = pose.get('x', 0)
                            y = pose.get('y', 0)
                            z = pose.get('z', 0)
                            
                            if pose_count[0] % 5 == 0:
                                print(f"📍 Pose #{pose_count[0]}: x={x:.2f}, y={y:.2f}, z={z:.2f}")
            except Exception:
                pass
        
        # Subscribe to odometry
        robot.subscribe('rt/lf/sportmodestate', on_odom)
        
        # Wait 15 seconds while monitoring
        await asyncio.sleep(15)
        
        print(f"\n✅ Received {pose_count[0]} pose updates")
        
        # Phase 6: Navigate
        print("\n" + "=" * 70)
        print("PHASE 6: TEST NAVIGATION")
        print("=" * 70)
        
        target_x = 0.5
        target_y = 0.5
        target_yaw = 0.0
        
        print(f"\nNavigating to ({target_x}, {target_y}, {target_yaw}°)...")
        
        # Convert yaw to quaternion
        yaw_rad = math.radians(target_yaw)
        quat = {
            'z': math.sin(yaw_rad / 2),
            'w': math.cos(yaw_rad / 2)
        }
        
        response = await robot.send_slam_request(
            SLAM_API['NAVIGATE'],
            {
                "targetPose": {
                    "x": target_x,
                    "y": target_y,
                    "z": 0.0,
                    "q_x": 0.0,
                    "q_y": 0.0,
                    "q_z": quat['z'],
                    "q_w": quat['w']
                },
                "mode": 1
            }
        )
        check_slam_response(response, "Navigate")
        print(f"✅ Navigation started")
        
        # Monitor navigation for 10 seconds
        print(f"Observing navigation for 10 seconds...")
        await asyncio.sleep(10)
        
        # Phase 7: Close SLAM
        print("\n" + "=" * 70)
        print("PHASE 7: CLOSE SLAM")
        print("=" * 70)
        
        print(f"\nClosing SLAM service...")
        response = await robot.send_slam_request(SLAM_API['CLOSE_SLAM'], {})
        check_slam_response(response, "Close SLAM")
        print(f"✅ SLAM closed")
        
        print("\n" + "=" * 70)
        print("✅ SLAM TEST COMPLETE")
        print("=" * 70 + "\n")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n❌ Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
