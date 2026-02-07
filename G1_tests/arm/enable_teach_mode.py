#!/usr/bin/env python3
"""
G1 Robot Teach Mode Controller
Enter/exit zero-gravity teach mode for recording arm movements

Usage:
    python3 enable_teach_mode.py          # Enable teach mode
    python3 enable_teach_mode.py --disable  # Disable teach mode
"""

import asyncio
import argparse
import sys
from pathlib import Path

repo_root = Path(__file__).resolve().parents[2]
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))
from robot_test_helpers import RobotTestConnection

async def main():
    parser = argparse.ArgumentParser(description='G1 Teach Mode Control')
    parser.add_argument('--disable', action='store_true',
                       help='Disable teach mode instead of enabling')
    args = parser.parse_args()
    
    async with RobotTestConnection() as robot:
        if args.disable:
            print("\n🔒 Disabling teach mode...")
            api_id = 7111  # DISABLE_TEACH_MODE
            action = "disable"
        else:
            print("\n🎓 Enabling teach mode (zero-gravity)...")
            api_id = 7110  # ENABLE_TEACH_MODE
            action = "enable"
        
        payload = {
            'api_id': api_id,
            'parameter': '{}'
        }
        
        await robot.datachannel.pub_sub.publish_request_new(
            'rt/api/arm_action/request',
            payload
        )
        
        await asyncio.sleep(0.5)
        
        if args.disable:
            print("✅ Teach mode disabled - arms back to normal control\n")
        else:
            print("✅ Teach mode enabled - arms are now in zero-gravity!")
            print("   You can physically move them to any position.\n")
            print("⚠️  Remember to disable teach mode when done:\n")
            print("   python3 enable_teach_mode.py --disable\n")

if __name__ == "__main__":
    asyncio.run(main())
