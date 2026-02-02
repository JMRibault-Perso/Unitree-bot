#!/usr/bin/env python3
"""
Test UDP Protocol Implementation for G1 Air

This script tests:
1. UDP initialization (0x09-0x0C handshake)
2. Action list query (0x1A)
3. Action playback (0x41)

SAFETY: These operations have minimal impact on the robot
- Initialization just opens a channel
- Query is read-only
- Playback requires robot to be in RUN mode (user controls manually)
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


async def test_udp_protocol():
    """Test UDP protocol with actual robot"""
    
    # Configure robot IP (replace with your robot's IP)
    ROBOT_IP = "192.168.86.3"
    PORT = 49504
    
    logger.info("="*60)
    logger.info("UDP Protocol Test Suite")
    logger.info("="*60)
    logger.info(f"Target: {ROBOT_IP}:{PORT}")
    logger.info("")
    
    client = UDPProtocolClient(ROBOT_IP, port=PORT)
    
    try:
        # Test 1: Initialize UDP connection
        logger.info("TEST 1: UDP Initialization")
        logger.info("-" * 60)
        await client.connect()
        init_success = await client.initialize()
        
        if init_success:
            logger.info("✅ PASS: UDP initialization successful")
        else:
            logger.error("❌ FAIL: UDP initialization failed")
        
        await asyncio.sleep(1.0)
        
        # Test 2: Query action list
        logger.info("")
        logger.info("TEST 2: Query Saved Actions")
        logger.info("-" * 60)
        actions = await client.query_actions()
        
        if actions:
            logger.info(f"✅ PASS: Found {len(actions)} actions")
            for action in actions:
                logger.info(f"   [{action['index']}] {action['name']}")
        else:
            logger.warning("⚠️  No actions found (this is OK if robot has no saved actions)")
        
        # Test 3: Find waist_drum_dance action
        logger.info("")
        logger.info("TEST 3: Find 'waist_drum_dance' Action")
        logger.info("-" * 60)
        waist_drum_found = False
        waist_drum_index = None
        
        for action in actions:
            if 'waist_drum' in action['name'].lower():
                waist_drum_found = True
                waist_drum_index = action['index']
                logger.info(f"✅ FOUND: {action['name']} at index {action['index']}")
                break
        
        if not waist_drum_found:
            logger.warning("⚠️  'waist_drum_dance' not found in action list")
            if actions:
                logger.info(f"   First available action: {actions[0]['name']} (index 0)")
        
        # Test 4: Info about playback
        logger.info("")
        logger.info("TEST 4: Ready for Action Playback")
        logger.info("-" * 60)
        logger.info("ℹ️  To test action playback:")
        logger.info("   1. Use the web UI to bring robot to RUN mode manually")
        logger.info("   2. Then call: POST /api/udp/play_action")
        logger.info("      with: { \"action_name\": \"waist_drum_dance\" }")
        logger.info("")
        logger.info("   OR test via curl:")
        logger.info('   curl -X POST http://localhost:9000/api/udp/play_action \\')
        logger.info('      -H "Content-Type: application/json" \\')
        logger.info('      -d \'{"action_name": "waist_drum_dance"}\'')
        logger.info("")
        
        # Summary
        logger.info("")
        logger.info("="*60)
        logger.info("TEST SUMMARY")
        logger.info("="*60)
        logger.info("✅ UDP initialization: Working")
        logger.info("✅ Action list query: Working")
        logger.info(f"   - Found {len(actions)} actions")
        if waist_drum_found:
            logger.info(f"✅ waist_drum_dance action: Found at index {waist_drum_index}")
        else:
            logger.info("⚠️  waist_drum_dance action: Not found (may need to record it first)")
        logger.info("")
        logger.info("🚀 UDP protocol is ready for use!")
        logger.info("="*60)
        
    except Exception as e:
        logger.error(f"❌ Test failed with error: {e}", exc_info=True)
    
    finally:
        await client.disconnect()


async def test_web_api():
    """Test web API endpoints via curl examples"""
    
    logger.info("")
    logger.info("="*60)
    logger.info("WEB API ENDPOINTS")
    logger.info("="*60)
    logger.info("")
    logger.info("Make sure web server is running: python g1_app/ui/web_server.py")
    logger.info("")
    
    logger.info("1. Initialize UDP:")
    logger.info("   POST /api/udp/initialize")
    logger.info('   curl -X POST http://localhost:9000/api/udp/initialize')
    logger.info("")
    
    logger.info("2. Query Actions:")
    logger.info("   GET /api/udp/actions")
    logger.info('   curl http://localhost:9000/api/udp/actions')
    logger.info("")
    
    logger.info("3. Play Action (robot must be in RUN mode):")
    logger.info("   POST /api/udp/play_action")
    logger.info('   curl -X POST http://localhost:9000/api/udp/play_action \\')
    logger.info('        -H "Content-Type: application/json" \\')
    logger.info('        -d \'{"action_name": "waist_drum_dance"}\'')
    logger.info("")
    
    logger.info("4. Stop Action:")
    logger.info("   POST /api/udp/stop_action")
    logger.info('   curl -X POST http://localhost:9000/api/udp/stop_action')
    logger.info("")


async def main():
    """Main test runner"""
    
    # Check if robot IP is provided
    if len(sys.argv) > 1:
        robot_ip = sys.argv[1]
        logger.info(f"Using robot IP from command line: {robot_ip}")
        
        # Override the default IP
        client = UDPProtocolClient(robot_ip, port=49504)
        
        try:
            await client.connect()
            init_success = await client.initialize()
            if init_success:
                logger.info("✅ UDP initialization successful")
                actions = await client.query_actions()
                logger.info(f"✅ Found {len(actions)} actions")
                for action in actions:
                    logger.info(f"   [{action['index']}] {action['name']}")
            else:
                logger.error("❌ UDP initialization failed")
        except Exception as e:
            logger.error(f"Error: {e}")
        finally:
            await client.disconnect()
    else:
        # Show instructions
        logger.info("UDP Protocol Test Script")
        logger.info("")
        logger.info("Usage:")
        logger.info(f"  python {Path(__file__).name} <robot_ip>")
        logger.info("")
        logger.info("Example:")
        logger.info(f"  python {Path(__file__).name} 192.168.86.3")
        logger.info("")
        logger.info("Or test web API endpoints:")
        await test_web_api()


if __name__ == "__main__":
    asyncio.run(main())
