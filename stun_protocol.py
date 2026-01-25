#!/usr/bin/env python3
"""
Decode Unitree G1 local control protocol (STUN-based WebRTC)

Based on packet analysis from g1-android.pcapng:
- Phone → Robot: 100-byte UDP packets (commands)
- Robot → Phone: 88-byte UDP packets (telemetry)
- Protocol: STUN (RFC 5389) with custom attributes
"""

import socket
import struct

# From pcap analysis
ROBOT_IP = "192.168.86.16"
ROBOT_PORT = 44932  # Robot listens on this port
PHONE_PORT = 37601  # Phone sends from this port

def decode_stun_packet(data):
    """Decode STUN packet structure"""
    if len(data) < 20:
        return None
    
    # STUN header
    msg_type = struct.unpack('>H', data[0:2])[0]
    msg_length = struct.unpack('>H', data[2:4])[0]
    magic_cookie = struct.unpack('>I', data[4:8])[0]
    transaction_id = data[8:20].hex()
    
    if magic_cookie != 0x2112A442:
        return None  # Not a STUN packet
    
    result = {
        'type': msg_type,
        'length': msg_length,
        'transaction_id': transaction_id,
        'attributes': []
    }
    
    # Parse attributes
    offset = 20
    while offset < len(data):
        if offset + 4 > len(data):
            break
            
        attr_type = struct.unpack('>H', data[offset:offset+2])[0]
        attr_length = struct.unpack('>H', data[offset+2:offset+4])[0]
        
        if offset + 4 + attr_length > len(data):
            break
            
        attr_value = data[offset+4:offset+4+attr_length]
        
        result['attributes'].append({
            'type': hex(attr_type),
            'length': attr_length,
            'value': attr_value.hex()
        })
        
        # Attributes are padded to 4-byte boundary
        offset += 4 + ((attr_length + 3) // 4) * 4
    
    return result

def create_stun_packet(transaction_id=None):
    """Create a STUN Binding Request packet"""
    import os
    
    if transaction_id is None:
        transaction_id = os.urandom(12)
    
    # STUN Binding Request
    msg_type = 0x0001
    msg_length = 0x0050  # 80 bytes of attributes (from captured packets)
    magic_cookie = 0x2112A442
    
    packet = struct.pack('>HHI', msg_type, msg_length, magic_cookie)
    packet += transaction_id
    
    # Add USERNAME attribute (0x0006) - "CqNH:E4v3"
    username = b"CqNH:E4v3"
    packet += struct.pack('>HH', 0x0006, len(username))
    packet += username
    packet += b'\x00' * (4 - len(username) % 4)  # Padding
    
    # Add custom attribute (0xC057) - observed in captures
    packet += struct.pack('>HHI', 0xC057, 4, 0x000003E7)
    
    # Add other attributes as needed...
    # (Would need to reverse-engineer the exact command format)
    
    return packet

def listen_for_telemetry(port=37601):
    """Listen for robot telemetry packets"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(('0.0.0.0', port))
    
    print(f"Listening for telemetry on port {port}...")
    
    while True:
        data, addr = sock.recvfrom(1024)
        print(f"\nFrom {addr}: {len(data)} bytes")
        
        stun_data = decode_stun_packet(data)
        if stun_data:
            print(f"  STUN Type: 0x{stun_data['type']:04x}")
            print(f"  Transaction ID: {stun_data['transaction_id']}")
            print(f"  Attributes: {len(stun_data['attributes'])}")
            for attr in stun_data['attributes']:
                print(f"    {attr['type']}: {attr['value'][:40]}...")
        else:
            print(f"  Hex: {data.hex()[:80]}...")

def send_command(command_data=None):
    """Send a command packet to the robot"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(('0.0.0.0', PHONE_PORT))
    
    if command_data is None:
        # Create a basic STUN packet
        command_data = create_stun_packet()
    
    sock.sendto(command_data, (ROBOT_IP, ROBOT_PORT))
    print(f"Sent {len(command_data)} bytes to {ROBOT_IP}:{ROBOT_PORT}")

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == 'listen':
        listen_for_telemetry()
    elif len(sys.argv) > 1 and sys.argv[1] == 'send':
        send_command()
    else:
        print("Usage:")
        print("  python3 stun_protocol.py listen  # Listen for telemetry")
        print("  python3 stun_protocol.py send    # Send test command")
        print("\nPacket analysis from g1-android.pcapng:")
        print("  Phone → Robot: 100-byte STUN packets @ 2Hz")
        print("  Robot → Phone: 88-byte STUN packets @ 20Hz")
        print("  Magic Cookie: 0x2112A442 (STUN RFC 5389)")
        print("  Username attr: 'CqNH:E4v3' (session identifier)")
