#!/usr/bin/env python3
"""
Search for literal "test" bytes in PCAP, check context
"""

with open('PCAPdroid_30_Jan_18_26_35.pcap', 'rb') as f:
    data = f.read()

print("=" * 70)
print("SEARCHING FOR LITERAL 'test' (0x74657374) IN ENTIRE PCAP")
print("=" * 70)

test_bytes = b'test'
pos = 0
occurrences = []

while True:
    pos = data.find(test_bytes, pos)
    if pos == -1:
        break
    occurrences.append(pos)
    pos += 1

print(f"Found {len(occurrences)} occurrences of 'test'\n")

if occurrences:
    for i, offset in enumerate(occurrences[:15]):
        print(f"\n[{i+1}] Found 'test' at offset 0x{offset:x} ({offset})")
        
        # Check if it's inside a 0x43 packet
        search_start = max(0, offset - 500)
        search_data = data[search_start:offset + 100]
        
        # Look backwards for command ID
        for j in range(len(search_data) - 1, -1, -1):
            if search_data[j:j+2] == b'\x17\xfe':
                cmd_offset = j + 13 if j + 13 < len(search_data) else -1
                if cmd_offset > 0 and cmd_offset < len(search_data):
                    cmd_id = search_data[cmd_offset]
                    rel_pos = offset - (search_start + j)
                    print(f"    Command: 0x{cmd_id:02x} at relative offset -{rel_pos}")
                    
                    if cmd_id == 0x43:
                        print(f"    ✓ FOUND 'test' INSIDE 0x43 RENAME PACKET!")
                        # Show context
                        ctx_start = max(0, offset - 50)
                        ctx_end = min(len(data), offset + 20)
                        context = data[ctx_start:ctx_end]
                        print(f"    Context: {context}")
                break
else:
    print("No 'test' string found in PCAP at all")
    print("\nSearching for common test-like patterns...")
    
    patterns = [
        b'Test',
        b'TEST', 
        b'tst',
        b'demo',
        b'Demo',
    ]
    
    for pattern in patterns:
        count = data.count(pattern)
        if count > 0:
            print(f"  Found {count}x '{pattern.decode()}'")
