#!/usr/bin/env python3
"""
Analyze PCAPdroid_30_Jan_22_57_36.pcap for rename to "AAAAAAAAAA"
Known plaintext attack to find encryption key
"""

import struct
from binascii import hexlify, unhexlify

def parse_pcap_for_rename(pcap_path):
    """Find 0x43 (rename) commands with known plaintext"""
    rename_packets = []
    
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
            
            if len(packet_data) < 60:
                continue
            
            # Search for 0x43 command ID in packet
            for i in range(len(packet_data) - 1):
                if packet_data[i] == 0x43:
                    # Found potential rename command
                    # Check if it's part of teaching protocol header
                    if i >= 13 and packet_data[i-13:i-10] == b'\x17\xfe\xfd':
                        # This is a teaching protocol packet!
                        context_start = max(0, i - 20)
                        context_end = min(len(packet_data), i + 150)
                        
                        rename_packets.append({
                            'packet_num': packet_num,
                            'offset_in_packet': i,
                            'header': packet_data[i-13:i],
                            'command_id': 0x43,
                            'payload': packet_data[i+1:i+120],
                            'full_context': packet_data[context_start:context_end],
                            'timestamp': f"{ts_sec}.{ts_usec:06d}"
                        })
                        break
    
    return rename_packets

def known_plaintext_attack(encrypted_payload, known_plaintext="AAAAAAAAAA"):
    """
    Use known plaintext to find XOR key
    
    Args:
        encrypted_payload: The encrypted bytes
        known_plaintext: The expected plaintext string
    
    Returns:
        Possible XOR key(s)
    """
    known_bytes = known_plaintext.encode('utf-8')
    
    print(f"\n🔍 Known Plaintext Attack")
    print(f"   Target string: '{known_plaintext}'")
    print(f"   Expected bytes: {hexlify(known_bytes).decode()}")
    print(f"   Length: {len(known_bytes)} bytes")
    
    # Search for XOR key at different offsets
    results = []
    
    for offset in range(min(len(encrypted_payload) - len(known_bytes), 100)):
        encrypted_segment = encrypted_payload[offset:offset+len(known_bytes)]
        
        # XOR to get potential key
        potential_key = bytes([e ^ k for e, k in zip(encrypted_segment, known_bytes)])
        
        # Test if key is repeating pattern
        key_hex = hexlify(potential_key).decode()
        
        # Check for patterns (repeating bytes, printable ASCII, etc.)
        unique_bytes = len(set(potential_key))
        printable_count = sum(1 for b in potential_key if 32 <= b <= 126)
        
        score = 0
        patterns = []
        
        # High score for mostly printable ASCII (likely a password/key)
        if printable_count > len(known_bytes) * 0.7:
            score += 50
            patterns.append('printable_key')
        
        # High score for repeating pattern (XOR key often repeats)
        if unique_bytes < len(known_bytes) / 2:
            score += 30
            patterns.append('repeating')
        
        # Check if it's the STUN username
        if b'n7Px' in potential_key or b'iq2R' in potential_key:
            score += 100
            patterns.append('STUN_username')
        
        if score > 0 or offset < 10:
            results.append({
                'offset': offset,
                'key': potential_key,
                'key_hex': key_hex,
                'score': score,
                'patterns': patterns,
                'printable_count': printable_count,
                'unique_bytes': unique_bytes
            })
    
    # Sort by score
    results.sort(key=lambda x: x['score'], reverse=True)
    return results

def test_xor_key_on_full_payload(payload, key):
    """Test XOR key on full payload to decrypt"""
    decrypted = bytearray()
    for i, byte in enumerate(payload):
        decrypted.append(byte ^ key[i % len(key)])
    return bytes(decrypted)

def main():
    pcap_file = "PCAPdroid_30_Jan_22_57_36.pcap"
    
    print("="*80)
    print("RENAME TO 'AAAAAAAAAA' - KNOWN PLAINTEXT ATTACK")
    print("="*80)
    print(f"PCAP: {pcap_file}")
    print()
    
    # Find rename commands
    rename_packets = parse_pcap_for_rename(pcap_file)
    
    print(f"Found {len(rename_packets)} rename commands (0x43)\n")
    
    if len(rename_packets) == 0:
        print("❌ No rename commands found in PCAP")
        print("\nSearching for ANY 0x43 bytes in file...")
        
        # Fallback: raw binary search
        with open(pcap_file, 'rb') as f:
            data = f.read()
            count = data.count(b'\x43')
            print(f"Found {count} occurrences of 0x43 byte in file")
            
            # Find first few
            pos = 0
            for i in range(min(5, count)):
                pos = data.find(b'\x43', pos)
                print(f"  Offset 0x{pos:x}: context = {hexlify(data[max(0,pos-10):pos+20]).decode()}")
                pos += 1
        return
    
    # Analyze each rename packet
    for i, pkt in enumerate(rename_packets, 1):
        print(f"{'='*80}")
        print(f"RENAME PACKET #{i} (packet #{pkt['packet_num']}, timestamp {pkt['timestamp']})")
        print(f"{'='*80}")
        
        print(f"\nHeader (13 bytes before 0x43):")
        print(f"  {hexlify(pkt['header']).decode()}")
        
        print(f"\nCommand ID: 0x43 (RENAME)")
        
        print(f"\nEncrypted Payload (first 80 bytes):")
        payload_hex = hexlify(pkt['payload'][:80]).decode()
        # Print in rows of 32 hex chars (16 bytes)
        for j in range(0, len(payload_hex), 32):
            print(f"  {payload_hex[j:j+32]}")
        
        print(f"\nFull Context (40 bytes):")
        print(f"  {hexlify(pkt['full_context'][:40]).decode()}")
        
        # Known plaintext attack
        results = known_plaintext_attack(pkt['payload'], "AAAAAAAAAA")
        
        if len(results) > 0:
            print(f"\n{'─'*80}")
            print(f"POTENTIAL XOR KEYS (top 10):")
            print(f"{'─'*80}")
            
            for j, r in enumerate(results[:10], 1):
                print(f"\n#{j}. Offset {r['offset']}, Score: {r['score']}")
                print(f"   Key (hex): {r['key_hex']}")
                
                # Try to display as ASCII
                try:
                    key_ascii = r['key'].decode('utf-8', errors='replace')
                    print(f"   Key (ASCII): '{key_ascii}'")
                except:
                    pass
                
                print(f"   Patterns: {', '.join(r['patterns']) if r['patterns'] else 'none'}")
                print(f"   Printable: {r['printable_count']}/{len(r['key'])}, Unique: {r['unique_bytes']}")
                
                # Test on full payload
                if r['score'] > 20:
                    decrypted = test_xor_key_on_full_payload(pkt['payload'], r['key'])
                    
                    # Check for AAAAAAAAAA
                    if b'AAAAAAAAAA' in decrypted:
                        print(f"\n   🎯 SUCCESS! Found 'AAAAAAAAAA' in decrypted data!")
                        print(f"   Decrypted (first 100 bytes):")
                        try:
                            text = decrypted[:100].decode('utf-8', errors='replace')
                            print(f"   {repr(text)}")
                        except:
                            print(f"   {hexlify(decrypted[:100]).decode()}")
                    else:
                        # Show sample anyway
                        preview = decrypted[:50]
                        printable = sum(1 for b in preview if 32 <= b <= 126)
                        if printable > len(preview) * 0.6:
                            try:
                                print(f"   Sample: {repr(preview.decode('utf-8', errors='replace'))}")
                            except:
                                print(f"   Sample: {hexlify(preview).decode()}")
        else:
            print("\n❌ No potential keys found")
        
        print(f"\n{'='*80}\n")
    
    print(f"\n{'='*80}")
    print("SUMMARY")
    print(f"{'='*80}")
    print(f"Total rename packets: {len(rename_packets)}")
    print(f"Known plaintext: 'AAAAAAAAAA'")
    print("If no match found, encryption may not be simple XOR")
    print("="*80)

if __name__ == "__main__":
    main()
