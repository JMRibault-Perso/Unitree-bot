#!/usr/bin/env python3
"""
Listen for Unitree robot discovery broadcasts
Robot sends JSON to multicast 231.1.1.2:10134 on boot
"""
import socket
import struct
import json

MCAST_GRP = '231.1.1.2'
MCAST_PORT = 10134

def listen_for_robots():
    """Listen for robot discovery broadcasts"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    # Bind to the multicast port
    sock.bind(('', MCAST_PORT))
    
    # Join multicast group
    mreq = struct.pack("4sl", socket.inet_aton(MCAST_GRP), socket.INADDR_ANY)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
    
    print(f"Listening for Unitree robots on {MCAST_GRP}:{MCAST_PORT}...")
    print("Power on your robot to see discovery packets\n")
    
    try:
        while True:
            data, addr = sock.recvfrom(1024)
            print(f"\n[{addr[0]}:{addr[1]}]")
            try:
                robot_info = json.loads(data.decode('utf-8'))
                print(f"  Serial:   {robot_info.get('sn', 'N/A')}")
                print(f"  Name:     {robot_info.get('name', 'N/A')}")
                print(f"  IP:       {robot_info.get('ip', 'N/A')}")
                print(f"  Key:      {robot_info.get('key', 'N/A')}")
            except:
                print(f"  Raw data: {data}")
                
    except KeyboardInterrupt:
        print("\nStopped listening")
    finally:
        sock.close()

if __name__ == '__main__':
    listen_for_robots()
