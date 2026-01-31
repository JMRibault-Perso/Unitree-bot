#!/usr/bin/env python3
"""
Check if phone ever directly communicates with robot,
or if ALL traffic is relayed through TURN server.
"""

from scapy.all import rdpcap, IP, UDP
import sys

def check_direct_communication(filename):
    print(f"{'='*80}")
    print(f"Direct Communication Check")
    print(f"{'='*80}\n")
    
    try:
        packets = rdpcap(filename)
    except Exception as e:
        print(f"Error: {e}")
        return
    
    robot_ip = "192.168.86.3"
    phone_ip = "192.168.86.6"  # From earlier analysis
    turn_relay = "10.215.173.1"
    turn_server = "47.251.71.128"
    
    # Count traffic patterns
    direct_phone_robot = 0
    phone_to_turn = 0
    turn_to_robot = 0
    robot_to_turn = 0
    turn_to_phone = 0
    
    for pkt in packets:
        if IP not in pkt:
            continue
        
        src = pkt[IP].src
        dst = pkt[IP].dst
        
        # Direct phone <-> robot
        if (src == phone_ip and dst == robot_ip) or (src == robot_ip and dst == phone_ip):
            direct_phone_robot += 1
        
        # Phone <-> TURN relay
        elif src == phone_ip and dst == turn_relay:
            phone_to_turn += 1
        elif src == turn_relay and dst == phone_ip:
            turn_to_phone += 1
        
        # Robot <-> TURN relay
        elif src == robot_ip and dst == turn_relay:
            robot_to_turn += 1
        elif src == turn_relay and dst == robot_ip:
            turn_to_robot += 1
    
    print(f"Traffic Analysis:")
    print(f"  Robot IP: {robot_ip}")
    print(f"  Phone IP: {phone_ip}")
    print(f"  TURN Relay: {turn_relay}")
    print()
    
    print(f"Communication Patterns:")
    print(f"  Direct Phone ↔ Robot:  {direct_phone_robot:6d} packets  {'✓ DIRECT' if direct_phone_robot > 0 else '✗ NO DIRECT'}")
    print(f"  Phone → TURN Relay:    {phone_to_turn:6d} packets")
    print(f"  TURN Relay → Phone:    {turn_to_phone:6d} packets")
    print(f"  Robot → TURN Relay:    {robot_to_turn:6d} packets")
    print(f"  TURN Relay → Robot:    {turn_to_robot:6d} packets")
    print()
    
    total_relayed = phone_to_turn + turn_to_phone + robot_to_turn + turn_to_robot
    
    if direct_phone_robot == 0 and total_relayed > 0:
        print(f"{'='*80}")
        print("FINDING: All traffic is RELAYED through TURN server!")
        print(f"{'='*80}\n")
        print("Implications:")
        print("  • Phone and robot are on SAME local network (192.168.86.x)")
        print("  • But they use TURN relay instead of direct connection")
        print("  • Possible reasons:")
        print("    - Firewall blocking direct UDP")
        print("    - App configured to always use TURN")
        print("    - ICE negotiation failed, fell back to TURN")
        print("    - Cloud relay required for encryption/authentication")
        print()
        print("For PC Controller:")
        print("  ⚠ May REQUIRE Unitree cloud access")
        print("  ⚠ Cannot bypass cloud with local-only connection")
        print("  ⚠ Need TURN credentials from cloud API")
        print()
        print("Alternative Approach:")
        print("  1. Implement direct WebRTC without TURN")
        print("  2. Send ICE candidates directly to robot")
        print("  3. Test if robot accepts non-relayed connections")
        print("  4. Or: reverse-engineer cloud API for TURN credentials")
    
    elif direct_phone_robot > 0:
        print(f"{'='*80}")
        print("FINDING: Direct communication detected!")
        print(f"{'='*80}\n")
        percent_direct = (direct_phone_robot / (direct_phone_robot + total_relayed)) * 100
        print(f"  {percent_direct:.1f}% of traffic is direct")
        print(f"  {100-percent_direct:.1f}% goes through TURN relay")
        print()
        print("For PC Controller:")
        print("  ✓ Direct connection possible!")
        print("  ✓ Can bypass cloud TURN server")
        print("  ✓ Implement local WebRTC client")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python check_direct_communication.py <pcap_file>")
        sys.exit(1)
    
    check_direct_communication(sys.argv[1])
