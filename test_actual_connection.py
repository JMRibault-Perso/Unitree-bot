#!/usr/bin/env python3
"""Test the ACTUAL connection flow to see what state/transitions are returned"""
import requests
import time

BASE_URL = "http://localhost:9000"

print("=" * 60)
print("Testing ACTUAL Connection Flow")
print("=" * 60)

# Step 0: Disconnect if already connected
print("\n0. POST /api/disconnect (cleanup)")
resp = requests.post(f"{BASE_URL}/api/disconnect")
print(f"Status: {resp.status_code}")
time.sleep(1)

# Step 1: Connect
print("\n1. POST /api/connect")
resp = requests.post(f"{BASE_URL}/api/connect?ip=192.168.86.2&serial_number=E21D1000PAHBMB06")
print(f"Status: {resp.status_code}")
if resp.status_code != 200:
    print("ERROR: Non-200 status. Response:", resp.text)
    exit(1)
data = resp.json()
print(f"Success: {data.get('success')}")
if 'state' in data:
    print(f"Initial State from connect: {data['state']['fsm_state']}")
    print(f"Initial Transitions from connect: {data['state'].get('allowed_transitions', [])}")
    print(f"Initial Transitions count: {len(data['state'].get('allowed_transitions', []))}")

# Step 2: Wait 1 second (matching UI behavior)
print("\n2. Waiting 1 second...")
time.sleep(1)

# Step 3: Get state (what refreshState() does)
print("\n3. GET /api/state (after 1 second)")
resp = requests.get(f"{BASE_URL}/api/state")
print(f"Status: {resp.status_code}")
data = resp.json()
print(f"Success: {data.get('success')}")
if 'state' in data:
    print(f"FSM State: {data['state']['fsm_state']}")
    print(f"Allowed Transitions: {data['state'].get('allowed_transitions', [])}")
    print(f"Transitions count: {len(data['state'].get('allowed_transitions', []))}")
    
    transitions = data['state'].get('allowed_transitions', [])
    expected = ['ZERO_TORQUE', 'DAMP', 'SQUAT_TO_STAND', 'SIT', 'STAND_TO_SQUAT', 
                'LYING_STAND', 'START', 'LOCK_STAND', 'LOCK_STAND_ADV']
    
    if len(transitions) == 9:
        print("\n✅ SUCCESS: Got 9 transitions as expected!")
    elif len(transitions) == 2:
        print("\n❌ PROBLEM: Only got 2 transitions (ZERO_TORQUE and DAMP)")
        print("   This means robot is still in ZERO_TORQUE state, not RUN state")
    else:
        print(f"\n❓ UNEXPECTED: Got {len(transitions)} transitions")

# Step 4: Disconnect
print("\n4. POST /api/disconnect")
resp = requests.post(f"{BASE_URL}/api/disconnect")
print(f"Status: {resp.status_code}")
print(f"Success: {resp.json().get('success')}")

print("\n" + "=" * 60)
