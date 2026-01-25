#!/usr/bin/env python3
"""Simulate EXACT JavaScript flow from the browser"""
import requests
import time

BASE_URL = "http://localhost:8000"

print("=" * 70)
print("SIMULATING BROWSER JAVASCRIPT FLOW")
print("=" * 70)

# Step 1: Disconnect (cleanup)
print("\n[Cleanup] POST /api/disconnect")
resp = requests.post(f"{BASE_URL}/api/disconnect")
print(f"  Status: {resp.status_code}")
time.sleep(1)

# Step 2: Connect (what connect() function does)
print("\n[Connect Button Clicked]")
print("1. POST /api/connect")
resp = requests.post(f"{BASE_URL}/api/connect?ip=192.168.86.2&serial_number=E21D1000PAHBMB06")
print(f"   Status: {resp.status_code}")
connect_data = resp.json()
print(f"   Response: {connect_data}")

if connect_data.get('success') and 'state' in connect_data:
    # This is what updateRobotState() does
    currentFsmState = connect_data['state']['fsm_state']
    allowedTransitions = connect_data['state'].get('allowed_transitions', [])
    
    print(f"\n   JavaScript variables after updateRobotState():")
    print(f"   - currentFsmState = '{currentFsmState}'")
    print(f"   - allowedTransitions = {allowedTransitions}")
    print(f"   - allowedTransitions.length = {len(allowedTransitions)}")
    
    # updateStateButtons() would run here
    print(f"\n   Buttons that would be ENABLED:")
    for state in allowedTransitions:
        print(f"     ✓ {state}")
    
    if len(allowedTransitions) == 0:
        print(f"     (NONE - only current state '{currentFsmState}' would be enabled)")

# Step 3: Wait 1 second (what the connect() function does)
print("\n2. Waiting 1 second...")
time.sleep(1)

# Step 4: refreshState() called
print("\n3. refreshState() - GET /api/state")
resp = requests.get(f"{BASE_URL}/api/state?_=" + str(int(time.time() * 1000)))
print(f"   Status: {resp.status_code}")
state_data = resp.json()
print(f"   Response: {state_data}")

if state_data.get('success') and 'state' in state_data:
    # This is what refreshState() does
    currentFsmState = state_data['state']['fsm_state']
    allowedTransitions = state_data['state'].get('allowed_transitions', [])
    
    print(f"\n   JavaScript variables after refreshState():")
    print(f"   - currentFsmState = '{currentFsmState}'")
    print(f"   - allowedTransitions = {allowedTransitions}")
    print(f"   - allowedTransitions.length = {len(allowedTransitions)}")
    
    # updateStateButtons() would run here
    print(f"\n   Buttons that would be ENABLED:")
    for state in allowedTransitions:
        print(f"     ✓ {state}")

# Step 5: Verify final state
print("\n" + "=" * 70)
print("EXPECTED UI STATE:")
print("=" * 70)
print(f"FSM State Display: {currentFsmState}")
print(f"Enabled Buttons: {len(allowedTransitions)} buttons")
print(f"Button List: {', '.join(allowedTransitions)}")

if len(allowedTransitions) == 9:
    print("\n✅ SUCCESS: 9 buttons should be enabled!")
elif len(allowedTransitions) == 2:
    print("\n❌ FAILURE: Only 2 buttons enabled (ZERO_TORQUE, DAMP)")
    print("   The refreshState() call didn't update the buttons properly")
else:
    print(f"\n❓ UNEXPECTED: {len(allowedTransitions)} buttons enabled")

# Cleanup
print("\n[Cleanup] POST /api/disconnect")
resp = requests.post(f"{BASE_URL}/api/disconnect")
print(f"  Status: {resp.status_code}\n")
