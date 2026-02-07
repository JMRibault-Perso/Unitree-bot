#!/usr/bin/env python3
"""
SLAM Topics Monitor - Check which odometry topics are publishing

This script subscribes to all SLAM odometry topics and shows which ones
are actually receiving data. Useful for diagnosing relocation issues.
"""

import asyncio
import sys
import os
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))
from robot_test_helpers import RobotTestConnection


class TopicsMonitor:
    def __init__(self):
        self.topics = {
            'rt/unitree/slam_mapping/odom': 0,
            'rt/unitree/slam_relocation/odom': 0,
            'rt/lf/sportmodestate': 0,
            'rt/unitree/slam_info': 0,
        }
        self.monitoring = False
    
    def _make_callback(self, topic_name):
        """Create a callback for a specific topic"""
        def callback(msg):
            if self.monitoring:
                self.topics[topic_name] += 1
        return callback


async def main():
    print("\n" + "="*70)
    print("SLAM TOPICS MONITOR - Check which topics are publishing")
    print("="*70)
    
    print("\nSubscribing to SLAM odometry topics...\n")
    
    monitor = TopicsMonitor()
    monitor.monitoring = True
    
    async with RobotTestConnection() as robot:
        # Subscribe to all topics
        for topic in monitor.topics:
            robot.subscribe(topic, monitor._make_callback(topic))
        
        await asyncio.sleep(1)  # Let subscriptions initialize
        
        # Monitor for 15 seconds
        print("Listening for 15 seconds...\n")
        for i in range(15, 0, -1):
            # Display current status
            print(f"\r⏱️  {i:2d}s | ", end='', flush=True)
            
            active = [t for t, count in monitor.topics.items() if count > 0]
            if active:
                for t in active:
                    print(f"{monitor.topics[t]:4d} ", end='', flush=True)
            else:
                print("(waiting for data...)", end='', flush=True)
            
            await asyncio.sleep(1)
        
        print("\n")
        monitor.monitoring = False
        
        # Display summary
        print("\n" + "="*70)
        print("TOPICS STATUS SUMMARY")
        print("="*70 + "\n")
        
        for topic, count in monitor.topics.items():
            status = f"✅ {count:4d} messages" if count > 0 else "❌ No data"
            print(f"  {status:20s} | {topic}")
        
        print("\n" + "="*70)
        print("INTERPRETATION")
        print("="*70 + "\n")
        
        mapping_active = monitor.topics['rt/unitree/slam_mapping/odom'] > 0
        relocation_active = monitor.topics['rt/unitree/slam_relocation/odom'] > 0
        
        if mapping_active or relocation_active:
            print("✅ SLAM ODOMETRY ACTIVE")
            if relocation_active:
                print("   - Relocation topic is publishing")
                print("   - Robot is in navigation/relocation mode")
            else:
                print("   - Only mapping topic is publishing")
                print("   - Robot may be in mapping mode, not navigation")
        else:
            print("❌ SLAM ODOMETRY NOT ACTIVE")
            print("   Possible causes:")
            print("   1. SLAM system not initialized")
            print("   2. Robot not in correct state")
            print("   3. DDS/WebRTC not connected properly")
        
        if monitor.topics['rt/lf/sportmodestate'] > 0:
            print("\n✅ Fallback sportmodestate available")
            print("   - Can use FSM state as position source")
        
        print()


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted")
        sys.exit(1)
