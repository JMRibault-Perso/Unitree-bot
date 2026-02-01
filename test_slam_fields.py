#!/usr/bin/env python3
"""
Test script to discover what fields are in slam_info during mapping.
This will help us find where the map/point cloud data is.
"""

import asyncio
import sys
import time
sys.path.insert(0, '/root/G1/unitree_sdk2')

from g1_app.core.robot_controller import RobotController

async def test_slam_fields():
    print("=" * 70)
    print("SLAM Fields Discovery Test")
    print("=" * 70)
    print()
    print("This script will:")
    print("1. Connect to G1_6937")
    print("2. Start SLAM mapping")
    print("3. Listen for slam_info messages for 10 seconds")
    print("4. Display all fields found")
    print()
    
    robot = RobotController("192.168.86.18", "G1_6937")
    
    # Connect
    print("Connecting to robot...")
    await robot.connect()
    await asyncio.sleep(2)
    
    if not robot.connected:
        print("❌ Failed to connect!")
        return
    
    print("✅ Connected!")
    print()
    
    # Start SLAM
    print("Starting SLAM mapping...")
    await robot.executor.slam_start_mapping()
    await asyncio.sleep(2)
    
    print("✅ SLAM started, collecting data for 10 seconds...")
    print("(Move the robot with WASD if you want more data)")
    print()
    
    # Wait for data
    for i in range(10):
        await asyncio.sleep(1)
        print(f"  {i+1}/10 seconds elapsed...")
    
    print()
    print("=" * 70)
    print("Check server_slam_debug.log for slam_info field discoveries:")
    print("grep 'SLAM data fields' server_slam_debug.log")
    print("grep 'Found ' server_slam_debug.log")
    print("=" * 70)
    
    # Stop SLAM
    print()
    print("Stopping SLAM...")
    await robot.executor.slam_stop_mapping()
    await asyncio.sleep(1)
    
    print("✅ Test complete!")
    print()
    print(f"Trajectory collected: {len(getattr(robot, 'slam_trajectory', []))} points")
    
    await robot.disconnect()

if __name__ == "__main__":
    asyncio.run(test_slam_fields())
