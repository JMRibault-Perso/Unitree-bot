#!/usr/bin/env python3
"""
Systematically decrypt teaching protocol payloads with STUN-derived keys.
Focus on port 57006 (teaching protocol) to find plaintext.
"""

import struct
import hashlib
import hmac
from pathlib import Path
from binascii import hexlify, unhexlify
from Crypto.Cipher import AES

# STUN credentials from port 51639 analysis
STUN_USERNAME = "n7Px:iq2R"
STUN_USERNAME_HEX = "6e3750783a69713252"

# 8 derived keys from STUN analysis
def derive_all_keys():
    """Generate all 8 STUN-derived keys"""
    keys = {}
    
    # Key 1: Direct ASCII bytes
    keys['ascii'] = STUN_USERNAME.encode('ascii')
    
    # Key 2: HMAC-SHA1 of username (no password)
    keys['hmac_sha1_nopass'] = hmac.new(b'', STUN_USERNAME.encode(), hashlib.sha1).digest()
    
    # Key 3: HMAC-SHA1 with username as key
    keys['hmac_sha1_self'] = hmac.new(STUN_USERNAME.encode(), STUN_USERNAME.encode(), hashlib.sha1).digest()
    
    # Key 4: HMAC-SHA1 with "unitree" as password
    keys['hmac_sha1_unitree'] = hmac.new(b'unitree', STUN_USERNAME.encode(), hashlib.sha1).digest()
    
    # Key 5: HMAC-SHA1 with reversed username
    reversed_user = STUN_USERNAME[::-1]
    keys['hmac_sha1_reversed'] = hmac.new(reversed_user.encode(), STUN_USERNAME.encode(), hashlib.sha1).digest()
    
    # Key 6: SHA1 hash
    keys['sha1'] = hashlib.sha1(STUN_USERNAME.encode()).digest()
    
    # Key 7: SHA256 hash (first 16 bytes for AES-128)
    keys['sha256'] = hashlib.sha256(STUN_USERNAME.encode()).digest()[:16]
    
    # Key 8: MD5 hash
    keys['md5'] = hashlib.md5(STUN_USERNAME.encode()).digest()
    
    return keys

def xor_decrypt(data, key):
    """XOR decryption with repeating key"""
    if len(key) == 0:
        return data
    result = bytearray()
    for i, byte in enumerate(data):
        result.append(byte ^ key[i % len(key)])
    return bytes(result)

def aes_decrypt(data, key):
    """Try AES-ECB decryption (no IV)"""
    try:
        # Pad key to 16 bytes if needed
        if len(key) < 16:
            key = key + b'\x00' * (16 - len(key))
        elif len(key) > 16:
            key = key[:16]
        
        cipher = AES.new(key, AES.MODE_ECB)
        
        # Pad data to 16-byte blocks
        pad_len = 16 - (len(data) % 16)
        if pad_len != 16:
            data = data + b'\x00' * pad_len
        
        return cipher.decrypt(data)
    except Exception as e:
        return None

def is_printable_ascii(data, min_ratio=0.7):
    """Check if data contains mostly printable ASCII"""
    if len(data) == 0:
        return False
    
    printable_count = sum(1 for b in data if 32 <= b <= 126 or b in (9, 10, 13))
    ratio = printable_count / len(data)
    return ratio >= min_ratio

def contains_keywords(data):
    """Check if decrypted data contains expected keywords"""
    keywords = [
        b'test', b'walk', b'arm', b'hand', b'move',
        b'action', b'name', b'old', b'new',
        b'delete', b'rename', b'execute',
        b'api_id', b'parameter', b'data',
        b'{', b'}', b'":', b'","'  # JSON markers
    ]
    data_lower = data.lower()
    matches = [kw for kw in keywords if kw in data_lower]
    return matches

def parse_pcap_teaching_protocol(pcap_path):
    """Extract teaching protocol payloads from port 57006"""
    teaching_payloads = []
    
    with open(pcap_path, 'rb') as f:
        # Skip PCAP global header (24 bytes)
        f.read(24)
        
        packet_num = 0
        while True:
            # Read packet header (16 bytes)
            pkt_header = f.read(16)
            if len(pkt_header) < 16:
                break
            
            ts_sec, ts_usec, incl_len, orig_len = struct.unpack('<IIII', pkt_header)
            packet_data = f.read(incl_len)
            packet_num += 1
            
            if len(packet_data) < 42:  # Min: Ethernet(14) + IP(20) + UDP(8)
                continue
            
            try:
                # Parse Ethernet header
                eth_type = struct.unpack('>H', packet_data[12:14])[0]
                if eth_type != 0x0800:  # Not IPv4
                    continue
                
                ip_start = 14
                ip_header = packet_data[ip_start:ip_start+20]
                
                # Check if UDP
                protocol = ip_header[9]
                if protocol != 17:  # Not UDP
                    continue
                
                # Get IP header length
                ip_version_ihl = ip_header[0]
                ip_header_len = (ip_version_ihl & 0x0F) * 4
                
                # Parse UDP header
                udp_start = ip_start + ip_header_len
                if udp_start + 8 > len(packet_data):
                    continue
                
                udp_header = packet_data[udp_start:udp_start+8]
                src_port, dst_port, udp_len, udp_checksum = struct.unpack('>HHHH', udp_header)
                
                # Filter for port 57006 (teaching protocol)
                if src_port == 57006 or dst_port == 57006:
                    payload_start = udp_start + 8
                    payload = packet_data[payload_start:]
                    
                    if len(payload) > 0:
                        # Get command ID (first byte)
                        cmd_id = payload[0] if len(payload) > 0 else 0
                        
                        teaching_payloads.append({
                            'packet_num': packet_num,
                            'src_port': src_port,
                            'dst_port': dst_port,
                            'cmd_id': cmd_id,
                            'length': len(payload),
                            'payload': payload
                        })
            
            except Exception as e:
                continue
    
    return teaching_payloads

def test_decryption_on_payload(payload_data, keys):
    """Test all decryption methods on a single payload"""
    results = []
    
    for key_name, key in keys.items():
        # Method 1: XOR decryption
        xor_result = xor_decrypt(payload_data, key)
        if is_printable_ascii(xor_result, min_ratio=0.5):
            keywords = contains_keywords(xor_result)
            results.append({
                'method': f'XOR ({key_name})',
                'key': hexlify(key[:16]).decode(),
                'decrypted': xor_result[:100],  # First 100 bytes
                'printable': True,
                'keywords': keywords,
                'score': len(keywords)
            })
        
        # Method 2: AES-ECB decryption
        aes_result = aes_decrypt(payload_data, key)
        if aes_result and is_printable_ascii(aes_result, min_ratio=0.5):
            keywords = contains_keywords(aes_result)
            results.append({
                'method': f'AES-ECB ({key_name})',
                'key': hexlify(key[:16]).decode(),
                'decrypted': aes_result[:100],
                'printable': True,
                'keywords': keywords,
                'score': len(keywords)
            })
    
    # Sort by score (number of keywords found)
    results.sort(key=lambda x: x['score'], reverse=True)
    return results

def main():
    pcap_files = [
        "PCAPdroid_30_Jan_18_26_35.pcap",
        "PCAPdroid_30_Jan_18_19_57.pcap"
    ]
    
    print("="*70)
    print("TEACHING PROTOCOL DECRYPTION TEST")
    print("="*70)
    print(f"STUN Username: {STUN_USERNAME}")
    print(f"Target Port: 57006 (teaching protocol)")
    print()
    
    # Derive all keys
    keys = derive_all_keys()
    print("Derived Encryption Keys:")
    for i, (name, key) in enumerate(keys.items(), 1):
        print(f"  {i}. {name:20s} = {hexlify(key[:16]).decode()}")
    print()
    
    # Process each PCAP
    for pcap_file in pcap_files:
        if not Path(pcap_file).exists():
            print(f"⚠️  {pcap_file} not found, skipping...")
            continue
        
        print(f"\n{'='*70}")
        print(f"PCAP: {pcap_file}")
        print(f"{'='*70}")
        
        payloads = parse_pcap_teaching_protocol(pcap_file)
        print(f"Found {len(payloads)} teaching protocol packets on port 57006")
        
        if len(payloads) == 0:
            print("❌ No teaching protocol packets found")
            continue
        
        # Group by command ID
        cmd_groups = {}
        for p in payloads:
            cmd_id = p['cmd_id']
            if cmd_id not in cmd_groups:
                cmd_groups[cmd_id] = []
            cmd_groups[cmd_id].append(p)
        
        print(f"\nCommand ID distribution:")
        for cmd_id in sorted(cmd_groups.keys()):
            count = len(cmd_groups[cmd_id])
            print(f"  0x{cmd_id:02x}: {count} packets")
        
        # Test decryption on first packet of each command type
        print(f"\n{'─'*70}")
        print("DECRYPTION ATTEMPTS")
        print(f"{'─'*70}")
        
        for cmd_id in sorted(cmd_groups.keys()):
            packets = cmd_groups[cmd_id]
            first_packet = packets[0]
            
            print(f"\n▶ Command 0x{cmd_id:02x} (packet #{first_packet['packet_num']}, {first_packet['length']} bytes)")
            print(f"  Raw payload (first 32 bytes): {hexlify(first_packet['payload'][:32]).decode()}")
            
            # Test all decryption methods
            results = test_decryption_on_payload(first_packet['payload'], keys)
            
            if len(results) == 0:
                print("  ❌ No printable results with any key")
            else:
                print(f"  ✅ Found {len(results)} potential decryptions:")
                for i, r in enumerate(results[:3], 1):  # Show top 3
                    print(f"\n  #{i}. {r['method']}")
                    print(f"     Key: {r['key']}")
                    print(f"     Keywords: {[k.decode() for k in r['keywords']]}")
                    
                    # Try to display as string
                    try:
                        text = r['decrypted'].decode('utf-8', errors='replace')
                        # Show first 80 chars
                        preview = text[:80].replace('\n', '\\n').replace('\r', '\\r')
                        print(f"     Preview: {preview}")
                    except:
                        print(f"     Hex: {hexlify(r['decrypted'][:32]).decode()}")
        
        print(f"\n{'─'*70}")
    
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    print("If no plaintext found, encryption may use:")
    print("  • Session-specific key (changes per connection)")
    print("  • Robot-specific key (hardware serial number)")
    print("  • Compound key (STUN + robot MAC + timestamp)")
    print("  • Custom encryption (not standard AES/XOR)")
    print("="*70)

if __name__ == "__main__":
    main()
