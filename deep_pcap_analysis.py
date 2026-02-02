#!/usr/bin/env python3
"""
Deep PCAP analysis to understand what protocols and data are present.
Checks for teaching protocol headers even if partially visible.
"""

from scapy.all import rdpcap, UDP, IP, Raw
import sys
from collections import defaultdict

def analyze_pcap(filename):
    print(f"{'='*80}")
    print(f"Deep Analysis: {filename}")
    print(f"{'='*80}\n")
    
    try:
        packets = rdpcap(filename)
    except Exception as e:
        print(f"Error reading PCAP: {e}")
        return
    
    # Statistics
    total_packets = len(packets)
    udp_packets = 0
    packets_with_raw = 0
    magic_header_count = 0
    port_stats = defaultdict(int)
    protocol_stats = defaultdict(int)
    
    # Track interesting packets
    interesting_packets = []
    
    print(f"Total packets: {total_packets}\n")
    
    for i, pkt in enumerate(packets):
        # Track protocols
        if IP in pkt:
            if UDP in pkt:
                udp_packets += 1
                src_port = pkt[UDP].sport
                dst_port = pkt[UDP].dport
                port_stats[f"{src_port}->{dst_port}"] += 1
                
                if Raw in pkt:
                    packets_with_raw += 1
                    payload = bytes(pkt[Raw].load)
                    
                    # Check for teaching protocol magic header
                    if len(payload) >= 3 and payload[0:3] == b'\x17\xfe\xfd':
                        magic_header_count += 1
                        
                        # Try to extract command byte
                        if len(payload) >= 14:
                            cmd = payload[13]
                            cmd_name = {
                                0x1A: "GET_ACTION_LIST",
                                0x41: "PLAY_ACTION",
                                0x42: "DELETE_ACTION",
                                0x43: "RENAME_ACTION"
                            }.get(cmd, f"UNKNOWN_0x{cmd:02X}")
                            
                            interesting_packets.append({
                                'index': i,
                                'src': f"{pkt[IP].src}:{src_port}",
                                'dst': f"{pkt[IP].dst}:{dst_port}",
                                'len': len(payload),
                                'cmd': cmd_name,
                                'first_20': payload[:20].hex()
                            })
                    
                    # Track payload protocol types
                    if len(payload) >= 3:
                        header = payload[0:3].hex()
                        protocol_stats[f"Header_{header}"] += 1
    
    # Print statistics
    print("=== Protocol Statistics ===")
    print(f"UDP packets: {udp_packets}")
    print(f"Packets with Raw payload: {packets_with_raw}")
    print(f"Teaching protocol magic headers (17 FE FD): {magic_header_count}\n")
    
    print("=== Top 10 Port Pairs ===")
    for port_pair, count in sorted(port_stats.items(), key=lambda x: -x[1])[:10]:
        print(f"{port_pair}: {count} packets")
    
    print("\n=== Top 10 Payload Headers ===")
    for header, count in sorted(protocol_stats.items(), key=lambda x: -x[1])[:10]:
        print(f"{header}: {count} packets")
    
    # Show interesting packets
    if interesting_packets:
        print(f"\n{'='*80}")
        print(f"Found {len(interesting_packets)} teaching protocol packets!")
        print(f"{'='*80}\n")
        
        for pkt_info in interesting_packets[:20]:  # Show first 20
            print(f"Packet #{pkt_info['index']}:")
            print(f"  {pkt_info['src']} -> {pkt_info['dst']}")
            print(f"  Command: {pkt_info['cmd']}")
            print(f"  Length: {pkt_info['len']} bytes")
            print(f"  First 20 bytes: {pkt_info['first_20']}")
            print()
    else:
        print(f"\n{'='*80}")
        print("No teaching protocol packets found (no 17 FE FD headers)")
        print(f"{'='*80}\n")
        
        # Show some sample payloads to understand what we have
        print("=== Sample UDP payloads (first 3) ===")
        sample_count = 0
        for pkt in packets:
            if UDP in pkt and Raw in pkt:
                payload = bytes(pkt[Raw].load)
                if len(payload) > 0:
                    print(f"\nPayload length: {len(payload)}")
                    print(f"First 40 bytes: {payload[:40].hex()}")
                    sample_count += 1
                    if sample_count >= 3:
                        break

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python deep_pcap_analysis.py <pcap_file>")
        sys.exit(1)
    
    analyze_pcap(sys.argv[1])
