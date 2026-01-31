#!/usr/bin/env python3
"""
Search PCAP binary directly for 0x42 and 0x43 commands
"""

# Read PCAP file directly
with open('PCAPdroid_30_Jan_18_26_35.pcap', 'rb') as f:
    data = f.read()

print("=" * 70)
print("SEARCHING FOR 0x42 AND 0x43 COMMANDS IN PCAP BINARY")
print("=" * 70)

# Search for 0x42 at offset 13 (command ID position in header)
print("\nSearching for 0x42 packets (Delete)...")
pos = 0
count_42 = 0
packets_42 = []

while pos < len(data) - 14:
    # Look for packet header pattern: 17 fe fd 00
    if data[pos:pos+2] == b'\x17\xfe':
        # Check if command ID at offset 13 is 0x42
        if pos + 13 < len(data) and data[pos + 13] == 0x42:
            count_42 += 1
            packets_42.append(pos)
            # Extract surrounding context
            start = max(0, pos - 5)
            end = min(len(data), pos + 80)
            hex_snippet = data[start:end].hex()
            print(f"\n✓ Found 0x42 packet #{count_42} at offset 0x{pos:x}")
            print(f"  Hex: {hex_snippet[:120]}")
            # Try to extract action name
            if pos + 48 < len(data):
                name_bytes = data[pos + 16:pos + 48]
                name = name_bytes.rstrip(b'\x00').decode('utf-8', errors='ignore')
                if name and len(name.strip()) > 0:
                    print(f"  Action name: {name}")
    pos += 1

print(f"\nTotal 0x42 packets found: {count_42}")

# Search for 0x43 (Rename)
print("\n" + "-" * 70)
print("Searching for 0x43 packets (Rename)...")
pos = 0
count_43 = 0
packets_43 = []

while pos < len(data) - 14:
    if data[pos:pos+2] == b'\x17\xfe':
        if pos + 13 < len(data) and data[pos + 13] == 0x43:
            count_43 += 1
            packets_43.append(pos)
            start = max(0, pos - 5)
            end = min(len(data), pos + 80)
            hex_snippet = data[start:end].hex()
            print(f"\n✓ Found 0x43 packet #{count_43} at offset 0x{pos:x}")
            print(f"  Hex: {hex_snippet[:120]}")
            # Try to extract rename data (old and new names)
            if pos + 80 < len(data):
                old_name = data[pos + 16:pos + 48].rstrip(b'\x00').decode('utf-8', errors='ignore')
                new_name = data[pos + 48:pos + 80].rstrip(b'\x00').decode('utf-8', errors='ignore')
                if old_name and len(old_name.strip()) > 0:
                    print(f"  Old name: {old_name}")
                if new_name and len(new_name.strip()) > 0:
                    print(f"  New name: {new_name}")
    pos += 1

print(f"\nTotal 0x43 packets found: {count_43}")

print("\n" + "=" * 70)
print(f"SUMMARY: 0x42 (delete)={count_42}, 0x43 (rename)={count_43}")
print("=" * 70)

# Show detailed hex for each packet found
if packets_42:
    print("\n\nDETAILED 0x42 PACKETS:")
    for i, offset in enumerate(packets_42[:3]):  # Show first 3
        print(f"\n--- 0x42 Packet {i+1} at 0x{offset:x} ---")
        packet_data = data[offset:offset+100]
        print("Hex:", packet_data.hex())
        print("ASCII (filtered):", ''.join(chr(b) if 32 <= b < 127 else '.' for b in packet_data))

if packets_43:
    print("\n\nDETAILED 0x43 PACKETS:")
    for i, offset in enumerate(packets_43[:3]):  # Show first 3
        print(f"\n--- 0x43 Packet {i+1} at 0x{offset:x} ---")
        packet_data = data[offset:offset+100]
        print("Hex:", packet_data.hex())
        print("ASCII (filtered):", ''.join(chr(b) if 32 <= b < 127 else '.' for b in packet_data))
