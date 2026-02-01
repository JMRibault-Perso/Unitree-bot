#!/usr/bin/env python3
"""
Capture and display raw encrypted teaching protocol responses
"""

import sys
import asyncio
import logging
sys.path.insert(0, '/root/G1/unitree_sdk2')

from g1_app.core.udp_protocol import UDPProtocolClient, UDPPacket

ROBOT_IP = "192.168.86.3"
TEST_PORTS = [57006, 49504, 43893]

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def capture_encrypted_response(port):
    print(f"\n{'='*70}")
    print(f"Testing port {port} - Capturing RAW encrypted responses")
    print('='*70)
    
    try:
        client = UDPProtocolClient(ROBOT_IP, port)
        await client.connect()
        
        # Send query
        cmd = client.action_client.query_action_list()
        print(f"📤 Sending 0x1A query ({len(cmd)} bytes): {cmd.hex()}")
        client.socket.sendto(cmd, (ROBOT_IP, port))
        
        # Wait for responses
        client.socket.settimeout(3.0)
        response_count = 0
        
        try:
            while True:
                response, addr = client.socket.recvfrom(4096)
                response_count += 1
                
                print(f"\n📥 Response #{response_count} from {addr}:")
                print(f"   Length: {len(response)} bytes")
                print(f"   Hex: {response.hex()}")
                
                # Try to parse header
                pkt = UDPPacket.from_bytes(response)
                if pkt:
                    print(f"   ✓ Valid packet structure:")
                    print(f"     - Command: 0x{pkt.command_id:02X}")
                    print(f"     - Sequence: {pkt.sequence}")
                    print(f"     - Payload length: {pkt.payload_length}")
                    print(f"     - Payload (encrypted): {pkt.payload[:64].hex()}")
                    
                    # Try to see if there are any readable ASCII characters
                    readable = ''.join(c if 32 <= ord(c) < 127 else '.' for c in pkt.payload.decode('latin-1'))
                    print(f"     - ASCII view: {readable[:64]}")
                    
                    # Save for analysis
                    with open(f'encrypted_response_port{port}_{response_count}.bin', 'wb') as f:
                        f.write(pkt.payload)
                    print(f"     - Saved to: encrypted_response_port{port}_{response_count}.bin")
                else:
                    print(f"   ✗ Invalid packet structure")
                
        except Exception as e:
            print(f"\n⏱️  No more responses (timeout or error: {e})")
        
        print(f"\n📊 Summary for port {port}: {response_count} responses received")
        
        await client.disconnect()
        return response_count
        
    except Exception as e:
        print(f"❌ Error on port {port}: {e}")
        return 0

async def main():
    print("="*70)
    print("ENCRYPTED TEACHING PROTOCOL RESPONSE CAPTURE")
    print("="*70)
    print("This tool captures raw encrypted responses from the robot")
    print("to help analyze the encryption used in teaching mode.")
    print()
    
    total_responses = 0
    for port in TEST_PORTS:
        count = await capture_encrypted_response(port)
        total_responses += count
    
    print("\n" + "="*70)
    print("FINAL SUMMARY")
    print("="*70)
    print(f"Total encrypted responses captured: {total_responses}")
    
    if total_responses > 0:
        print("\n✅ Encrypted data captured successfully!")
        print("Next steps:")
        print("1. Check encrypted_response_*.bin files")
        print("2. Try decryption with known Unitree keys")
        print("3. Run XOR brute force analysis")
    else:
        print("\n❌ No responses received on any port")
        print("Possible issues:")
        print("- Robot not in teaching mode")
        print("- Robot has no saved actions")
        print("- Network connectivity problem")

if __name__ == "__main__":
    asyncio.run(main())
