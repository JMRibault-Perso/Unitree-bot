#!/usr/bin/env python3
"""
Listen for Unitree G1 UDP telemetry on ports seen in pcap:
- Port 47707, 33280, 51042 (88-byte packets)
- These are the ports the robot sends status to
"""
import socket
import struct
import threading
import time

PORTS = [47707, 33280, 51042]

def listen_on_port(port):
    """Listen for UDP packets on a specific port"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    try:
        sock.bind(('0.0.0.0', port))
        print(f"[*] Listening on UDP port {port}")
        
        while True:
            data, addr = sock.recvfrom(1024)
            timestamp = time.strftime("%H:%M:%S")
            print(f"\n[{timestamp}] From {addr[0]}:{addr[1]} → Port {port}")
            print(f"    Length: {len(data)} bytes")
            
            # Show hex dump of first 64 bytes
            hex_str = ' '.join(f'{b:02x}' for b in data[:64])
            print(f"    Data: {hex_str}")
            
            # Try to find patterns
            if len(data) >= 8:
                # Check for magic bytes or identifiers
                magic = struct.unpack('>I', data[:4])[0]
                print(f"    First 4 bytes: 0x{magic:08x}")
                
    except Exception as e:
        print(f"[!] Error on port {port}: {e}")
    finally:
        sock.close()

def main():
    print("=" * 60)
    print("Unitree G1 Telemetry Listener")
    print("=" * 60)
    print(f"Robot IP: 192.168.86.16")
    print(f"Listening on ports: {PORTS}")
    print("Waiting for robot to send telemetry...")
    print("=" * 60)
    
    threads = []
    for port in PORTS:
        thread = threading.Thread(target=listen_on_port, args=(port,), daemon=True)
        thread.start()
        threads.append(thread)
    
    try:
        # Keep main thread alive
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\nStopped listening")

if __name__ == '__main__':
    main()
