#!/usr/bin/env python3
"""
Find the actual phone IP and analyze direct robot communication.
"""

from scapy.all import rdpcap, IP, UDP, Raw
import sys
from collections import defaultdict

def find_all_endpoints(filename):
    print(f"{'='*80}")
    print(f"Network Endpoint Discovery")
    print(f"{'='*80}\n")
    
    try:
        packets = rdpcap(filename)
    except Exception as e:
        print(f"Error: {e}")
        return
    
    robot_ip = "192.168.86.3"
    
    # Track all IPs that communicate with robot
    robot_peers = defaultdict(lambda: {'sent': 0, 'received': 0, 'ports': set()})
    
    # Track all unique IPs seen
    all_ips = set()
    
    for pkt in packets:
        if IP not in pkt:
            continue
        
        src = pkt[IP].src
        dst = pkt[IP].dst
        all_ips.add(src)
        all_ips.add(dst)
        
        if UDP in pkt:
            src_port = pkt[UDP].sport
            dst_port = pkt[UDP].dport
            
            # Traffic TO robot
            if dst == robot_ip:
                robot_peers[src]['sent'] += 1
                robot_peers[src]['ports'].add(f"{src_port}→{dst_port}")
            
            # Traffic FROM robot
            elif src == robot_ip:
                robot_peers[dst]['received'] += 1
                robot_peers[dst]['ports'].add(f"{src_port}→{dst_port}")
    
    print(f"All unique IPs in capture: {sorted(all_ips)}\n")
    
    print(f"{'='*80}")
    print(f"Robot ({robot_ip}) Communication Partners:")
    print(f"{'='*80}\n")
    
    for peer_ip in sorted(robot_peers.keys(), key=lambda x: -(robot_peers[x]['sent'] + robot_peers[x]['received'])):
        sent = robot_peers[peer_ip]['sent']
        received = robot_peers[peer_ip]['received']
        total = sent + received
        ports = list(robot_peers[peer_ip]['ports'])[:5]  # Show first 5 port pairs
        
        print(f"{peer_ip:20s}: {total:6d} packets ({sent:5d} sent, {received:5d} received)")
        print(f"  Port pairs: {', '.join(ports)}")
        
        # Identify likely phone vs TURN
        if peer_ip.startswith("192.168.86"):
            print(f"  → LIKELY PHONE (same subnet as robot)")
        elif peer_ip.startswith("10."):
            print(f"  → LIKELY TURN RELAY (private IP)")
        elif not peer_ip.startswith("192.168") and not peer_ip.startswith("10."):
            print(f"  → LIKELY EXTERNAL SERVER")
        print()
    
    # Now check for teaching protocol packets
    print(f"{'='*80}")
    print(f"Teaching Protocol Packet Sources:")
    print(f"{'='*80}\n")
    
    teaching_sources = defaultdict(int)
    
    for pkt in packets:
        if IP in pkt and UDP in pkt and Raw in pkt:
            payload = bytes(pkt[Raw].load)
            
            # Check for teaching protocol magic
            if len(payload) >= 14 and payload[0:3] == b'\x17\xfe\xfd':
                src = pkt[IP].src
                dst = pkt[IP].dst
                
                if src == robot_ip:
                    teaching_sources[f"Robot→{dst}"] += 1
                elif dst == robot_ip:
                    teaching_sources[f"{src}→Robot"] += 1
    
    for direction, count in sorted(teaching_sources.items(), key=lambda x: -x[1]):
        print(f"  {direction:40s}: {count:5d} packets")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python find_phone_ip.py <pcap_file>")
        sys.exit(1)
    
    find_all_endpoints(sys.argv[1])
