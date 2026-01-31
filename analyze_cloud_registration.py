#!/usr/bin/env python3
"""
Analyze cloud registration pattern in TURN credentials.
The username format appears to be: <timestamp>:<robot_serial>
"""

import time
from datetime import datetime

# From PCAP analysis
turn_username = "1769845747:E21D1000PAHBMB06"
robot_serial = "E21D1000PAHBMB06"
realm = "turn-us.unitree.com"
turn_server = "47.251.71.128:5349"

print("="*80)
print("Unitree Cloud Registration Analysis")
print("="*80)
print()

# Parse username
parts = turn_username.split(':')
timestamp_str = parts[0]
serial = parts[1]

timestamp = int(timestamp_str)
dt = datetime.fromtimestamp(timestamp)

print(f"TURN Username: {turn_username}")
print(f"  Timestamp: {timestamp_str} ({timestamp})")
print(f"  Date/Time: {dt.strftime('%Y-%m-%d %H:%M:%S UTC')}")
print(f"  Robot Serial: {serial}")
print()

print(f"TURN Server:")
print(f"  Realm: {realm}")
print(f"  Address: {turn_server}")
print(f"  Software: Coturn-4.5.2 'dan Eider'")
print()

# Analyze timestamp
current_time = int(time.time())
time_diff = current_time - timestamp

print(f"Timestamp Analysis:")
print(f"  Current time: {current_time}")
print(f"  Capture time: {timestamp}")
print(f"  Difference: {time_diff} seconds (~{time_diff//3600} hours ago)")
print()

print("="*80)
print("Cloud Registration Process (Hypothesis):")
print("="*80)
print()
print("1. Android App Discovery:")
print("   - App discovers robot on local network (BLE or mDNS)")
print("   - Retrieves robot serial number: E21D1000PAHBMB06")
print()
print("2. Cloud Authentication:")
print("   - App/Robot contacts Unitree cloud: turn-us.unitree.com")
print("   - Generates TURN credentials using:")
print("     * Current timestamp (Unix epoch)")
print("     * Robot serial number")
print("     * Format: <timestamp>:<serial>")
print()
print("3. TURN Server Authorization:")
print("   - Cloud validates robot serial number")
print("   - Grants time-limited TURN access")
print("   - Returns NONCE for session authentication")
print()
print("4. WebRTC Connection:")
print("   - Phone and robot use TURN relay for NAT traversal")
print("   - TURN server acts as intermediary")
print("   - Teaching protocol encrypted over DTLS datachannel")
print()

print("="*80)
print("Implications for PC Controller:")
print("="*80)
print()
print("✓ Robot serial is VISIBLE in STUN packets (not encrypted)")
print("✓ TURN credentials use predictable format: <timestamp>:<serial>")
print("✓ Cloud registration may require:")
print("  - Valid robot serial number")
print("  - Unitree account authentication")
print("  - Time-synchronized credentials")
print()
print("⚠ Challenges:")
print("  - Cloud may validate serial against registered accounts")
print("  - TURN password not visible (likely derived from account credentials)")
print("  - May need to reverse-engineer cloud API authentication")
print()
print("💡 Possible Approaches:")
print("  1. Use Unitree account credentials to request TURN access")
print("  2. Reverse-engineer Android app's cloud authentication")
print("  3. Bypass cloud by implementing local-only WebRTC")
print("  4. Capture complete TURN handshake including password/hash")
print()

print("="*80)
print("Next Steps:")
print("="*80)
print()
print("1. Extract TURN password from Android app (decompile APK)")
print("2. Test if TURN server accepts connections with known serial")
print("3. Monitor for cloud API calls (register.unitree.com, api.unitree.com, etc.)")
print("4. Check if robot broadcasts mDNS/BLE with serial number")
print("5. Analyze MESSAGE-INTEGRITY to understand password derivation")
