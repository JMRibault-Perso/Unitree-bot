#!/usr/bin/env python3
"""
Extract all PLAY_ACTION (0x41) packets with timing information.
This helps identify which packets correspond to which action plays.
"""

from scapy.all import rdpcap, UDP, IP, Raw
import sys
from datetime import datetime

def extract_play_commands(filename):
    print(f"{'='*80}")
    print(f"PLAY_ACTION (0x41) Command Extraction: {filename}")
    print(f"{'='*80}\n")
    
    try:
        packets = rdpcap(filename)
    except Exception as e:
        print(f"Error reading PCAP: {e}")
        return
    
    play_packets = []
    
    for i, pkt in enumerate(packets):
        if UDP in pkt and Raw in pkt:
            payload = bytes(pkt[Raw].load)
            
            # Check for teaching protocol with 0x41 command
            if len(payload) >= 14 and payload[0:3] == b'\x17\xfe\xfd' and payload[13] == 0x41:
                timestamp = float(pkt.time)
                dt = datetime.fromtimestamp(timestamp)
                
                play_packets.append({
                    'index': i,
                    'timestamp': timestamp,
                    'time_str': dt.strftime('%H:%M:%S.%f')[:-3],
                    'src': pkt[IP].src,
                    'dst': pkt[IP].dst,
                    'src_port': pkt[UDP].sport,
                    'dst_port': pkt[UDP].dport,
                    'length': len(payload),
                    'payload': payload
                })
    
    print(f"Found {len(play_packets)} PLAY_ACTION commands\n")
    print(f"{'='*80}")
    print("All PLAY_ACTION packets (with timing):")
    print(f"{'='*80}\n")
    
    if not play_packets:
        print("No PLAY_ACTION packets found!")
        return
    
    # Calculate time deltas
    first_time = play_packets[0]['timestamp']
    
    for i, pkt_info in enumerate(play_packets):
        delta = pkt_info['timestamp'] - first_time
        
        print(f"#{i+1:2d} | Packet #{pkt_info['index']:5d} | T+{delta:7.3f}s | {pkt_info['time_str']}")
        print(f"     {pkt_info['src']}:{pkt_info['src_port']} -> {pkt_info['dst']}:{pkt_info['dst_port']}")
        print(f"     Length: {pkt_info['length']:4d} bytes")
        print(f"     Hex: {pkt_info['payload'].hex()}")
        print()
    
    # Show summary by packet length (might correlate with action name length)
    print(f"\n{'='*80}")
    print("Summary by Packet Length:")
    print(f"{'='*80}\n")
    
    from collections import defaultdict
    length_groups = defaultdict(list)
    for i, pkt in enumerate(play_packets):
        length_groups[pkt['length']].append(i+1)
    
    for length in sorted(length_groups.keys()):
        indices = length_groups[length]
        print(f"{length:4d} bytes: {len(indices):2d} packets - indices {indices[:10]}")
    
    print(f"\n{'='*80}")
    print("Analysis:")
    print(f"{'='*80}\n")
    print("The packets are still encrypted, but you can:")
    print("1. Correlate packet times with when you clicked play in the app")
    print("2. Use packet length as a clue (longer payload might be 'AAAAAAAAA', shorter might be 'handshake')")
    print("3. Look for patterns in the hex that might indicate XOR encryption")
    print("\nWhat actions did you play and in what order?")
    print("This will help identify which packets correspond to which actions.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python extract_play_commands.py <pcap_file>")
        sys.exit(1)
    
    extract_play_commands(sys.argv[1])
