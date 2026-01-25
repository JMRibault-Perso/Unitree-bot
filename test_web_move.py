#!/usr/bin/env python3
"""
Test web server movement endpoint
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_move():
    """Test the move endpoint"""
    print("Testing /api/move endpoint...")
    
    # Test forward movement
    response = requests.post(f"{BASE_URL}/api/move", params={"vx": 0.3})
    print(f"\nForward (vx=0.3): {json.dumps(response.json(), indent=2)}")
    
    time.sleep(2)
    
    # Stop
    response = requests.post(f"{BASE_URL}/api/move", params={"vx": 0.0})
    print(f"\nStop: {json.dumps(response.json(), indent=2)}")

def check_status():
    """Check robot connection status"""
    print("Checking robot status...")
    response = requests.get(f"{BASE_URL}/api/status")
    print(f"\nStatus: {json.dumps(response.json(), indent=2)}")

if __name__ == "__main__":
    check_status()
    test_move()
