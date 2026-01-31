#!/usr/bin/env python3
"""Extract encrypted payloads on port 51639 and test STUN keys"""

import struct
from binascii import hexlify, unhexlify

# Derived keys
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

def try_xor_decrypt(payload, key):
    """Try XOR decryption"""
    decrypted = bytearray()
    for i, byte in enumerate(payload):
        decrypted.append(byte ^ key[i % len(key)])
    return bytes(decrypted)

def search_plaintext(data):
    """Search for common plaintext patterns"""
    patterns = [
        b'test', b'walk', b'arm', b'hand', b'head', b'jump', b'run', b'stand',
        b'sit', b'hello', b'dance', b'wave', b'stretch', b'bow', b'action',
        b'teach', b'mode', b'get', b'set', b'cmd', b'req', b'resp',
    ]
    found = []
    for pattern in patterns:
        if pattern in data:
            found.append(pattern.decode())
    return found

# Get packets from main PCAP
print("[*] Extracting port 51639 packets...")
packets = parse_pcap_packets('PCAPdroid_30_Jan_18_26_35.pcap')

port_51639_packets = []
for pkt in packets:
    info = extract_ip_udp_payload(pkt['data'])
    if info and (info['src_port'] == 51639 or info['dst_port'] == 51639):
        port_51639_packets.append(info)

print(f"[*] Found {len(port_51639_packets)} packets on port 51639")

# Get command 0x14, 0x16, 0x17 (looks like encrypted application data)
print(f"\n[*] Testing 0x14 packets with STUN keys (XOR)...")
for pkt in port_51639_packets[:20]:
    if pkt['payload'][0] == 0x14:
        payload = pkt['payload'][1:]  # Skip command byte
        print(f"\n  0x14 payload: {len(payload)} bytes")
        for key_name, key in DERIVED_KEYS.items():
            xor_result = try_xor_decrypt(payload, key)
            patterns = search_plaintext(xor_result)
            if patterns:
                print(f"    [!!!] XOR with {key_name} MATCH: {patterns}")
                print(f"          {hexlify(xor_result[:60]).decode()}")

print(f"\n[*] Testing 0x16 packets with STUN keys (XOR)...")
for pkt in port_51639_packets[:20]:
    if pkt['payload'][0] == 0x16:
        payload = pkt['payload'][1:]  # Skip command byte
        print(f"\n  0x16 payload: {len(payload)} bytes")
        for key_name in ['direct_ascii', 'hmac_sha1_self']:
            key = DERIVED_KEYS[key_name]
            xor_result = try_xor_decrypt(payload, key)
            patterns = search_plaintext(xor_result)
            if patterns:
                print(f"    [!!!] XOR with {key_name} MATCH: {patterns}")
                print(f"          {hexlify(xor_result[:60]).decode()}")
        # Just show first few chars decrypted with best key
        xor_result = try_xor_decrypt(payload[:40], DERIVED_KEYS['direct_ascii'])
        print(f"    Sample XOR with direct_ascii: {hexlify(xor_result).decode()}")

print(f"\n[*] Sample 0x17 (high volume - telemetry):")
for i, pkt in enumerate(port_51639_packets):
    if pkt['payload'][0] == 0x17:
        print(f"    {pkt['src_port']} → {pkt['dst_port']}, {len(pkt['payload'])} bytes")
        if i < 3:
            print(f"      {hexlify(pkt['payload'][:40]).decode()}")
        break
