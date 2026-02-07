#!/usr/bin/env python3
"""
Simple G1 controller - sends commands without waiting for responses
This avoids connection timeout issues
"""
import asyncio
import sys
sys.path.insert(0, '/root/G1/go2_webrtc_connect')

from unitree_webrtc_connect.webrtc_driver import UnitreeWebRTCConnection
from unitree_webrtc_connect.constants import WebRTCConnectionMethod

ROBOT_IP = "192.168.86.16"
ROBOT_SN = "E21D1000PAHBMB06"

# Command IDs from SPORT_CMD
COMMANDS = {
    'd': ('DAMP', 1001),
    'r': ('READY', 1005),
    'b': ('BALANCE_STAND', 1002),
    'u': ('STAND_UP', 1004),
    's': ('SIT', 1009),
    'h': ('HELLO', 1016),
}

async def send_quick_command(cmd_key):
    """Send a command and disconnect immediately"""
    if cmd_key not in COMMANDS:
        print(f"❌ Unknown command: {cmd_key}")
        return
    
    name, api_id = COMMANDS[cmd_key]
    
    print(f"📤 Sending {name} (api_id: {api_id})...")
    
    try:
        conn = UnitreeWebRTCConnection(
            WebRTCConnectionMethod.LocalSTA,
            ip=ROBOT_IP,
            serialNumber=ROBOT_SN
        )
        await conn.connect()
        
        # Wait for data channel to be ready
        await asyncio.sleep(1.0)
        
        # Send command
        await conn.datachannel.pub_sub.publish_request_new(
            "rt/api/sport/request",
            {"api_id": api_id}
        )
        
        # Wait briefly for command to be sent
        await asyncio.sleep(0.5)
        
        print(f"✅ {name} sent!")
        
        await conn.disconnect()
        
    except Exception as e:
        print(f"❌ Error: {e}")

async def interactive():
    """Interactive mode - send commands one at a time"""
    print("=" * 60)
    print("G1 QUICK CONTROL - Send commands quickly")
    print("=" * 60)
    print("\n⚠️  PROPER SEQUENCE: d → r → b/u/s/h")
    print("\nCommands:")
    print("  d = DAMP mode (Step 1)")
    print("  r = READY mode (Step 2)")
    print("  b = BALANCE STAND")
    print("  u = STAND UP")
    print("  s = SIT")
    print("  h = HELLO")
    print("  q = quit\n")
    
    while True:
        cmd = input("Command [d/r/b/u/s/h/q] > ").strip().lower()
        
        if cmd == 'q':
            break
        
        await send_quick_command(cmd)
        print()
    
    print("✅ Done!")

if __name__ == "__main__":
    asyncio.run(interactive())
