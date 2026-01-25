#!/usr/bin/env python3
"""
Test the actual web server API to see what it returns
"""
import requests
import time
import json

BASE_URL = "http://localhost:8000"

def test_api():
    print("="*80)
    print("TESTING WEB SERVER API")
    print("="*80)
    
    # 1. Connect to robot
    print("\n1. Connecting to robot...")
    resp = requests.post(f"{BASE_URL}/api/connect", params={
        "ip": "192.168.86.2",
        "serial_number": "E21D1000PAHBMB06"
    })
    print(f"Status: {resp.status_code}")
    print(f"Response: {json.dumps(resp.json(), indent=2)}")
    
    if not resp.json().get("success"):
        print("❌ Connection failed!")
        return False
    
    # Wait for connection to stabilize
    time.sleep(2)
    
    # 2. Get current state and allowed transitions
    print("\n2. Getting current state...")
    resp = requests.get(f"{BASE_URL}/api/state")
    print(f"Status: {resp.status_code}")
    data = resp.json()
    print(f"Response: {json.dumps(data, indent=2)}")
    
    if not data.get("success"):
        print("❌ Failed to get state!")
        return False
    
    state = data["state"]
    current_state = state["fsm_state"]
    allowed = state["allowed_transitions"]
    
    print(f"\n{'='*80}")
    print(f"Current State: {current_state}")
    print(f"Allowed Transitions ({len(allowed)}):")
    for t in allowed:
        print(f"  - {t}")
    print(f"{'='*80}")
    
    # 3. Test debug endpoint
    print("\n3. Testing debug endpoint...")
    resp = requests.get(f"{BASE_URL}/api/debug/transitions")
    print(f"Status: {resp.status_code}")
    print(f"Response: {json.dumps(resp.json(), indent=2)}")
    
    # 4. Verify expected transitions
    print(f"\n{'='*80}")
    print("VERIFICATION:")
    print(f"{'='*80}")
    
    expected = ["LOCK_STAND", "LOCK_STAND_ADV", "STAND_TO_SQUAT", "DAMP", "ZERO_TORQUE", "START", "SIT"]
    
    for exp in expected:
        found = exp in allowed
        symbol = "✓" if found else "✗"
        print(f"{symbol} {exp:20s} - {'FOUND' if found else 'MISSING'}")
    
    missing = [e for e in expected if e not in allowed]
    if missing:
        print(f"\n❌ FAILED: Missing transitions: {missing}")
        print(f"Only showing: {allowed}")
        return False
    else:
        print(f"\n✅ SUCCESS: All expected transitions found!")
        return True

if __name__ == "__main__":
    import sys
    try:
        success = test_api()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
