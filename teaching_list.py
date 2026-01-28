#!/usr/bin/env python3
"""
Simple teaching mode list command via UDP
"""

import socket
import struct
import zlib
import time

def build_list_teaching_packet():
    """Build a 0x1A packet to query teaching actions"""
    packet = bytearray()
    
    # Header (13 bytes)
    packet.append(0x17)                    # Message type
    packet.extend([0xFE, 0xFD, 0x00])     # Magic
    packet.extend([0x01, 0x00])            # Flags
    packet.extend([0x00, 0x00])            # Sequence
    packet.extend([0x00, 0x00])            # Reserved
    packet.extend([0x00, 0x01])            # Reserved
    packet.append(0x1A)                    # Command ID: LIST
    
    # Payload (44 bytes standard)
    payload = bytes(44)
    packet.extend(struct.pack('>H', len(payload)))  # Payload length
    packet.extend(payload)
    
    # CRC32 checksum
    crc = zlib.crc32(packet) & 0xFFFFFFFF
    packet.extend(struct.pack('>I', crc))
    
    return bytes(packet)

def send_list_command(robot_ip: str, port: int = 49504, timeout: int = 3):
    """Send list teaching command and wait for response"""
    packet = build_list_teaching_packet()
    
    print(f"Building 0x1A (LIST) packet: {len(packet)} bytes")
    print(f"Hex: {packet.hex()}")
    print(f"\nSending to {robot_ip}:{port}...")
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(timeout)
    
    try:
        # Send command
        sock.sendto(packet, (robot_ip, port))
        print(f"✅ Packet sent")
        
        # Wait for response
        print(f"\nWaiting for response (timeout={timeout}s)...")
        while True:
            try:
                data, addr = sock.recvfrom(4096)
                print(f"\n✅ Response received from {addr[0]}:{addr[1]}")
                print(f"   Size: {len(data)} bytes")
                print(f"   Hex: {data.hex()[:200]}")
                return data
            except socket.timeout:
                break
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        sock.close()

if __name__ == "__main__":
    import sys
    
    robot_ip = sys.argv[1] if len(sys.argv) > 1 else "192.168.86.2"
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 49504
    
    send_list_command(robot_ip, port)
