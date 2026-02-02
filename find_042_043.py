#!/usr/bin/env python3
"""Find 0x42 and 0x43 commands specifically"""

import struct
from binascii import hexlify

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

for pcap_name in ['PCAPdroid_30_Jan_18_19_57.pcap', 'PCAPdroid_30_Jan_18_26_35.pcap']:
    print(f"\n[{pcap_name}] Searching for 0x42 and 0x43...")
    packets = parse_pcap_packets(pcap_name)
    
    found_42 = []
    found_43 = []
    
    for pkt in packets:
        info = extract_ip_udp_payload(pkt['data'])
        if info and len(info['payload']) > 0:
            cmd_id = info['payload'][0]
            if cmd_id == 0x42:
                found_42.append(info)
            elif cmd_id == 0x43:
                found_43.append(info)
    
    print(f"  0x42 (delete): {len(found_42)} packets")
    for pkt in found_42[:3]:
        print(f"    {pkt['src_port']} → {pkt['dst_port']}, {len(pkt['payload'])} bytes")
        print(f"      {hexlify(pkt['payload'][:80]).decode()}")
    
    print(f"  0x43 (rename): {len(found_43)} packets")
    for pkt in found_43[:3]:
        print(f"    {pkt['src_port']} → {pkt['dst_port']}, {len(pkt['payload'])} bytes")
        print(f"      {hexlify(pkt['payload'][:80]).decode()}")
