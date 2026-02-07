#!/usr/bin/env python3
"""
G1 Robot Simple Motion Controller
Interactive FSM command sender following standardized pattern

Commands:
  d = DAMP mode (zero torque, safe)
  r = READY mode (standing, ready for motion)
  b = BALANCE STAND
  u = STAND UP
  s = SIT
  h = HELLO (wave gesture)
  q = quit

Sequence: DAMP → READY → Motion commands
"""

import asyncio
import sys
from pathlib import Path

repo_root = Path(__file__).resolve().parents[2]
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))
from robot_test_helpers import RobotTestConnection

# Motion command API IDs
COMMANDS = {
    'd': 1001,  # DAMP (L2+B) - Zero torque
    'r': 1005,  # READY (L2+UP) - Standing ready
    'b': 1002,  # BALANCE_STAND
    'u': 1004,  # STAND_UP
    's': 1009,  # SIT
    'h': 1016,  # HELLO (wave)
    'q': None,  # Quit
}

COMMAND_NAMES = {
    'd': 'DAMP',
    'r': 'READY',
    'b': 'BALANCE_STAND',
    'u': 'STAND_UP',
    's': 'SIT',
    'h': 'HELLO'
}

async def send_motion_command(robot, api_id, name):
    """Send motion command via sport_request API"""
    print(f"📤 Sending {name} (api_id: {api_id})...")
    
    payload = {
        'api_id': api_id,
        'parameter': '{}'
    }
    
    # Publish to sport control topic
    topic = 'rt/api/sport/request'
    await robot.datachannel.pub_sub.publish_request_new(topic, payload)
    
    print(f"✅ {name} command sent!")
    await asyncio.sleep(0.1)  # Processing delay

async def main():
    async with RobotTestConnection() as robot:
        print("\n" + "=" * 60)
        print("G1 SIMPLE MOTION CONTROLLER")
        print("=" * 60)
        print("\n⚠️  SEQUENCE: d (Damp) → r (Ready) → b/u/s/h (Motion)\n")
        print("Commands:")
        print("  d = DAMP mode (zero torque, SAFE)")
        print("  r = READY mode (standing)")
        print("  b = BALANCE STAND")
        print("  u = STAND UP")
        print("  s = SIT")
        print("  h = HELLO (wave)")
        print("  q = quit\n")
        
        while True:
            try:
                cmd = input("Command > ").strip().lower()
                
                if cmd == 'q':
                    print("\n👋 Exiting...")
                    break
                elif cmd in COMMANDS and COMMANDS[cmd]:
                    await send_motion_command(
                        robot,
                        COMMANDS[cmd],
                        COMMAND_NAMES[cmd]
                    )
                else:
                    print(f"❌ Unknown command: {cmd}")
                    
            except EOFError:
                print("\n👋 Exiting...")
                break

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted! Exiting...")
