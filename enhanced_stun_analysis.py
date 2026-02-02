#!/usr/bin/env python3
"""
Enhanced STUN analysis focusing on what TLS decryption exposes.
Looks for port mappings, credentials, and ICE candidate information.
"""

from scapy.all import rdpcap, UDP, IP, Raw
import struct
import sys

STUN_MAGIC = 0x2112A442

def parse_stun_packet(payload):
    """Parse a STUN packet and extract all details."""
    if len(payload) < 20:
        return None
    
    msg_type = struct.unpack('!H', payload[0:2])[0]
    msg_length = struct.unpack('!H', payload[2:4])[0]
    magic = struct.unpack('!I', payload[4:8])[0]
    
    if magic != STUN_MAGIC:
        return None
    
    txn_id = payload[8:20].hex()
    
    # Parse attributes
    attributes = []
    offset = 20
    
    while offset < len(payload):
        if offset + 4 > len(payload):
            break
        
        attr_type = struct.unpack('!H', payload[offset:offset+2])[0]
        attr_len = struct.unpack('!H', payload[offset+2:offset+4])[0]
        
        if offset + 4 + attr_len > len(payload):
            break
        
        attr_value = payload[offset+4:offset+4+attr_len]
        
        attr_info = {
            'type': attr_type,
            'length': attr_len,
            'value_hex': attr_value.hex()
        }
        
        # Decode known attributes
        if attr_type == 0x0001:  # MAPPED-ADDRESS
            attr_info['name'] = 'MAPPED-ADDRESS'
            if attr_len >= 8:
                family = attr_value[1]
                port = struct.unpack('!H', attr_value[2:4])[0]
                ip = '.'.join(str(b) for b in attr_value[4:8])
                attr_info['decoded'] = f"{ip}:{port}"
        
        elif attr_type == 0x0020:  # XOR-MAPPED-ADDRESS
            attr_info['name'] = 'XOR-MAPPED-ADDRESS'
            if attr_len >= 8:
                family = attr_value[1]
                xor_port = struct.unpack('!H', attr_value[2:4])[0]
                port = xor_port ^ (STUN_MAGIC >> 16)
                
                xor_ip = struct.unpack('!I', attr_value[4:8])[0]
                ip_int = xor_ip ^ STUN_MAGIC
                ip = '.'.join(str((ip_int >> (8*i)) & 0xFF) for i in range(3, -1, -1))
                attr_info['decoded'] = f"{ip}:{port}"
        
        elif attr_type == 0x0006:  # USERNAME
            attr_info['name'] = 'USERNAME'
            try:
                attr_info['decoded'] = attr_value.decode('utf-8', errors='ignore')
            except:
                pass
        
        elif attr_type == 0x0014:  # REALM
            attr_info['name'] = 'REALM'
            try:
                attr_info['decoded'] = attr_value.decode('utf-8', errors='ignore')
            except:
                pass
        
        elif attr_type == 0x0015:  # NONCE
            attr_info['name'] = 'NONCE'
            try:
                attr_info['decoded'] = attr_value.decode('utf-8', errors='ignore')
            except:
                pass
        
        elif attr_type == 0x0008:  # MESSAGE-INTEGRITY
            attr_info['name'] = 'MESSAGE-INTEGRITY'
        
        elif attr_type == 0x8028:  # FINGERPRINT
            attr_info['name'] = 'FINGERPRINT'
        
        elif attr_type == 0x8022:  # SOFTWARE
            attr_info['name'] = 'SOFTWARE'
            try:
                attr_info['decoded'] = attr_value.decode('utf-8', errors='ignore')
            except:
                pass
        
        else:
            attr_info['name'] = f'UNKNOWN(0x{attr_type:04X})'
        
        attributes.append(attr_info)
        
        # Move to next attribute (with padding)
        offset += 4 + attr_len
        if attr_len % 4:
            offset += 4 - (attr_len % 4)
    
    return {
        'msg_type': msg_type,
        'msg_length': msg_length,
        'txn_id': txn_id,
        'attributes': attributes
    }

def analyze_stun_pcap(filename):
    print(f"{'='*80}")
    print(f"Enhanced STUN Analysis: {filename}")
    print(f"{'='*80}\n")
    
    try:
        packets = rdpcap(filename)
    except Exception as e:
        print(f"Error reading PCAP: {e}")
        return
    
    stun_packets = []
    port_mappings = {}
    credentials = set()
    
    for i, pkt in enumerate(packets):
        if UDP in pkt and Raw in pkt:
            payload = bytes(pkt[Raw].load)
            stun_info = parse_stun_packet(payload)
            
            if stun_info:
                src = f"{pkt[IP].src}:{pkt[UDP].sport}"
                dst = f"{pkt[IP].dst}:{pkt[UDP].dport}"
                
                stun_packets.append({
                    'index': i,
                    'src': src,
                    'dst': dst,
                    'stun': stun_info
                })
                
                # Extract port mappings
                for attr in stun_info['attributes']:
                    if attr['name'] in ['MAPPED-ADDRESS', 'XOR-MAPPED-ADDRESS'] and 'decoded' in attr:
                        if src not in port_mappings:
                            port_mappings[src] = []
                        port_mappings[src].append(attr['decoded'])
                    
                    # Extract credentials
                    if attr['name'] in ['USERNAME', 'REALM'] and 'decoded' in attr:
                        credentials.add((attr['name'], attr['decoded']))
    
    print(f"Found {len(stun_packets)} STUN packets\n")
    
    # Show credentials
    if credentials:
        print(f"{'='*80}")
        print("ICE/TURN Credentials Discovered:")
        print(f"{'='*80}\n")
        for cred_type, value in sorted(credentials):
            print(f"{cred_type:15s}: {value}")
        print()
    
    # Show port mappings
    if port_mappings:
        print(f"{'='*80}")
        print("Port Mappings (NAT Traversal):")
        print(f"{'='*80}\n")
        for src, mappings in port_mappings.items():
            unique_mappings = list(set(mappings))
            if unique_mappings:
                print(f"{src:30s} ↔ {', '.join(unique_mappings)}")
        print()
    
    # Show first few packets with details
    print(f"{'='*80}")
    print("Sample STUN Packets (first 5 with interesting attributes):")
    print(f"{'='*80}\n")
    
    count = 0
    for pkt_info in stun_packets:
        if count >= 5:
            break
        
        # Only show packets with USERNAME or XOR-MAPPED-ADDRESS
        has_interesting = any(
            attr['name'] in ['USERNAME', 'XOR-MAPPED-ADDRESS', 'REALM']
            for attr in pkt_info['stun']['attributes']
        )
        
        if has_interesting:
            count += 1
            print(f"Packet #{pkt_info['index']}:")
            print(f"  {pkt_info['src']} → {pkt_info['dst']}")
            print(f"  Type: 0x{pkt_info['stun']['msg_type']:04X}")
            print(f"  Transaction ID: {pkt_info['stun']['txn_id']}")
            print(f"  Attributes:")
            
            for attr in pkt_info['stun']['attributes']:
                if 'decoded' in attr:
                    print(f"    • {attr['name']:20s}: {attr['decoded']}")
                else:
                    print(f"    • {attr['name']:20s}: (binary data)")
            print()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python enhanced_stun_analysis.py <pcap_file>")
        sys.exit(1)
    
    analyze_stun_pcap(sys.argv[1])
