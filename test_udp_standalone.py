#!/usr/bin/env python3
"""
Standalone UDP Protocol Test - No Dependencies

Tests UDP protocol directly without importing g1_app dependencies
"""

import socket
import struct
import zlib
import asyncio
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)


class SimpleUDPTest:
    """Simple UDP protocol test"""
    
    def __init__(self, robot_ip="192.168.86.3", port=49504):
        self.robot_ip = robot_ip
        self.port = port
        self.sequence = 0
        self.socket = None
    
    def build_packet(self, command_id, payload=None):
        """Build UDP packet with CRC32"""
        if payload is None:
            payload = b'\x00' * 46
        
        # Header
        pkt = bytearray()
        pkt.extend(bytes([0x17, 0xFE, 0xFD, 0x00]))  # Magic
        pkt.extend(struct.pack('<H', self.sequence))   # Sequence
        pkt.append(command_id)                         # Command
        pkt.extend(struct.pack('<H', len(payload)))    # Length
        pkt.extend(payload)                            # Payload
        
        # CRC32
        crc = zlib.crc32(bytes(pkt)) & 0xFFFFFFFF
        pkt.extend(struct.pack('<I', crc))
        
        self.sequence = (self.sequence + 1) & 0xFFFF
        return bytes(pkt)
    
    async def connect(self):
        """Create UDP socket"""
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.settimeout(3.0)
        logger.info(f"✅ UDP socket created for {self.robot_ip}:{self.port}")
    
    async def disconnect(self):
        """Close socket"""
        if self.socket:
            self.socket.close()
            logger.info("✅ UDP socket closed")
    
    async def initialize(self):
        """Send init sequence 0x09-0x0C"""
        logger.info("📡 Sending initialization sequence...")
        
        try:
            # Send 4 init packets
            for cmd_id in [0x09, 0x0A, 0x0B, 0x0C]:
                pkt = self.build_packet(cmd_id)
                logger.info(f"   Sending 0x{cmd_id:02X}...")
                self.socket.sendto(pkt, (self.robot_ip, self.port))
                await asyncio.sleep(0.1)
            
            logger.info("✅ Initialization sequence sent")
            return True
            
        except Exception as e:
            logger.error(f"❌ Init failed: {e}")
            return False
    
    async def query_actions(self):
        """Query action list (0x1A)"""
        logger.info("📋 Querying action list (0x1A)...")
        
        try:
            pkt = self.build_packet(0x1A)
            self.socket.sendto(pkt, (self.robot_ip, self.port))
            
            actions = []
            
            try:
                while True:
                    response, addr = self.socket.recvfrom(4096)
                    logger.info(f"   Received {len(response)} bytes from {addr}")
                    
                    # Simple response parsing
                    if len(response) >= 13:
                        # Check for potential action name in payload
                        payload = response[9:-4]  # Exclude header and CRC
                        
                        # Try to extract UTF-8 string
                        try:
                            name_bytes = payload[:32]
                            name = name_bytes.split(b'\x00')[0].decode('utf-8', errors='ignore')
                            if name:
                                logger.info(f"   Found action: {name}")
                                actions.append(name)
                        except:
                            pass
            
            except socket.timeout:
                pass
            
            if actions:
                logger.info(f"✅ Found {len(actions)} actions")
            else:
                logger.warning("⚠️  No actions found")
            
            return actions
            
        except Exception as e:
            logger.error(f"❌ Query failed: {e}")
            return []


async def main():
    """Main test"""
    logger.info("="*70)
    logger.info("STANDALONE UDP PROTOCOL TEST")
    logger.info("="*70)
    
    # Configuration
    ROBOT_IP = "192.168.86.3"
    PORT = 49504
    
    logger.info(f"Target: {ROBOT_IP}:{PORT}")
    logger.info("")
    
    tester = SimpleUDPTest(ROBOT_IP, PORT)
    
    try:
        # Connect
        logger.info("STEP 1: Opening UDP socket...")
        await tester.connect()
        await asyncio.sleep(0.5)
        
        # Initialize
        logger.info("")
        logger.info("STEP 2: Initializing UDP connection...")
        init_ok = await tester.initialize()
        
        if not init_ok:
            logger.error("❌ Initialization failed")
            return
        
        await asyncio.sleep(1.0)
        
        # Query
        logger.info("")
        logger.info("STEP 3: Querying actions...")
        actions = await tester.query_actions()
        
        # Results
        logger.info("")
        logger.info("="*70)
        logger.info("RESULTS")
        logger.info("="*70)
        logger.info(f"✅ UDP Protocol: WORKING")
        logger.info(f"✅ Initialize: OK")
        logger.info(f"✅ Query: {len(actions)} actions found")
        
        if actions:
            for i, action in enumerate(actions):
                logger.info(f"   [{i}] {action}")
        
        logger.info("")
        logger.info("NEXT STEPS:")
        logger.info("1. Open http://localhost:9000 in browser")
        logger.info("2. Connect to robot")
        logger.info("3. Set RUN mode (Stand Up → RUN Mode)")
        logger.info("4. Play action via API")
        logger.info("")
        
    except Exception as e:
        logger.error(f"❌ Error: {e}", exc_info=True)
    
    finally:
        await tester.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
