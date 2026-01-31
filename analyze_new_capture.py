#!/usr/bin/env python3
"""
Analyze PCAPdroid_31_Jan_16_50_12.pcap for direct Android↔Robot communication
"""

from scapy.all import rdpcap, IP, UDP, TCP
from collections import defaultdict, Counter

def analyze_capture(pcap_file):
    print(f"\n{'='*80}")
    print(f"Analyzing: {pcap_file}")
    print(f"{'='*80}\n")
    
    packets = rdpcap(pcap_file)
    print(f"Total packets: {len(packets)}")
    
    # Track all unique IPs
    all_ips = set()
    ip_pairs = Counter()
    protocols = Counter()
    ports = Counter()
    
    # Known endpoints
    robot_ips = ['192.168.86.3']  # Known from previous captures
    turn_ips = ['10.215.173.1', '47.251.71.128']
    
    direct_packets = []
    turn_packets = []
    other_packets = []
    
    for pkt in packets:
        if IP in pkt:
            src = pkt[IP].src
            dst = pkt[IP].dst
            all_ips.add(src)
            all_ips.add(dst)
            
            # Track IP pairs
            pair = tuple(sorted([src, dst]))
            ip_pairs[pair] += 1
            
            # Track protocols
            if UDP in pkt:
                protocols['UDP'] += 1
                ports[('UDP', pkt[UDP].dport)] += 1
                ports[('UDP', pkt[UDP].sport)] += 1
            elif TCP in pkt:
                protocols['TCP'] += 1
                ports[('TCP', pkt[TCP].dport)] += 1
                ports[('TCP', pkt[TCP].sport)] += 1
            
            # Categorize traffic
            if any(ip in [src, dst] for ip in turn_ips):
                turn_packets.append(pkt)
            elif any(ip in [src, dst] for ip in robot_ips):
                direct_packets.append(pkt)
            else:
                # Check if destination looks like robot (192.168.x.x private network)
                if dst.startswith('192.168.') and not dst.startswith('192.168.86.'):
                    # Possible robot on different subnet (AP mode)
                    direct_packets.append(pkt)
                    robot_ips.append(dst)
                elif src.startswith('192.168.') and not src.startswith('192.168.86.'):
                    direct_packets.append(pkt)
                    robot_ips.append(src)
                else:
                    other_packets.append(pkt)
    
    print(f"\n{'='*80}")
    print("NETWORK TOPOLOGY")
    print(f"{'='*80}")
    print(f"\nAll unique IPs ({len(all_ips)}):")
    for ip in sorted(all_ips):
        print(f"  {ip}")
    
    print(f"\n{'='*80}")
    print("TRAFFIC BREAKDOWN")
    print(f"{'='*80}")
    print(f"\nDirect packets (phone ↔ robot): {len(direct_packets)}")
    print(f"TURN relay packets: {len(turn_packets)}")
    print(f"Other packets: {len(other_packets)}")
    
    print(f"\n{'='*80}")
    print("PROTOCOL DISTRIBUTION")
    print(f"{'='*80}")
    for proto, count in protocols.most_common():
        print(f"  {proto}: {count}")
    
    print(f"\n{'='*80}")
    print("TOP 20 IP PAIRS")
    print(f"{'='*80}")
    for pair, count in ip_pairs.most_common(20):
        print(f"  {pair[0]:15s} ↔ {pair[1]:15s} : {count:5d} packets")
    
    print(f"\n{'='*80}")
    print("TOP 20 PORTS")
    print(f"{'='*80}")
    for (proto, port), count in sorted(ports.items(), key=lambda x: x[1], reverse=True)[:20]:
        print(f"  {proto:3s} {port:5d}: {count:5d}")
    
    # Check for teaching protocol
    teaching_packets = []
    teaching_magic = b'\x17\xFE\xFD'
    
    for pkt in packets:
        if pkt.haslayer('Raw'):
            payload = bytes(pkt['Raw'].load)
            if teaching_magic in payload:
                teaching_packets.append(pkt)
    
    print(f"\n{'='*80}")
    print("TEACHING PROTOCOL")
    print(f"{'='*80}")
    print(f"Packets with teaching magic (17 FE FD): {len(teaching_packets)}")
    
    if teaching_packets:
        print(f"\nFirst 5 teaching protocol packets:")
        for i, pkt in enumerate(teaching_packets[:5]):
            if IP in pkt:
                print(f"  #{i+1}: {pkt[IP].src} → {pkt[IP].dst}")
                if UDP in pkt:
                    print(f"       UDP {pkt[UDP].sport} → {pkt[UDP].dport}")
    
    # Summary
    print(f"\n{'='*80}")
    print("SUMMARY")
    print(f"{'='*80}")
    
    if len(direct_packets) > 0 and len(turn_packets) == 0:
        print("\n✅ DIRECT COMMUNICATION DETECTED!")
        print("   All traffic appears to be direct phone↔robot (no TURN relay)")
        print(f"   Robot IP candidates: {list(set(robot_ips))}")
    elif len(turn_packets) > 0 and len(direct_packets) == 0:
        print("\n❌ TURN RELAY ONLY")
        print("   All traffic goes through TURN server (no direct communication)")
    elif len(direct_packets) > 0 and len(turn_packets) > 0:
        print("\n⚠️  MIXED TRAFFIC")
        print(f"   Direct: {len(direct_packets)} packets")
        print(f"   TURN relay: {len(turn_packets)} packets")
    else:
        print("\n⚠️  UNCLEAR")
        print("   Cannot determine communication pattern")
    
    print()

if __name__ == '__main__':
    analyze_capture('PCAPdroid_31_Jan_16_50_12.pcap')
