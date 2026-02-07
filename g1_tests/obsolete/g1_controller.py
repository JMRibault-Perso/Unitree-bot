#!/usr/bin/env python3
"""
G1 Robot Controller - Android App Replacement
Sends locomotion commands via WebRTC-DDS
"""

import asyncio
import json
import sys
sys.path.insert(0, '/root/G1/go2_webrtc_connect')

from unitree_webrtc_connect.webrtc_driver import UnitreeWebRTCConnection
from unitree_webrtc_connect.constants import WebRTCConnectionMethod

# Robot config
ROBOT_IP = "192.168.86.16"
ROBOT_SN = "E21D1000PAHBMB06"

# G1 Locomotion commands (uses "sport" service with LocoClient API)
# From g1_loco_api.py: ROBOT_API_ID_LOCO_SET_FSM_ID = 7101
# G1 uses SetFsmId() to control state machine, not individual sport commands
#
# FSM States (from official SDK):
#   0 = Zero Torque
#   1 = Damp
#   200 = Start/Ready
#   706 = Squat2StandUp
#
# The command format for G1 is:
#   {"api_id": 7101, "parameter": json.dumps({"data": <fsm_id>})}

LOCO_API_SET_FSM_ID = 7101

# FSM States
FSM_STATES = {
    'zero_torque': 0,
    'damp': 1,
    'start': 200,      # Ready mode
    'squat2stand': 706,
    'sit': 3,
    'stand2squat': 706,
}

class G1Controller:
    def __init__(self):
        self.conn = None
        self.connected = False
        self.last_response = None
        self.response_received = asyncio.Event()
        self.current_task_id = None
        self.current_fsm_mode = None
    
    async def connect(self):
        """Establish WebRTC connection"""
        print(f"🔌 Connecting to G1 at {ROBOT_IP}...")
        
        self.conn = UnitreeWebRTCConnection(
            WebRTCConnectionMethod.LocalSTA,
            ip=ROBOT_IP,
            serialNumber=ROBOT_SN
        )
        
        await self.conn.connect()
        self.connected = True
        
        # Subscribe to sport mode state to monitor task changes
        def on_sport_state(data):
            if isinstance(data, dict) and 'data' in data:
                state = data['data']
                task_id = state.get('task_id')
                fsm_mode = state.get('fsm_mode')
                
                if task_id != self.current_task_id or fsm_mode != self.current_fsm_mode:
                    self.current_task_id = task_id
                    self.current_fsm_mode = fsm_mode
                    print(f"🤖 Robot mode changed: task_id={task_id}, fsm_mode={fsm_mode}")
                    self.response_received.set()
        
        # Subscribe to state topic
        try:
            self.conn.datachannel.pub_sub.subscribe("rt/lf/sportmodestate", on_sport_state)
            print(f"📡 Subscribed to rt/lf/sportmodestate")
        except Exception as e:
            print(f"⚠️  Could not subscribe: {e}")
        
        print("✅ Connected!\n")
    
    async def send_command(self, cmd_name, params=None, wait_for_response=False):
        """Send G1 loco command using SetFsmId API"""
        if not self.connected:
            print("❌ Not connected!")
            return False
        
        if cmd_name not in FSM_STATES:
            print(f"❌ Unknown command: {cmd_name}")
            return False
        
        fsm_id = FSM_STATES[cmd_name]
        
        # G1 uses API 7101 (SetFsmId) with {"data": fsm_id}
        payload = {
            "api_id": LOCO_API_SET_FSM_ID,
            "parameter": json.dumps({"data": fsm_id})
        }
        
        print(f"→ Sending: {cmd_name.upper()} (FSM ID: {fsm_id})")
        
        await self.conn.datachannel.pub_sub.publish_request_new(
            "rt/api/sport/request",
            payload
        )
        
        # Just wait a bit to ensure command is sent
        await asyncio.sleep(0.3)
        print(f"✅ {cmd_name} sent!")
        
        return True
    
    async def disconnect(self):
        """Close connection"""
        if self.conn:
            await self.conn.disconnect()
            print("\n🔌 Disconnected")

async def demo_sequence():
    """Manual toggle with response monitoring"""
    controller = G1Controller()
    
    try:
        await controller.connect()
        
        print("=" * 60)
        print("TOGGLE CONTROLLER WITH MODE MONITORING")
        print("=" * 60)
        print(f"\nCurrent state: task_id={controller.current_task_id}, fsm_mode={controller.current_fsm_mode}")
        print("\n⚠️  PROPER SEQUENCE: Zero Torque → Damp → Start (Ready)")
        print("\nCommands:")
        print("  z = ZERO TORQUE (FSM 0)")
        print("  d = DAMP mode (FSM 1)")
        print("  s = START/READY mode (FSM 200)")
        print("  u = SQUAT TO STAND (FSM 706)")
        print("  q = quit\n")
        
        while True:
            cmd = input("Command [z/d/s/u/q] > ").strip().lower()
            
            if cmd == 'q':
                break
            elif cmd == 'z':
                print("📤 Sending ZERO TORQUE...")
                await controller.send_command('zero_torque')
            elif cmd == 'd':
                print("📤 Sending DAMP...")
                await controller.send_command('damp')
            elif cmd == 's':
                print("📤 Sending START (Ready)...")
                await controller.send_command('start')
            elif cmd == 'u':
                print("📤 Sending SQUAT TO STAND...")
                await controller.send_command('squat2stand')
            else:
                print(f"❌ Unknown: {cmd}")
            
            await asyncio.sleep(0.5)
        
        print("\n✅ Done!")
        
    finally:
        await controller.disconnect()

async def interactive_mode():
    """Interactive command sender"""
    controller = G1Controller()
    
    try:
        await controller.connect()
        
        print("=" * 60)
        print("INTERACTIVE MODE")
        print("=" * 60)
        print("\nAvailable commands:")
        for cmd in COMMANDS:
            print(f"  - {cmd}")
        print("\nType 'quit' to exit\n")
        
        while True:
            cmd = input("Command > ").strip().lower()
            
            if cmd == 'quit':
                break
            elif cmd in COMMANDS:
                await controller.send_command(cmd)
                await asyncio.sleep(0.5)
            else:
                print(f"❌ Unknown: {cmd}")
        
    finally:
        await controller.disconnect()

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == '--interactive':
        asyncio.run(interactive_mode())
    else:
        asyncio.run(demo_sequence())
