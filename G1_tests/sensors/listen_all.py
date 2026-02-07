#!/usr/bin/env python3
"""
Listen to All Robot Topics
Monitor and log all WebRTC topic messages

Usage:
    python3 listen_all.py
    python3 listen_all.py > output.log  # Save to file
"""

import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path

repo_root = Path(__file__).resolve().parents[2]
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))
from robot_test_helpers import RobotTestConnection

class TopicLogger:
    def __init__(self):
        self.message_counts = {}
        self.topics_seen = set()
    
    def create_handler(self, topic):
        """Create a handler function for a specific topic"""
        def handler(msg):
            # Track statistics
            self.topics_seen.add(topic)
            self.message_counts[topic] = self.message_counts.get(topic, 0) + 1
            
            # Log the message
            timestamp = datetime.now().strftime('%H:%M:%S.%f')[:-3]
            print(f"\n[{timestamp}] 📡 {topic}")
            
            try:
                # Try to pretty-print JSON
                if isinstance(msg, dict):
                    print(json.dumps(msg, indent=2))
                else:
                    print(msg)
            except:
                print(msg)
            
            print("-" * 60)
        
        return handler
    
    def summary(self):
        """Print statistics summary"""
        print("\n" + "=" * 60)
        print("TOPIC STATISTICS")
        print("=" * 60)
        
        for topic in sorted(self.topics_seen):
            count = self.message_counts.get(topic, 0)
            print(f"{topic:50s} {count:6d} msgs")
        
        print(f"\nTotal topics: {len(self.topics_seen)}")
        print(f"Total messages: {sum(self.message_counts.values())}\n")

async def main():
    logger = TopicLogger()
    
    async with RobotTestConnection() as robot:
        print("🔌 Connected! Listening to all topics...")
        print("(Messages will appear below)\n")
        print("=" * 60)
        
        # Subscribe to common topics
        common_topics = [
            'rt/lf/sportmodestate',
            'rt/lf/bmsstate',
            'rt/lf/lowstate',
            'rt/utlidar/cloud_livox_mid360',
            'rt/utlidar/cloud',
            'rt/utlidar/imu',
            'rt/api/slam_operate/response',
            'rt/api/sport/response',
            'rt/api/arm_action/response',
            'rt/audio_msg',
        ]
        
        for topic in common_topics:
            await robot.subscribe(topic, logger.create_handler(topic))
        
        # Monitor continuously
        try:
            while True:
                await asyncio.sleep(1.0)
        except KeyboardInterrupt:
            logger.summary()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 Exiting...")
