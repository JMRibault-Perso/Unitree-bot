#!/usr/bin/env python3
"""
Quick UDP Protocol Initialization Script

This script:
1. Discovers the robot on the network
2. Initializes the UDP connection
3. Queries the action list
4. Shows readiness for action playback
"""

import asyncio
import sys
from pathlib import Path

# Add workspace to path
_root = Path(__file__).parent
sys.path.insert(0, str(_root))

from g1_app.core.udp_protocol import UDPProtocolClient
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger(__name__)


async def main():
    """Main test function"""
    
    # Robot configuration
    ROBOT_IP = "192.168.86.3"  # Change if needed
    PORT = 49504
    
    logger.info("="*70)
    logger.info("UDP PROTOCOL INITIALIZATION - QUICK START")
    logger.info("="*70)
    logger.info(f"Target Robot: {ROBOT_IP}:{PORT}")
    logger.info("")
    
    # Create UDP client
    client = UDPProtocolClient(ROBOT_IP, port=PORT)
    
    try:
        # Step 1: Connect
        logger.info("STEP 1: Opening UDP socket...")
        await client.connect()
        logger.info("✅ UDP socket opened")
        logger.info("")
        
        # Step 2: Initialize
        logger.info("STEP 2: Initializing UDP connection (0x09-0x0C handshake)...")
        init_success = await client.initialize()
        
        if init_success:
            logger.info("✅ UDP initialization complete")
            logger.info("")
        else:
            logger.error("❌ UDP initialization failed")
            return
        
        # Wait a moment
        await asyncio.sleep(0.5)
        
        # Step 3: Query actions
        logger.info("STEP 3: Querying saved actions (0x1A)...")
        actions = await client.query_actions()
        
        if actions:
            logger.info(f"✅ Found {len(actions)} actions:")
            for action in actions:
                logger.info(f"   [{action['index']}] {action['name']}")
        else:
            logger.warning("⚠️  No actions found (robot may have none saved yet)")
        
        logger.info("")
        logger.info("="*70)
        logger.info("UDP PROTOCOL INITIALIZATION SUCCESSFUL ✅")
        logger.info("="*70)
        logger.info("")
        logger.info("NEXT STEPS:")
        logger.info("1. Open http://localhost:9000 in your browser")
        logger.info("2. Connect to robot via web UI")
        logger.info("3. Use web UI buttons to manually set RUN mode:")
        logger.info("   - Click 'Stand Up'")
        logger.info("   - Click 'RUN Mode'")
        logger.info("4. Then play actions via:")
        logger.info("")
        logger.info("   curl -X POST http://localhost:9000/api/udp/play_action \\")
        logger.info("     -H 'Content-Type: application/json' \\")
        logger.info("     -d '{\"action_name\": \"waist_drum_dance\"}'")
        logger.info("")
        
    except Exception as e:
        logger.error(f"❌ Error: {e}", exc_info=True)
    
    finally:
        await client.disconnect()
        logger.info("✅ UDP socket closed")


if __name__ == "__main__":
    asyncio.run(main())
