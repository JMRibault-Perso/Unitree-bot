#!/usr/bin/env python3
"""
Test the exact web UI flow
"""
import requests
import time
import json

BASE_URL = "http://localhost:8000"

print("="*80)
print("SIMULATING WEB UI FLOW")
print("="*80)

# 1. Connect
print("\n1. POST /api/connect")
resp = requests.post(f"{BASE_URL}/api/connect", params={
    "ip": "192.168.86.2",
    "serial_number": "E21D1000PAHBMB06"
})
print(f"Response: {json.dumps(resp.json(), indent=2)}")

# 2. Wait a moment (simulate what browser does)
print("\n2. Waiting 2 seconds for state to stabilize...")
time.sleep(2)

# 3. Get state (this is what refreshState() calls)
print("\n3. GET /api/state (this is refreshState())")
resp = requests.get(f"{BASE_URL}/api/state")
data = resp.json()
print(f"Response: {json.dumps(data, indent=2)}")

if data.get("success"):
    state = data["state"]
    print(f"\n{'='*80}")
    print(f"Current FSM State: {state['fsm_state']}")
    print(f"Allowed Transitions: {state['allowed_transitions']}")
    print(f"Count: {len(state['allowed_transitions'])}")
    print(f"{'='*80}")
    
    if len(state['allowed_transitions']) != 9:
        print(f"\n❌ PROBLEM: Only {len(state['allowed_transitions'])} transitions!")
        print(f"Expected 9 transitions from RUN state")
        print(f"Getting transitions for: {state['fsm_state']}")
    else:
        print(f"\n✅ Correct: 9 transitions found")

# 4. Disconnect
print("\n4. POST /api/disconnect")
resp = requests.post(f"{BASE_URL}/api/disconnect")
print(f"Response: {json.dumps(resp.json(), indent=2)}")
