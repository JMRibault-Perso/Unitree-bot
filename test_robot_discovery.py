#!/usr/bin/env python3
"""
Test robot discovery by listening for multicast announcements
"""
import sys
sys.path.insert(0, '/root/G1/unitree_sdk2')

import asyncio
import logging
from g1_app.core.robot_discovery import get_discovery

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)

async def main():
    discovery = get_discovery()
    
    print("=" * 70)
    print("Robot Discovery Test")
    print("=" * 70)
    print("\nStarting multicast listener on 231.1.1.2:10134...")
    print("Robots will announce themselves on this multicast address.\n")
    
    discovery.start()
    
    print("Listening for 15 seconds... (Power on your robot if it's off)")
    print("Press Ctrl+C to stop early\n")
    
    try:
        for i in range(15):
            await asyncio.sleep(1)
            robots = discovery.get_robots()
            
            if robots:
                print(f"\n[{i+1}s] Found {len(robots)} robot(s):")
                for robot in robots:
                    print(f"  • {robot.name} ({robot.serial_number})")
                    print(f"    IP: {robot.ip}")
                    if robot.key:
                        print(f"    Key: {robot.key}")
                    print(f"    Last seen: {robot.last_seen.strftime('%H:%M:%S')}")
            else:
                if (i + 1) % 3 == 0:
                    print(f"[{i+1}s] No robots discovered yet...")
                    
    except KeyboardInterrupt:
        print("\n\nStopped by user")
    
    print("\n" + "=" * 70)
    print("Final Results:")
    print("=" * 70)
    
    robots = discovery.get_robots()
    if robots:
        for robot in robots:
            print(f"\n✅ Robot: {robot.name}")
            print(f"   Serial: {robot.serial_number}")
            print(f"   IP:     {robot.ip}")
            print(f"   Status: Online")
    else:
        print("\n❌ No robots discovered")
        print("\nPossible reasons:")
        print("  1. Robot is not powered on")
        print("  2. Robot is not on the same network")
        print("  3. Multicast is blocked by firewall/router")
        print("  4. Robot may not broadcast discovery packets (model dependent)")
    
    discovery.stop()
    print("\nDiscovery service stopped.")

if __name__ == '__main__':
    asyncio.run(main())
