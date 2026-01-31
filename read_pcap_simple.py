#!/usr/bin/env python3
from scapy.all import rdpcap

packets = rdpcap('PCAPdroid_30_Jan_18_26_35.pcap')
print(f'Total packets: {len(packets)}')

# Get unique flows
from collections import defaultdict
flows = defaultdict(list)

for i, pkt in enumerate(packets):
    src = pkt.src if hasattr(pkt, 'src') else 'unknown'
    dst = pkt.dst if hasattr(pkt, 'dst') else 'unknown'
    sport = pkt.sport if hasattr(pkt, 'sport') else 'unknown'
    dport = pkt.dport if hasattr(pkt, 'dport') else 'unknown'
    
    flow_key = f"{src}:{sport} -> {dst}:{dport}"
    flows[flow_key].append(i)

print("\nNetwork flows:")
for flow, packet_indices in sorted(flows.items()):
    print(f"  {flow}: {len(packet_indices)} packets")

# Print first 10 packets with detail
print("\nFirst 10 packets:")
for i, pkt in enumerate(packets[:10]):
    print(f"{i}: {pkt.summary()}")
    if hasattr(pkt, 'payload') and len(bytes(pkt.payload)) > 0:
        payload = bytes(pkt.payload)[:50]
        print(f"   Payload (first 50 bytes): {payload.hex()}")
