#!/usr/bin/env python3
"""Direct test of multicast discovery listening"""
import socket
import struct
import time
import sys

MCAST_GRP = '231.1.1.2'
MCAST_PORT = 10134
MULTICAST_TTL = 2

def test_multicast_listen():
    print(f"🔍 Listening for multicast on {MCAST_GRP}:{MCAST_PORT}...")
    print("   (Waiting 10 seconds for robot broadcasts)\n")
    
    # Create UDP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    # Bind to the multicast port
    sock.bind(('', MCAST_PORT))
    
    # Join multicast group on any interface
    try:
        group_bin = socket.inet_aton(MCAST_GRP)
        mreq = struct.pack('4sL', group_bin, socket.INADDR_ANY)
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
    except Exception as e:
        print(f"❌ Failed to join multicast group: {e}")
        return False
    
    # Set timeout to 15 seconds
    sock.settimeout(15)
    
    packets_received = 0
    robot_ips = set()
    
    try:
        while True:
            try:
                data, (src_ip, src_port) = sock.recvfrom(1024)
                packets_received += 1
                robot_ips.add(src_ip)
                
                print(f"✅ Packet {packets_received} from {src_ip}:{src_port}")
                print(f"   Data (first 100 bytes): {data[:100]}")
                print(f"   Data (hex): {data[:50].hex()}\n")
                
            except socket.timeout:
                break
                
    except KeyboardInterrupt:
        print("\n⏹️  Interrupted by user")
    finally:
        sock.close()
    
    print(f"\n📊 Results:")
    print(f"   Total packets received: {packets_received}")
    print(f"   Unique robot IPs: {robot_ips if robot_ips else 'NONE'}")
    
    if packets_received == 0:
        print("\n⚠️  No multicast packets received!")
        print("   This could mean:")
        print("   1. Robot is not broadcasting (check if it's powered on and in correct mode)")
        print("   2. Multicast is blocked by firewall/network settings")
        print("   3. Network interface is not configured correctly")
        print("   4. Robot is not on the same network")
        return False
    
    return True

if __name__ == '__main__':
    try:
        success = test_multicast_listen()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
