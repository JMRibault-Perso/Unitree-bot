#!/usr/bin/env python3
"""
Test web server connection and movement
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000"

def discover():
    """Discover robots"""
    print("Discovering robots...")
    response = requests.get(f"{BASE_URL}/api/discover")
    data = response.json()
    print(f"\nDiscovery result: {json.dumps(data, indent=2)}")
    return data.get("robots", [])

def connect_robot(robot):
    """Connect to robot"""
    print(f"\nConnecting to {robot['name']} at {robot['ip']}...")
    response = requests.post(
        f"{BASE_URL}/api/connect",
        params={
            "ip": robot["ip"],
            "serial_number": robot["serial_number"]
        }
    )
    data = response.json()
    print(f"Connection result: {json.dumps(data, indent=2)}")
    return data.get("success", False)

def get_state():
    """Get robot state"""
    print("\nGetting robot state...")
    response = requests.get(f"{BASE_URL}/api/state")
    data = response.json()
    print(f"State: {json.dumps(data, indent=2)}")
    return data

def set_state(state_name):
    """Set FSM state"""
    print(f"\nSetting state to {state_name}...")
    response = requests.post(
        f"{BASE_URL}/api/set_state",
        params={"state_name": state_name}
    )
    data = response.json()
    print(f"Result: {json.dumps(data, indent=2)}")
    return data.get("success", False)

def move(vx=0, vy=0, omega=0):
    """Send velocity command"""
    print(f"\nSending move command: vx={vx}, vy={vy}, omega={omega}...")
    response = requests.post(
        f"{BASE_URL}/api/move",
        params={"vx": vx, "vy": vy, "omega": omega}
    )
    data = response.json()
    print(f"Result: {json.dumps(data, indent=2)}")
    return data.get("success", False)

if __name__ == "__main__":
    # Discover robots
    robots = discover()
    if not robots:
        print("No robots found!")
        exit(1)
    
    # Use first robot
    robot = robots[0]
    
    # Connect
    if not connect_robot(robot):
        print("Failed to connect!")
        exit(1)
    
    time.sleep(2)
    
    # Get current state
    state = get_state()
    current_state = state.get("state", {}).get("fsm_state")
    print(f"\nCurrent FSM state: {current_state}")
    
    # If not in a motion-ready state, try to switch
    if current_state not in ["LOCK_STAND", "LOCK_STAND_ADV", "RUN"]:
        print("\nNot in motion-ready state, switching to LOCK_STAND...")
        set_state("LOCK_STAND")
        time.sleep(2)
        get_state()
    
    # Test movement
    print("\n=== Testing Movement ===")
    move(vx=0.2)
    time.sleep(2)
    move(vx=0)
    
    print("\nTest complete!")
