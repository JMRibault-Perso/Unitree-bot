#!/usr/bin/env python3
"""Find teaching protocol payloads on port 57006"""

import struct

def parse_pcap_packets(pcap_file):
    packets = []
    with open(pcap_file, 'rb') as f:
        global_header = f.read(24)
        while True:
            packet_header = f.read(16)
            if len(packet_header) < 16:
                break
            ts_sec, ts_usec, incl_len, orig_len = struct.unpack('<IIII', packet_header)
            packet_data = f.read(incl_len)
            if len(packet_data) < incl_len:
                break
            packets.append({'data': packet_data})
    return packets

def extract_ip_udp_payload(packet_data):
    try:
        if len(packet_data) > 34:
            eth_type = struct.unpack('>H', packet_data[12:14])[0]
            ip_offset = 14 if eth_type == 0x0800 else 0
        else:
            ip_offset = 0
        
        if len(packet_data) < ip_offset + 20:
            return None
        
        version_ihl = packet_data[ip_offset]
        ihl = (version_ihl & 0x0F) * 4
        
        if len(packet_data) < ip_offset + ihl + 8:
            return None
        
        udp_offset = ip_offset + ihl
        src_port = struct.unpack('>H', packet_data[udp_offset:udp_offset+2])[0]
        dst_port = struct.unpack('>H', packet_data[udp_offset+2:udp_offset+4])[0]
        
        payload_offset = udp_offset + 8
        udp_payload = packet_data[payload_offset:]
        
        return {'src_port': src_port, 'dst_port': dst_port, 'payload': udp_payload}
    except:
        return None

# Search both PCAPs
for (pcap_name, port_target) in [
    ('PCAPdroid_30_Jan_18_19_57.pcap', 57006),
    ('PCAPdroid_30_Jan_18_26_35.pcap', 57006),
    ('PCAPdroid_30_Jan_18_19_57.pcap', 51639),
    ('PCAPdroid_30_Jan_18_26_35.pcap', 51639),
]:
    print(f"\n[{pcap_name}] Looking for port {port_target}...")
    packets = parse_pcap_packets(pcap_name)
    
    found_on_port = []
    for pkt in packets:
        info = extract_ip_udp_payload(pkt['data'])
        if info and (info['src_port'] == port_target or info['dst_port'] == port_target):
            found_on_port.append(info)
    
    print(f"  Found {len(found_on_port)} packets on port {port_target}")
    
    if found_on_port:
        # Show unique command IDs
        cmd_ids = {}
        for pkt in found_on_port:
            payload = pkt['payload']
            if len(payload) > 0:
                cmd_id = payload[0]
                if cmd_id not in cmd_ids:
                    cmd_ids[cmd_id] = []
                cmd_ids[cmd_id].append({
                    'src': pkt['src_port'],
                    'dst': pkt['dst_port'],
                    'len': len(payload),
                    'payload': payload[:min(60, len(payload))]
                })
        
        print(f"  Command IDs on this port:")
        for cmd_id in sorted(cmd_ids.keys()):
            examples = cmd_ids[cmd_id]
            print(f"    0x{cmd_id:02x}: {len(examples)} packets")
            for ex in examples[:2]:  # Show first 2
                from binascii import hexlify
                print(f"           {ex['src']} → {ex['dst']}, {ex['len']} bytes: {hexlify(ex['payload']).decode()}")
