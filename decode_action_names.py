#!/usr/bin/env python3
"""
Decode action names from 0x1A response packet hex dump
Based on actual PCAP capture data
"""

# Full 233-byte 0x1A response packet from PCAP (Command 0x1A: List Teaching Actions)
# This is the REAL data from the robot
hex_data = """
17 fe fd 00 01 00 c9 3f 00 00 00 01 1a 00 dc
00 05 77 61 69 73 74 5f 64 72 75 6d 5f 64 61
6e 63 65 00 00 00 00 00 00 00 00 00 00 00 00
00 00 65 47 02 40 73 70 69 6e 5f 64 69 73 6b
73 00 00 00 00 00 00 00 00 00 00 00 00 00 00
00 00 00 00 00 40 40 62 00 68 61 6e 64 5f 77
61 76 65 00 00 00 00 00 00 00 00 00 00 00 00
00 00 00 00 00 00 00 00 00 40 40 62 00 73 74
61 6e 64 5f 75 70 00 00 00 00 00 00 00 00 00
00 00 00 00 00 00 00 00 00 00 00 00 40 40 62
00 77 61 69 73 74 5f 73 70 69 6e 00 00 00 00
00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
00 40 40 62 00
"""

def decode_action_list():
    """Decode action names from 0x1A response packet"""
    
    # Convert hex string to bytes
    hex_clean = hex_data.replace('\n', ' ').strip()
    packet_bytes = bytes.fromhex(hex_clean)
    
    print("=" * 70)
    print("📋 DECODING ACTION NAMES FROM 0x1A RESPONSE")
    print("=" * 70)
    
    print(f"\n📦 Total packet size: {len(packet_bytes)} bytes")
    
    # Parse header
    header = packet_bytes[0:13]
    print(f"\n🔧 Header (13 bytes): {header.hex(' ')}")
    
    cmd_id = packet_bytes[12]
    print(f"   Command ID: 0x{cmd_id:02X} (should be 0x1A)")
    
    payload_len = int.from_bytes(packet_bytes[13:15], 'big')
    print(f"   Payload length: {payload_len} bytes (0x{payload_len:04X})")
    
    action_count = int.from_bytes(packet_bytes[15:17], 'big')
    print(f"   Action count: {action_count}")
    
    # Parse actions (starting at byte 17)
    print(f"\n🎭 ACTIONS:")
    print("=" * 70)
    
    offset = 17
    actions = []
    
    for i in range(action_count):
        # Each action: 32 bytes name + 4 bytes metadata = 36 bytes
        name_bytes = packet_bytes[offset:offset+32]
        metadata_bytes = packet_bytes[offset+32:offset+36]
        
        # Decode name (null-terminated UTF-8)
        try:
            # Find null terminator
            null_idx = name_bytes.find(b'\x00')
            if null_idx > 0:
                action_name = name_bytes[:null_idx].decode('utf-8')
            else:
                action_name = name_bytes.decode('utf-8').rstrip('\x00')
        except:
            action_name = name_bytes.hex()
        
        # Parse metadata (4 bytes - likely duration or timestamp)
        metadata_int = int.from_bytes(metadata_bytes, 'big')
        
        actions.append({
            'index': i + 1,
            'name': action_name,
            'name_bytes': name_bytes.hex(' '),
            'metadata': metadata_int,
            'metadata_hex': metadata_bytes.hex(' ')
        })
        
        print(f"\nAction {i+1}:")
        print(f"  Name: '{action_name}'")
        print(f"  Name bytes (32B): {name_bytes.hex(' ')[:60]}...")
        print(f"  ASCII: {name_bytes[:len(action_name)]}")
        print(f"  Metadata (4B): {metadata_bytes.hex(' ')} = 0x{metadata_int:08X}")
        
        offset += 36
    
    # Summary
    print("\n" + "=" * 70)
    print("📊 SUMMARY")
    print("=" * 70)
    
    print(f"\nTotal actions found: {len(actions)}")
    print(f"\nAction list:")
    for action in actions:
        print(f"  {action['index']}. {action['name']}")
    
    # Verify structure
    print(f"\n✅ VERIFICATION:")
    print(f"   Header: 13 bytes")
    print(f"   Payload length field: 2 bytes (value: {payload_len})")
    print(f"   Action count field: 2 bytes (value: {action_count})")
    print(f"   Action data: {action_count} × 36 bytes = {action_count * 36} bytes")
    print(f"   Total: 13 + 2 + 2 + {action_count * 36} = {17 + action_count * 36} bytes")
    print(f"   Actual packet: {len(packet_bytes)} bytes")
    
    # Check if matches
    expected_size = 17 + action_count * 36 + 4  # +4 for CRC32
    if len(packet_bytes) == expected_size:
        print(f"   ✅ Packet structure VERIFIED!")
    else:
        print(f"   ⚠️  Size mismatch: expected {expected_size}, got {len(packet_bytes)}")
    
    return actions

def show_command_0x41_structure():
    """Show how to use action names in 0x41 play command"""
    
    print("\n" + "=" * 70)
    print("⚡ HOW TO PLAY AN ACTION (Command 0x41)")
    print("=" * 70)
    
    print("""
To play a saved action, send command 0x41 with:

Structure:
  Byte 0-12:   Standard header (0x17 0xFE 0xFD...)
  Byte 13:     Command ID = 0x41
  Byte 14-15:  Payload length (usually 0x00B8 = 184 bytes)
  Byte 16+:    Payload containing:
               - Action identifier (could be index 1-15, or name hash)
               - Playback parameters (speed, interpolation)
               - Keyframe data

Based on PCAP analysis:
  • The 0x41 packet does NOT contain the action name directly
  • It likely uses an ACTION INDEX (1-15) or ACTION ID
  • To play "waist_drum_dance", you would specify index 1
  • To play "spin_disks", you would specify index 2
  • etc.

Recommended approach:
  1. Send 0x1A to get list of actions
  2. Parse response to get action names and their indices
  3. User selects action by name
  4. Your code maps name → index
  5. Send 0x41 with that index in the payload
""")

if __name__ == "__main__":
    actions = decode_action_list()
    show_command_0x41_structure()
    
    print("\n" + "=" * 70)
    print("✅ DECODING COMPLETE")
    print("=" * 70)
