#!/usr/bin/env python3
"""
Test rt/arm_sdk direct motor control

This demonstrates the rt/arm_sdk topic which allows direct position control
of the G1's arm motors. This is similar to the C++ examples:
- g1_arm5_sdk_dds_example.cpp (5-DOF per arm)
- g1_arm7_sdk_dds_example.cpp (7-DOF per arm)

The rt/arm_sdk topic uses the LowCmd message structure with:
- 35 motor slots (29 real motors + 6 special slots)
- motor_cmd[29].q = weight (0.0 to 1.0) for smooth transitions
- Each joint: q (position), dq (velocity), tau (torque), kp, kd

SAFETY: Start with small movements and low weight values!
"""

import asyncio
import argparse
import logging
import sys
import math
from typing import Optional

# Add parent directory to path
sys.path.insert(0, '/root/G1/unitree_sdk2')

from g1_app.core.robot_controller import RobotController
from g1_app.utils.arp_discovery import discover_robot_ip
from g1_app.api.constants import SystemService

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Joint indices for G1 (from g1_arm5_sdk_dds_example.cpp)
class JointIndex:
    # Left leg
    LEFT_HIP_PITCH = 0
    LEFT_HIP_ROLL = 1
    LEFT_HIP_YAW = 2
    LEFT_KNEE = 3
    LEFT_ANKLE = 4
    LEFT_ANKLE_ROLL = 5
    
    # Right leg
    RIGHT_HIP_PITCH = 6
    RIGHT_HIP_ROLL = 7
    RIGHT_HIP_YAW = 8
    RIGHT_KNEE = 9
    RIGHT_ANKLE = 10
    RIGHT_ANKLE_ROLL = 11
    
    # Waist
    WAIST_YAW = 12
    WAIST_ROLL = 13
    WAIST_PITCH = 14
    
    # Left arm (5-DOF)
    LEFT_SHOULDER_PITCH = 15
    LEFT_SHOULDER_ROLL = 16
    LEFT_SHOULDER_YAW = 17
    LEFT_ELBOW_PITCH = 18
    LEFT_ELBOW_ROLL = 19
    
    # Right arm (5-DOF)
    RIGHT_SHOULDER_PITCH = 22
    RIGHT_SHOULDER_ROLL = 23
    RIGHT_SHOULDER_YAW = 24
    RIGHT_ELBOW_PITCH = 25
    RIGHT_ELBOW_ROLL = 26
    
    # Special slots
    NOT_USED_JOINT = 29  # Weight parameter
    NOT_USED_JOINT_1 = 30
    NOT_USED_JOINT_2 = 31
    NOT_USED_JOINT_3 = 32
    NOT_USED_JOINT_4 = 33
    NOT_USED_JOINT_5 = 34


async def enable_arm_sdk_mode(robot: RobotController) -> bool:
    """
    Enable arm_sdk mode by disabling g1_arm_example service
    
    According to Unitree docs:
    "If you need to independently develop upper limb actions via the /arm_sdk topic, 
     you must first turn off Unitree's built-in Arm Control Service."
    
    Service name: g1_arm_example
    """
    logger.info("🔧 Disabling g1_arm_example service to enable arm_sdk mode...")
    
    try:
        result = await robot.executor.service_switch(
            SystemService.ARM_EXAMPLE, 
            enable=False
        )
        
        if result and result.get('status') == 0:
            logger.info("✅ g1_arm_example service disabled - arm_sdk mode enabled")
            return True
        else:
            logger.warning(f"⚠️ Service switch returned: {result}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Failed to disable g1_arm_example: {e}")
        return False


async def disable_arm_sdk_mode(robot: RobotController) -> bool:
    """
    Disable arm_sdk mode by re-enabling g1_arm_example service
    
    This restores normal gesture functionality (APIs 7107/7108)
    """
    logger.info("🔧 Re-enabling g1_arm_example service...")
    
    try:
        result = await robot.executor.service_switch(
            SystemService.ARM_EXAMPLE,
            enable=True
        )
        
        if result and result.get('status') == 0:
            logger.info("✅ g1_arm_example service enabled - gesture mode restored")
            return True
        else:
            logger.warning(f"⚠️ Service switch returned: {result}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Failed to enable g1_arm_example: {e}")
        return False


async def subscribe_to_arm_sdk(robot: RobotController, duration: float = 5.0):
    """Subscribe to rt/arm_sdk topic to see what the robot is publishing"""
    
    logger.info(f"🔍 Subscribing to rt/arm_sdk for {duration} seconds...")
    
    received_messages = []
    
    def on_message(msg):
        received_messages.append(msg)
        logger.info(f"📨 Received rt/arm_sdk message: {type(msg)}")
        if hasattr(msg, 'keys'):
            logger.info(f"   Keys: {list(msg.keys())}")
        
    # Subscribe
    robot.conn.datachannel.pub_sub.subscribe("rt/arm_sdk", on_message)
    
    # Wait
    await asyncio.sleep(duration)
    
    # Unsubscribe
    robot.conn.datachannel.pub_sub.unsubscribe("rt/arm_sdk", on_message)
    
    logger.info(f"📊 Received {len(received_messages)} messages from rt/arm_sdk")
    return received_messages


async def send_arm_position_simple(robot: RobotController, weight: float = 0.5, topic: str = "rt/arm_sdk"):
    """
    Send a simple arm position command
    
    Args:
        robot: Robot controller instance
        weight: Transition weight (0.0 to 1.0). Start low for safety!
        topic: DDS topic name to publish to (rt/arm_sdk, rt/lowcmd, or rt/lf/lowcmd)
    """
    
    logger.info(f"🤖 Sending simple arm position command (weight={weight}, topic={topic})...")
    
    # Build command: Raise left arm slightly
    # Using small movements for safety
    arm_command = {
        "enable_arm_sdk": True,
        "topic": topic,  # Pass topic name to executor
        "joints": [
            # Left shoulder pitch (raise arm forward slightly)
            {
                "motor_index": JointIndex.LEFT_SHOULDER_PITCH,
                "q": 0.2,  # Small angle (radians)
                "dq": 0.0,
                "tau": 0.0,
                "kp": 60.0,  # Stiffness
                "kd": 1.5    # Damping
            },
            # Left shoulder roll (keep neutral)
            {
                "motor_index": JointIndex.LEFT_SHOULDER_ROLL,
                "q": 0.0,
                "dq": 0.0,
                "tau": 0.0,
                "kp": 60.0,
                "kd": 1.5
            },
        ]
    }
    
    # Send command
    result = robot.executor.send_lowcmd_arm_command(arm_command)
    
    if result:
        logger.info("✅ Command sent successfully!")
        logger.info("   The arm should move slowly to the commanded position")
        logger.info("   Weight parameter controls how strongly it follows the command")
    else:
        logger.error("❌ Failed to send command")
    
    return result


async def send_zero_position(robot: RobotController):
    """Send command to return arms to zero position"""
    
    logger.info("🔄 Sending zero position command...")
    
    # Command all arm joints to zero
    arm_joints_indices = [
        JointIndex.LEFT_SHOULDER_PITCH,
        JointIndex.LEFT_SHOULDER_ROLL,
        JointIndex.LEFT_SHOULDER_YAW,
        JointIndex.LEFT_ELBOW_PITCH,
        JointIndex.LEFT_ELBOW_ROLL,
        JointIndex.RIGHT_SHOULDER_PITCH,
        JointIndex.RIGHT_SHOULDER_ROLL,
        JointIndex.RIGHT_SHOULDER_YAW,
        JointIndex.RIGHT_ELBOW_PITCH,
        JointIndex.RIGHT_ELBOW_ROLL,
    ]
    
    joints = []
    for idx in arm_joints_indices:
        joints.append({
            "motor_index": idx,
            "q": 0.0,  # Zero position
            "dq": 0.0,
            "tau": 0.0,
            "kp": 60.0,
            "kd": 1.5
        })
    
    arm_command = {
        "enable_arm_sdk": True,
        "joints": joints
    }
    
    result = robot.executor.send_lowcmd_arm_command(arm_command)
    
    if result:
        logger.info("✅ Zero position command sent")
    else:
        logger.error("❌ Failed to send zero position")
    
    return result


async def wave_arm_demo(robot: RobotController, duration: float = 5.0):
    """
    Demo: Wave left arm back and forth
    
    Args:
        robot: Robot controller
        duration: How long to wave (seconds)
    """
    
    logger.info(f"👋 Starting arm wave demo for {duration} seconds...")
    logger.info("   (Press Ctrl+C to stop early)")
    
    start_time = asyncio.get_event_loop().time()
    
    try:
        while (asyncio.get_event_loop().time() - start_time) < duration:
            # Calculate sine wave for smooth motion
            t = asyncio.get_event_loop().time() - start_time
            angle = 0.3 * math.sin(2 * math.pi * 0.5 * t)  # 0.5 Hz oscillation, ±0.3 rad
            
            # Command left shoulder roll to wave
            arm_command = {
                "enable_arm_sdk": True,
                "joints": [{
                    "motor_index": JointIndex.LEFT_SHOULDER_ROLL,
                    "q": angle,
                    "dq": 0.0,
                    "tau": 0.0,
                    "kp": 60.0,
                    "kd": 1.5
                }]
            }
            
            robot.executor.send_lowcmd_arm_command(arm_command)
            
            # Send at ~20Hz
            await asyncio.sleep(0.05)
        
        logger.info("✅ Wave demo complete")
        
    except KeyboardInterrupt:
        logger.info("⚠️ Demo interrupted by user")
    
    # Return to zero
    await send_zero_position(robot)


async def main():
    parser = argparse.ArgumentParser(
        description='Test rt/arm_sdk direct motor control',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Listen to rt/arm_sdk topic for 10 seconds
  python3 test_arm_sdk.py --listen --duration 10
  
  # Send a simple position command
  python3 test_arm_sdk.py --simple --weight 0.5
  
  # Wave the left arm for 5 seconds
  python3 test_arm_sdk.py --wave --duration 5
  
  # Return arms to zero position
  python3 test_arm_sdk.py --zero

SAFETY WARNING:
  Start with low weight values (0.3-0.5) and small angles!
  The robot will move - make sure it has clearance!
        """
    )
    
    parser.add_argument('--listen', action='store_true',
                        help='Subscribe to rt/arm_sdk and listen for messages')
    parser.add_argument('--simple', action='store_true',
                        help='Send a simple arm position command')
    parser.add_argument('--wave', action='store_true',
                        help='Wave the left arm back and forth')
    parser.add_argument('--zero', action='store_true',
                        help='Send command to return arms to zero position')
    parser.add_argument('--weight', type=float, default=0.5,
                        help='Transition weight 0.0-1.0 (default: 0.5)')
    parser.add_argument('--duration', type=float, default=5.0,
                        help='Duration in seconds (default: 5.0)')
    parser.add_argument('--robot-ip', type=str,
                        help='Robot IP (auto-discovers if not provided)')
    
    args = parser.parse_args()
    
    # Validate weight
    if args.weight < 0.0 or args.weight > 1.0:
        logger.error("Weight must be between 0.0 and 1.0")
        return 1
    
    # Discover robot
    if args.robot_ip:
        robot_ip = args.robot_ip
        logger.info(f"Using provided robot IP: {robot_ip}")
    else:
        logger.info("🔍 Auto-discovering robot via ARP...")
        robot_mac = "fc:23:cd:92:60:02"
        robot_ip = discover_robot_ip(robot_mac)
        
        if not robot_ip:
            logger.error(f"❌ Could not find robot with MAC {robot_mac}")
            logger.error("   Make sure robot is on the network and try --robot-ip")
            return 1
        
        logger.info(f"✅ Found robot at {robot_ip}")
    
    # Connect to robot
    logger.info(f"🔌 Connecting to robot at {robot_ip}:8081...")
    robot = RobotController(robot_ip, "G1_6937")  # Robot serial number
    
    try:
        await robot.connect()
        logger.info("✅ Connected to robot!")
        
        # Wait for connection to stabilize
        await asyncio.sleep(1.0)
        
        # Enable arm_sdk mode (disable g1_arm_example service)
        logger.info("")
        logger.info("=" * 70)
        logger.info("ENABLING ARM SDK MODE")
        logger.info("=" * 70)
        
        if not await enable_arm_sdk_mode(robot):
            logger.error("⚠️ Failed to enable arm_sdk mode - continuing anyway...")
            logger.error("   (Robot may not respond to rt/arm_sdk commands)")
        
        logger.info("")
        
        try:
            # Execute requested action
            if args.listen:
                await subscribe_to_arm_sdk(robot, args.duration)
                
            elif args.simple:
                # Try different topics to see which one works
                logger.info("Testing rt/arm_sdk topic...")
                result_arm_sdk = await send_arm_position_simple(robot, args.weight, "rt/arm_sdk")
                
                if not result_arm_sdk:
                    logger.warning("⚠️ rt/arm_sdk failed, trying rt/lf/lowcmd...")
                    result_lf_lowcmd = await send_arm_position_simple(robot, args.weight, "rt/lf/lowcmd")
                    
                    if not result_lf_lowcmd:
                        logger.warning("⚠️ rt/lf/lowcmd failed, trying rt/lowcmd...")
                        await send_arm_position_simple(robot, args.weight, "rt/lowcmd")
                
                logger.info(f"💡 Holding position for {args.duration} seconds...")
                await asyncio.sleep(args.duration)
                await send_zero_position(robot)
                
            elif args.wave:
                await wave_arm_demo(robot, args.duration)
                
            elif args.zero:
                await send_zero_position(robot)
                
            else:
                logger.error("❌ No action specified. Use --listen, --simple, --wave, or --zero")
                parser.print_help()
                return 1
            
            logger.info("✅ Test complete!")
            
        finally:
            # Always restore gesture mode when done
            logger.info("")
            logger.info("=" * 70)
            logger.info("RESTORING GESTURE MODE")
            logger.info("=" * 70)
            
            await disable_arm_sdk_mode(robot)
            logger.info("")
        
        return 0
        
    except Exception as e:
        logger.error(f"❌ Error: {e}", exc_info=True)
        return 1
        
    finally:
        await robot.disconnect()


if __name__ == '__main__':
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
