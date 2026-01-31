#!/usr/bin/env python3
"""
Extract 0x42/0x43 commands from raw PCAP offsets and decrypt with STUN keys.
Based on documented offsets from PCAP_0x42_0x43_VERIFIED.md
"""

import hashlib
import hmac
from binascii import hexlify, unhexlify

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
    """XOR decryption with repeating key"""
    if len(key) == 0:
        return data
    result = bytearray()
    for i, byte in enumerate(data):
        result.append(byte ^ key[i % len(key)])
    return bytes(result)

def find_plaintext_patterns(data):
    """Check for plaintext indicators"""
    patterns = []
    score = 0
    
    # Check for printable ASCII
    printable_count = sum(1 for b in data if 32 <= b <= 126)
    if printable_count > len(data) * 0.6:
        score += 10
        patterns.append(f'ascii={printable_count}/{len(data)}')
    
    # Check for keywords (case-insensitive)
    keywords = [b'test', b'walk', b'arm', b'name', b'action', b'delete', b'rename', b'move', b'hand']
    for kw in keywords:
        if kw in data.lower():
            score += 20
            patterns.append(f'"{kw.decode()}"')
    
    # Check for null-terminated strings
    if b'\x00' in data[:30]:
        idx = data.index(b'\x00')
        if idx > 2:
            score += 5
            patterns.append(f'null@{idx}')
    
    # Check for JSON markers
    json_markers = {b'{': 'json_start', b'}': 'json_end', b'"': 'quote', b':': 'colon'}
    json_found = [name for marker, name in json_markers.items() if marker in data]
    if len(json_found) >= 3:
        score += 15
        patterns.append('json_struct')
    
    return score, patterns

def extract_and_decrypt(pcap_path, offset, cmd_id, length=100):
    """Extract data at offset and try all decryption keys"""
    with open(pcap_path, 'rb') as f:
        f.seek(offset)
        raw_data = f.read(length)
    
    print(f"\n{'='*80}")
    print(f"OFFSET: 0x{offset:x} | COMMAND: 0x{cmd_id:02x} | LENGTH: {length} bytes")
    print(f"{'='*80}")
    print(f"Raw hex: {hexlify(raw_data).decode()}")
    print()
    
    # Find command ID in data
    if cmd_id in raw_data:
        cmd_index = raw_data.index(cmd_id)
        print(f"✅ Command ID 0x{cmd_id:02x} found at index {cmd_index}")
        print(f"Context: {hexlify(raw_data[max(0,cmd_index-5):cmd_index+15]).decode()}")
        
        # Extract payload after command ID (skip command byte itself)
        encrypted_payload = raw_data[cmd_index+1:]
        print(f"\n📦 Encrypted payload ({len(encrypted_payload)} bytes):")
        print(f"   {hexlify(encrypted_payload[:64]).decode()}...")
    else:
        print(f"⚠️  Command ID 0x{cmd_id:02x} NOT found in raw data")
        encrypted_payload = raw_data
    
    # Test all STUN keys
    keys = derive_all_keys()
    results = []
    
    print(f"\n{'─'*80}")
    print("DECRYPTION ATTEMPTS")
    print(f"{'─'*80}")
    
    for key_name, key in keys.items():
        decrypted = xor_decrypt(encrypted_payload, key)
        score, patterns = find_plaintext_patterns(decrypted)
        
        if score > 0:
            results.append({
                'key_name': key_name,
                'key_hex': hexlify(key[:16]).decode(),
                'score': score,
                'patterns': patterns,
                'decrypted': decrypted
            })
    
    # Sort by score
    results.sort(key=lambda x: x['score'], reverse=True)
    
    if len(results) == 0:
        print("❌ No plaintext patterns found with any STUN key")
        return None
    
    print(f"✅ Found {len(results)} potential decryptions:\n")
    
    for i, r in enumerate(results[:5], 1):  # Top 5
        print(f"#{i}. Key: {r['key_name']} (score={r['score']})")
        print(f"   Patterns: {', '.join(r['patterns'])}")
        
        # Try to show as text
        preview = r['decrypted'][:80]
        try:
            text = preview.decode('utf-8', errors='replace')
            # Replace non-printable
            clean_text = ''.join(c if 32 <= ord(c) <= 126 else f'\\x{ord(c):02x}' for c in text)
            print(f"   Text: {clean_text}")
        except:
            print(f"   Hex:  {hexlify(preview).decode()}")
        print()
    
    return results[0] if results else None

def main():
    pcap_file = "PCAPdroid_30_Jan_18_26_35.pcap"
    
    print("="*80)
    print("DECRYPT 0x42/0x43 FROM RAW PCAP OFFSETS")
    print("="*80)
    print(f"PCAP: {pcap_file}")
    print(f"STUN Username: {STUN_USERNAME}")
    print(f"Testing 8 STUN-derived encryption keys")
    print("="*80)
    
    # Known offsets from PCAP_0x42_0x43_VERIFIED.md
    test_cases = [
        {'offset': 0x48a96, 'cmd_id': 0x42, 'name': 'DELETE #1'},
        {'offset': 0x445b2, 'cmd_id': 0x43, 'name': 'RENAME #1'},
        # Try a few more from the claimed 96+103 packets
        {'offset': 0x48a96 + 100, 'cmd_id': 0x42, 'name': 'DELETE #2'},
        {'offset': 0x445b2 + 100, 'cmd_id': 0x43, 'name': 'RENAME #2'},
    ]
    
    best_decryptions = []
    
    for tc in test_cases:
        print(f"\n\n{'█'*80}")
        print(f"TEST CASE: {tc['name']}")
        print(f"{'█'*80}")
        
        result = extract_and_decrypt(pcap_file, tc['offset'], tc['cmd_id'], length=120)
        if result:
            best_decryptions.append({'test': tc['name'], 'result': result})
    
    # Summary
    print(f"\n\n{'='*80}")
    print("FINAL SUMMARY")
    print(f"{'='*80}")
    
    if len(best_decryptions) == 0:
        print("❌ No successful decryptions found")
        print("\nPossible reasons:")
        print("  • Encryption key is session-specific (not derived from STUN)")
        print("  • Encryption uses robot serial number or MAC address")
        print("  • Custom encryption algorithm (not simple XOR)")
        print("  • Key is exchanged during WebRTC handshake")
    else:
        print(f"✅ Found {len(best_decryptions)} potential decryptions:\n")
        for i, bd in enumerate(best_decryptions, 1):
            r = bd['result']
            print(f"{i}. {bd['test']}: {r['key_name']} (score={r['score']})")
            print(f"   Patterns: {', '.join(r['patterns'])}")
        
        print(f"\n{'─'*80}")
        print("RECOMMENDATION:")
        if best_decryptions[0]['result']['score'] >= 20:
            print("✅ High confidence - plaintext keywords found!")
            print(f"   Use key: {best_decryptions[0]['result']['key_name']}")
        else:
            print("⚠️  Low confidence - more analysis needed")
    
    print("="*80)

if __name__ == "__main__":
    main()
