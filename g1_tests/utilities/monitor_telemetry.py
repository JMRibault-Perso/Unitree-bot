#!/usr/bin/env python3
"""
Monitor Robot Telemetry
Real-time display of robot state, battery, position

Usage:
    python3 monitor_telemetry.py
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

class TelemetryMonitor:
    def __init__(self):
        self.last_update = None
        self.battery_soc = None
        self.fsm_state = None
        self.position = {'x': 0, 'y': 0, 'z': 0}
        
    def update_state(self, msg):
        """Handle sportmodestate messages"""
        try:
            if 'data' in msg:
                data = json.loads(msg['data']) if isinstance(msg['data'], str) else msg['data']
                
                # Update FSM state
                if 'mode' in data:
                    self.fsm_state = data['mode']
                
                # Update position (odometry)
                if 'position' in data:
                    pos = data['position']
                    self.position = {
                        'x': pos.get('x', 0),
                        'y': pos.get('y', 0),
                        'z': pos.get('z', 0)
                    }
                
                self.last_update = datetime.now()
                self.display()
        except Exception as e:
            pass  # Silent errors for cleaner display
    
    def update_battery(self, msg):
        """Handle battery state messages"""
        try:
            if 'data' in msg:
                data = json.loads(msg['data']) if isinstance(msg['data'], str) else msg['data']
                
                if 'soc' in data:
                    self.battery_soc = data['soc']
                    self.display()
        except Exception as e:
            pass
    
    def display(self):
        """Clear screen and show current telemetry"""
        # ANSI codes for cursor control
        print('\033[2J\033[H', end='')  # Clear screen, move cursor to top
        
        print("=" * 60)
        print("G1 ROBOT TELEMETRY MONITOR")
        print("=" * 60)
        
        if self.last_update:
            print(f"\n🕒 Last Update: {self.last_update.strftime('%H:%M:%S')}")
        
        print(f"\n🔋 Battery: {self.battery_soc}%" if self.battery_soc is not None else "\n🔋 Battery: --")
        print(f"🤖 FSM State: {self.fsm_state}" if self.fsm_state is not None else "🤖 FSM State: --")
        
        print(f"\n📍 Position:")
        print(f"   X: {self.position['x']:.3f} m")
        print(f"   Y: {self.position['y']:.3f} m")
        print(f"   Z: {self.position['z']:.3f} m")
        
        print("\n(Press Ctrl+C to exit)")

async def main():
    monitor = TelemetryMonitor()
    
    async with RobotTestConnection() as robot:
        print("🔌 Connected! Monitoring telemetry...\n")
        
        # Subscribe to key topics
        await robot.subscribe('rt/lf/sportmodestate', monitor.update_state)
        await robot.subscribe('rt/lf/bmsstate', monitor.update_battery)
        
        # Keep running until interrupted
        try:
            while True:
                await asyncio.sleep(0.5)
        except KeyboardInterrupt:
            print("\n\n👋 Exiting monitor...")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n")
