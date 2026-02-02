#!/usr/bin/env python3
"""
Extract and analyze teaching protocol packets from TLS-decrypted PCAP.
The packets have 17 FE FD header but may have additional encryption layer.
"""

from scapy.all import rdpcap, UDP, IP, Raw
import sys
from collections import defaultdict

def analyze_teaching_protocol(filename):
    print(f"{'='*80}")
    print(f"Teaching Protocol Analysis: {filename}")
    print(f"{'='*80}\n")
    
    try:
        packets = rdpcap(filename)
    except Exception as e:
        print(f"Error reading PCAP: {e}")
        return
    
    # Find all teaching protocol packets
    teaching_packets = []
    cmd_stats = defaultdict(int)
    
    for i, pkt in enumerate(packets):
        if UDP in pkt and Raw in pkt:
            payload = bytes(pkt[Raw].load)
            
            # Check for teaching protocol magic header
            if len(payload) >= 14 and payload[0:3] == b'\x17\xfe\xfd':
                cmd = payload[13]
                cmd_stats[cmd] += 1
                
                # Store packet info
                teaching_packets.append({
                    'index': i,
                    'src': pkt[IP].src,
                    'dst': pkt[IP].dst,
                    'src_port': pkt[UDP].sport,
                    'dst_port': pkt[UDP].dport,
                    'cmd': cmd,
                    'payload': payload
                })
    
    print(f"Total teaching protocol packets: {len(teaching_packets)}\n")
    
    # Show command distribution
    print("=== Command Byte Distribution (Top 20) ===")
    for cmd, count in sorted(cmd_stats.items(), key=lambda x: -x[1])[:20]:
        known_cmds = {
            0x1A: "GET_ACTION_LIST",
            0x41: "PLAY_ACTION",
            0x42: "DELETE_ACTION",
            0x43: "RENAME_ACTION"
        }
        cmd_name = known_cmds.get(cmd, f"UNKNOWN")
        print(f"0x{cmd:02X} ({cmd_name:20s}): {count:5d} packets")
    
    # Look specifically for known commands
    print(f"\n{'='*80}")
    print("Looking for known commands (0x1A, 0x41, 0x42, 0x43)...")
    print(f"{'='*80}\n")
    
    for target_cmd in [0x1A, 0x41, 0x42, 0x43]:
        cmd_name = {
            0x1A: "GET_ACTION_LIST",
            0x41: "PLAY_ACTION",
            0x42: "DELETE_ACTION",
            0x43: "RENAME_ACTION"
        }[target_cmd]
        
        matching = [p for p in teaching_packets if p['cmd'] == target_cmd]
        print(f"\nCommand 0x{target_cmd:02X} ({cmd_name}): {len(matching)} packets")
        
        if matching:
            # Show first 3 examples
            for pkt_info in matching[:3]:
                payload = pkt_info['payload']
                print(f"\n  Packet #{pkt_info['index']}:")
                print(f"    {pkt_info['src']}:{pkt_info['src_port']} -> {pkt_info['dst']}:{pkt_info['dst_port']}")
                print(f"    Length: {len(payload)} bytes")
                print(f"    Full hex: {payload.hex()}")
                
                # Try to decode assuming standard structure
                if len(payload) >= 18:
                    payload_len = int.from_bytes(payload[14:16], 'big')
                    print(f"    Payload length field: {payload_len}")
                    
                    if target_cmd == 0x1A and len(payload) >= 18:
                        # Action list response
                        action_count = int.from_bytes(payload[16:18], 'big')
                        print(f"    Action count: {action_count}")
                    
                    if target_cmd == 0x41:
                        # Play action command
                        print(f"    Bytes 16-20: {payload[16:20].hex()}")
                        # Check if action name is visible
                        if len(payload) > 20:
                            try:
                                # Try to find null-terminated string
                                action_name = payload[18:].split(b'\x00')[0].decode('utf-8', errors='ignore')
                                if action_name.isprintable() and len(action_name) > 0:
                                    print(f"    Possible action name: '{action_name}'")
                            except:
                                pass

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python extract_decrypted_teaching_packets.py <pcap_file>")
        sys.exit(1)
    
    analyze_teaching_protocol(sys.argv[1])
