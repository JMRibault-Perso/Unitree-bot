#!/usr/bin/env python3
"""
Scan multiple ports to find the teaching service
"""

import sys
import asyncio
sys.path.insert(0, '/root/G1/unitree_sdk2')

from g1_app.core.udp_protocol import UDPProtocolClient

ROBOT_IP = "192.168.86.3"
TEST_PORTS = [57006, 49504, 43893, 51639, 45559]  # Ports from PCAP and previous tests

async def test_port(port):
    try:
        print(f"\n{'='*60}")
        print(f"Testing port {port}...")
        print('='*60)
        
        client = UDPProtocolClient(ROBOT_IP, port)
        actions = await client.query_actions()
        
        if actions:
            print(f"✅ Port {port}: Found {len(actions)} actions!")
            for i, action in enumerate(actions, 1):
                print(f"  {i}. {action}")
            return port
        else:
            print(f"⚠️  Port {port}: No actions (empty response)")
            return None
            
    except Exception as e:
        print(f"❌ Port {port}: Error - {e}")
        return None

async def main():
    print(f"Scanning {len(TEST_PORTS)} ports for teaching service...")
    
    working_ports = []
    for port in TEST_PORTS:
        result = await test_port(port)
        if result:
            working_ports.append(result)
    
    print(f"\n\n{'='*60}")
    print("SUMMARY")
    print('='*60)
    if working_ports:
        print(f"✅ Teaching service found on: {working_ports}")
    else:
        print("❌ No teaching service found on any port")

if __name__ == "__main__":
    asyncio.run(main())
