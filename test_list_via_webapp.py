#!/usr/bin/env python3
"""
Test Get/List Actions using the web app's robot connection
"""

import asyncio
import aiohttp
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main():
    """Query actions via web app server"""
    
    logger.info("=" * 80)
    logger.info("Testing Get/List Actions via Web App")
    logger.info("=" * 80)
    logger.info("")
    logger.info("Make sure the web app is running and connected to robot!")
    logger.info("")
    
    # Send request to web app server
    url = "http://localhost:8000/api/custom_action/list"
    
    try:
        async with aiohttp.ClientSession() as session:
            logger.info(f"📤 Querying saved actions...")
            async with session.get(url) as resp:
                result = await resp.json()
                
                logger.info("")
                logger.info("=" * 80)
                logger.info("RESPONSE:")
                logger.info("=" * 80)
                logger.info(f"Full response: {result}")
                logger.info("")
                
                if result.get("success"):
                    actions = result.get('actions', [])
                    logger.info(f"✅ Found {len(actions)} saved actions")
                    logger.info("")
                    
                    for i, action in enumerate(actions, 1):
                        logger.info(f"Action {i}:")
                        logger.info(f"  Encrypted name: {action['encrypted_name']}")
                        logger.info(f"  Timestamp: {action['timestamp']}")
                        logger.info(f"  Checksum: {action['checksum']}")
                        logger.info("")
                else:
                    logger.error(f"❌ Error: {result.get('error', 'Unknown')}")
                
    except aiohttp.ClientConnectorError:
        logger.error("❌ Cannot connect to web app server")
        logger.info("   Start the server with: python3 -m g1_app.ui.web_server")
        return
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)


if __name__ == "__main__":
    asyncio.run(main())
