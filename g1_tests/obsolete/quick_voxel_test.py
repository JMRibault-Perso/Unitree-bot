import asyncio, sys
sys.path.insert(0, '/root/G1/unitree_sdk2')
from g1_app.core.robot_controller import RobotController

async def test():
    robot = RobotController("192.168.86.18", "G1_6937")
    await robot.connect()
    await asyncio.sleep(3)
    print("\n✅ Connected - waiting for voxel data...")
    await robot.executor.slam_start_mapping()
    await asyncio.sleep(10)
    print(f"\n📊 Voxel data received: {robot.latest_lidar_voxels is not None}")
    if robot.latest_lidar_voxels:
        print(f"   Type: {type(robot.latest_lidar_voxels)}")
        if isinstance(robot.latest_lidar_voxels, dict):
            print(f"   Keys: {list(robot.latest_lidar_voxels.keys())}")
    await robot.disconnect()

asyncio.run(test())
