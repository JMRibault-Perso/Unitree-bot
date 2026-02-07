#!/usr/bin/env python3
"""
G1 Robot Action List Viewer
Shows all available preset and custom actions

Usage:
    python3 list_actions.py
"""

import asyncio
import json
import sys
from pathlib import Path

repo_root = Path(__file__).resolve().parents[2]
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))
from robot_test_helpers import RobotTestConnection

async def main():
    async with RobotTestConnection() as robot:
        print("\n🎭 Fetching action list from robot...\n")
        
        # Subscribe to response topic
        responses = []
        def handle_response(msg):
            responses.append(msg)
        
        await robot.subscribe('rt/api/arm_action/response', handle_response)
        
        # Request action list (API 7107)
        payload = {
            'api_id': 7107,
            'parameter': '{}'
        }
        
        await robot.datachannel.pub_sub.publish_request_new(
            'rt/api/arm_action/request',
            payload
        )
        
        # Wait for response
        await asyncio.sleep(1.0)
        
        if responses:
            response = responses[-1]
            if 'data' in response and 'data' in response['data']:
                data = json.loads(response['data']['data'])
                
                if 'action_list' in data:
                    actions = data['action_list']
                    
                    print("=" * 60)
                    print(f"AVAILABLE ACTIONS ({len(actions)} total)")
                    print("=" * 60)
                    
                    # Separate preset and custom
                    preset = [a for a in actions if a.get('id', 0) < 100]
                    custom = [a for a in actions if a.get('id', 0) >= 100]
                    
                    if preset:
                        print("\n📋 Preset Actions:")
                        for action in preset:
                            print(f"  [{action.get('id', '?')}] {action.get('name', 'unnamed')}")
                    
                    if custom:
                        print("\n🎨 Custom Actions:")
                        for action in custom:
                            print(f"  [{action.get('id', '?')}] {action.get('name', 'unnamed')}")
                    
                    print("\n✅ Use these names with test_playback.py\n")
                else:
                    print("❌ No action_list in response")
            else:
                print(f"📡 Raw response: {response}")
        else:
            print("❌ No response received")

if __name__ == "__main__":
    asyncio.run(main())
