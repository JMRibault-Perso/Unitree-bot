#!/usr/bin/env python3
"""Simple test to verify discovery endpoint works"""
import requests
import time

BASE_URL = "http://localhost:8000"

print("=" * 60)
print("Testing DISCOVERY Only (No Connection)")
print("=" * 60)

try:
    # Test /api/discover endpoint
    print("\n1. GET /api/discover (timeout=5 seconds)")
    start = time.time()
    resp = requests.get(f"{BASE_URL}/api/discover", timeout=5)
    elapsed = time.time() - start
    
    print(f"Status: {resp.status_code}")
    print(f"Time: {elapsed:.2f}s")
    
    if resp.status_code != 200:
        print(f"ERROR: Non-200 status. Response: {resp.text}")
        exit(1)
    
    data = resp.json()
    print(f"\nResponse type: {type(data)}")
    print(f"Response: {data}")
    
    if isinstance(data, dict):
        robots = data.get("robots", [])
    else:
        robots = data if isinstance(data, list) else []
    
    print(f"\nTotal robots: {len(robots)}")
    
    for r in robots:
        print(f"  - {r.get('name')} @ {r.get('ip')} (online={r.get('is_online')})")
    
    online = [r for r in robots if r.get("is_online")]
    print(f"\nOnline robots: {len(online)}")
    
    if not online:
        print("\nWARNING: No online robots found!")
        exit(0)
    
    target = online[0]
    print(f"\nTarget robot:")
    print(f"  Name: {target.get('name')}")
    print(f"  IP: {target.get('ip')}")
    print(f"  Serial: {target.get('serial_number')}")
    print(f"  MAC: {target.get('mac_address')}")
    
    print("\n✅ SUCCESS: Discovery endpoint works!")
    
except requests.exceptions.Timeout:
    print(f"ERROR: Request timed out after 5 seconds")
    exit(1)
except requests.exceptions.ConnectionError as e:
    print(f"ERROR: Cannot connect to web server: {e}")
    print(f"Make sure web server is running at {BASE_URL}")
    exit(1)
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
    exit(1)
