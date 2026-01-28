#!/usr/bin/env python3
"""
Simple test: Connect and watch logs
"""
import requests
import time

# Discover robot
resp = requests.get("http://localhost:8000/api/discover")
robot = resp.json()["robots"][0]
print(f"Found: {robot['serial_number']} at {robot['ip']}")

# Connect
print("Connecting...")
resp = requests.post("http://localhost:8000/api/connect", params={
    "ip": robot["ip"],
    "serial_number": robot["serial_number"]
})
print(f"Connected: {resp.json()['success']}")

# Wait for state updates
print("Waiting 10 seconds for state updates...")
print("(Check /tmp/web_server.log for broadcasts)")
time.sleep(10)

# Disconnect
requests.post("http://localhost:8000/api/disconnect")
print("Disconnected")
