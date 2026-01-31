#!/usr/bin/env python3
"""
Debug STUN packet structure from PCAP.
"""

import scapy.all as scapy
from binascii import hexlify

pcap_file = 'PCAPdroid_30_Jan_18_26_35.pcap'
packets = scapy.rdpcap(pcap_file)

print(f"[*] Scanning {len(packets)} packets for STUN...")

stun_count = 0
for i, pkt in enumerate(packets):
    if scapy.IP in pkt and scapy.UDP in pkt:
        payload = bytes(pkt[scapy.UDP].payload)
        
        # STUN magic cookie: 0x2112A442
        if len(payload) >= 20 and payload[0:4] == b'\x21\x12\xa4\x42':
            stun_count += 1
            if stun_count == 1:  # Show first one
                print(f"\n[+] Found STUN packet at index {i}")
                print(f"    Source: {pkt[scapy.IP].src}:{pkt[scapy.UDP].sport}")
                print(f"    Dest: {pkt[scapy.IP].dst}:{pkt[scapy.UDP].dport}")
                print(f"    Length: {len(payload)} bytes\n")
                
                print(f"    Header (20 bytes):")
                print(f"      Magic: {hexlify(payload[0:4]).decode()}")
                print(f"      Type: {hexlify(payload[4:6]).decode()}")
                print(f"      Length: {int.from_bytes(payload[6:8], 'big')}")
                print(f"      TransID: {hexlify(payload[8:20]).decode()}\n")
                
                print(f"    Attributes ({len(payload) - 20} bytes):")
                attr_offset = 20
                attr_num = 0
                while attr_offset < len(payload):
                    if attr_offset + 4 > len(payload):
                        break
                    
                    attr_type = int.from_bytes(payload[attr_offset:attr_offset+2], 'big')
                    attr_len = int.from_bytes(payload[attr_offset+2:attr_offset+4], 'big')
                    
                    print(f"      [{attr_num}] Type: 0x{attr_type:04x}, Length: {attr_len}")
                    
                    # Parse specific attribute types
                    if attr_type == 0x0006 and attr_len > 0:  # USERNAME
                        value_start = attr_offset + 4
                        value_end = value_start + attr_len
                        if value_end <= len(payload):
                            username = payload[value_start:value_end]
                            print(f"            Username: {username.decode('utf-8', errors='ignore')}")
                            print(f"            Hex: {hexlify(username).decode()}")
                    
                    elif attr_type == 0x0008 and attr_len == 20:  # MESSAGE-INTEGRITY
                        value_start = attr_offset + 4
                        integrity = payload[value_start:value_start+20]
                        print(f"            HMAC-SHA1: {hexlify(integrity).decode()}")
                    
                    elif attr_type == 0x8028 and attr_len == 4:  # FINGERPRINT
                        value_start = attr_offset + 4
                        fp = int.from_bytes(payload[value_start:value_start+4], 'big')
                        print(f"            CRC32: 0x{fp:08x}")
                    
                    elif attr_type == 0x8020:  # XOR-MAPPED-ADDRESS
                        value_start = attr_offset + 4
                        if attr_len >= 8:
                            family = int.from_bytes(payload[value_start:value_start+2], 'big')
                            xor_port = int.from_bytes(payload[value_start+2:value_start+4], 'big')
                            # Unmask port with magic cookie
                            port = xor_port ^ 0x2112
                            print(f"            XOR-MAPPED-ADDRESS port: {port}")
                            print(f"            Raw: {hexlify(payload[value_start:value_start+8]).decode()}")
                    
                    # Show all other attributes in hex
                    value_start = attr_offset + 4
                    value_end = min(value_start + attr_len, len(payload))
                    attr_hex = hexlify(payload[value_start:value_end]).decode()
                    print(f"            Data: {attr_hex}")
                    
                    # Padding to 4-byte boundary
                    padded_len = 4 + ((attr_len + 3) // 4) * 4
                    attr_offset += padded_len
                    attr_num += 1
                
                # Show raw hex of full packet for debugging
                print(f"\n    Full packet hex:")
                for j in range(0, len(payload), 32):
                    hex_line = hexlify(payload[j:j+32]).decode()
                    print(f"      {hex_line}")

print(f"\n[*] Total STUN packets found: {stun_count}")
