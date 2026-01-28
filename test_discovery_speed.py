#!/usr/bin/env python3
"""Test robot discovery speed"""
import sys
import asyncio
import time
sys.path.insert(0, '/root/G1/unitree_sdk2/g1_app/core')

from robot_discovery import RobotDiscovery

async def test_discovery():
    discovery = RobotDiscovery()
    
    print("Starting discovery test...")
    print(f"Looking for robot with MAC: fc:23:cd:92:60:02")
    
    start = time.time()
    robots = await discovery.get_robots()
    elapsed = time.time() - start
    
    print(f"\nDiscovery completed in {elapsed:.2f} seconds")
    print(f"Found {len(robots)} robot(s):")
    
    for robot in robots:
        print(f"\n  Name: {robot.name}")
        print(f"  Serial: {robot.serial_number}")
        print(f"  IP: {robot.ip}")
        print(f"  MAC: {robot.mac_address}")
        print(f"  Online: {robot.is_online}")

if __name__ == "__main__":
    asyncio.run(test_discovery())
