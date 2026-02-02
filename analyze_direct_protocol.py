#!/usr/bin/env python3
"""
Analyze direct Android app <-> Robot protocol negotiation.
Focus on local communication, ignoring cloud TURN relay.
"""

from scapy.all import rdpcap, UDP, IP, TCP, Raw
import struct
import sys
from collections import defaultdict

STUN_MAGIC = 0x2112A442
TEACHING_MAGIC = b'\x17\xfe\xfd'

def is_stun_packet(payload):
    """Check if payload is a STUN packet."""
    if len(payload) < 20:
        return False
    magic = struct.unpack('!I', payload[4:8])[0]
    return magic == STUN_MAGIC

def is_teaching_protocol(payload):
    """Check if payload is teaching protocol."""
    return len(payload) >= 3 and payload[0:3] == TEACHING_MAGIC

def analyze_direct_negotiation(filename):
    print(f"{'='*80}")
    print(f"Direct Android App ↔ Robot Protocol Analysis")
    print(f"{'='*80}\n")
    
    try:
        packets = rdpcap(filename)
    except Exception as e:
        print(f"Error reading PCAP: {e}")
        return
    
    # Identify endpoints
    robot_ip = "192.168.86.3"
    phone_ips = set()
    
    # Categorize traffic
    direct_stun = []
    teaching_protocol = []
    other_udp = []
    tcp_traffic = []
    
    protocol_stats = defaultdict(int)
    
    for i, pkt in enumerate(packets):
        if IP not in pkt:
            continue
        
        src = pkt[IP].src
        dst = pkt[IP].dst
        
        # Track phone IPs (anything talking to robot that's not TURN server)
        if dst == robot_ip and not src.startswith("47.251"):
            phone_ips.add(src)
        elif src == robot_ip and not dst.startswith("47.251"):
            phone_ips.add(dst)
        
        # Skip TURN server traffic
        if "47.251.71.128" in [src, dst] or "10.215.173.1" in [src, dst]:
            continue
        
        # Analyze UDP traffic
        if UDP in pkt and Raw in pkt:
            payload = bytes(pkt[Raw].load)
            src_port = pkt[UDP].sport
            dst_port = pkt[UDP].dport
            
            # Check packet type
            if is_stun_packet(payload):
                direct_stun.append({
                    'index': i,
                    'src': f"{src}:{src_port}",
                    'dst': f"{dst}:{dst_port}",
                    'len': len(payload),
                    'payload': payload
                })
                protocol_stats['STUN (Direct ICE)'] += 1
            
            elif is_teaching_protocol(payload):
                cmd = payload[13] if len(payload) > 13 else 0
                teaching_protocol.append({
                    'index': i,
                    'src': f"{src}:{src_port}",
                    'dst': f"{dst}:{dst_port}",
                    'len': len(payload),
                    'cmd': cmd,
                    'payload': payload
                })
                protocol_stats[f'Teaching Protocol (0x{cmd:02X})'] += 1
            
            else:
                other_udp.append({
                    'index': i,
                    'src': f"{src}:{src_port}",
                    'dst': f"{dst}:{dst_port}",
                    'len': len(payload),
                    'payload': payload[:40]
                })
                protocol_stats['Other UDP'] += 1
        
        # TCP traffic
        elif TCP in pkt:
            src_port = pkt[TCP].sport
            dst_port = pkt[TCP].dport
            tcp_traffic.append({
                'index': i,
                'src': f"{src}:{src_port}",
                'dst': f"{dst}:{dst_port}",
                'flags': pkt[TCP].flags
            })
            protocol_stats['TCP'] += 1
    
    # Print summary
    print(f"Network Topology:")
    print(f"  Robot: {robot_ip}")
    print(f"  Phone/App: {', '.join(sorted(phone_ips))}")
    print()
    
    print(f"Protocol Statistics:")
    for proto, count in sorted(protocol_stats.items(), key=lambda x: -x[1]):
        print(f"  {proto:30s}: {count:5d} packets")
    print()
    
    # Analyze direct STUN negotiation
    if direct_stun:
        print(f"{'='*80}")
        print(f"Direct ICE/STUN Negotiation (Phone ↔ Robot)")
        print(f"{'='*80}\n")
        
        print(f"Total direct STUN packets: {len(direct_stun)}\n")
        
        # Show first few
        for pkt_info in direct_stun[:5]:
            print(f"Packet #{pkt_info['index']}:")
            print(f"  {pkt_info['src']} → {pkt_info['dst']}")
            print(f"  Length: {pkt_info['len']} bytes")
            
            # Parse STUN
            payload = pkt_info['payload']
            msg_type = struct.unpack('!H', payload[0:2])[0]
            txn_id = payload[8:20].hex()
            
            print(f"  Type: 0x{msg_type:04X}")
            print(f"  Transaction ID: {txn_id}")
            
            # Look for USERNAME
            offset = 20
            while offset < len(payload):
                if offset + 4 > len(payload):
                    break
                attr_type = struct.unpack('!H', payload[offset:offset+2])[0]
                attr_len = struct.unpack('!H', payload[offset+2:offset+4])[0]
                
                if attr_type == 0x0006:  # USERNAME
                    username = payload[offset+4:offset+4+attr_len].decode('utf-8', errors='ignore')
                    print(f"  Username: {username}")
                    break
                
                offset += 4 + attr_len
                if attr_len % 4:
                    offset += 4 - (attr_len % 4)
            
            print()
    
    # Analyze teaching protocol
    if teaching_protocol:
        print(f"{'='*80}")
        print(f"Teaching Protocol Packets (Phone ↔ Robot)")
        print(f"{'='*80}\n")
        
        print(f"Total teaching protocol packets: {len(teaching_protocol)}\n")
        
        # Group by command
        by_cmd = defaultdict(list)
        for pkt in teaching_protocol:
            by_cmd[pkt['cmd']].append(pkt)
        
        print("Commands observed:")
        for cmd in sorted(by_cmd.keys()):
            cmd_name = {
                0x1A: "GET_ACTION_LIST",
                0x41: "PLAY_ACTION",
                0x42: "DELETE_ACTION",
                0x43: "RENAME_ACTION"
            }.get(cmd, f"UNKNOWN")
            
            print(f"  0x{cmd:02X} ({cmd_name:20s}): {len(by_cmd[cmd]):5d} packets")
        print()
        
        # Show first packet of each command type
        print("Sample packets:")
        for cmd in sorted(by_cmd.keys())[:4]:
            pkt_info = by_cmd[cmd][0]
            cmd_name = {
                0x1A: "GET_ACTION_LIST",
                0x41: "PLAY_ACTION",
                0x42: "DELETE_ACTION",
                0x43: "RENAME_ACTION"
            }.get(cmd, f"UNKNOWN")
            
            print(f"\nCommand 0x{cmd:02X} ({cmd_name}):")
            print(f"  Packet #{pkt_info['index']}")
            print(f"  {pkt_info['src']} → {pkt_info['dst']}")
            print(f"  Length: {pkt_info['len']} bytes")
            print(f"  First 40 bytes: {pkt_info['payload'][:40].hex()}")
    
    # Analyze TCP
    if tcp_traffic:
        print(f"\n{'='*80}")
        print(f"TCP Traffic (Phone ↔ Robot)")
        print(f"{'='*80}\n")
        
        # Group by port
        port_pairs = defaultdict(int)
        for pkt in tcp_traffic:
            port_pairs[f"{pkt['src']} ↔ {pkt['dst']}"] += 1
        
        print("TCP connections:")
        for pair, count in sorted(port_pairs.items(), key=lambda x: -x[1])[:10]:
            print(f"  {pair:50s}: {count:5d} packets")
        print()
    
    # Timeline analysis
    print(f"\n{'='*80}")
    print(f"Protocol Negotiation Timeline")
    print(f"{'='*80}\n")
    
    print("Typical sequence:")
    print("1. STUN Binding Requests (ICE negotiation)")
    print("   - Phone and robot exchange ICE candidates")
    print("   - Discover direct connection path")
    print("   - Establish DTLS tunnel")
    print()
    print("2. WebRTC Datachannel Opened")
    print("   - DTLS handshake completes")
    print("   - Teaching protocol channel established")
    print()
    print("3. Teaching Protocol Commands")
    print("   - GET_ACTION_LIST (0x1A) - Query available actions")
    print("   - PLAY_ACTION (0x41) - Execute action")
    print("   - DELETE_ACTION (0x42) - Remove action")
    print("   - RENAME_ACTION (0x43) - Rename action")
    print()
    
    print(f"\n{'='*80}")
    print(f"Key Findings for PC Controller Implementation")
    print(f"{'='*80}\n")
    
    print("Required Components:")
    print("  1. WebRTC client (aiortc, peerjs, etc.)")
    print("  2. ICE negotiation with robot")
    print("  3. DTLS encryption/decryption")
    print("  4. Teaching protocol encoder/decoder")
    print()
    
    print("Known Protocol Details:")
    print("  • Magic Header: 17 FE FD")
    print("  • Command at offset 13")
    print("  • Action names XOR-encrypted")
    print("  • STUN credentials: Snxa:59Cu (local)")
    print("  • Direct UDP connection (no TURN needed if on same network)")
    print()
    
    print("Next Steps:")
    print("  1. Implement WebRTC datachannel client")
    print("  2. Replicate ICE negotiation (offer/answer)")
    print("  3. Build teaching protocol packet encoder")
    print("  4. Test direct connection to robot")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python analyze_direct_protocol.py <pcap_file>")
        sys.exit(1)
    
    analyze_direct_negotiation(sys.argv[1])
