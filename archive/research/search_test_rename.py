#!/usr/bin/env python3
"""
Search for "test" in 0x43 rename packets
"""

# Read PCAP file
with open('PCAPdroid_30_Jan_18_26_35.pcap', 'rb') as f:
    data = f.read()

print("=" * 70)
print("SEARCHING FOR 'test' IN RENAME (0x43) PACKETS")
print("=" * 70)

# Find all 0x43 packets and check for "test"
pos = 0
test_packets = []

while pos < len(data) - 14:
    if data[pos:pos+2] == b'\x17\xfe':
        if pos + 13 < len(data) and data[pos + 13] == 0x43:
            # Check if this packet contains 'test'
            packet_end = min(pos + 300, len(data))
            packet_data = data[pos:packet_end]
            
            if b'test' in packet_data:
                test_packets.append(pos)
                print(f"\n✓ Found 'test' in 0x43 packet at offset 0x{pos:x}")
                
                # Show hex
                hex_snippet = packet_data[:120].hex()
                print(f"  Hex (first 120 chars): {hex_snippet}")
                
                # Show ASCII
                ascii_text = ''.join(chr(b) if 32 <= b < 127 else '.' for b in packet_data[:120])
                print(f"  ASCII: {ascii_text}")
                
                # Try to extract names
                if pos + 80 < len(data):
                    old_name_raw = data[pos + 16:pos + 48]
                    new_name_raw = data[pos + 48:pos + 80]
                    
                    old_name = old_name_raw.rstrip(b'\x00').decode('utf-8', errors='ignore')
                    new_name = new_name_raw.rstrip(b'\x00').decode('utf-8', errors='ignore')
                    
                    print(f"  Old name: {old_name}")
                    print(f"  New name: {new_name}")
                    
                    # Look for 'test' in both
                    if 'test' in old_name.lower():
                        print(f"  ✓ 'test' found in OLD name: {old_name}")
                    if 'test' in new_name.lower():
                        print(f"  ✓ 'test' found in NEW name: {new_name}")
    pos += 1

print(f"\n\nTotal 0x43 packets containing 'test': {len(test_packets)}")

if test_packets:
    print("\nPacket offsets with 'test':")
    for offset in test_packets[:10]:  # Show first 10
        print(f"  0x{offset:x}")
else:
    print("\n⚠️ No 'test' found in any 0x43 rename packets")
    print("Searching for 'test' anywhere in PCAP...")
    
    # Search entire PCAP for 'test'
    pos = 0
    test_positions = []
    while pos < len(data) - 4:
        if data[pos:pos+4] == b'test':
            test_positions.append(pos)
        pos += 1
    
    if test_positions:
        print(f"\nFound {len(test_positions)} instances of 'test' in PCAP")
        for i, offset in enumerate(test_positions[:5]):
            print(f"\n  Instance {i+1} at offset 0x{offset:x}")
            context_start = max(0, offset - 20)
            context_end = min(len(data), offset + 30)
            context = data[context_start:context_end]
            print(f"    Hex: {context.hex()}")
            print(f"    ASCII: {''.join(chr(b) if 32 <= b < 127 else '.' for b in context)}")
