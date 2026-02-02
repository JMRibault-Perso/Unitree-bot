#!/usr/bin/env python3
"""
Extract STUN credentials from PCAP and derive encryption keys.
Uses raw PCAP parsing like analyze_stun_port_discovery.py
"""

import struct
from pathlib import Path
from binascii import hexlify, unhexlify
import hmac
import hashlib
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
            else:
                return None, None, None
        else:
            ip_offset = 0
        
        # Parse IP header
        if len(packet_data) < ip_offset + 20:
            return None, None, None
        
        version_ihl = packet_data[ip_offset]
        ihl = (version_ihl & 0x0F) * 4
        
        src_ip = struct.unpack('>I', packet_data[ip_offset+12:ip_offset+16])[0]
        dst_ip = struct.unpack('>I', packet_data[ip_offset+16:ip_offset+20])[0]
        
        # Parse UDP header
        if len(packet_data) < ip_offset + ihl + 8:
            return None, None, None
        
        udp_offset = ip_offset + ihl
        src_port = struct.unpack('>H', packet_data[udp_offset:udp_offset+2])[0]
        dst_port = struct.unpack('>H', packet_data[udp_offset+2:udp_offset+4])[0]
        
        # Extract UDP payload
        payload_offset = udp_offset + 8
        udp_payload = packet_data[payload_offset:]
        
        return (src_ip, src_port, dst_ip, dst_port), udp_payload, ihl
    except:
        return None, None, None

def ip_to_str(ip_int):
    """Convert IP integer to string"""
    return '.'.join(str((ip_int >> (8*i)) & 0xFF) for i in [3, 2, 1, 0])

def extract_stun_attributes(stun_payload):
    """Extract STUN attributes from payload"""
    attributes = {}
    
    if len(stun_payload) < 20:
        return attributes
    
    # Verify STUN magic cookie
    magic = struct.unpack('>I', stun_payload[4:8])[0]
    if magic != STUN_MAGIC:
        return attributes
    
    msg_len = struct.unpack('>H', stun_payload[2:4])[0]
    
    # Parse attributes
    offset = 20
    while offset + 4 <= len(stun_payload):
        attr_type = struct.unpack('>H', stun_payload[offset:offset+2])[0]
        attr_len = struct.unpack('>H', stun_payload[offset+2:offset+4])[0]
        
        if offset + 4 + attr_len > len(stun_payload):
            break
        
        attr_data = stun_payload[offset+4:offset+4+attr_len]
        
        # Store attribute
        if attr_type not in attributes:
            attributes[attr_type] = []
        attributes[attr_type].append(attr_data)
        
        # Move to next attribute (with padding to 4-byte boundary)
        padded_len = 4 + ((attr_len + 3) // 4) * 4
        offset += padded_len
    
    return attributes

def extract_credentials_from_pcap(pcap_file):
    """Extract STUN credentials from PCAP"""
    packets = parse_pcap_packets(pcap_file)
    credentials = set()
    stun_count = 0
    
    print(f"[*] Scanning {len(packets)} packets for STUN...")
    
    for pkt in packets:
        info, payload, ihl = extract_ip_udp_payload(pkt['data'])
        
        if info is None or payload is None:
            continue
        
        src_ip, src_port, dst_ip, dst_port = info
        
        if len(payload) < 20:
            continue
        
        # Check for STUN magic cookie
        magic = struct.unpack('>I', payload[4:8])[0]
        if magic == STUN_MAGIC:
            stun_count += 1
            attrs = extract_stun_attributes(payload)
            
            # Extract USERNAME (0x0006)
            if 0x0006 in attrs:
                for username_data in attrs[0x0006]:
                    try:
                        username = username_data.decode('utf-8')
                        credentials.add(username)
                        print(f"[+] Found USERNAME: {username}")
                        print(f"    Hex: {hexlify(username_data).decode()}")
                        print(f"    From: {ip_to_str(src_ip)}:{src_port} → {ip_to_str(dst_ip)}:{dst_port}")
                    except:
                        pass
            
            # Extract MESSAGE-INTEGRITY (0x0008)
            if 0x0008 in attrs and stun_count <= 3:
                for integrity_data in attrs[0x0008]:
                    print(f"[+] MESSAGE-INTEGRITY: {hexlify(integrity_data).decode()}")
            
            # Extract REALM (0x0014)
            if 0x0014 in attrs:
                for realm_data in attrs[0x0014]:
                    try:
                        realm = realm_data.decode('utf-8')
                        print(f"[+] Found REALM: {realm}")
                    except:
                        pass
            
            # Extract NONCE (0x0015)
            if 0x0015 in attrs and stun_count <= 3:
                for nonce_data in attrs[0x0015]:
                    print(f"[+] NONCE: {hexlify(nonce_data).decode()}")
    
    print(f"\n[*] Total STUN packets found: {stun_count}")
    return credentials

def derive_keys_from_stun_username(username):
    """Derive potential encryption keys from STUN username"""
    keys = {}
    
    # Method 1: Direct ASCII
    keys['direct_ascii'] = username.encode()
    print(f"[Method 1] Direct ASCII: {hexlify(keys['direct_ascii']).decode()}")
    
    # Method 2: HMAC-SHA1 with empty key (per RFC 5389)
    keys['hmac_sha1_empty'] = hmac.new(b'', username.encode(), hashlib.sha1).digest()
    print(f"[Method 2] HMAC-SHA1(empty_key, username): {hexlify(keys['hmac_sha1_empty']).decode()}")
    
    # Method 3: HMAC-SHA1 with username as key
    keys['hmac_sha1_self'] = hmac.new(username.encode(), username.encode(), hashlib.sha1).digest()
    print(f"[Method 3] HMAC-SHA1(username, username): {hexlify(keys['hmac_sha1_self']).decode()}")
    
    # Method 4: HMAC-SHA1 with "unitree" key
    keys['hmac_sha1_unitree'] = hmac.new(b'unitree', username.encode(), hashlib.sha1).digest()
    print(f"[Method 4] HMAC-SHA1('unitree', username): {hexlify(keys['hmac_sha1_unitree']).decode()}")
    
    # Method 5: SHA1 hash of username
    keys['sha1_username'] = hashlib.sha1(username.encode()).digest()
    print(f"[Method 5] SHA1(username): {hexlify(keys['sha1_username']).decode()}")
    
    # Method 6: SHA256 hash of username
    keys['sha256_username'] = hashlib.sha256(username.encode()).digest()
    print(f"[Method 6] SHA256(username): {hexlify(keys['sha256_username']).decode()}")
    
    # Method 7: First 16 bytes of HMAC-SHA1 (for AES-128)
    keys['aes128_from_hmac'] = keys['hmac_sha1_self'][:16]
    print(f"[Method 7] AES-128 from HMAC-SHA1: {hexlify(keys['aes128_from_hmac']).decode()}")
    
    # Method 8: MD5 hash of username (Blowfish alternative)
    keys['md5_username'] = hashlib.md5(username.encode()).digest()
    print(f"[Method 8] MD5(username): {hexlify(keys['md5_username']).decode()}")
    
    return keys

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 decrypt_with_stun_credentials.py <pcap_file>")
        sys.exit(1)
    
    pcap_file = sys.argv[1]
    
    print(f"[*] Analyzing {pcap_file} for STUN credentials...")
    print(f"{'='*60}\n")
    
    # Extract credentials
    credentials = extract_credentials_from_pcap(pcap_file)
    
    if not credentials:
        print("[-] No STUN credentials found")
        return
    
    print(f"\n{'='*60}")
    print(f"[*] Found {len(credentials)} unique credential(s)")
    print(f"{'='*60}\n")
    
    for username in credentials:
        print(f"[*] Deriving keys from STUN username: {username}")
        keys = derive_keys_from_stun_username(username)
        print()

if __name__ == '__main__':
    main()
