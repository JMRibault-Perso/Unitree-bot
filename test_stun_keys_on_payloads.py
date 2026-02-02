#!/usr/bin/env python3
"""
Test 8 derived STUN credential keys on teaching protocol rename payloads.
Try multiple decryption methods to find plaintext action names.
"""

import struct
from binascii import hexlify, unhexlify
import sys

# STUN magic cookie (RFC 5389)
STUN_MAGIC = 0x2112A442

# Derived keys from STUN username "n7Px:iq2R"
DERIVED_KEYS = {
    'direct_ascii': bytes.fromhex('6e3750783a69713252'),
    'hmac_sha1_empty': bytes.fromhex('872a83c74b2983d0446504a795893934979ba821'),
    'hmac_sha1_self': bytes.fromhex('c985e775994233047396f5796e6b8d7e9c5368b3'),
    'hmac_sha1_unitree': bytes.fromhex('e278cc4b524fcd338e70a60d481abef938441e9a'),
    'sha1_username': bytes.fromhex('a439021cdf370de9919d66c86312147d09413747'),
    'sha256_username': bytes.fromhex('59626fb5894cd61e0ec3c4558fa16db9cfeaed1aa5d8b6a32ccf872b90c14516'),
    'aes128_from_hmac': bytes.fromhex('c985e775994233047396f5796e6b8d7e'),
    'md5_username': bytes.fromhex('82df3b3e0842cf1576becb063bb920dd'),
}

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

def extract_teaching_commands_from_pcap(pcap_file):
    """Extract teaching protocol commands from PCAP"""
    packets = parse_pcap_packets(pcap_file)
    commands = {}  # cmd_id -> [payloads]
    
    print(f"[*] Scanning {len(packets)} packets for teaching protocol commands...")
    
    for pkt in packets:
        info, payload, ihl = extract_ip_udp_payload(pkt['data'])
        
        if info is None or payload is None or len(payload) < 1:
            continue
        
        # Teaching protocol commands are NOT STUN (no 0x2112A442 magic)
        if len(payload) >= 4:
            magic = struct.unpack('>I', payload[0:4])[0]
            if magic == STUN_MAGIC:
                continue  # Skip STUN packets
        
        cmd_id = payload[0]
        
        # Look for teaching commands (0x41-0x43, 0x1A, etc.)
        if cmd_id in [0x1A, 0x41, 0x42, 0x43, 0x2B] or cmd_id in range(0x09, 0x10):
            if cmd_id not in commands:
                commands[cmd_id] = []
            commands[cmd_id].append(payload)
    
    return commands

def try_xor_decrypt(payload, key):
    """Try XOR decryption"""
    decrypted = bytearray()
    for i, byte in enumerate(payload):
        decrypted.append(byte ^ key[i % len(key)])
    return bytes(decrypted)

def try_caesar(payload, shift):
    """Try Caesar cipher"""
    return bytes([(b - shift) % 256 for b in payload])

def try_simple_aes_ecb(payload, key):
    """Try simple AES-ECB (if PyCryptodome available)"""
    try:
        from Crypto.Cipher import AES
        # Pad key to 16, 24, or 32 bytes for AES
        key_len = len(key)
        if key_len >= 32:
            aes_key = key[:32]
        elif key_len >= 24:
            aes_key = key[:24]
        else:
            aes_key = (key * ((16 // len(key)) + 1))[:16]
        
        cipher = AES.new(aes_key, AES.MODE_ECB)
        if len(payload) % 16 == 0:
            return cipher.decrypt(payload)
    except:
        pass
    return None

def is_printable_ascii(data, min_ratio=0.5):
    """Check if data is mostly printable ASCII"""
    printable = sum(1 for b in data if 32 <= b < 127 or b in (9, 10, 13))
    return printable / len(data) >= min_ratio if len(data) > 0 else False

def search_plaintext(data):
    """Search for common plaintext patterns"""
    patterns = [
        b'test', b'walk', b'arm', b'hand', b'head', b'jump', b'run', b'stand',
        b'sit', b'hello', b'dance', b'wave', b'stretch', b'bow', b'action',
        b'name', b'teach', b'mode', b'motor', b'cmd', b'data', b'msg',
    ]
    
    found = []
    for pattern in patterns:
        if pattern in data:
            found.append(pattern.decode())
    
    return found

def test_decryption_on_commands(commands, derived_keys):
    """Test all decryption methods on extracted commands"""
    
    for cmd_id in sorted(commands.keys()):
        payloads = commands[cmd_id]
        print(f"\n{'='*70}")
        print(f"Command 0x{cmd_id:02x} ({len(payloads)} payloads)")
        print(f"{'='*70}")
        
        if cmd_id == 0x43:  # Rename command - focus on this
            print(f"[*] Focus: This is RENAME command (0x43)")
        
        # Test first 3 payloads
        for payload_idx, payload in enumerate(payloads[:3]):
            print(f"\n[Payload {payload_idx + 1}] {len(payload)} bytes")
            print(f"  Hex: {hexlify(payload[:min(64, len(payload))]).decode()}")
            if len(payload) > 64:
                print(f"       ... ({len(payload) - 64} more bytes)")
            
            # Skip command byte, test payload data
            test_payload = payload[1:]
            
            for key_name, key in derived_keys.items():
                # Method 1: XOR
                xor_result = try_xor_decrypt(test_payload, key)
                if is_printable_ascii(xor_result):
                    patterns = search_plaintext(xor_result)
                    if patterns:
                        print(f"\n  [!!!] XOR with {key_name} MATCH: {patterns}")
                        print(f"        {xor_result[:80]}")
                
                # Method 2: Caesar (try shifts 0-25)
                for shift in range(26):
                    caesar_result = try_caesar(test_payload, shift)
                    patterns = search_plaintext(caesar_result)
                    if patterns:
                        print(f"\n  [!!!] Caesar(shift={shift}) with {key_name} MATCH: {patterns}")
                        print(f"        {caesar_result[:80]}")
                
                # Method 3: AES-ECB
                aes_result = try_simple_aes_ecb(test_payload, key)
                if aes_result and is_printable_ascii(aes_result):
                    patterns = search_plaintext(aes_result)
                    if patterns:
                        print(f"\n  [!!!] AES-ECB with {key_name} MATCH: {patterns}")
                        print(f"        {aes_result[:80]}")

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 test_stun_keys_on_payloads.py <pcap_file>")
        sys.exit(1)
    
    pcap_file = sys.argv[1]
    
    print(f"[*] Extracting teaching protocol commands from {pcap_file}...")
    commands = extract_teaching_commands_from_pcap(pcap_file)
    
    print(f"\n[*] Found {sum(len(v) for v in commands.values())} total teaching payloads")
    for cmd_id in sorted(commands.keys()):
        print(f"    0x{cmd_id:02x}: {len(commands[cmd_id])} payloads")
    
    print(f"\n[*] Testing {len(DERIVED_KEYS)} decryption keys on payloads...")
    print(f"    Keys: {list(DERIVED_KEYS.keys())}")
    
    test_decryption_on_commands(commands, DERIVED_KEYS)

if __name__ == '__main__':
    main()
