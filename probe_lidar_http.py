#!/usr/bin/env python3
"""Probe robot HTTP endpoints for LiDAR control"""

import requests
import json

robot_ip = "192.168.86.18"

# Possible HTTP endpoints based on other APIs we've discovered
test_endpoints = [
    # Service control
    "/api/service/list",
    "/api/service/start",
    "/api/service/status",
    "/api/lidar/enable",
    "/api/lidar/status",
    "/api/lidar/start",
    # Settings
    "/api/settings",
    "/api/config",
    "/api/system/services",
]

print("🔍 Probing robot HTTP endpoints...")

for endpoint in test_endpoints:
    url = f"http://{robot_ip}{endpoint}"
    try:
        # Try GET
        resp = requests.get(url, timeout=2)
        if resp.status_code != 404:
            print(f"✅ GET  {endpoint}: {resp.status_code}")
            try:
                data = resp.json()
                print(f"   Response: {json.dumps(data, indent=2)}")
            except:
                print(f"   Response: {resp.text[:200]}")
    except requests.exceptions.Timeout:
        pass
    except requests.exceptions.ConnectionError:
        pass
    
    try:
        # Try POST
        resp = requests.post(url, json={}, timeout=2)
        if resp.status_code != 404:
            print(f"✅ POST {endpoint}: {resp.status_code}")
            try:
                data = resp.json()
                print(f"   Response: {json.dumps(data, indent=2)}")
            except:
                print(f"   Response: {resp.text[:200]}")
    except requests.exceptions.Timeout:
        pass
    except requests.exceptions.ConnectionError:
        pass

print("\n💡 If no endpoints found, LiDAR control may be:")
print("   1. Only via DDS topic (requires service already running)")
print("   2. Requires Android app-specific authentication")
print("   3. Part of SLAM/Navigation mode activation")
