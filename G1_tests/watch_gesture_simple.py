#!/usr/bin/env python3
"""Simple motor position logger - watch rt/lowstate during gesture"""

import asyncio
import logging
import time
from g1_app.utils.arp_discovery import discover_robot_ip
from g1_app.core.robot_controller import RobotController

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

G1_MAC = "fc:23:cd:92:60:02"
G1_SN = "G1_6937"

async def watch_gesture():
    # Connect
    robot_ip = discover_robot_ip(G1_MAC)
    robot = RobotController(robot_ip, G1_SN)
    await robot.connect()
    await asyncio.sleep(3)
    
    logger.info("="*80)
    logger.info(f"Current FSM: {robot.state_machine.current_state}")
    logger.info("="*80)
    
    # Get initial positions
    left = await robot.request_arm_state('left')
    right = await robot.request_arm_state('right')
    logger.info("\nINITIAL POSITIONS:")
    logger.info(f"Left:  {[f'{j:.3f}' for j in left['joints']]}")
    logger.info(f"Right: {[f'{j:.3f}' for j in right['joints']]}")
    
    # Send gesture command
    logger.info("\n" + "="*80)
    logger.info("EXECUTING GESTURE: Wave Hand High (ID 26)")
    logger.info("="*80)
    
    response = await robot.executor.send_api_request(7108, {"action_id": 26})
    logger.info(f"Response: {response}")
    
    # Sample positions during gesture
    logger.info("\nSAMPLING POSITIONS (every 0.2s for 5s):")
    logger.info("-"*80)
    
    for i in range(25):  # 5 seconds at 0.2s intervals
        await asyncio.sleep(0.2)
        left = await robot.request_arm_state('left')
        right = await robot.request_arm_state('right')
        
        if left and right:
            # Print compact format showing motors that moved
            logger.info(f"t={i*0.2:.1f}s  L:[{','.join([f'{j:.2f}' for j in left['joints'][:4]])}]  "
                       f"R:[{','.join([f'{j:.2f}' for j in right['joints'][:4]])}]")
    
    # Final positions
    left = await robot.request_arm_state('left')
    right = await robot.request_arm_state('right')
    logger.info("\nFINAL POSITIONS:")
    logger.info(f"Left:  {[f'{j:.3f}' for j in left['joints']]}")
    logger.info(f"Right: {[f'{j:.3f}' for j in right['joints']]}")
    logger.info("="*80)

if __name__ == "__main__":
    asyncio.run(watch_gesture())
