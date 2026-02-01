#!/usr/bin/env python3
"""
Analyze teaching mode PCAP to find port discovery mechanism
"""

import sys
import struct

def parse_pcap(filename):
    """Parse PCAP file and find teaching protocol packets"""
    
    with open(filename, 'rb') as f:
        # Skip PCAP global header (24 bytes)
        f.read(24)
        
        packet_num = 0
        teaching_packets = []
        stun_packets = []
        
        while True:
            # Read packet header (16 bytes)
            pkt_header = f.read(16)
            if len(pkt_header) < 16:
                break
                
            ts_sec, ts_usec, incl_len, orig_len = struct.unpack('IIII', pkt_header)
            
            # Read packet data
            packet_data = f.read(incl_len)
            packet_num += 1
            
            # Skip Ethernet header (14 bytes) + IP header (20 bytes) + UDP header (8 bytes) = 42 bytes minimum
            if len(packet_data) < 42:
                continue
            
            # Parse UDP payload
            udp_payload = packet_data[42:]
            
            # Check for teaching protocol (starts with 17 fe fd)
            if len(udp_payload) >= 3 and udp_payload[0:3] == b'\x17\xfe\xfd':
                # Parse IP addresses and ports from packet
                ip_header = packet_data[14:34]
                src_ip = '.'.join(str(b) for b in ip_header[12:16])
                dst_ip = '.'.join(str(b) for b in ip_header[16:20])
                
                udp_header = packet_data[34:42]
                src_port = struct.unpack('!H', udp_header[0:2])[0]
                dst_port = struct.unpack('!H', udp_header[2:4])[0]
                
                teaching_packets.append({
                    'packet_num': packet_num,
                    'time': f"{ts_sec}.{ts_usec:06d}",
                    'src': f"{src_ip}:{src_port}",
                    'dst': f"{dst_ip}:{dst_port}",
                    'size': len(udp_payload),
                    'data': udp_payload[:16].hex()
                })
            
            # Check for STUN packets (starts with 00 01 or 01 01 followed by message type)
            # STUN binding request/response has magic cookie 0x2112a442
            if len(udp_payload) >= 20:
                if udp_payload[4:8] == b'\x21\x12\xa4\x42':
                    ip_header = packet_data[14:34]
                    src_ip = '.'.join(str(b) for b in ip_header[12:16])
                    dst_ip = '.'.join(str(b) for b in ip_header[16:20])
                    
                    udp_header = packet_data[34:42]
                    src_port = struct.unpack('!H', udp_header[0:2])[0]
                    dst_port = struct.unpack('!H', udp_header[2:4])[0]
                    
                    stun_packets.append({
                        'packet_num': packet_num,
                        'time': f"{ts_sec}.{ts_usec:06d}",
                        'src': f"{src_ip}:{src_port}",
                        'dst': f"{dst_ip}:{dst_port}",
                        'size': len(udp_payload),
                        'type': udp_payload[0:2].hex()
                    })
        
        return teaching_packets, stun_packets

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: analyze_teaching_port.py <pcap_file>")
        sys.exit(1)
    
    teaching_pkts, stun_pkts = parse_pcap(sys.argv[1])
    
    print("=" * 80)
    print("STUN PACKETS (WebRTC port discovery)")
    print("=" * 80)
    for pkt in stun_pkts[:10]:  # Show first 10 STUN packets
        print(f"[{pkt['packet_num']:4d}] {pkt['time']:15s} {pkt['src']:25s} -> {pkt['dst']:25s} (type={pkt['type']})")
    
    print(f"\n... Total {len(stun_pkts)} STUN packets\n")
    
    print("=" * 80)
    print("TEACHING PROTOCOL PACKETS (17 fe fd)")
    print("=" * 80)
    for pkt in teaching_pkts:
        print(f"[{pkt['packet_num']:4d}] {pkt['time']:15s} {pkt['src']:25s} -> {pkt['dst']:25s} size={pkt['size']:3d} data={pkt['data']}")
    
    print(f"\n... Total {len(teaching_pkts)} teaching packets")
    
    # Find port discovery: check if teaching packets came after STUN
    if stun_pkts and teaching_pkts:
        first_stun = int(stun_pkts[0]['packet_num'])
        first_teaching = int(teaching_pkts[0]['packet_num'])
        
        print("\n" + "=" * 80)
        print("ANALYSIS")
        print("=" * 80)
        print(f"First STUN packet: #{first_stun}")
        print(f"First teaching packet: #{first_teaching}")
        
        if first_stun < first_teaching:
            print("\n✅ STUN happened BEFORE teaching protocol")
            print("   → Port 51639 was likely negotiated via WebRTC/STUN")
        else:
            print("\n⚠️  Teaching protocol started before STUN")
            print("   → Port may be hardcoded or discovered differently")
        
        # Extract robot port from teaching packets
        robot_ports = set()
        for pkt in teaching_pkts:
            if '192.168.86.3' in pkt['src']:
                port = pkt['src'].split(':')[1]
                robot_ports.add(port)
        
        print(f"\nRobot UDP ports used: {', '.join(robot_ports)}")
