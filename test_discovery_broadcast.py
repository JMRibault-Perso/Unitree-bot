#!/usr/bin/env python3
"""
Test multicast discovery by simulating robot broadcast
"""
import socket
import json
import time

MCAST_GRP = '231.1.1.2'
MCAST_PORT = 10134

def send_fake_broadcast():
    """Send a fake robot discovery broadcast to test the system"""
    
    # Robot info from the PCAP
    robot_data = {
        "sn": "E21D1000PAHBMB06", 
        "key": "", 
        "name": "unitree_dapengche",
        "ip": "192.168.86.16"
    }
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)
    
    message = json.dumps(robot_data).encode('utf-8')
    
    print(f"Broadcasting fake robot discovery to {MCAST_GRP}:{MCAST_PORT}")
    print(f"Data: {robot_data}")
    
    for i in range(3):
        sock.sendto(message, (MCAST_GRP, MCAST_PORT))
        print(f"Sent broadcast {i+1}/3")
        time.sleep(1)
    
    sock.close()
    print("Test broadcast complete")

if __name__ == '__main__':
    send_fake_broadcast()