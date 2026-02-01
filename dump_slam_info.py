#!/usr/bin/env python3
"""
Print full slam_info content to see pcdName and address fields
"""

import asyncio
import sys
import json
sys.path.insert(0, '/root/G1/unitree_sdk2')

from g1_app.core.robot_controller import RobotController

slam_info_samples = []

async def test():
    global slam_info_samples
    
    robot = RobotController("192.168.86.18", "G1_6937")
    
    # Capture slam_info
    original_callback = None
    def capture_callback(data: dict):
        try:
            if isinstance(data, dict) and 'data' in data:
                slam_data = json.loads(data['data']) if isinstance(data['data'], str) else data['data']
                slam_info_samples.append(slam_data)
        except:
            pass
    
    await robot.connect()
    await asyncio.sleep(2)
    
    # Hijack the callback
    robot.conn.datachannel.pub_sub.subscribe("rt/slam_info", capture_callback)
    
    print("Starting SLAM...")
    await robot.executor.slam_start_mapping()
    await asyncio.sleep(5)
    
    print("\n" + "=" * 70)
    print(f"Captured {len(slam_info_samples)} slam_info messages")
    print("=" * 70)
    
    if slam_info_samples:
        print("\nFirst sample:")
        print(json.dumps(slam_info_samples[0], indent=2))
        
        print("\nLast sample:")
        print(json.dumps(slam_info_samples[-1], indent=2))
        
        # Check for address values
        addresses = [s.get('data', {}).get('address', '') for s in slam_info_samples if s.get('type') == 'mapping_info']
        pcd_names = [s.get('data', {}).get('pcdName', '') for s in slam_info_samples if s.get('type') == 'mapping_info']
        
        print(f"\nUnique addresses: {set(addresses)}")
        print(f"Unique pcdNames: {set(pcd_names)}")
    
    await robot.executor.slam_stop_mapping()
    await robot.disconnect()

if __name__ == "__main__":
    asyncio.run(test())
