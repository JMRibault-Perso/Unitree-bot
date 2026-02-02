#!/usr/bin/env python3
"""
Extract DELETE (0x42) and PLAY (0x41) packets to identify:
1. Delete AAAAAAAAA command
2. Play handshake command
"""

from scapy.all import rdpcap, UDP, IP, Raw
import sys
from datetime import datetime

def extract_commands(filename):
    print(f"{'='*80}")
    print(f"DELETE and PLAY Command Extraction: {filename}")
    print(f"{'='*80}\n")
    
    try:
        packets = rdpcap(filename)
    except Exception as e:
        print(f"Error reading PCAP: {e}")
        return
    
    delete_packets = []
    play_packets = []
    
    for i, pkt in enumerate(packets):
        if UDP in pkt and Raw in pkt:
            payload = bytes(pkt[Raw].load)
            
            # Check for teaching protocol
            if len(payload) >= 14 and payload[0:3] == b'\x17\xfe\xfd':
                cmd = payload[13]
                timestamp = float(pkt.time)
                dt = datetime.fromtimestamp(timestamp)
                
                direction = "PHONE->ROBOT" if pkt[IP].src.startswith("192.168.86") and pkt[UDP].sport != 53338 else "ROBOT->PHONE"
                
                pkt_info = {
                    'index': i,
                    'timestamp': timestamp,
                    'time_str': dt.strftime('%H:%M:%S.%f')[:-3],
                    'src': pkt[IP].src,
                    'dst': pkt[IP].dst,
                    'src_port': pkt[UDP].sport,
                    'dst_port': pkt[UDP].dport,
                    'direction': direction,
                    'length': len(payload),
                    'payload': payload
                }
                
                if cmd == 0x42:
                    delete_packets.append(pkt_info)
                elif cmd == 0x41:
                    play_packets.append(pkt_info)
    
    # Show DELETE packets
    print(f"Found {len(delete_packets)} DELETE_ACTION (0x42) packets")
    print(f"Found {len(play_packets)} PLAY_ACTION (0x41) packets\n")
    
    print(f"{'='*80}")
    print("DELETE_ACTION packets (user-initiated only):")
    print(f"{'='*80}\n")
    
    first_time = delete_packets[0]['timestamp'] if delete_packets else 0
    user_deletes = [p for p in delete_packets if p['direction'] == "PHONE->ROBOT"]
    
    for i, pkt_info in enumerate(user_deletes[:10]):  # Show first 10
        delta = pkt_info['timestamp'] - first_time
        
        print(f"#{i+1:2d} | Packet #{pkt_info['index']:5d} | T+{delta:7.3f}s | {pkt_info['time_str']}")
        print(f"     {pkt_info['direction']}: {pkt_info['src']}:{pkt_info['src_port']} -> {pkt_info['dst']}:{pkt_info['dst_port']}")
        print(f"     Length: {pkt_info['length']:4d} bytes")
        print(f"     Hex: {pkt_info['payload'][:60].hex()}...")
        print()
    
    # Show PLAY packets (user-initiated only)
    print(f"\n{'='*80}")
    print("PLAY_ACTION packets (user-initiated only):")
    print(f"{'='*80}\n")
    
    first_time = play_packets[0]['timestamp'] if play_packets else 0
    user_plays = [p for p in play_packets if p['direction'] == "PHONE->ROBOT"]
    
    for i, pkt_info in enumerate(user_plays[:10]):  # Show first 10
        delta = pkt_info['timestamp'] - first_time
        
        print(f"#{i+1:2d} | Packet #{pkt_info['index']:5d} | T+{delta:7.3f}s | {pkt_info['time_str']}")
        print(f"     {pkt_info['direction']}: {pkt_info['src']}:{pkt_info['src_port']} -> {pkt_info['dst']}:{pkt_info['dst_port']}")
        print(f"     Length: {pkt_info['length']:4d} bytes")
        print(f"     Hex: {pkt_info['payload'].hex()}")
        print()
    
    # Summary
    print(f"\n{'='*80}")
    print("Analysis:")
    print(f"{'='*80}\n")
    print(f"User-initiated DELETE commands: {len(user_deletes)}")
    print(f"User-initiated PLAY commands: {len(user_plays)}")
    print("\nLikely candidates:")
    if user_deletes:
        print(f"  - DELETE AAAAAAAAA: Packet #{user_deletes[0]['index']} (first DELETE)")
    if user_plays:
        print(f"  - PLAY handshake: Packet #{user_plays[0]['index']} (first PLAY)")
    
    print("\nPacket lengths might indicate action name length:")
    if user_deletes:
        print(f"  - First DELETE: {user_deletes[0]['length']} bytes")
    if user_plays:
        print(f"  - First PLAY: {user_plays[0]['length']} bytes")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python extract_delete_and_play.py <pcap_file>")
        sys.exit(1)
    
    extract_commands(sys.argv[1])
