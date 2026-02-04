#!/usr/bin/env python3
"""Manual arm control - move individual joints interactively"""

import asyncio
import logging
from g1_app.utils.arp_discovery import discover_robot_ip
from g1_app.core.robot_controller import RobotController
from g1_app.arm_controller import ArmController

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

G1_MAC = "fc:23:cd:92:60:02"
G1_SN = "G1_6937"

async def manual_control():
    """Interactive manual arm control"""
    
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
    
    # Create arm controller
    arm_ctrl = ArmController(robot)
    
    # Read current arm positions
    logger.info("\n" + "="*60)
    logger.info("📖 CURRENT ARM POSITIONS")
    logger.info("="*60)
    
    left_data = await robot.request_arm_state('left')
    right_data = await robot.request_arm_state('right')
    
    if not left_data or not right_data:
        logger.error("❌ Could not read arm state")
        return
    
    left_joints = left_data['joints']
    right_joints = right_data['joints']
    
    joint_names = ['shoulder_pitch', 'shoulder_roll', 'shoulder_yaw', 'elbow', 'wrist_roll', 'wrist_pitch', 'wrist_yaw']
    
    print("\nLEFT ARM:")
    for i, (name, angle) in enumerate(zip(joint_names, left_joints)):
        print(f"  {i}: {name:16s} = {angle:6.3f} rad ({angle*180/3.14159:6.1f}°)")
    
    print("\nRIGHT ARM:")
    for i, (name, angle) in enumerate(zip(joint_names, right_joints)):
        print(f"  {i}: {name:16s} = {angle:6.3f} rad ({angle*180/3.14159:6.1f}°)")
    
    # Interactive control loop
    logger.info("\n" + "="*60)
    logger.info("🎮 MANUAL ARM CONTROL")
    logger.info("="*60)
    logger.info("Commands:")
    logger.info("  l <joint> <angle>  - Move LEFT arm joint (e.g., 'l 3 1.5')")
    logger.info("  r <joint> <angle>  - Move RIGHT arm joint (e.g., 'r 0 0.5')")
    logger.info("  show               - Show current positions")
    logger.info("  q                  - Quit")
    logger.info("")
    logger.info(f"Current FSM: {robot.current_state.name if robot.current_state else 'Unknown'}")
    logger.info("⚠️  Robot will stay in current state - no FSM changes")
    logger.info("="*60 + "\n")
    
    current_left = list(left_joints)
    current_right = list(right_joints)
    
    while True:
        try:
            cmd = input(">>> ").strip().lower()
            
            if cmd == 'q':
                logger.info("👋 Exiting...")
                break
            
            if cmd == 'show':
                left_data = await robot.request_arm_state('left')
                right_data = await robot.request_arm_state('right')
                if left_data and right_data:
                    current_left = left_data['joints']
                    current_right = right_data['joints']
                    print("\nLEFT ARM:")
                    for i, (name, angle) in enumerate(zip(joint_names, current_left)):
                        print(f"  {i}: {name:16s} = {angle:6.3f} rad ({angle*180/3.14159:6.1f}°)")
                    print("\nRIGHT ARM:")
                    for i, (name, angle) in enumerate(zip(joint_names, current_right)):
                        print(f"  {i}: {name:16s} = {angle:6.3f} rad ({angle*180/3.14159:6.1f}°)")
                continue
            
            parts = cmd.split()
            if len(parts) != 3:
                print("❌ Invalid command. Use: l/r <joint> <angle>")
                continue
            
            arm_cmd, joint_str, angle_str = parts
            
            if arm_cmd not in ['l', 'r']:
                print("❌ Invalid arm. Use 'l' for left or 'r' for right")
                continue
            
            try:
                joint_idx = int(joint_str)
                angle = float(angle_str)
            except ValueError:
                print("❌ Invalid numbers")
                continue
            
            if joint_idx < 0 or joint_idx >= 7:
                print("❌ Joint index must be 0-6")
                continue
            
            arm = 'left' if arm_cmd == 'l' else 'right'
            joints = list(current_left if arm == 'left' else current_right)
            joints[joint_idx] = angle
            
            logger.info(f"🤖 Moving {arm} arm joint {joint_idx} ({joint_names[joint_idx]}) to {angle:.3f} rad ({angle*180/3.14159:.1f}°)")
            
            # Send command with moderate stiffness
            success = await arm_ctrl.send_arm_command(
                arm=arm,
                joints=joints,
                kp=[80.0] * 7,  # Moderate stiffness
                kd=[5.0] * 7    # Moderate damping
            )
            
            if success:
                logger.info(f"✅ Command sent")
                if arm == 'left':
                    current_left = joints
                else:
                    current_right = joints
            else:
                logger.error("❌ Command failed")
            
            await asyncio.sleep(0.1)
            
        except KeyboardInterrupt:
            logger.info("\n👋 Exiting...")
            break
        except Exception as e:
            logger.error(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(manual_control())
