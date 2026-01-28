#!/usr/bin/env python3
"""
Test script for UDP Get/List Actions (0x42) command
SAFE OPERATION: Read-only query, no state changes
"""

import asyncio
import logging
import sys
import socket

sys.path.insert(0, '/root/G1/unitree_sdk2')
from g1_app.core.udp_commands import UDPClient

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(name)s: %(message)s')
logger = logging.getLogger(__name__)


async def discover_robot() -> str:
    """Discover robot IP by MAC address"""
    robot_mac = "fc:23:cd:92:60:02"
    logger.info(f"🔍 Discovering robot by MAC: {robot_mac}")
    
    # Check ARP cache
    try:
        result = await asyncio.create_subprocess_shell(
            f"arp -n | grep -i '{robot_mac}' | awk '{{print $1}}'",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, _ = await result.communicate()
        if stdout:
            ip = stdout.decode().strip()
            if ip:
                logger.info(f"✅ Found robot at {ip}")
                return ip
    except Exception:
        pass
    
    raise Exception("Robot not found. Is it powered on?")


async def main():
    """Test Get/List Actions command"""
    
    logger.info("=" * 80)
    logger.info("UDP Query Test: Get/List Actions (0x42)")
    logger.info("=" * 80)
    logger.info("")
    
    try:
        robot_ip = await discover_robot()
    except Exception as e:
        logger.error(f"❌ {e}")
        sys.exit(1)
    
    logger.info("")
    logger.info("SAFE OPERATION: Read-only query")
    logger.info("")
    
    try:
        client = UDPClient(robot_ip)
        await client.connect()
        actions = await client.query_actions()
        
        logger.info("")
        logger.info("=" * 80)
        logger.info("RESULTS:")
        logger.info("=" * 80)
        logger.info(f"Total saved actions: {len(actions)}")
        logger.info("")
        
        if actions:
            for i, action in enumerate(actions, 1):
                logger.info(f"\nAction {i}:")
                logger.info(f"  Encrypted name: {action['encrypted_name'].hex()}")
                logger.info(f"  Timestamp: {action['timestamp']}")
                logger.info(f"  Checksum: {action['checksum'].hex()}")
        else:
            logger.info("No saved actions found")
        
        await client.disconnect()
        
    except Exception as e:
        logger.error(f"Test failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
