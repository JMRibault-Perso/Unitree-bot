#!/usr/bin/env python3
"""
Known Plaintext Attack - Find XOR key using 'test' rename action
Assumes user renamed something to 'test' (which we saw in PCAP)
"""

import struct
from pathlib import Path
import sys

def extract_rename_packets(pcap_file):
    """Extract all 0x43 packets"""
    packets = []
    
    with open(pcap_file, 'rb') as f:
        data = f.read()
    
    pos = 0
    while pos < len(data) - 14:
        if data[pos:pos+2] == b'\x17\xfe':
            if pos + 13 < len(data) and data[pos + 13] == 0x43:
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
        pos += 1
    
    return packets

def find_key_from_new_name(packets, known_new_name):
    """
    If we know the new_name field contains 'test', find the XOR key
    The new_name is at bytes [32:64] of the payload
    """
    print(f"\n{'='*70}")
    print(f"SEARCHING FOR PACKETS WHERE new_name CONTAINS '{known_new_name}'")
    print(f"{'='*70}")
    
    # Pad known string to 32 bytes
    known_bytes = known_new_name.encode().ljust(32, b'\x00')
    
    found_keys = []
    
    for pkt_idx, pkt in enumerate(packets):
        new_name_enc = pkt['new_name_bytes']
        
        # Try to derive key: encrypted ^ known_plaintext = key
        derived_key = bytes(a ^ b for a, b in zip(new_name_enc, known_bytes))
        
        # Check if the old_name field also decrypts to something readable
        old_name_enc = pkt['old_name_bytes']
        old_name_dec = bytes(a ^ b for a, b in zip(old_name_enc, derived_key))
        
        # Count printable characters
        printable = sum(1 for b in old_name_dec if (32 <= b < 127) or b == 0)
        ratio = printable / 32
        
        if ratio > 0.6:  # At least 60% printable
            old_str = old_name_dec.rstrip(b'\x00').decode('utf-8', errors='replace')
            new_str = known_new_name
            
            print(f"\n✓ Packet {pkt_idx} - Possible key found!")
            print(f"  Key: {derived_key.hex()}")
            print(f"  Old name: '{old_str}'")
            print(f"  New name: '{new_str}'")
            print(f"  Confidence: {ratio*100:.0f}%")
            
            found_keys.append(derived_key)
    
    if found_keys:
        # Verify key works across multiple packets
        best_key = found_keys[0]  # Use first found key
        
        print(f"\n{'='*70}")
        print(f"VERIFYING KEY: {best_key.hex()}")
        print(f"{'='*70}")
        
        valid_count = 0
        for pkt in packets:
            old_dec = bytes(a ^ b for a, b in zip(pkt['old_name_bytes'], best_key))
            new_dec = bytes(a ^ b for a, b in zip(pkt['new_name_bytes'], best_key))
            
            old_print = sum(1 for b in old_dec if (32 <= b < 127) or b == 0)
            new_print = sum(1 for b in new_dec if (32 <= b < 127) or b == 0)
            
            if old_print >= 16 and new_print >= 16:  # At least 50% each
                valid_count += 1
        
        print(f"✓ Key validates on {valid_count}/{len(packets)} packets")
        
        if valid_count > len(packets) * 0.5:
            print(f"\n✅ KEY SUCCESSFULLY FOUND AND VALIDATED!")
            return best_key
    
    return None

def decrypt_all_with_key(packets, key):
    """Decrypt all rename operations with the found key"""
    print(f"\n{'='*70}")
    print(f"DECRYPTING ALL RENAME OPERATIONS WITH KEY: {key.hex()}")
    print(f"{'='*70}")
    
    renames = []
    for pkt_idx, pkt in enumerate(packets):
        old_dec = bytes(a ^ b for a, b in zip(pkt['old_name_bytes'], key))
        new_dec = bytes(a ^ b for a, b in zip(pkt['new_name_bytes'], key))
        
        old_str = old_dec.rstrip(b'\x00').decode('utf-8', errors='replace')
        new_str = new_dec.rstrip(b'\x00').decode('utf-8', errors='replace')
        
        # Skip completely empty entries
        if old_str.strip() or new_str.strip():
            renames.append({
                'index': pkt_idx,
                'old': old_str,
                'new': new_str,
                'hex_old': old_dec.hex(),
                'hex_new': new_dec.hex(),
            })
    
    # Sort by new name for easier reading
    renames.sort(key=lambda x: x['new'])
    
    print(f"\nFound {len(renames)} non-empty rename operations:\n")
    for r in renames:
        # Highlight the 'test' rename
        if 'test' in r['new'].lower():
            print(f"  ✓ [{r['index']}] '{r['old']}' → '{r['new']}'  ← TARGET RENAME!")
        else:
            print(f"  [{r['index']}] '{r['old']}' → '{r['new']}'")
    
    return renames

def main():
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <pcap_file> [known_name_substring]")
        print(f"Example: {sys.argv[0]} PCAPdroid_30_Jan_18_26_35.pcap test")
        print(f"\nSearches for packets where the new_name contains the known substring,")
        print(f"derives the XOR key, and decrypts all rename operations.")
        sys.exit(1)
    
    pcap_file = Path(sys.argv[1])
    known_name = sys.argv[2] if len(sys.argv) > 2 else "test"
    
    if not pcap_file.exists():
        print(f"✗ File not found: {pcap_file}")
        sys.exit(1)
    
    print(f"Reading PCAP: {pcap_file}")
    packets = extract_rename_packets(pcap_file)
    print(f"Found {len(packets)} x 0x43 (rename) packets")
    
    if not packets:
        print("✗ No 0x43 packets found!")
        sys.exit(1)
    
    # Find key using known plaintext
    key = find_key_from_new_name(packets, known_name)
    
    if key:
        # Decrypt all operations
        renames = decrypt_all_with_key(packets, key)
        
        # Save to file
        output_file = pcap_file.parent / "decrypted_renames.txt"
        with open(output_file, 'w') as f:
            f.write(f"XOR Key: {key.hex()}\n")
            f.write(f"Decrypted Rename Operations:\n\n")
            for r in renames:
                f.write(f"[{r['index']}] '{r['old']}' → '{r['new']}'\\n")
        
        print(f"\n✓ Results saved to: {output_file}")
    else:
        print(f"\n✗ Could not find key from '{known_name}' substring")
        print(f"Suggestions:")
        print(f"  1. Try different substring: python {sys.argv[0]} {pcap_file} demo")
        print(f"  2. Try XOR brute force: python xor_brute_force.py {pcap_file}")
        print(f"  3. Capture new PCAP with known input for guaranteed success")

if __name__ == '__main__':
    main()
