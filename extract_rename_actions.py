#!/usr/bin/env python3
"""
Extract ALL rename actions from 0x43 packets to find the test rename
"""

with open('PCAPdroid_30_Jan_18_26_35.pcap', 'rb') as f:
    data = f.read()

print("=" * 70)
print("EXTRACTING ALL RENAME (0x43) PACKET DATA")
print("=" * 70)

pos = 0
rename_count = 0
rename_actions = []

while pos < len(data) - 14:
    if data[pos:pos+2] == b'\x17\xfe':
        if pos + 13 < len(data) and data[pos + 13] == 0x43:
            rename_count += 1
            
            if pos + 80 < len(data):
                old_name_raw = data[pos + 16:pos + 48]
                new_name_raw = data[pos + 48:pos + 80]
                
                old_name = old_name_raw.rstrip(b'\x00').decode('utf-8', errors='replace')
                new_name = new_name_raw.rstrip(b'\x00').decode('utf-8', errors='replace')
                
                # Skip empty names
                if old_name.strip() and new_name.strip():
                    rename_actions.append((rename_count, old_name, new_name))
    pos += 1

print(f"Total 0x43 rename packets: {rename_count}")
print(f"Non-empty renames found: {len(rename_actions)}\n")

if rename_actions:
    print("RENAME ACTIONS CAPTURED:")
    print("-" * 70)
    for seq, old, new in rename_actions[:20]:  # Show first 20
        print(f"[{seq}] '{old}' → '{new}'")
        if 'test' in new.lower():
            print(f"      ✓ FOUND TARGET: 'test' in new name!")
else:
    print("No non-empty rename actions found")
