#!/usr/bin/env python3
"""Test robot discovery logic"""
import subprocess
import json
from pathlib import Path

# Read bindings
BINDINGS_FILE = Path.home() / ".unitree_robot_bindings.json"
with open(BINDINGS_FILE, 'r') as f:
    bindings = json.load(f)

print(f"Loaded bindings: {bindings}")

# Get ARP table
result = subprocess.run(['arp', '-n'], capture_output=True, text=True, timeout=2)
print(f"\nARP output:\n{result.stdout}")

# Parse ARP entries
arp_entries = []
for line in result.stdout.split('\n'):
    parts = line.split()
    if len(parts) >= 3:
        ip = parts[0]
        mac = parts[2].lower()
        arp_entries.append((ip, mac))
        
print(f"\nParsed {len(arp_entries)} ARP entries")

# Check for matches
for mac_from_file, data in bindings.items():
    mac_to_find = mac_from_file.lower()
    print(f"\nLooking for MAC: {mac_to_find}")
    
    for ip, mac in arp_entries:
        if mac == mac_to_find:
            print(f"  ✓ FOUND at IP {ip}")
            # Test ping
            ping_result = subprocess.run(['ping', '-c', '1', '-W', '2', ip], 
                                        capture_output=True, timeout=3)
            if ping_result.returncode == 0:
                print(f"  ✓ PING SUCCESS")
            else:
                print(f"  ✗ PING FAILED")
            break
    else:
        print(f"  ✗ NOT FOUND in ARP table")
