#!/usr/bin/env python3
"""
Monitor LiDAR Point Cloud Data
Real-time LiDAR data monitoring and statistics

Usage:
    python3 monitor_lidar.py
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

class LiDARMonitor:
    def __init__(self):
        self.frame_count = 0
        self.last_frame_time = None
        self.point_counts = []
        self.last_display = None
        
    def handle_pointcloud(self, msg):
        """Process point cloud messages"""
        self.frame_count += 1
        self.last_frame_time = datetime.now()
        
        # Try to extract point count
        try:
            if 'data' in msg:
                data = msg['data']
                if isinstance(data, str):
                    data = json.loads(data)
                
                # PointCloud2 format
                if 'width' in data and 'height' in data:
                    points = data['width'] * data['height']
                    self.point_counts.append(points)
                    if len(self.point_counts) > 10:
                        self.point_counts.pop(0)
        except:
            pass
        
        # Update display every second
        now = datetime.now()
        if not self.last_display or (now - self.last_display).total_seconds() >= 1.0:
            self.display()
            self.last_display = now
    
    def display(self):
        """Show current statistics"""
        print('\033[2J\033[H', end='')  # Clear screen
        
        print("=" * 60)
        print("G1 LiDAR MONITOR")
        print("=" * 60)
        
        print(f"\n📡 Frames Received: {self.frame_count}")
        
        if self.last_frame_time:
            print(f"🕒 Last Frame: {self.last_frame_time.strftime('%H:%M:%S.%f')[:-3]}")
        
        if self.point_counts:
            avg_points = sum(self.point_counts) / len(self.point_counts)
            print(f"\n📊 Points per Frame:")
            print(f"   Average: {int(avg_points):,}")
            print(f"   Latest: {self.point_counts[-1]:,}")
        
        print("\n🎯 Subscribed Topics:")
        print("   • rt/utlidar/cloud_livox_mid360")
        print("   • rt/utlidar/cloud")
        
        print("\n(Press Ctrl+C to exit)")

async def main():
    monitor = LiDARMonitor()
    
    async with RobotTestConnection() as robot:
        print("🔌 Connected! Monitoring LiDAR...\n")
        
        # Subscribe to LiDAR topics
        await robot.subscribe('rt/utlidar/cloud_livox_mid360', monitor.handle_pointcloud)
        await robot.subscribe('rt/utlidar/cloud', monitor.handle_pointcloud)
        
        # Monitor continuously
        try:
            while True:
                await asyncio.sleep(0.1)
        except KeyboardInterrupt:
            print("\n\n👋 Exiting monitor...")
            print(f"✅ Total frames received: {monitor.frame_count}\n")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n")
