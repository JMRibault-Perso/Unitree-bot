#!/usr/bin/env python3
"""Test connection with real serial number from robot name"""
import requests
import time

BASE_URL = "http://localhost:8000"

print("=" * 60)
print("Testing Connection with Real Serial Number")
print("=" * 60)

# The robot name is G1_6937, so try using that
robot_ip = "192.168.86.3"
serial_number = "G1_6937"  # Use robot's actual name

print(f"\nTarget: {serial_number} @ {robot_ip}")

# Step 1: Disconnect if already connected
print("\n1. POST /api/disconnect (cleanup)")
resp = requests.post(f"{BASE_URL}/api/disconnect")
print(f"Status: {resp.status_code}")
time.sleep(1)

# Step 2: Connect with real serial
print(f"\n2. POST /api/connect (timeout=15 seconds)")
try:
    resp = requests.post(
        f"{BASE_URL}/api/connect?ip={robot_ip}&serial_number={serial_number}&mode=sta",
        timeout=15
    )
    print(f"Status: {resp.status_code}")
    if resp.status_code == 200:
        data = resp.json()
        print(f"Success: {data.get('success')}")
        if 'state' in data:
            print(f"Initial FSM State: {data['state'].get('fsm_state')}")
        print("\n✅ CONNECTION SUCCESS!")
    else:
        print(f"Response: {resp.text[:200]}")
except requests.exceptions.Timeout:
    print(f"ERROR: Connection timed out - robot not responding on WebRTC")
except Exception as e:
    print(f"ERROR: {e}")
