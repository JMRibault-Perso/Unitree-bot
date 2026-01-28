#!/usr/bin/env python3
"""
Debug script to inspect raw UDP response from 0x42 query
"""

import asyncio
import logging
import sys
import socket
import struct

sys.path.insert(0, '/root/G1/unitree_sdk2')

from g1_app.core.udp_commands import UDPCommandBuilder

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)


async def main():
    """Test Get/List Actions command with raw response inspection"""
    
    robot_ip = "192.168.86.8"
    robot_port = 43893
    
    logger.info("=" * 80)
    logger.info("UDP DEBUG: Get/List Actions (0x42) - Raw Response Inspection")
    logger.info("=" * 80)
    logger.info("")
    
    try:
        # Build command
        builder = UDPCommandBuilder()
        query_cmd = builder.get_list_actions()
        
        logger.info(f"Sending command ({len(query_cmd)} bytes):")
        logger.info(f"  Hex: {query_cmd.hex()}")
        logger.info("")
        
        # Send raw UDP
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(3.0)
        
        logger.info(f"📤 Sending to {robot_ip}:{robot_port}")
        sock.sendto(query_cmd, (robot_ip, robot_port))
        
        # Receive response
        logger.info("⏳ Waiting for response (3 second timeout)...")
        response, addr = sock.recvfrom(4096)
        
        logger.info("")
        logger.info("=" * 80)
        logger.info("RAW RESPONSE:")
        logger.info("=" * 80)
        logger.info(f"Source: {addr}")
        logger.info(f"Size: {len(response)} bytes")
        logger.info("")
        
        # Show hex dump
        logger.info("Hex dump (16 bytes per line):")
        for i in range(0, len(response), 16):
            hex_part = ' '.join(f'{b:02x}' for b in response[i:i+16])
            ascii_part = ''.join(chr(b) if 32 <= b < 127 else '.' for b in response[i:i+16])
            logger.info(f"  0x{i:02x}: {hex_part:<48} {ascii_part}")
        
        logger.info("")
        
        # Parse header
        logger.info("Header analysis:")
        if len(response) >= 0x20:
            logger.info(f"  Bytes 0x00-0x03: {response[0x00:0x04].hex()} (should be FE FD 00 XX)")
            logger.info(f"  Bytes 0x04-0x0F: {response[0x04:0x10].hex()} (reserved?)")
            logger.info(f"  Bytes 0x10-0x13: {struct.unpack('<I', response[0x10:0x14])[0]:08x} (sequence?)")
            logger.info(f"  Bytes 0x14-0x17: {struct.unpack('<I', response[0x14:0x18])[0]:02x} (cmd ID?)")
            logger.info(f"  Bytes 0x18-0x1B: {response[0x18:0x1C].hex()} (unknown?)")
            logger.info(f"  Bytes 0x1C-0x1F: {response[0x1C:0x20].hex()} (header? 01 01 00 38?)")
        
        logger.info("")
        
        # Check for action data
        if len(response) > 0x20:
            logger.info(f"Data section starts at 0x20, length: {len(response) - 0x20} bytes")
            logger.info(f"Expected structure per action: 76 bytes (0x4C bytes)")
            
            # Try to identify action boundaries
            action_count = (len(response) - 0x20) // 76
            logger.info(f"Potential action count: {action_count}")
            
            if action_count > 0:
                logger.info("")
                for act_idx in range(min(action_count, 3)):  # Show first 3
                    offset = 0x20 + (act_idx * 76)
                    logger.info(f"\nAction {act_idx}:")
                    logger.info(f"  Offset: 0x{offset:02x}")
                    logger.info(f"  Bytes 0x{offset:02x}-0x{offset+4:02x}: {response[offset:offset+4].hex()}")
                    logger.info(f"  Bytes 0x{offset+4:02x}-0x{offset+20:02x} (name?): {response[offset+4:offset+20].hex()}")
        
        sock.close()
        
    except socket.timeout:
        logger.error("❌ Socket timeout - robot did not respond")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
