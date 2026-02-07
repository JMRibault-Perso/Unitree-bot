#!/usr/bin/env python3
"""
List All Available WebRTC Topics
Shows all topics the robot is publishing

Usage:
    python3 list_topics.py
"""

import asyncio
import sys
from pathlib import Path

repo_root = Path(__file__).resolve().parents[2]
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))
from robot_test_helpers import RobotTestConnection

async def main():
    async with RobotTestConnection() as robot:
        print("\n📡 Connected to robot. Listening for topics...\n")
        print("(This will take ~5 seconds to discover all topics)\n")
        
        discovered = set()
        
        def topic_handler(topic):
            """Callback for any new topic"""
            if topic not in discovered:
                discovered.add(topic)
                print(f"  • {topic}")
        
        # The WebRTC connection automatically discovers topics
        # We just need to wait and listen
        await asyncio.sleep(5.0)
        
        print(f"\n✅ Discovered {len(discovered)} topics\n")
        
        # Categorize if possible
        slam_topics = [t for t in discovered if 'slam' in t.lower()]
        lidar_topics = [t for t in discovered if 'lidar' in t.lower()]
        state_topics = [t for t in discovered if 'state' in t.lower()]
        
        if slam_topics:
            print("🗺️  SLAM Topics:")
            for t in sorted(slam_topics):
                print(f"   {t}")
        
        if lidar_topics:
            print("\n📡 LiDAR Topics:")
            for t in sorted(lidar_topics):
                print(f"   {t}")
        
        if state_topics:
            print("\n📊 State Topics:")
            for t in sorted(state_topics):
                print(f"   {t}")
        
        print()

if __name__ == "__main__":
    asyncio.run(main())
