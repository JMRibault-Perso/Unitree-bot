#!/usr/bin/env python3
"""
Test if the discovered 8-byte session key can decrypt all packets
by brute-forcing the 2-byte prefix
"""

import struct
from binascii import hexlify, unhexlify

def parse_pcap_for_rename(pcap_path):
    """Find 0x43 (rename) commands"""
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
            
            # Search for 0x43 command ID
            for i in range(len(packet_data) - 1):
                if packet_data[i] == 0x43:
                    if i >= 13 and packet_data[i-13:i-10] == b'\x17\xfe\xfd':
                        rename_packets.append({
                            'packet_num': packet_num,
                            'offset': i,
                            'header': packet_data[i-13:i],
                            'payload': packet_data[i+1:i+120],
                            'full_data': packet_data,
                            'timestamp': ts_sec + ts_usec / 1000000.0
                        })
                        break
    
    return rename_packets

# Known session key from packets 9 and 15
SESSION_KEY_8BYTES = unhexlify("4641404661604141")
TARGET = b'AAAAAAAAAA'

print("="*80)
print("TESTING SESSION KEY ON ALL PACKETS")
print("="*80)
print(f"\nSession key (8 bytes): {hexlify(SESSION_KEY_8BYTES).decode()}")
print(f"Session key ASCII: '{SESSION_KEY_8BYTES.decode('latin1')}'")
print(f"Target plaintext: '{TARGET.decode()}'")
print()

rename_packets = parse_pcap_for_rename("PCAPdroid_30_Jan_22_57_36.pcap")
print(f"Found {len(rename_packets)} rename packets\n")

successful_decrypts = 0

for idx, pkt in enumerate(rename_packets, 1):
    print(f"{'='*80}")
    print(f"PACKET #{idx} (packet {pkt['packet_num']}, timestamp {pkt['timestamp']})")
    print(f"{'='*80}")
    
    payload = pkt['payload']
    found_match = False
    
    # Try brute-forcing the 2-byte prefix
    # First, try known prefixes from successful packets
    known_prefixes = [
        unhexlify('dbfa'),  # Packet 7
        unhexlify('fa1e'),  # Packet 9
        unhexlify('4e33'),  # Packet 12
        unhexlify('1bfd'),  # Packet 15
        unhexlify('6994'),  # Packet 17
    ]
    
    for prefix in known_prefixes:
        full_key = prefix + SESSION_KEY_8BYTES
        
        # Try at different offsets
        for offset in range(min(100, len(payload) - 10)):
            encrypted = payload[offset:offset+10]
            decrypted = bytes([e ^ k for e, k in zip(encrypted, full_key)])
            
            if decrypted == TARGET:
                print(f"✓ SUCCESS with known prefix 0x{hexlify(prefix).decode()}")
                print(f"  Offset: {offset}")
                print(f"  Full key: {hexlify(full_key).decode()}")
                
                # Show surrounding context
                context_start = max(0, offset - 20)
                context_end = min(len(payload), offset + 30)
                full_decrypt = bytes([payload[i] ^ full_key[i - offset] if offset <= i < offset + 10 
                                     else payload[i] 
                                     for i in range(context_start, context_end)])
                print(f"  Context (offset {context_start}-{context_end}):")
                print(f"    {repr(full_decrypt[:50])}")
                
                found_match = True
                successful_decrypts += 1
                break
        
        if found_match:
            break
    
    if not found_match:
        # Try to find "AAAAAAAAAA" with ANY 10-byte key (brute-force search)
        print("Known prefix failed. Searching for any valid XOR key...")
        
        for offset in range(min(100, len(payload) - 10)):
            encrypted = payload[offset:offset+10]
            test_key = bytes([e ^ t for e, t in zip(encrypted, TARGET)])
            
            # Check if last 8 bytes match session key
            if test_key[2:] == SESSION_KEY_8BYTES:
                prefix_hex = hexlify(test_key[:2]).decode()
                print(f"✓ FOUND with NEW prefix 0x{prefix_hex}")
                print(f"  Offset: {offset}")
                print(f"  Full key: {hexlify(test_key).decode()}")
                print(f"  First 2 bytes: 0x{prefix_hex} ({test_key[0]}, {test_key[1]})")
                
                # Check if key looks reasonable
                printable = sum(1 for b in test_key if 32 <= b <= 126)
                print(f"  Printable chars: {printable}/10")
                
                found_match = True
                successful_decrypts += 1
                break
        
        if not found_match:
            # Last resort: find ANY XOR key that produces "AAAAAAAAAA"
            print("Session key mismatch. Searching for ANY valid XOR key...")
            
            for offset in range(min(100, len(payload) - 10)):
                encrypted = payload[offset:offset+10]
                test_key = bytes([e ^ t for e, t in zip(encrypted, TARGET)])
                
                # Verify decryption works
                verify = bytes([e ^ k for e, k in zip(encrypted, test_key)])
                if verify == TARGET:
                    printable = sum(1 for b in test_key if 32 <= b <= 126)
                    if printable >= 5:  # At least 5 printable chars
                        print(f"✗ DIFFERENT KEY FOUND (not matching session key)")
                        print(f"  Offset: {offset}")
                        print(f"  Key: {hexlify(test_key).decode()}")
                        print(f"  ASCII: '{test_key.decode('latin1')}'")
                        print(f"  Printable: {printable}/10")
                        print(f"  → This suggests a DIFFERENT SESSION or encryption method")
                        found_match = True
                        break
    
    if not found_match:
        print("✗ NO VALID XOR KEY FOUND for this packet")
        print("  Possible reasons:")
        print("  - Different encryption method")
        print("  - String not present in analyzed range")
        print("  - Additional encryption layer")
    
    print()

print("="*80)
print("SUMMARY")
print("="*80)
print(f"Total packets: {len(rename_packets)}")
print(f"Successfully decrypted: {successful_decrypts}")
print(f"Success rate: {successful_decrypts / len(rename_packets) * 100:.1f}%")
print()

if successful_decrypts < len(rename_packets):
    print(f"⚠️  {len(rename_packets) - successful_decrypts} packets could not be decrypted")
    print("   This suggests multiple sessions or different encryption methods")
else:
    print("🎉 ALL PACKETS DECRYPTED!")
    print("   The session key is valid for the entire capture")
