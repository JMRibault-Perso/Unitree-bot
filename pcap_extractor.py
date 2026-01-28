#!/usr/bin/env python3
"""
Extract actual 0x42 command and response from PCAP for testing
"""

def extract_pcap_data():
    """Extract real command and response from PCAP"""
    with open('g1_app/PCAPdroid_26_Jan_10_28_24.pcap', 'rb') as f:
        data = f.read()
    
    # Extract first 0x42 command
    cmd_offset = 0x3b73
    # Find the 17 fe fd 00 pattern near this offset
    for offset in range(cmd_offset, cmd_offset+100):
        if data[offset:offset+4] == bytes([0x17, 0xfe, 0xfd, 0x00]):
            cmd_data = data[offset:offset+58]
            print("0x42 COMMAND FROM PCAP:")
            print(f"  Offset: 0x{offset:x}")
            print(f"  Hex: {cmd_data.hex()}")
            print(f"  Structure:")
            print(f"    Header (0x00-0x03): {cmd_data[0:4].hex()}")
            print(f"    Sequence (0x04-0x07): {int.from_bytes(cmd_data[4:8], 'little')}")
            print(f"    Cmd ID (0x0a-0x0b): 0x{int.from_bytes(cmd_data[10:12], 'little'):04x}")
            print(f"    Payload start (0x0c): {cmd_data[12:14].hex()}")
            break
    
    # Extract first response
    print("\n0x42 RESPONSE FROM PCAP:")
    resp_offset = 0x4610
    resp_data = data[resp_offset:resp_offset+76]
    print(f"  Offset: 0x{resp_offset:x}")
    print(f"  Hex: {resp_data.hex()}")
    print(f"  Structure:")
    print(f"    Header (0x00-0x03): {resp_data[0:4].hex()}")
    print(f"    Magic (0x04-0x07): {resp_data[4:8].hex()}")
    print(f"    Encrypted name (0x08-0x17): {resp_data[8:24].hex()}")
    
    # Try to find if encrypted names decode to action names
    print("\n\nLooking for action names in responses...")
    print("We know actions are: 'waist_drum_dance' and 'spin_disks'")
    print("Searching PCAP for plain text versions...")
    
    # Search for action names
    if b'waist_drum_dance' in data:
        pos = data.find(b'waist_drum_dance')
        print(f"\nFound 'waist_drum_dance' at 0x{pos:x}!")
        chunk = data[max(0, pos-50):min(len(data), pos+100)]
        print(f"  Context: {chunk.hex()}")
    
    if b'spin_disks' in data:
        pos = data.find(b'spin_disks')
        print(f"\nFound 'spin_disks' at 0x{pos:x}!")
        chunk = data[max(0, pos-50):min(len(data), pos+100)]
        print(f"  Context: {chunk.hex()}")

if __name__ == "__main__":
    extract_pcap_data()
