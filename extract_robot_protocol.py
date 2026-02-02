#!/usr/bin/env python3
"""
Extract teaching protocol packets from PCAP
Focus on UDP port 49504 (robot command/control port)
"""
from scapy.all import rdpcap
from scapy.layers.inet import UDP, IP
import struct

PCAP_FILE = 'PCAPdroid_30_Jan_18_26_35.pcap'

packets = rdpcap(PCAP_FILE)
print(f"Total packets: {len(packets)}")

# Focus on UDP traffic
udp_packets = []
for pkt in packets:
    if pkt.haslayer(UDP):
        udp = pkt[UDP]
        # Try to identify robot traffic by size and pattern
        payload = bytes(udp.payload) if udp.payload else b''
        if len(payload) > 12:
            # Check for our protocol magic bytes (0x17 0xFE)
            if payload[0:2] == b'\x17\xfe':
                udp_packets.append((pkt, payload))

print(f"\nRobot protocol packets (0x17 0xFE magic): {len(udp_packets)}")

# Analyze command types
from collections import defaultdict
commands = defaultdict(list)

for pkt, payload in udp_packets:
    if len(payload) < 14:
        continue
    
    cmd_id = payload[13]
    size = len(payload)
    
    commands[cmd_id].append({
        'size': size,
        'payload': payload
    })
    
    cmd_names = {
        0x17: "Heartbeat",
        0x1A: "List Actions",
        0x0D: "Enter Teaching",
        0x0E: "Exit Teaching",
        0x0F: "Record Toggle",
        0x2B: "Save Action",
        0x41: "Play Action",
        0x42: "Delete Action",
        0x43: "Rename Action",
    }
    
    print(f"0x{cmd_id:02X} ({cmd_names.get(cmd_id, 'Unknown'):20s}): {len(payload):4d} bytes")

print("\n" + "="*80)
print("COMMAND ANALYSIS")
print("="*80)

for cmd_id in sorted(commands.keys()):
    cmd_names = {
        0x17: "Heartbeat",
        0x1A: "List Actions",
        0x0D: "Enter Teaching",
        0x0E: "Exit Teaching",
        0x0F: "Record Toggle",
        0x2B: "Save Action",
        0x41: "Play Action",
        0x42: "Delete Action",
        0x43: "Rename Action",
    }
    
    cmd_name = cmd_names.get(cmd_id, f'0x{cmd_id:02X}')
    count = len(commands[cmd_id])
    sizes = [c['size'] for c in commands[cmd_id]]
    
    print(f"\n0x{cmd_id:02X} - {cmd_name}")
    print(f"  Count: {count}")
    print(f"  Sizes: {set(sizes)} bytes")
    
    # Show first occurrence
    if count > 0:
        payload = commands[cmd_id][0]['payload']
        print(f"  First packet hex: {payload[:60].hex()}")
        
        # Parse based on command type
        if cmd_id == 0x1A and len(payload) > 20:
            # List Actions - parse action count
            action_count = struct.unpack('<H', payload[16:18])[0]
            print(f"  Action count in response: {action_count}")
            
            # Extract action names
            print(f"  Actions:")
            offset = 18
            for i in range(min(action_count, 5)):
                if offset + 32 <= len(payload):
                    name_bytes = payload[offset:offset+32]
                    name = name_bytes.rstrip(b'\x00').decode('utf-8', errors='replace')
                    if name.strip():
                        print(f"    [{i+1}] {name}")
                    offset += 36
        
        elif cmd_id == 0x2B and len(payload) > 50:
            # Save Action - parse name
            name_bytes = payload[16:48]
            name = name_bytes.rstrip(b'\x00').decode('utf-8', errors='replace')
            print(f"  Action name: {name}")
            print(f"  Keyframe/trajectory data: {len(payload) - 48} bytes")
        
        elif cmd_id == 0x41 and len(payload) > 32:
            # Play Action - parse action ID
            action_id = struct.unpack('<I', payload[16:20])[0]
            frame_count = struct.unpack('<I', payload[20:24])[0]
            print(f"  Action ID: 0x{action_id:08x}")
            print(f"  Frame count: {frame_count}")
        
        elif cmd_id == 0x0D and len(payload) > 50:
            # Enter Teaching - contains full robot state
            print(f"  Full state payload: {len(payload)} bytes")

print("\n" + "="*80)
print("ACTION LIST (From all 0x1A responses)")
print("="*80)

all_actions = set()
for cmd_entry in commands[0x1A]:
    payload = cmd_entry['payload']
    if len(payload) > 20:
        action_count = struct.unpack('<H', payload[16:18])[0]
        offset = 18
        for i in range(min(action_count, 15)):
            if offset + 32 <= len(payload):
                name_bytes = payload[offset:offset+32]
                name = name_bytes.rstrip(b'\x00').decode('utf-8', errors='replace')
                if name.strip():
                    all_actions.add(name)
                offset += 36

if all_actions:
    for i, action in enumerate(sorted(all_actions), 1):
        print(f"  {i}. {action}")
else:
    print("  No actions found!")
