#!/usr/bin/env python3
"""
Test teaching mode endpoints via HTTP
Run this AFTER connecting via the web UI
"""

import requests
import json
import time
import sys

BASE_URL = "http://localhost:8000"

def test_teaching():
    print("=" * 80)
    print("TESTING TEACHING MODE ENDPOINTS")
    print("=" * 80)
    print("\nMake sure robot is connected via web UI first!")
    print()
    
    # Test 1: List actions
    print("[1] Testing /api/teaching/list...")
    r = requests.post(f"{BASE_URL}/api/teaching/list")
    result = r.json()
    print(f"Status: {result.get('success')}")
    if result.get('success'):
        print(f"Result: {json.dumps(result.get('result'), indent=2)}")
    else:
        print(f"Error: {result.get('error')}")
    print()
    
    # Test 2: Enter damping
    print("[2] Testing /api/teaching/enter_damping...")
    print("⚠️  WARNING: Robot will become compliant if command succeeds!")
    time.sleep(2)
    r = requests.post(f"{BASE_URL}/api/teaching/enter_damping")
    result = r.json()
    print(f"Status: {result.get('success')}")
    print(f"Message: {result.get('message')}")
    if not result.get('success'):
        print(f"Error: {result.get('error')}")
    print()
    
    if result.get('success'):
        # Wait a moment
        time.sleep(2)
        
        # Test 3: Exit damping
        print("[3] Testing /api/teaching/exit_damping...")
        r = requests.post(f"{BASE_URL}/api/teaching/exit_damping")
        result = r.json()
        print(f"Status: {result.get('success')}")
        print(f"Message: {result.get('message')}")
        if not result.get('success'):
            print(f"Error: {result.get('error')}")
    print()
    
    print("=" * 80)
    print("TESTS COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    try:
        test_teaching()
    except requests.exceptions.ConnectionError:
        print("❌ ERROR: Web server not running on localhost:8000")
        print("Start it with: python3 g1_app/ui/web_server.py")
        sys.exit(1)
    except Exception as e:
        print(f"❌ ERROR: {e}")
        sys.exit(1)
