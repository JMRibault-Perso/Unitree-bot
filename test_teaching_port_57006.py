#!/usr/bin/env python3
"""
Test teaching protocol on port 57006 (discovered from PCAP)
"""

import sys
import asyncio
sys.path.insert(0, '/root/G1/unitree_sdk2')

from g1_app.core.udp_protocol import UDPProtocolClient

ROBOT_IP = "192.168.86.3"
TEACHING_PORT = 57006  # From PCAP: XOR-MAPPED-ADDRESS in STUN response

async def test_teaching():
    print(f"Testing teaching protocol on {ROBOT_IP}:{TEACHING_PORT}")
    print("=" * 60)

    try:
        client = UDPProtocolClient(ROBOT_IP, TEACHING_PORT)
        print(f"✅ Created UDP client for {ROBOT_IP}:{TEACHING_PORT}")
        
        print("\n🔍 Querying teaching actions...")
        actions = await client.query_actions()
        
        if actions:
            print(f"✅ SUCCESS! Found {len(actions)} teaching actions:")
            for i, action in enumerate(actions, 1):
                print(f"  {i}. {action}")
        else:
            print("⚠️  No actions returned (empty response)")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_teaching())
