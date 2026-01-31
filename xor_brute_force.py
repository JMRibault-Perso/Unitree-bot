#!/usr/bin/env python3
"""
XOR Brute Force Decryption for G1 PCAP
Try all 256 single-byte XOR keys on 0x43 (rename) packets
"""

import struct
import sys
from collections import Counter
from pathlib import Path

def calculate_entropy(data):
    """Calculate Shannon entropy of data (0.0-8.0)"""
    if not data:
        return 0.0
    counts = Counter(data)
    import math
    entropy = 0
    for count in counts.values():
        p = count / len(data)
        if p > 0:
            entropy -= p * math.log2(p)
    return entropy

def is_probably_plaintext(data):
    """Check if data looks like plaintext (mostly ASCII/printable)"""
    printable = sum(1 for b in data if (32 <= b < 127) or b in [0, 9, 10, 13])
    ratio = printable / len(data) if data else 0
    return ratio > 0.6

def try_single_byte_xor(data, key_byte):
    """Decrypt data with single-byte XOR key"""
    return bytes(b ^ key_byte for b in data)

def try_repeating_key_xor(data, key_bytes):
    """Decrypt data with repeating multi-byte XOR key"""
    decrypted = bytearray()
    for i, byte in enumerate(data):
        decrypted.append(byte ^ key_bytes[i % len(key_bytes)])
    return bytes(decrypted)

def extract_rename_packets(pcap_file):
    """Extract all 0x43 (rename) packet payloads from PCAP"""
    packets = []
    
    with open(pcap_file, 'rb') as f:
        data = f.read()
    
    pos = 0
    count = 0
    while pos < len(data) - 14:
        # Look for command header
        if data[pos:pos+2] == b'\x17\xfe':
            if pos + 13 < len(data) and data[pos + 13] == 0x43:  # 0x43 = rename
                # Extract payload (variable length)
                if pos + 9 < len(data):
                    payload_len = struct.unpack('<H', data[pos + 7:pos + 9])[0]
                    if pos + 9 + payload_len <= len(data):
                        payload = data[pos + 9:pos + 9 + payload_len]
                        packets.append({
                            'offset': pos,
                            'payload': payload,
                            'old_name_bytes': payload[0:32],
                            'new_name_bytes': payload[32:64] if len(payload) > 32 else b'',
                        })
                        count += 1
        pos += 1
    
    print(f"Found {count} x 0x43 (rename) packets")
    return packets

def brute_force_single_byte(packets):
    """Try all 256 single-byte XOR keys"""
    print("\n" + "="*70)
    print("SINGLE-BYTE XOR BRUTE FORCE")
    print("="*70)
    
    results = {}
    
    for key_byte in range(256):
        valid_count = 0
        
        for pkt in packets:
            old_decrypted = try_single_byte_xor(pkt['old_name_bytes'], key_byte)
            new_decrypted = try_single_byte_xor(pkt['new_name_bytes'], key_byte)
            
            # Check if both fields look like text
            if is_probably_plaintext(old_decrypted) and is_probably_plaintext(new_decrypted):
                valid_count += 1
        
        if valid_count > 0:
            results[key_byte] = valid_count
            if valid_count > 50:  # More than half
                print(f"✓ Key 0x{key_byte:02X}: {valid_count}/{len(packets)} packets look like plaintext")
    
    return results

def brute_force_repeating_keys(packets):
    """Try common repeating multi-byte keys"""
    print("\n" + "="*70)
    print("REPEATING MULTI-BYTE XOR KEYS")
    print("="*70)
    
    # Common key patterns
    test_keys = [
        b'\x12\x34\x56\x78',
        b'\xAA\xBB\xCC\xDD',
        b'\xFF\xFF\xFF\xFF',
        b'\x00\xFF\x00\xFF',
        b'\xDE\xAD\xBE\xEF',
        bytes([i]) * 32 for i in range(256)  # All repeating bytes
    ]
    
    # Also try from known strings
    for known_str in ['test', 'demo', 'action', 'teach']:
        test_keys.append(known_str.encode() + b'\x00' * 28)
    
    results = {}
    
    for key in test_keys:
        valid_count = 0
        
        for pkt in packets:
            old_decrypted = try_repeating_key_xor(pkt['old_name_bytes'], key)
            new_decrypted = try_repeating_key_xor(pkt['new_name_bytes'], key)
            
            if is_probably_plaintext(old_decrypted) and is_probably_plaintext(new_decrypted):
                valid_count += 1
        
        if valid_count > len(packets) * 0.5:  # More than half match
            results[key.hex()[:16]] = valid_count
            print(f"✓ Key {key.hex()[:16]}...: {valid_count}/{len(packets)} packets look like plaintext")
    
    return results

def try_known_plaintext(packets, known_string):
    """Use known plaintext to find XOR key"""
    print(f"\n" + "="*70)
    print(f"KNOWN PLAINTEXT ATTACK (looking for: '{known_string}')")
    print("="*70)
    
    known_bytes = known_string.encode().ljust(32, b'\x00')
    
    for pkt_idx, pkt in enumerate(packets):
        old_name_enc = pkt['old_name_bytes']
        
        # Try to derive key assuming this is the old_name
        derived_key = bytes(a ^ b for a, b in zip(old_name_enc, known_bytes))
        
        # Check if derived key is reasonable (mostly printable byte values)
        if sum(1 for b in derived_key if 32 <= b < 127 or b == 0) >= 8:
            # Test key on all packets
            valid_count = 0
            for test_pkt in packets:
                old_decrypted = try_repeating_key_xor(test_pkt['old_name_bytes'], derived_key)
                new_decrypted = try_repeating_key_xor(test_pkt['new_name_bytes'], derived_key)
                
                if is_probably_plaintext(old_decrypted) and is_probably_plaintext(new_decrypted):
                    valid_count += 1
            
            if valid_count > len(packets) * 0.5:
                print(f"✓ Found likely key from packet {pkt_idx}: {derived_key.hex()[:16]}...")
                return derived_key
    
    print("✗ Known plaintext attack unsuccessful")
    return None

def show_samples(packets, key_byte=None, key_bytes=None):
    """Display sample decryptions"""
    print("\n" + "="*70)
    print("SAMPLE DECRYPTIONS")
    print("="*70)
    
    if key_byte is not None:
        print(f"\nUsing single-byte key: 0x{key_byte:02X}")
        for i, pkt in enumerate(packets[:5]):
            old_dec = try_single_byte_xor(pkt['old_name_bytes'], key_byte)
            new_dec = try_single_byte_xor(pkt['new_name_bytes'], key_byte)
            
            old_str = old_dec.rstrip(b'\x00').decode('utf-8', errors='replace')
            new_str = new_dec.rstrip(b'\x00').decode('utf-8', errors='replace')
            
            print(f"\n  [{i}] '{old_str}' → '{new_str}'")
    
    elif key_bytes is not None:
        print(f"\nUsing multi-byte key: {key_bytes.hex()[:16]}...")
        for i, pkt in enumerate(packets[:5]):
            old_dec = try_repeating_key_xor(pkt['old_name_bytes'], key_bytes)
            new_dec = try_repeating_key_xor(pkt['new_name_bytes'], key_bytes)
            
            old_str = old_dec.rstrip(b'\x00').decode('utf-8', errors='replace')
            new_str = new_dec.rstrip(b'\x00').decode('utf-8', errors='replace')
            
            print(f"\n  [{i}] '{old_str}' → '{new_str}'")

def main():
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <pcap_file> [known_plaintext]")
        print(f"Example: {sys.argv[0]} PCAPdroid_30_Jan_18_26_35.pcap test")
        sys.exit(1)
    
    pcap_file = Path(sys.argv[1])
    if not pcap_file.exists():
        print(f"✗ File not found: {pcap_file}")
        sys.exit(1)
    
    print(f"Reading PCAP: {pcap_file}")
    packets = extract_rename_packets(pcap_file)
    
    if not packets:
        print("✗ No 0x43 packets found!")
        sys.exit(1)
    
    # Try methods in order
    print("\n" + "="*70)
    print("DECRYPTION ANALYSIS")
    print("="*70)
    
    # Method 1: Single-byte XOR
    single_byte_results = brute_force_single_byte(packets)
    
    if single_byte_results and max(single_byte_results.values()) > len(packets) * 0.7:
        best_key = max(single_byte_results, key=single_byte_results.get)
        print(f"\n✅ BEST SINGLE-BYTE KEY FOUND: 0x{best_key:02X}")
        show_samples(packets, key_byte=best_key)
        return
    
    # Method 2: Known plaintext (if provided)
    if len(sys.argv) > 2:
        known_str = sys.argv[2]
        derived_key = try_known_plaintext(packets, known_str)
        
        if derived_key:
            print(f"\n✅ DERIVED KEY FROM KNOWN PLAINTEXT")
            show_samples(packets, key_bytes=derived_key)
            return
    
    # Method 3: Multi-byte patterns
    multi_byte_results = brute_force_repeating_keys(packets)
    
    if not single_byte_results and not multi_byte_results:
        print("\n✗ No successful decryption found")
        print("✓ Try again with known plaintext: python xor_brute_force.py file.pcap 'action_name'")
    else:
        print("\n✓ Check samples above - if they look like action names, decryption succeeded!")

if __name__ == '__main__':
    main()
