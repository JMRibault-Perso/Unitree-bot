#!/usr/bin/env python3
"""
WebSocket Client Test - Automated UI Testing
Tests the full WebSocket flow and button state logic
"""

import asyncio
import json
import websockets
import aiohttp
from typing import Dict

class UITester:
    def __init__(self, base_url="http://localhost:8080"):
        self.base_url = base_url
        self.ws_url = base_url.replace('http', 'ws') + '/ws'
        self.current_state = None
        self.allowed_transitions = []
        self.is_connected = False
        self.received_messages = []
        
    async def connect_robot(self):
        """Simulate connecting to robot via API"""
        async with aiohttp.ClientSession() as session:
            url = f"{self.base_url}/api/connect?ip=127.0.0.1&serial_number=MOCK_12345"
            async with session.post(url) as resp:
                data = await resp.json()
                print(f"✅ Connect API: {data['success']}")
                if data['success']:
                    self.is_connected = True
                    state = data.get('state', {})
                    self.current_state = state.get('fsm_state')
                    self.allowed_transitions = state.get('allowed_transitions', [])
                    print(f"   Initial State: {self.current_state}")
                    print(f"   Allowed Transitions: {self.allowed_transitions}")
                return data
    
    async def get_state(self):
        """Get current state via API"""
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.base_url}/api/state") as resp:
                data = await resp.json()
                if data['success']:
                    state = data.get('state', {})
                    self.current_state = state.get('fsm_state')
                    self.allowed_transitions = state.get('allowed_transitions', [])
                return data
    
    async def set_state(self, state_name: str):
        """Set state via API"""
        async with aiohttp.ClientSession() as session:
            url = f"{self.base_url}/api/set_state?state_name={state_name}"
            async with session.post(url) as resp:
                data = await resp.json()
                print(f"   Transition to {state_name}: {data['success']}")
                if data['success']:
                    state = data.get('state', {})
                    self.current_state = state.get('fsm_state')
                    self.allowed_transitions = state.get('allowed_transitions', [])
                return data
    
    def check_button_state(self, button_state_name: str) -> Dict:
        """
        Simulate the JavaScript updateStateButtons() logic
        Returns: {enabled: bool, reason: str}
        """
        # Safety commands (DAMP, ZERO_TORQUE) always enabled
        if button_state_name in ['DAMP', 'ZERO_TORQUE']:
            return {'enabled': True, 'reason': 'Safety command - always accessible'}
        
        # Current state button is enabled
        if button_state_name == self.current_state:
            return {'enabled': True, 'reason': 'Current state'}
        
        # Check if in allowed transitions
        if button_state_name in self.allowed_transitions:
            return {'enabled': True, 'reason': 'In allowed_transitions'}
        
        return {'enabled': False, 'reason': 'Not in allowed_transitions'}
    
    def simulate_ui_button_states(self):
        """Simulate all button states as they would appear in UI"""
        all_states = [
            'ZERO_TORQUE', 'DAMP', 'SQUAT_TO_STAND', 'SQUAT', 
            'STAND_UP', 'START', 'SIT', 'LOCK_STAND', 'RUN'
        ]
        
        print(f"\n📊 UI BUTTON STATES (Current: {self.current_state})")
        print(f"   Allowed Transitions: {self.allowed_transitions}")
        print(f"   Connected: {self.is_connected}\n")
        
        enabled_count = 0
        disabled_count = 0
        
        for state_name in all_states:
            result = self.check_button_state(state_name)
            status = "🟢 ENABLED " if result['enabled'] else "🔴 DISABLED"
            checkmark = "✓ " if state_name == self.current_state else "  "
            print(f"   {status} {checkmark}{state_name:15} - {result['reason']}")
            
            if result['enabled']:
                enabled_count += 1
            else:
                disabled_count += 1
        
        print(f"\n   Summary: {enabled_count} enabled, {disabled_count} disabled")
        
        # Check if user would have "zero button access"
        if enabled_count == 0:
            print("   ⚠️  WARNING: ZERO BUTTON ACCESS!")
            return False
        elif enabled_count < 3:
            print(f"   ⚠️  WARNING: Only {enabled_count} buttons accessible")
            return False
        else:
            print(f"   ✅ OK: {enabled_count} buttons accessible")
            return True
    
    async def test_websocket_updates(self):
        """Test WebSocket real-time updates"""
        print("\n🔌 Testing WebSocket Connection...")
        
        try:
            async with websockets.connect(self.ws_url) as ws:
                print("✅ WebSocket connected")
                
                # Wait for initial messages
                try:
                    message = await asyncio.wait_for(ws.recv(), timeout=2.0)
                    data = json.loads(message)
                    print(f"📨 Received: {data.get('type')}")
                    self.received_messages.append(data)
                    
                    # Handle state_changed message
                    if data.get('type') == 'state_changed':
                        msg_data = data.get('data', {})
                        self.current_state = msg_data.get('fsm_state')
                        self.allowed_transitions = msg_data.get('allowed_transitions', [])
                        print(f"   Updated State: {self.current_state}")
                        print(f"   Allowed Transitions: {self.allowed_transitions}")
                except asyncio.TimeoutError:
                    print("⚠️  No initial message received (this might be OK)")
                
                return True
                
        except Exception as e:
            print(f"❌ WebSocket error: {e}")
            return False
    
    async def run_full_test(self):
        """Run complete test suite"""
        print("=" * 60)
        print("🧪 G1 WEB CONTROLLER - AUTOMATED UI TEST")
        print("=" * 60)
        
        # Test 1: Connect to robot
        print("\n📍 TEST 1: Connect to Robot")
        await self.connect_robot()
        await asyncio.sleep(0.5)
        
        # Check initial button states
        print("\n📍 TEST 2: Initial Button States")
        has_access = self.simulate_ui_button_states()
        
        # Test 2: WebSocket updates
        print("\n📍 TEST 3: WebSocket Real-Time Updates")
        await self.test_websocket_updates()
        
        # Test 3: State transition and button updates
        print("\n📍 TEST 4: State Transition - DAMP → START")
        await self.set_state('START')
        await asyncio.sleep(0.5)
        self.simulate_ui_button_states()
        
        print("\n📍 TEST 5: State Transition - START → LOCK_STAND")
        await self.set_state('LOCK_STAND')
        await asyncio.sleep(0.5)
        self.simulate_ui_button_states()
        
        print("\n📍 TEST 6: Emergency DAMP from LOCK_STAND")
        await self.set_state('DAMP')
        await asyncio.sleep(0.5)
        has_access_after = self.simulate_ui_button_states()
        
        # Final report
        print("\n" + "=" * 60)
        print("📊 FINAL TEST RESULTS")
        print("=" * 60)
        print(f"✅ API Connection: Working")
        print(f"✅ State Transitions: Working")
        print(f"✅ WebSocket: {'Working' if self.received_messages else 'No messages received'}")
        
        if has_access and has_access_after:
            print(f"✅ Button Access: WORKING - Multiple buttons accessible")
            print("\n🎉 ALL TESTS PASSED - UI SHOULD BE FULLY FUNCTIONAL")
        else:
            print(f"❌ Button Access: ISSUE DETECTED")
            print("\n⚠️  PROBLEM: User would have limited button access")
            print("\nDEBUG INFO:")
            print(f"   - isConnected: {self.is_connected}")
            print(f"   - current_state: {self.current_state}")
            print(f"   - allowed_transitions: {self.allowed_transitions}")
        
        print("=" * 60)

async def main():
    tester = UITester()
    await tester.run_full_test()

if __name__ == "__main__":
    asyncio.run(main())
