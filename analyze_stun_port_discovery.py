#!/usr/bin/env python3
"""
STUN Protocol Analysis for Unitree G1 Teaching Mode
Analyzes PCAP files to find STUN port discovery and negotiation
"""

import struct
from pathlib import Path
from collections import defaultdict
import sys

# STUN magic cookie (RFC 5389)
STUN_MAGIC = 0x2112A442

def parse_pcap_packets(pcap_file):
    """Parse PCAP file and extract packets"""
    packets = []
    
    with open(pcap_file, 'rb') as f:
        # Skip PCAP global header (24 bytes)
        global_header = f.read(24)
        
        while True:
            packet_header = f.read(16)
            if len(packet_header) < 16:
                break
            
            ts_sec, ts_usec, incl_len, orig_len = struct.unpack('<IIII', packet_header)
            packet_data = f.read(incl_len)
            
            if len(packet_data) < incl_len:
                break
            
            packets.append({
                'timestamp': ts_sec + ts_usec / 1e6,
                'data': packet_data,
                'size': orig_len
            })
    
    return packets

def extract_ip_udp_payload(packet_data):
    """Extract IP header info and UDP payload"""
    try:
        # Skip Ethernet header (14 bytes) if present
        if len(packet_data) > 34:
            eth_type = struct.unpack('>H', packet_data[12:14])[0]
            
            if eth_type == 0x0800:  # IPv4
                ip_offset = 14
                ip_version = packet_data[ip_offset] >> 4
                ip_header_len = (packet_data[ip_offset] & 0x0F) * 4
                
                if packet_data[ip_offset + 9] == 17:  # UDP protocol
                    ip_src = '.'.join(str(b) for b in packet_data[ip_offset+12:ip_offset+16])
                    ip_dst = '.'.join(str(b) for b in packet_data[ip_offset+16:ip_offset+20])
                    
                    udp_offset = ip_offset + ip_header_len
                    src_port, dst_port, udp_len = struct.unpack('>HHH', packet_data[udp_offset:udp_offset+6])
                    
                    payload = packet_data[udp_offset+8:]
                    
                    return {
                        'src_ip': ip_src,
                        'dst_ip': ip_dst,
                        'src_port': src_port,
                        'dst_port': dst_port,
                        'payload': payload
                    }
    except:
        pass
    
    return None

def is_stun_packet(payload):
    """Check if payload is a STUN packet"""
    if len(payload) < 20:
        return False
    
    # STUN starts with message type (2 bytes) + message length (2 bytes) + magic cookie (4 bytes)
    msg_type = struct.unpack('>H', payload[0:2])[0]
    msg_len = struct.unpack('>H', payload[2:4])[0]
    magic = struct.unpack('>I', payload[4:8])[0]
    
    return magic == STUN_MAGIC

def parse_stun_packet(payload):
    """Parse STUN packet and extract attributes"""
    if len(payload) < 20:
        return None
    
    msg_type = struct.unpack('>H', payload[0:2])[0]
    msg_len = struct.unpack('>H', payload[2:4])[0]
    magic = struct.unpack('>I', payload[4:8])[0]
    transaction_id = payload[8:20]
    
    # Determine message type
    msg_class = msg_type & 0x0110
    msg_method = msg_type & 0x3EEF
    
    if msg_method == 0x0001:
        method_name = "Binding Request"
    elif msg_method == 0x0101:
        method_name = "Binding Response"
    elif msg_method == 0x0111:
        method_name = "Binding Error Response"
    elif msg_method == 0x0002:
        method_name = "Allocate"
    elif msg_method == 0x0102:
        method_name = "Allocate Response"
    else:
        method_name = f"Unknown (0x{msg_method:04X})"
    
    stun_info = {
        'type': msg_type,
        'method': method_name,
        'length': msg_len,
        'transaction_id': transaction_id.hex(),
        'attributes': []
    }
    
    # Parse attributes
    attr_offset = 20
    while attr_offset < 20 + msg_len and attr_offset + 4 <= len(payload):
        attr_type = struct.unpack('>H', payload[attr_offset:attr_offset+2])[0]
        attr_len = struct.unpack('>H', payload[attr_offset+2:attr_offset+4])[0]
        attr_value = payload[attr_offset+4:attr_offset+4+attr_len]
        
        # Parse common attributes
        attr_name = get_stun_attribute_name(attr_type)
        
        if attr_type == 0x0020:  # XOR-MAPPED-ADDRESS
            stun_info['attributes'].append(parse_xor_mapped_address(attr_value))
        elif attr_type == 0x0001:  # MAPPED-ADDRESS
            stun_info['attributes'].append(parse_mapped_address(attr_value))
        else:
            stun_info['attributes'].append({
                'name': attr_name,
                'type': attr_type,
                'length': attr_len,
                'hex': attr_value[:16].hex()  # First 16 bytes
            })
        
        # Padding to 4-byte boundary
        attr_offset += 4 + ((attr_len + 3) & ~3)
    
    return stun_info

def get_stun_attribute_name(attr_type):
    """Map STUN attribute type to name"""
    names = {
        0x0001: "MAPPED-ADDRESS",
        0x0002: "RESPONSE-ADDRESS",
        0x0003: "CHANGE-REQUEST",
        0x0004: "SOURCE-ADDRESS",
        0x0005: "CHANGED-ADDRESS",
        0x0006: "USERNAME",
        0x0007: "PASSWORD",
        0x0008: "MESSAGE-INTEGRITY",
        0x0009: "ERROR-CODE",
        0x000A: "UNKNOWN-ATTRIBUTES",
        0x000B: "REFLECTED-FROM",
        0x0014: "REALM",
        0x0015: "NONCE",
        0x0020: "XOR-MAPPED-ADDRESS",
        0x8022: "SOFTWARE",
        0x8023: "ALTERNATE-SERVER",
        0x8028: "FINGERPRINT",
    }
    return names.get(attr_type, f"UNKNOWN(0x{attr_type:04X})")

def parse_mapped_address(data):
    """Parse MAPPED-ADDRESS attribute"""
    if len(data) < 4:
        return {'name': 'MAPPED-ADDRESS', 'error': 'too short'}
    
    family = data[1]  # 0x01 = IPv4, 0x02 = IPv6
    port = struct.unpack('>H', data[2:4])[0]
    
    if family == 1 and len(data) >= 8:
        ip = '.'.join(str(b) for b in data[4:8])
        return {'name': 'MAPPED-ADDRESS', 'ip': ip, 'port': port}
    
    return {'name': 'MAPPED-ADDRESS', 'family': family, 'port': port}

def parse_xor_mapped_address(data):
    """Parse XOR-MAPPED-ADDRESS attribute"""
    if len(data) < 4:
        return {'name': 'XOR-MAPPED-ADDRESS', 'error': 'too short'}
    
    family = data[1]
    xor_port = struct.unpack('>H', data[2:4])[0]
    port = xor_port ^ 0x2112  # XOR with STUN magic high word
    
    if family == 1 and len(data) >= 8:
        xor_ip = data[4:8]
        magic_bytes = struct.pack('>I', STUN_MAGIC)
        ip_bytes = bytes(a ^ b for a, b in zip(xor_ip, magic_bytes))
        ip = '.'.join(str(b) for b in ip_bytes)
        return {'name': 'XOR-MAPPED-ADDRESS', 'ip': ip, 'port': port}
    
    return {'name': 'XOR-MAPPED-ADDRESS', 'family': family, 'port': port}

def analyze_pcap_for_stun(pcap_file):
    """Analyze PCAP for STUN protocol"""
    print(f"\n{'='*70}")
    print(f"STUN PROTOCOL ANALYSIS: {pcap_file.name}")
    print(f"{'='*70}")
    
    packets = parse_pcap_packets(pcap_file)
    stun_packets = []
    port_mapping = defaultdict(list)
    
    for pkt in packets:
        udp_info = extract_ip_udp_payload(pkt['data'])
        
        if udp_info and is_stun_packet(udp_info['payload']):
            stun_info = parse_stun_packet(udp_info['payload'])
            
            if stun_info:
                stun_info['src_ip'] = udp_info['src_ip']
                stun_info['dst_ip'] = udp_info['dst_ip']
                stun_info['src_port'] = udp_info['src_port']
                stun_info['dst_port'] = udp_info['dst_port']
                stun_info['timestamp'] = pkt['timestamp']
                
                stun_packets.append(stun_info)
                
                # Track port mapping
                port_mapping[f"{udp_info['src_ip']}:{udp_info['src_port']}"].append({
                    'external': f"{udp_info['dst_ip']}:{udp_info['dst_port']}",
                    'method': stun_info['method'],
                    'time': pkt['timestamp']
                })
    
    if not stun_packets:
        print("✗ No STUN packets found")
        return None
    
    print(f"\n✓ Found {len(stun_packets)} STUN packets\n")
    
    # Display STUN packets
    for i, pkt in enumerate(stun_packets[:10]):  # Show first 10
        print(f"[{i+1}] {pkt['method']}")
        print(f"    Source: {pkt['src_ip']}:{pkt['src_port']}")
        print(f"    Destination: {pkt['dst_ip']}:{pkt['dst_port']}")
        print(f"    Transaction ID: {pkt['transaction_id']}")
        
        if pkt['attributes']:
            print(f"    Attributes:")
            for attr in pkt['attributes']:
                if 'ip' in attr:
                    print(f"      • {attr['name']}: {attr['ip']}:{attr['port']}")
                else:
                    print(f"      • {attr['name']}: {attr}")
        print()
    
    # Analyze port discovery pattern
    print(f"\n{'='*70}")
    print("PORT DISCOVERY PATTERN")
    print(f"{'='*70}")
    
    # Find teaching mode UDP port from STUN responses
    teaching_ports = set()
    for pkt in stun_packets:
        for attr in pkt['attributes']:
            if 'port' in attr and attr.get('name') in ['MAPPED-ADDRESS', 'XOR-MAPPED-ADDRESS']:
                teaching_ports.add(attr['port'])
                print(f"✓ Discovered port: {attr['port']} ({attr.get('ip', 'N/A')})")
    
    return stun_packets, teaching_ports

def compare_pcaps(*pcap_files):
    """Compare STUN patterns across multiple PCAP files"""
    print(f"\n{'='*70}")
    print("COMPARING STUN PATTERNS ACROSS PCAP FILES")
    print(f"{'='*70}\n")
    
    all_ports = defaultdict(int)
    
    for pcap_file in pcap_files:
        result = analyze_pcap_for_stun(pcap_file)
        if result:
            _, ports = result
            for port in ports:
                all_ports[port] += 1
    
    print(f"\nPort Summary Across All Captures:")
    for port in sorted(all_ports.keys()):
        print(f"  Port {port}: Found in {all_ports[port]} capture(s)")

def main():
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <pcap_file> [<pcap_file2> ...]")
        print(f"Example: {sys.argv[0]} PCAPdroid_30_Jan_18_19_57.pcap PCAPdroid_30_Jan_18_26_35.pcap")
        sys.exit(1)
    
    pcap_files = [Path(f) for f in sys.argv[1:]]
    
    for pcap_file in pcap_files:
        if not pcap_file.exists():
            print(f"✗ File not found: {pcap_file}")
            continue
        
        analyze_pcap_for_stun(pcap_file)
    
    if len(pcap_files) > 1:
        compare_pcaps(*pcap_files)

if __name__ == '__main__':
    main()
