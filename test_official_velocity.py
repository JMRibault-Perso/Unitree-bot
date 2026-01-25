#!/usr/bin/env python3
"""
Test script using EXACT same code as official example
to verify robot responds to velocity commands
"""

import asyncio
import logging
import json
import sys

sys.path.insert(0, '/root/G1/go2_webrtc_connect')

from unitree_webrtc_connect.webrtc_driver import UnitreeWebRTCConnection, WebRTCConnectionMethod

# Enable debug logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    try:
        # Connect to robot (update IP if needed)
        logger.info("Connecting to robot at 192.168.86.2...")
        conn = UnitreeWebRTCConnection(WebRTCConnectionMethod.LocalSTA, ip="192.168.86.2")
        
        await conn.connect()
        logger.info("✅ Connected!")
        
        # Switch to Walk mode (500)
        logger.info("Switching to Walk mode (500)...")
        await conn.datachannel.pub_sub.publish_request_new(
            "rt/api/sport/request", 
            {
                "api_id": 7101,
                "parameter": {"data": 500}  # 500 = Walk mode
            }
        )
        await asyncio.sleep(3)
        
        # Test 1: Rotate in place (exactly like official example)
        logger.info("🎮 Test 1: Rotating in place (rx=1.0)...")
        conn.datachannel.pub_sub.publish_without_callback(
            "rt/wirelesscontroller", 
            {
                "lx": 0.0,
                "ly": 0.0,
                "rx": 1.0,  # Full rotation speed
                "ry": 0.0,
                "keys": 0
            }
        )
        await asyncio.sleep(3)
        
        # STOP
        logger.info("⏹️ Stopping...")
        conn.datachannel.pub_sub.publish_without_callback(
            "rt/wirelesscontroller", 
            {
                "lx": 0.0,
                "ly": 0.0,
                "rx": 0.0,
                "ry": 0.0,
                "keys": 0
            }
        )
        await asyncio.sleep(1)
        
        # Test 2: Move forward
        logger.info("🎮 Test 2: Moving forward (ly=0.5)...")
        conn.datachannel.pub_sub.publish_without_callback(
            "rt/wirelesscontroller", 
            {
                "lx": 0.0,
                "ly": 0.5,  # Half forward speed
                "rx": 0.0,
                "ry": 0.0,
                "keys": 0
            }
        )
        await asyncio.sleep(2)
        
        # STOP
        logger.info("⏹️ Stopping...")
        conn.datachannel.pub_sub.publish_without_callback(
            "rt/wirelesscontroller", 
            {
                "lx": 0.0,
                "ly": 0.0,
                "rx": 0.0,
                "ry": 0.0,
                "keys": 0
            }
        )
        
        logger.info("✅ Test complete! Did the robot move?")
        
        await asyncio.sleep(2)
    
    except Exception as e:
        logger.error(f"❌ Error: {e}", exc_info=True)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⏹️ Interrupted by user")
