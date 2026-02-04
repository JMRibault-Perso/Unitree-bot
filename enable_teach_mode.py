#!/usr/bin/env python3
"""Enable teach mode - allows manual arm movement while robot stays balanced"""

import asyncio
import logging
from g1_app.utils.arp_discovery import discover_robot_ip
from g1_app.core.robot_controller import RobotController

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

G1_MAC = "fc:23:cd:92:60:02"
G1_SN = "G1_6937"

async def enable_teach_mode():
    """Enable teach mode - zero torque on arms, balance on legs"""
    
    # Connect to robot
    logger.info("🔍 Discovering robot...")
    robot_ip = discover_robot_ip(G1_MAC)
    if not robot_ip:
        logger.error("❌ Failed to discover robot")
        return
    
    logger.info(f"✅ Found robot at {robot_ip}")
    robot = RobotController(robot_ip, G1_SN)
    
    try:
        await robot.connect()
        logger.info("✅ Connected to robot")
    except Exception as e:
        logger.error(f"❌ Connection failed: {e}")
        return
    
    # Wait for initial state
    await asyncio.sleep(3)
    
    logger.info("\n" + "="*60)
    logger.info("🎓 ENABLING TEACH MODE")
    logger.info("="*60)
    logger.info("Current FSM: " + (robot.current_state.name if robot.current_state else 'Unknown'))
    battery = robot.get_battery_state()
    if battery:
        logger.info(f"Battery: {battery.get('soc', '?')}%")
    
    logger.info("\n⚠️  IMPORTANT:")
    logger.info("   - Balance mode 0 = Arms compliant (zero torque)")
    logger.info("   - Legs will remain balanced/standing")
    logger.info("   - You can physically move the arms")
    logger.info("   - Robot should transition to FSM state 501 (LOCK_STAND_ADV)")
    
    # Confirm with user
    print("\n" + "="*60)
    response = input("Enable teach mode? (type 'yes' to confirm): ").strip().lower()
    
    if response != 'yes':
        logger.info("❌ Cancelled by user")
        return
    
    logger.info("\n🤖 Sending balance mode 0 command...")
    
    try:
        result = await robot.executor.set_balance_mode(0)
        logger.info(f"✅ Command sent: {result}")
        
        # Wait for state change
        await asyncio.sleep(2)
        
        logger.info(f"\n📊 New FSM state: {robot.current_state.name if robot.current_state else 'Unknown'}")
        logger.info("✅ Teach mode enabled - you can now manually move the arms")
        logger.info("\n💡 To disable teach mode:")
        logger.info("   - Use Android app 'Exit Teach Mode' button")
        logger.info("   - Or send balance mode 1 command")
        
    except Exception as e:
        logger.error(f"❌ Failed to enable teach mode: {e}")

if __name__ == "__main__":
    asyncio.run(enable_teach_mode())
