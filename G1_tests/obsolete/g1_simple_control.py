#!/usr/bin/env python3
"""
G1 Robot Simple Controller - Quick command sender
"""

import asyncio
import sys
sys.path.insert(0, '/root/G1/go2_webrtc_connect')

from unitree_webrtc_connect.webrtc_driver import UnitreeWebRTCConnection
from unitree_webrtc_connect.constants import WebRTCConnectionMethod

ROBOT_IP = "192.168.86.16"
ROBOT_SN = "E21D1000PAHBMB06"

# FSM Sequence: Zero Torque → Damp → Ready → Motion
COMMANDS = {
    'd': 1001,  # Damp (L2+B)
    'r': 1005,  # Ready (L2+UP)
    'b': 1002,  # Balance Stand
    'u': 1004,  # Stand Up
    's': 1009,  # Sit
    'h': 1016,  # Hello
    'q': None,  # Quit
}

async def send_command(conn, api_id, name):
    """Send command without waiting"""
    print(f"📤 Sending {name} (api_id: {api_id})...")
    payload = {"api_id": api_id}
    conn.publish_request_new(payload)
    print(f"✅ Sent!")
    await asyncio.sleep(0.5)  # Brief pause

async def main():
    print("🔌 Connecting to G1...")
    conn = UnitreeWebRTCConnection(
        connectionMethod=WebRTCConnectionMethod.LocalSTA,
        serialNumber=ROBOT_SN,
        ip=ROBOT_IP
    )
    
    try:
        await conn.connect()
        print("✅ Connected!\n")
        
        print("=" * 60)
        print("SIMPLE G1 CONTROLLER")
        print("=" * 60)
        print("\n⚠️  SEQUENCE: d (Damp) → r (Ready) → b/u/s/h (Motion)\n")
        print("Commands:")
        print("  d = DAMP mode")
        print("  r = READY mode")
        print("  b = BALANCE STAND")
        print("  u = STAND UP")
        print("  s = SIT")
        print("  h = HELLO")
        print("  q = quit\n")
        
        while True:
            cmd = input("Command > ").strip().lower()
            
            if cmd == 'q':
                break
            elif cmd in COMMANDS and COMMANDS[cmd]:
                names = {
                    'd': 'DAMP',
                    'r': 'READY',
                    'b': 'BALANCE_STAND',
                    'u': 'STAND_UP',
                    's': 'SIT',
                    'h': 'HELLO'
                }
                await send_command(conn, COMMANDS[cmd], names[cmd])
            else:
                print(f"❌ Unknown: {cmd}")
        
        print("\n✅ Disconnecting...")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted!")
    finally:
        await conn.disconnect()
        print("🔌 Disconnected")

if __name__ == "__main__":
    asyncio.run(main())
