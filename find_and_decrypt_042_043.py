#!/usr/bin/env python3
"""
Find which ports actually contain 0x42 (delete) and 0x43 (rename) commands.
Then decrypt those specific payloads with STUN keys.
"""

import struct
import hashlib
import hmac
from pathlib import Path
from binascii import hexlify

# STUN credentials
STUN_USERNAME = "n7Px:iq2R"

def derive_all_keys():
    """Generate all 8 STUN-derived keys"""
    keys = {}
    keys['ascii'] = STUN_USERNAME.encode('ascii')
    keys['hmac_sha1_nopass'] = hmac.new(b'', STUN_USERNAME.encode(), hashlib.sha1).digest()
    keys['hmac_sha1_self'] = hmac.new(STUN_USERNAME.encode(), STUN_USERNAME.encode(), hashlib.sha1).digest()
    keys['hmac_sha1_unitree'] = hmac.new(b'unitree', STUN_USERNAME.encode(), hashlib.sha1).digest()
    reversed_user = STUN_USERNAME[::-1]
    keys['hmac_sha1_reversed'] = hmac.new(reversed_user.encode(), STUN_USERNAME.encode(), hashlib.sha1).digest()
    keys['sha1'] = hashlib.sha1(STUN_USERNAME.encode()).digest()
    keys['sha256'] = hashlib.sha256(STUN_USERNAME.encode()).digest()[:16]
    keys['md5'] = hashlib.md5(STUN_USERNAME.encode()).digest()
    return keys

def xor_decrypt(data, key):
    """XOR decryption"""
    if len(key) == 0:
        return data
    result = bytearray()
    for i, byte in enumerate(data):
        result.append(byte ^ key[i % len(key)])
    return bytes(result)

def find_042_043_packets(pcap_path):
    """Find all packets with 0x42 or 0x43 command IDs"""
    packets_042 = []
    packets_043 = []
    
    with open(pcap_path, 'rb') as f:
        f.read(24)  # Skip global header
        
        packet_num = 0
        while True:
            pkt_header = f.read(16)
            if len(pkt_header) < 16:
                break
            
            ts_sec, ts_usec, incl_len, orig_len = struct.unpack('<IIII', pkt_header)
            packet_data = f.read(incl_len)
            packet_num += 1
            
            if len(packet_data) < 42:
                continue
            
            try:
                eth_type = struct.unpack('>H', packet_data[12:14])[0]
                if eth_type != 0x0800:
                    continue
                
                ip_start = 14
                ip_header = packet_data[ip_start:ip_start+20]
                protocol = ip_header[9]
                
                if protocol != 17:  # Not UDP
                    continue
                
                ip_version_ihl = ip_header[0]
                ip_header_len = (ip_version_ihl & 0x0F) * 4
                
                udp_start = ip_start + ip_header_len
                if udp_start + 8 > len(packet_data):
                    continue
                
                udp_header = packet_data[udp_start:udp_start+8]
                src_port, dst_port = struct.unpack('>HH', udp_header[:4])
                
                payload_start = udp_start + 8
                payload = packet_data[payload_start:]
                
                if len(payload) > 0:
                    cmd_id = payload[0]
                    
                    packet_info = {
                        'packet_num': packet_num,
                        'src_port': src_port,
                        'dst_port': dst_port,
                        'cmd_id': cmd_id,
                        'length': len(payload),
                        'payload': payload
                    }
                    
                    if cmd_id == 0x42:
                        packets_042.append(packet_info)
                    elif cmd_id == 0x43:
                        packets_043.append(packet_info)
            
            except Exception:
                continue
    
    return packets_042, packets_043

def test_all_decryptions(payload, keys):
    """Test all keys with XOR and look for plaintext"""
    results = []
    
    for key_name, key in keys.items():
        decrypted = xor_decrypt(payload, key)
        
        # Check for common patterns
        score = 0
        patterns = []
        
        # Check for printable ASCII
        printable_count = sum(1 for b in decrypted if 32 <= b <= 126)
        if printable_count > len(decrypted) * 0.5:
            score += 1
            patterns.append('ascii')
        
        # Check for keywords
        keywords = [b'test', b'walk', b'arm', b'name', b'action', b'delete', b'rename']
        for kw in keywords:
            if kw in decrypted.lower():
                score += 5
                patterns.append(kw.decode())
        
        # Check for JSON markers
        json_markers = [b'{', b'}', b'"', b':', b',']
        json_count = sum(1 for m in json_markers if m in decrypted)
        if json_count >= 3:
            score += 3
            patterns.append('json')
        
        # Check for null-terminated strings
        if b'\x00' in decrypted[:20]:
            score += 1
            patterns.append('null-term')
        
        if score > 0 or len(patterns) > 0:
            results.append({
                'key_name': key_name,
                'key_hex': hexlify(key[:16]).decode(),
                'score': score,
                'patterns': patterns,
                'decrypted': decrypted
            })
    
    results.sort(key=lambda x: x['score'], reverse=True)
    return results

def main():
    pcap_files = [
        "PCAPdroid_30_Jan_18_26_35.pcap",
        "PCAPdroid_30_Jan_18_19_57.pcap",
        "complete_capture.pcap",
        "robot_app_connected_191557.pcap",
        "android_robot_traffic_20260122_192919.pcap",
        "all_traffic_test.pcap"
    ]
    
    print("="*80)
    print("FINDING AND DECRYPTING 0x42/0x43 PACKETS")
    print("="*80)
    
    keys = derive_all_keys()
    print(f"\nDerived {len(keys)} encryption keys from STUN username: {STUN_USERNAME}\n")
    
    total_042 = 0
    total_043 = 0
    
    for pcap_file in pcap_files:
        if not Path(pcap_file).exists():
            continue
        
        print(f"\n{'='*80}")
        print(f"PCAP: {pcap_file}")
        print(f"{'='*80}")
        
        packets_042, packets_043 = find_042_043_packets(pcap_file)
        total_042 += len(packets_042)
        total_043 += len(packets_043)
        
        print(f"Found: {len(packets_042)} packets with 0x42 (DELETE)")
        print(f"Found: {len(packets_043)} packets with 0x43 (RENAME)")
        
        # Process 0x42 packets
        if len(packets_042) > 0:
            print(f"\n{'─'*80}")
            print("0x42 (DELETE) PACKETS")
            print(f"{'─'*80}")
            
            for i, pkt in enumerate(packets_042, 1):
                print(f"\n[Packet #{pkt['packet_num']}] Port {pkt['src_port']} → {pkt['dst_port']}, {pkt['length']} bytes")
                print(f"Raw (first 48 bytes): {hexlify(pkt['payload'][:48]).decode()}")
                
                # Try all decryptions
                results = test_all_decryptions(pkt['payload'], keys)
                
                if len(results) > 0:
                    print(f"\n🔍 Top decryption candidates:")
                    for j, r in enumerate(results[:3], 1):
                        print(f"\n  #{j}. Key: {r['key_name']} (score={r['score']})")
                        print(f"     Patterns: {', '.join(r['patterns'])}")
                        
                        # Show decrypted bytes
                        preview = r['decrypted'][:64]
                        try:
                            text = preview.decode('utf-8', errors='replace')
                            print(f"     Text: {repr(text)}")
                        except:
                            print(f"     Hex:  {hexlify(preview).decode()}")
                else:
                    print("  ❌ No patterns found with any key")
        
        # Process 0x43 packets
        if len(packets_043) > 0:
            print(f"\n{'─'*80}")
            print("0x43 (RENAME) PACKETS")
            print(f"{'─'*80}")
            
            for i, pkt in enumerate(packets_043, 1):
                print(f"\n[Packet #{pkt['packet_num']}] Port {pkt['src_port']} → {pkt['dst_port']}, {pkt['length']} bytes")
                print(f"Raw (first 48 bytes): {hexlify(pkt['payload'][:48]).decode()}")
                
                results = test_all_decryptions(pkt['payload'], keys)
                
                if len(results) > 0:
                    print(f"\n🔍 Top decryption candidates:")
                    for j, r in enumerate(results[:3], 1):
                        print(f"\n  #{j}. Key: {r['key_name']} (score={r['score']})")
                        print(f"     Patterns: {', '.join(r['patterns'])}")
                        
                        preview = r['decrypted'][:64]
                        try:
                            text = preview.decode('utf-8', errors='replace')
                            print(f"     Text: {repr(text)}")
                        except:
                            print(f"     Hex:  {hexlify(preview).decode()}")
                else:
                    print("  ❌ No patterns found with any key")
    
    print(f"\n{'='*80}")
    print(f"TOTAL: {total_042} × 0x42 (DELETE), {total_043} × 0x43 (RENAME)")
    print(f"{'='*80}")

if __name__ == "__main__":
    main()
