#!/usr/bin/env python3
"""
Analysis of successful XOR keys that decrypted 'AAAAAAAAAA'
Looking for patterns in the keys
"""

from binascii import hexlify, unhexlify

# Successful keys that found 'AAAAAAAAAA'
successful_keys = [
    {
        'packet': 1,
        'offset': 90,
        'key_hex': 'dbfa3438253668612420',
        'key_ascii': '��48%6ha$ ',
        'timestamp': '1769831926.935691'
    },
    {
        'packet': 3,
        'offset': 40,
        'key_hex': 'fa1e4e41404661604141',
        'key_ascii': '�NA@Fa`AA',
        'timestamp': '1769831934.254722'
    },
    {
        'packet': 15,
        'offset': 40,
        'key_hex': '1bfd4641404661604141',
        'key_ascii': '�FA@Fa`AA',
        'timestamp': '1769831952.725727'
    },
    {
        'packet': 17,
        'offset': 50,
        'key_hex': '6994142f283533242461',
        'key_ascii': 'i�/(53$$a',
        'timestamp': '1769831967.693236'
    }
]

print("="*80)
print("SUCCESSFUL XOR KEY ANALYSIS")
print("="*80)
print()

print("Keys that successfully decrypted 'AAAAAAAAAA':\n")

for i, key in enumerate(successful_keys, 1):
    print(f"{i}. Packet #{key['packet']}, Offset {key['offset']}")
    print(f"   Timestamp: {key['timestamp']}")
    print(f"   Hex: {key['key_hex']}")
    print(f"   ASCII: '{key['key_ascii']}'")
    print(f"   Bytes: {[f'0x{b:02x}' for b in unhexlify(key['key_hex'])]}")
    print()

print("="*80)
print("PATTERN ANALYSIS")
print("="*80)
print()

# Check for common patterns
print("1. KEY LENGTH: All keys are 10 bytes (matches 'AAAAAAAAAA' length)")
print()

print("2. COMMON BYTES:")
# Find common bytes across all keys
all_bytes = [unhexlify(k['key_hex']) for k in successful_keys]
common_positions = []

for pos in range(10):
    bytes_at_pos = [key[pos] for key in all_bytes]
    if len(set(bytes_at_pos)) == 1:
        common_positions.append((pos, bytes_at_pos[0]))

if common_positions:
    for pos, byte in common_positions:
        print(f"   Position {pos}: 0x{byte:02x} ('{chr(byte) if 32 <= byte <= 126 else '?'}')")
else:
    print("   No common bytes at same positions")

print()

print("3. TIMESTAMP CORRELATION:")
timestamps = [float(k['timestamp']) for k in successful_keys]
time_diffs = [timestamps[i+1] - timestamps[i] for i in range(len(timestamps)-1)]
print(f"   Time differences: {[f'{d:.2f}s' for d in time_diffs]}")
print(f"   Total session time: {timestamps[-1] - timestamps[0]:.2f} seconds")
print()

print("4. OFFSET PATTERN:")
offsets = [k['offset'] for k in successful_keys]
print(f"   Offsets: {offsets}")
print(f"   Observation: Offset 40 appears twice (packets 3 and 15)")
print()

print("5. KEY STRUCTURE:")
print("   Packet 1:  db fa 34 38 25 36 68 61 24 20")
print("   Packet 3:  fa 1e 4e 41 40 46 61 60 41 41  ← Contains ASCII 'A' pattern")
print("   Packet 15: 1b fd 46 41 40 46 61 60 41 41  ← Very similar to packet 3!")
print("   Packet 17: 69 94 14 2f 28 35 33 24 24 61")
print()
print("   NOTE: Packets 3 and 15 share pattern: xx xx 46 41 40 46 61 60 41 41")
print("         This suggests: [random][random]F A @ F a ` A A")
print("         Contains ASCII 'A@Fa`AA' at end")
print()

print("="*80)
print("HYPOTHESIS")
print("="*80)
print()
print("The encryption uses a DYNAMIC XOR key that changes per packet or session.")
print()
print("Evidence:")
print("  1. Different keys for different packets")
print("  2. Keys at offset 40/50 (likely after some header/metadata)")
print("  3. Some keys contain ASCII patterns (A, F, a, @, etc.)")
print("  4. Two packets have very similar keys (only first 2 bytes differ)")
print()
print("Possible key generation:")
print("  - Time-based: key derived from timestamp")
print("  - Sequence-based: key changes with packet sequence number")  
print("  - Session key: established during connection, changes per session")
print("  - Hybrid: STUN username + timestamp + sequence number")
print()
print("Next step: Extract packet sequence numbers and check correlation")
print("="*80)
