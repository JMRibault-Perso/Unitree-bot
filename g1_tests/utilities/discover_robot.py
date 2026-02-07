#!/usr/bin/env python3
"""
G1 Robot Discovery
Auto-discover G1 robot on network via ARP MAC address scan

Usage:
    python3 discover_robot.py
"""

import asyncio
import sys
from pathlib import Path

repo_root = Path(__file__).resolve().parents[2]
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

# Import the ARP discovery function
from g1_app.utils.arp_discovery import discover_robot_ip

async def main():
    print("\n🔍 Discovering G1 robot via ARP scan...")
    print("   Looking for MAC: fc:23:cd:92:60:02\n")
    
    robot_ip = discover_robot_ip()
    
    if robot_ip:
        print(f"✅ Found robot at: {robot_ip}\n")
        print("Next steps:")
        print(f"  1. Verify connection: ping {robot_ip}")
        print("  2. Test WebRTC: python3 verify_connection.py")
        print("  3. Run tests from g1_tests/ directories\n")
        return 0
    else:
        print("❌ Robot not found on network\n")
        print("Troubleshooting:")
        print("  1. Verify robot is powered on")
        print("  2. Check robot is on same WiFi network")
        print("  3. Check WiFi LED indicator on robot")
        print("  4. Try switching to AP mode if STA mode fails\n")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
