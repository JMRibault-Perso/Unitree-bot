#!/usr/bin/env python3
"""
Test which topics are actually available on the G1 Air robot.
Tests all topics defined in constants.RTC_TOPIC.
"""

import asyncio
import sys
import logging

sys.path.insert(0, '/root/G1/go2_webrtc_connect')
from unitree_webrtc_connect.webrtc_driver import UnitreeWebRTCConnection, WebRTCConnectionMethod
from unitree_webrtc_connect.constants import RTC_TOPIC

logging.basicConfig(level=logging.WARNING)

async def test_topic(conn, topic_name, topic_path):
    """Try to subscribe to a topic and see if it's valid"""
    try:
        # Try to subscribe
        def dummy_callback(msg):
            pass
        
        conn.datachannel.pub_sub.subscribe(topic_path, dummy_callback)
        await asyncio.sleep(0.5)  # Wait for potential error response
        
        # If we get here without error, topic might be valid
        return True
    except Exception as e:
        return False

async def main():
    try:
        print("🔌 Connecting to G1 Air robot...")
        conn = UnitreeWebRTCConnection(WebRTCConnectionMethod.LocalSTA, ip="192.168.86.18")
        await conn.connect()
        print("✅ Connected!\n")
        
        await conn.datachannel.disableTrafficSaving(True)
        
        print("📋 Testing all topics from RTC_TOPIC constants...\n")
        print(f"{'Topic Name':<30} {'Topic Path':<50} {'Status'}")
        print("=" * 90)
        
        valid_topics = []
        invalid_topics = []
        
        # Test each topic
        for name, path in RTC_TOPIC.items():
            # Skip testing - just subscribe and see what happens
            result = await test_topic(conn, name, path)
            
            # For display purposes, we'll just list them all
            print(f"{name:<30} {path:<50} ❓ Unknown")
            
        print("\n" + "=" * 90)
        print(f"\n📊 Total topics defined: {len(RTC_TOPIC)}")
        print(f"\nℹ️  Note: To actually test which topics are available, we need to:")
        print("   1. Subscribe to each topic")
        print("   2. Try to publish to it (if it's a command topic)")
        print("   3. Listen for error messages from the robot")
        print("\n   The robot will respond with 'Invalid Topic.xx' if unavailable.")
        
        # Now let's try the LiDAR topics specifically
        print("\n\n🔍 Testing LiDAR topics specifically...\n")
        
        lidar_topics = {
            "ULIDAR_SWITCH": "rt/utlidar/switch",
            "ULIDAR": "rt/utlidar/voxel_map",
            "ULIDAR_ARRAY": "rt/utlidar/voxel_map_compressed",
            "ULIDAR_STATE": "rt/utlidar/lidar_state",
            "ROBOTODOM": "rt/utlidar/robot_pose",
        }
        
        for name, path in lidar_topics.items():
            print(f"Testing {name} ({path})...")
            
            # Try to publish to switch (if it's the switch topic)
            if "switch" in path:
                conn.datachannel.pub_sub.publish_without_callback(path, "on")
                await asyncio.sleep(0.5)
            else:
                # Try to subscribe
                def test_cb(msg):
                    print(f"  ✅ Received data on {path}!")
                conn.datachannel.pub_sub.subscribe(path, test_cb)
                await asyncio.sleep(0.5)
        
        print("\n⏳ Waiting 5 seconds for any responses...")
        await asyncio.sleep(5)
        
        print("\n✅ Test complete!")
        
    except Exception as e:
        logging.error(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⚠️ Interrupted by user")
        sys.exit(0)
