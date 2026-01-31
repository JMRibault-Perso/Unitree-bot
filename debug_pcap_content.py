#!/usr/bin/env python3
"""Debug: Show all unique command IDs in PCAP"""

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
            packets.append({'data': packet_data, 'size': orig_len})
    return packets

def extract_ip_udp_payload(packet_data):
    try:
        if len(packet_data) > 34:
            eth_type = struct.unpack('>H', packet_data[12:14])[0]
            ip_offset = 14 if eth_type == 0x0800 else 0
        else:
            ip_offset = 0
        
        if len(packet_data) < ip_offset + 20:
            return None, None
        
        version_ihl = packet_data[ip_offset]
        ihl = (version_ihl & 0x0F) * 4
        
        if len(packet_data) < ip_offset + ihl + 8:
            return None, None
        
        udp_offset = ip_offset + ihl
        src_port = struct.unpack('>H', packet_data[udp_offset:udp_offset+2])[0]
        dst_port = struct.unpack('>H', packet_data[udp_offset+2:udp_offset+4])[0]
        
        payload_offset = udp_offset + 8
        udp_payload = packet_data[payload_offset:]
        
        return (src_port, dst_port), udp_payload
    except:
        return None, None

for pcap_name in ['PCAPdroid_30_Jan_18_19_57.pcap', 'PCAPdroid_30_Jan_18_26_35.pcap']:
    print(f"\n[{pcap_name}]")
    packets = parse_pcap_packets(pcap_name)
    
    cmd_ids = {}
    port_pairs = {}
    
    for pkt in packets:
        info, payload = extract_ip_udp_payload(pkt['data'])
        if info and payload and len(payload) > 0:
            port_key = info
            if port_key not in port_pairs:
                port_pairs[port_key] = 0
            port_pairs[port_key] += 1
            
            # Check command ID (first byte if not STUN)
            if len(payload) >= 4:
                magic = struct.unpack('>I', payload[0:4])[0]
                if magic != 0x2112A442:  # Not STUN
                    cmd_id = payload[0]
                    if cmd_id not in cmd_ids:
                        cmd_ids[cmd_id] = 0
                    cmd_ids[cmd_id] += 1
    
    print(f"  Command IDs found (non-STUN):")
    if cmd_ids:
        for cmd_id in sorted(cmd_ids.keys()):
            print(f"    0x{cmd_id:02x}: {cmd_ids[cmd_id]} packets")
    else:
        print(f"    None (all STUN or other)")
    
    print(f"  Port pairs:")
    for (src, dst), count in sorted(port_pairs.items()):
        print(f"    {src} → {dst}: {count} packets")
