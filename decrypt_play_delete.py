#!/usr/bin/env python3
"""
Known-plaintext attack on teaching protocol encryption.
Attempts to decrypt PLAY and DELETE commands using known action names.
"""

import sys

def xor_decrypt(encrypted_hex, known_plaintext):
    """
    Attempt XOR decryption with known plaintext.
    Returns the extracted keystream if successful.
    """
    encrypted = bytes.fromhex(encrypted_hex)
    known = known_plaintext.encode('utf-8') + b'\x00'  # Add null terminator
    
    if len(encrypted) < len(known):
        print(f"ERROR: Encrypted data too short ({len(encrypted)} bytes) for plaintext ({len(known)} bytes)")
        return None
    
    # Extract keystream by XORing encrypted with known plaintext
    keystream = bytes([e ^ k for e, k in zip(encrypted, known)])
    
    return keystream

def analyze_packet(name, packet_hex, known_action, start_offset):
    """
    Analyze a teaching protocol packet with known action name.
    """
    print(f"\n{'='*80}")
    print(f"{name}")
    print(f"{'='*80}")
    
    # Convert full packet to bytes
    packet = bytes.fromhex(packet_hex.replace(' ', '').replace('\n', ''))
    
    print(f"Total packet length: {len(packet)} bytes")
    print(f"Magic header: {packet[0:3].hex()}")
    print(f"Command byte: 0x{packet[13]:02X}")
    
    # Try different offsets for action name start
    print(f"\nTrying to decrypt action name at various offsets:")
    print(f"Known action: '{known_action}' ({len(known_action)} chars + null = {len(known_action)+1} bytes)")
    
    for offset in range(start_offset-2, start_offset+5):
        if offset + len(known_action) + 1 > len(packet):
            continue
        
        encrypted_chunk = packet[offset:offset+len(known_action)+10].hex()
        keystream = xor_decrypt(encrypted_chunk, known_action)
        
        if keystream:
            print(f"\nOffset {offset}:")
            print(f"  Encrypted: {encrypted_chunk[:40]}...")
            print(f"  Keystream: {keystream[:len(known_action)+1].hex()}")
            
            # Try decrypting more bytes with this keystream
            extended_decrypt = bytes([packet[offset+i] ^ keystream[i % len(keystream)] 
                                     for i in range(min(50, len(packet)-offset))])
            
            # Check if decrypted text is printable
            printable_count = sum(1 for b in extended_decrypt if 32 <= b <= 126 or b == 0)
            ratio = printable_count / len(extended_decrypt)
            
            print(f"  Extended decrypt (50 bytes): {extended_decrypt.hex()}")
            print(f"  As ASCII: {repr(extended_decrypt[:30])}")
            print(f"  Printable ratio: {ratio:.2%}")
            
            if ratio > 0.7:  # If >70% printable, likely correct
                print(f"  ✓ LIKELY CORRECT OFFSET!")

def main():
    # PLAY "handshake" command - Packet #122
    play_handshake = """
17fefd000100000000000f00b041cb5fbc04be132724daaba88e9e68622c1577ef
db3e5542108ac4edc1f427d2167478e4af56f101b2615d4be36c52436e738d49
7ab39a4333591358c0f709368b330afb8b5a25337880e5298b8233c12161e82d
ee367a5ab6ca7e92cec940a6a5ba3c43c8d50ec96ecba4478130d9a2ca9402dc
4840777f30e7958473f594af56f415949b24778f631ab2093ad00b716039dfe6
2c794b7cf0e5415ba2281f930a688b822fb08d778200e9aea27dddaf
"""
    
    # DELETE "AAAAAAAAA" command - Packet #390
    delete_aaaa = """
17fefd00010000000000a800e0426cecf1edc89709e872bedd5d80befc4b5409
7f999980d09be0772b6e2e1f7390134967568804c822b6d6abbdc527948557d9
5b220297d63e1081ea620e1dd3c9230e8668ecc1803a42a4a5304cca854cd63
89c3bf160ac06fe82682f8f1ec7ce0e9e30f83404aa1a110b82ece73f4998830
50dc986bbed7be59f2ef7d984ebff406959f7d642e7bc955fd535e32f1413b06
83bbc94c6b65431926471712ec9cae1ae225627d89653b9074b127ee2f7f0ff3
f655d990feae8b22afa3577c76082d083e2159fc98e4f4df4f7c763fcd98bf81
014b91137c36d6703e36448daaf
"""
    
    # Analyze both packets
    analyze_packet(
        "PLAY_ACTION (0x41) - handshake",
        play_handshake,
        "handshake",
        start_offset=16
    )
    
    analyze_packet(
        "DELETE_ACTION (0x42) - AAAAAAAAA",
        delete_aaaa,
        "AAAAAAAAA",
        start_offset=16
    )
    
    print(f"\n{'='*80}")
    print("Analysis Complete")
    print(f"{'='*80}\n")
    
    print("Next steps:")
    print("1. If printable ratio >70%, we found the correct offset and keystream")
    print("2. Test keystream on other packets to verify consistency")
    print("3. Analyze keystream pattern (is it repeating? derived from sequence number?)")
    print("4. Implement full encryption/decryption algorithm")

if __name__ == "__main__":
    main()
