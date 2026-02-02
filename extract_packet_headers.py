#!/usr/bin/env python3
"""
Extract full packet headers for packets 3 and 15 to find what correlates
with the first 2 bytes of the XOR key
"""

import struct
from binascii import hexlify

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
            
            # Search for 0x43 command ID in packet
            for i in range(len(packet_data) - 1):
                if packet_data[i] == 0x43:
                    # Found potential rename command
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

rename_packets = parse_pcap_for_rename("PCAPdroid_30_Jan_22_57_36.pcap")

rename_packets = parse_pcap_for_rename("PCAPdroid_30_Jan_22_57_36.pcap")

print("="*80)
print(f"Found {len(rename_packets)} rename packets (0x43)")
print("="*80)
print()

# Focus on packets 3 and 15 (0-indexed: 2 and 14)
if len(rename_packets) >= 15:
    packets_of_interest = {
        'Packet 3': rename_packets[2],
        'Packet 15': rename_packets[14]
    }
    
    for name, pkt in packets_of_interest.items():
        print(f"\n{'='*80}")
        print(f"{name}")
        print(f"{'='*80}")
        
        print(f"\nTimestamp: {pkt['timestamp']}")
        print(f"Packet number: {pkt['packet_num']}")
        print(f"Offset in packet: {pkt['offset']}")
        
        # Show header (13 bytes before 0x43)
        print(f"\nHeader (13 bytes before 0x43):")
        print(f"  {hexlify(pkt['header']).decode()}")
        
        header = pkt['header']
        if len(header) == 13:
            print(f"\n  Breakdown:")
            print(f"    Bytes 0-2:  {hexlify(header[0:3]).decode()} (DTLS?)")
            print(f"    Bytes 3-10: {hexlify(header[3:11]).decode()}")
            print(f"    Bytes 11-12: {hexlify(header[11:13]).decode()} = {struct.unpack('>H', header[11:13])[0]}")
        
        # Show first 100 bytes of payload
        payload = pkt['payload']
        print(f"\nPayload first 100 bytes:")
        print(f"  {hexlify(payload[:100]).decode()}")
        
        # Try to find 'AAAAAAAAAA' in payload
        target = b'AAAAAAAAAA'
        print(f"\nSearching for XOR with 'AAAAAAAAAA'...")
        
        for offset in range(len(payload) - 10):
            encrypted = payload[offset:offset+10]
            xor_key = bytes([e ^ t for e, t in zip(encrypted, target)])
            
            # Check if key looks reasonable (printable ASCII)
            printable_count = sum(1 for b in xor_key if 32 <= b <= 126)
            if printable_count >= 5:  # At least 5 printable chars
                decrypted = bytes([e ^ k for e, k in zip(encrypted, xor_key)])
                if decrypted == target:
                    print(f"  ✓ FOUND at offset {offset}")
                    print(f"    XOR key: {hexlify(xor_key).decode()}")
                    print(f"    First 2 bytes: 0x{xor_key[0]:02x} 0x{xor_key[1]:02x}")
                    print(f"    Remaining 8: {hexlify(xor_key[2:]).decode()}")
                    print(f"    ASCII: '{xor_key.decode('latin1')}'")
                    break

print("\n" + "="*80)
print("CORRELATION CHECK")
print("="*80)
print()


# Get data from both packets for correlation
if len(rename_packets) >= 15:
    pkt3 = rename_packets[2]
    pkt15 = rename_packets[14]
    
    print(f"Packet 3 timestamp:  {pkt3['timestamp']}")
    print(f"Packet 15 timestamp: {pkt15['timestamp']}")
    time_diff = pkt15['timestamp'] - pkt3['timestamp']
    print(f"Time difference: {time_diff:.6f} seconds")
    print(f"Time diff in milliseconds: {time_diff * 1000:.0f} ms")
    print()
    
    # Check header bytes
    print("Header comparison:")
    print(f"  Packet 3:  {hexlify(pkt3['header']).decode()}")
    print(f"  Packet 15: {hexlify(pkt15['header']).decode()}")
    
    # Check for sequence number in header
    if len(pkt3['header']) >= 13 and len(pkt15['header']) >= 13:
        seq3 = struct.unpack('>H', pkt3['header'][11:13])[0]
        seq15 = struct.unpack('>H', pkt15['header'][11:13])[0]
        print(f"\n  Sequence at bytes 11-12:")
        print(f"    Packet 3:  {seq3} (0x{seq3:04x})")
        print(f"    Packet 15: {seq15} (0x{seq15:04x})")
        print(f"    Difference: {seq15 - seq3}")
    
    # Compare with XOR key first 2 bytes
    print(f"\nXOR key first 2 bytes comparison:")
    print(f"  Packet 3:  0xfa1e = {0xfa1e}")
    print(f"  Packet 15: 0x1bfd = {0x1bfd}")
    print(f"  Difference: {0x1bfd - 0xfa1e} = 0x{0x1bfd - 0xfa1e:04x}")

