#!/usr/bin/env python3
"""
Complete Teaching Mode Protocol Analyzer
Extracts ALL teaching operations from PCAP: UDP init, action list, delete, rename, record
"""

import scapy.all as scapy
from scapy.layers.inet import IP, UDP
import struct
from collections import defaultdict

PCAP_FILE = "PCAPdroid_30_Jan_18_26_35.pcap"

# Command type mapping
COMMANDS = {
    0x17: "Heartbeat/Ack",
    0x1A: "List Actions",
    0x0D: "Enter Teaching",
    0x0E: "Exit Teaching",
    0x0F: "Record Toggle",
    0x2B: "Save Action",
    0x41: "Play Action",
    0x42: "Delete Action",      # Predicted based on pattern
    0x43: "Rename Action",      # Predicted based on pattern
    0x44: "Get Action Details", # Predicted based on pattern
}

def parse_header(data):
    """Parse standard packet header"""
    if len(data) < 16:
        return None
    
    magic = data[0:2]
    if magic != b'\x17\xfe':
        return None
    
    cmd_id = data[13]
    payload_len = struct.unpack('<H', data[14:16])[0]
    
    return {
        'magic': magic.hex(),
        'cmd_id': cmd_id,
        'cmd_name': COMMANDS.get(cmd_id, f'0x{cmd_id:02X}'),
        'payload_len': payload_len,
        'total_len': len(data)
    }

def parse_list_actions(data):
    """Parse 0x1A List Actions response"""
    if len(data) < 20:
        return None
    
    action_count = struct.unpack('<H', data[16:18])[0]
    actions = []
    
    # Each action is 36 bytes: 32B name + 4B metadata
    offset = 18
    for i in range(min(action_count, 15)):  # Max 15 actions
        if offset + 36 > len(data):
            break
        
        name_bytes = data[offset:offset+32]
        name = name_bytes.rstrip(b'\x00').decode('utf-8', errors='replace')
        metadata = struct.unpack('<I', data[offset+32:offset+36])[0]
        
        actions.append({
            'index': i + 1,
            'name': name,
            'metadata': f'0x{metadata:08x}'
        })
        offset += 36
    
    return {
        'action_count': action_count,
        'actions': actions
    }

def parse_save_action(data):
    """Parse 0x2B Save Action command"""
    if len(data) < 50:
        return None
    
    payload_len = struct.unpack('<H', data[14:16])[0]
    
    # Parse action name and trajectory data
    name_bytes = data[16:48]
    name = name_bytes.rstrip(b'\x00').decode('utf-8', errors='replace')
    
    keyframe_count = struct.unpack('<H', data[48:50])[0] if len(data) >= 50 else 0
    
    return {
        'action_name': name,
        'payload_length': payload_len,
        'keyframe_count': keyframe_count,
        'trajectory_data_size': payload_len - 32
    }

def parse_play_action(data):
    """Parse 0x41 Play Action command"""
    if len(data) < 32:
        return None
    
    payload_len = struct.unpack('<H', data[14:16])[0]
    action_id = struct.unpack('<I', data[16:20])[0]
    frame_count = struct.unpack('<I', data[20:24])[0]
    duration_override = struct.unpack('<I', data[24:28])[0]
    interpolation = struct.unpack('<I', data[28:32])[0]
    
    return {
        'action_id': f'0x{action_id:08x}',
        'frame_count': frame_count,
        'duration_override': duration_override,
        'interpolation_mode': interpolation,
        'payload_length': payload_len
    }

def parse_delete_action(data):
    """Parse delete action (0x42 predicted)"""
    if len(data) < 24:
        return None
    
    payload_len = struct.unpack('<H', data[14:16])[0]
    action_id = struct.unpack('<I', data[16:20])[0] if len(data) >= 20 else None
    
    return {
        'action_id': f'0x{action_id:08x}' if action_id else 'Unknown',
        'payload_length': payload_len
    }

def parse_rename_action(data):
    """Parse rename action (0x43 predicted)"""
    if len(data) < 50:
        return None
    
    payload_len = struct.unpack('<H', data[14:16])[0]
    action_id = struct.unpack('<I', data[16:20])[0] if len(data) >= 20 else None
    old_name_bytes = data[20:52] if len(data) >= 52 else data[20:52]
    old_name = old_name_bytes.rstrip(b'\x00').decode('utf-8', errors='replace') if len(data) >= 52 else ''
    
    new_name_bytes = data[52:84] if len(data) >= 84 else data[52:]
    new_name = new_name_bytes.rstrip(b'\x00').decode('utf-8', errors='replace')
    
    return {
        'action_id': f'0x{action_id:08x}' if action_id else 'Unknown',
        'old_name': old_name,
        'new_name': new_name,
        'payload_length': payload_len
    }

def parse_enter_teaching(data):
    """Parse 0x0D Enter Teaching mode"""
    if len(data) < 20:
        return None
    
    payload_len = struct.unpack('<H', data[14:16])[0]
    
    # Full robot state in payload
    return {
        'payload_length': payload_len,
        'contains_full_state': True,
        'expected_state_size': 161
    }

def parse_record_toggle(data):
    """Parse 0x0F Record toggle"""
    if len(data) < 20:
        return None
    
    payload_len = struct.unpack('<H', data[14:16])[0]
    record_flag = data[16] if len(data) > 16 else None
    
    return {
        'payload_length': payload_len,
        'record_flag': 'Recording ON' if record_flag == 1 else 'Recording OFF' if record_flag == 0 else 'Unknown'
    }

def analyze_pcap():
    """Main PCAP analysis"""
    print("=" * 80)
    print("COMPLETE TEACHING MODE PROTOCOL ANALYSIS")
    print(f"PCAP File: {PCAP_FILE}")
    print("=" * 80)
    
    try:
        packets = scapy.rdpcap(PCAP_FILE)
    except Exception as e:
        print(f"ERROR: Cannot read PCAP file: {e}")
        return
    
    # Group packets by command type
    commands_by_type = defaultdict(list)
    udp_streams = defaultdict(list)
    
    teaching_session_start = None
    operations = []
    
    for packet_num, packet in enumerate(packets):
        if not packet.haslayer(UDP):
            continue
        
        udp = packet[UDP]
        payload = bytes(udp.payload)
        
        if len(payload) < 14:
            continue
        
        # Track UDP port for session identification
        src_dst = f"{packet[IP].src}:{udp.sport} -> {packet[IP].dst}:{udp.dport}"
        
        header = parse_header(payload)
        if not header:
            continue
        
        cmd_id = header['cmd_id']
        cmd_name = header['cmd_name']
        
        commands_by_type[cmd_id].append({
            'packet_num': packet_num,
            'size': len(payload),
            'time': packet.time if hasattr(packet, 'time') else 0
        })
        
        udp_streams[src_dst].append({
            'packet_num': packet_num,
            'cmd_id': cmd_id,
            'cmd_name': cmd_name
        })
        
        # Parse specific commands
        parsed = None
        if cmd_id == 0x1A:
            parsed = parse_list_actions(payload)
            if parsed:
                operations.append({
                    'packet': packet_num,
                    'operation': 'LIST_ACTIONS',
                    'data': parsed
                })
        elif cmd_id == 0x0D:
            parsed = parse_enter_teaching(payload)
            if parsed:
                teaching_session_start = packet_num
                operations.append({
                    'packet': packet_num,
                    'operation': 'ENTER_TEACHING',
                    'data': parsed
                })
        elif cmd_id == 0x0E:
            operations.append({
                'packet': packet_num,
                'operation': 'EXIT_TEACHING',
                'data': {}
            })
        elif cmd_id == 0x0F:
            parsed = parse_record_toggle(payload)
            if parsed:
                operations.append({
                    'packet': packet_num,
                    'operation': 'RECORD_TOGGLE',
                    'data': parsed
                })
        elif cmd_id == 0x2B:
            parsed = parse_save_action(payload)
            if parsed:
                operations.append({
                    'packet': packet_num,
                    'operation': 'SAVE_ACTION',
                    'data': parsed
                })
        elif cmd_id == 0x41:
            parsed = parse_play_action(payload)
            if parsed:
                operations.append({
                    'packet': packet_num,
                    'operation': 'PLAY_ACTION',
                    'data': parsed
                })
        elif cmd_id == 0x42:
            parsed = parse_delete_action(payload)
            if parsed:
                operations.append({
                    'packet': packet_num,
                    'operation': 'DELETE_ACTION',
                    'data': parsed
                })
        elif cmd_id == 0x43:
            parsed = parse_rename_action(payload)
            if parsed:
                operations.append({
                    'packet': packet_num,
                    'operation': 'RENAME_ACTION',
                    'data': parsed
                })
    
    # Print UDP Session Information
    print("\n[1] UDP SESSION INITIALIZATION")
    print("-" * 80)
    for stream, packets_info in sorted(udp_streams.items()):
        print(f"\nStream: {stream}")
        print(f"  Packets in stream: {len(packets_info)}")
        print(f"  Commands: {', '.join(set(p['cmd_name'] for p in packets_info))}")
        if len(packets_info) > 0:
            first_cmd = packets_info[0]['cmd_name']
            print(f"  First command: {first_cmd} (packet #{packets_info[0]['packet_num']})")
    
    # Print Command Summary
    print("\n[2] COMMAND FREQUENCY ANALYSIS")
    print("-" * 80)
    for cmd_id in sorted(commands_by_type.keys()):
        count = len(commands_by_type[cmd_id])
        cmd_name = COMMANDS.get(cmd_id, f'0x{cmd_id:02X}')
        size = commands_by_type[cmd_id][0]['size'] if count > 0 else 0
        print(f"  0x{cmd_id:02X} ({cmd_name:20s}): {count:3d} packets, ~{size:4d} bytes each")
    
    # Print Operations Chronologically
    print("\n[3] TEACHING PROTOCOL OPERATIONS (CHRONOLOGICAL)")
    print("-" * 80)
    for op in sorted(operations, key=lambda x: x['packet']):
        packet_num = op['packet']
        operation = op['operation']
        data = op['data']
        
        print(f"\nPacket #{packet_num}: {operation}")
        
        if operation == 'LIST_ACTIONS':
            print(f"  Action Count: {data.get('action_count', 0)}")
            for action in data.get('actions', []):
                print(f"    [{action['index']}] {action['name']:30s} (metadata: {action['metadata']})")
        
        elif operation == 'ENTER_TEACHING':
            print(f"  Payload Size: {data.get('payload_length', 0)} bytes")
            print(f"  Contains: Full robot state (joints, IMU, foot forces)")
        
        elif operation == 'RECORD_TOGGLE':
            print(f"  Status: {data.get('record_flag', 'Unknown')}")
        
        elif operation == 'SAVE_ACTION':
            print(f"  Action Name: {data.get('action_name', 'Unknown')}")
            print(f"  Keyframes: {data.get('keyframe_count', 0)}")
            print(f"  Trajectory Data: {data.get('trajectory_data_size', 0)} bytes")
        
        elif operation == 'PLAY_ACTION':
            print(f"  Action ID: {data.get('action_id', 'Unknown')}")
            print(f"  Frame Count: {data.get('frame_count', 0)}")
            print(f"  Interpolation Mode: {data.get('interpolation_mode', 0)}")
        
        elif operation == 'DELETE_ACTION':
            print(f"  Action ID: {data.get('action_id', 'Unknown')}")
        
        elif operation == 'RENAME_ACTION':
            print(f"  Old Name: {data.get('old_name', 'Unknown')}")
            print(f"  New Name: {data.get('new_name', 'Unknown')}")
    
    # Print Summary
    print("\n[4] PROTOCOL SUMMARY")
    print("-" * 80)
    list_ops = sum(1 for o in operations if o['operation'] == 'LIST_ACTIONS')
    save_ops = sum(1 for o in operations if o['operation'] == 'SAVE_ACTION')
    play_ops = sum(1 for o in operations if o['operation'] == 'PLAY_ACTION')
    delete_ops = sum(1 for o in operations if o['operation'] == 'DELETE_ACTION')
    rename_ops = sum(1 for o in operations if o['operation'] == 'RENAME_ACTION')
    
    print(f"  List Actions:     {list_ops} times")
    print(f"  Save Action:      {save_ops} times")
    print(f"  Play Action:      {play_ops} times")
    print(f"  Delete Action:    {delete_ops} times")
    print(f"  Rename Action:    {rename_ops} times")
    print(f"  Teaching Sessions: {sum(1 for o in operations if o['operation'] == 'ENTER_TEACHING')}")
    
    print("\n[5] DISCOVERED ACTIONS (From LIST_ACTIONS responses)")
    print("-" * 80)
    all_actions = set()
    for op in operations:
        if op['operation'] == 'LIST_ACTIONS':
            for action in op['data'].get('actions', []):
                all_actions.add(action['name'])
    
    for i, action in enumerate(sorted(all_actions), 1):
        print(f"  {i}. {action}")
    
    print("\n" + "=" * 80)
    print("ANALYSIS COMPLETE")
    print("=" * 80)

if __name__ == '__main__':
    analyze_pcap()
