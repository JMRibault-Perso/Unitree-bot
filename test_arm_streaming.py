#!/usr/bin/env python3
"""Test continuous rt/arm_sdk command streaming to G1 robot."""

import asyncio
import sys
import argparse
from pathlib import Path
import logging
import time

# Add parent directory to path to import g1_app modules
sys.path.insert(0, str(Path(__file__).parent))

from g1_app.core.robot_controller import RobotController

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)


async def stream_arm_commands(robot: RobotController, target_angle: float = 0.3, 
                               frequency: float = 50.0, duration: float = 5.0):
    """
    Stream continuous rt/arm_sdk commands at specified frequency.
    
    Args:
        robot: Robot controller instance
        target_angle: Target angle in radians for left shoulder pitch
        frequency: Command frequency in Hz (50-100 recommended)
        duration: How long to hold the position
    """
    logger.info(f"🌊 Streaming rt/arm_sdk commands at {frequency}Hz for {duration}s")
    logger.info(f"   Target: Left shoulder pitch = {target_angle} rad")
    
    period = 1.0 / frequency
    start_time = time.time()
    command_count = 0
    
    # Build the command once
    arm_command = {
        "enable_arm_sdk": True,
        "topic": "rt/arm_sdk",
        "joints": [
            {"index": 15, "q": target_angle, "kp": 60.0, "kd": 1.5},  # Left shoulder pitch
        ]
    }
    
    try:
        while (time.time() - start_time) < duration:
            loop_start = time.time()
            
            # Send command via robot executor
            if robot.executor.send_lowcmd_arm_command(arm_command):
                command_count += 1
                if command_count % int(frequency) == 0:  # Log every second
                    logger.info(f"   Commands sent: {command_count} ({frequency}Hz)")
            else:
                logger.warning(f"⚠️ Command {command_count} failed to send")
            
            # Sleep to maintain frequency
            elapsed = time.time() - loop_start
            sleep_time = max(0, period - elapsed)
            await asyncio.sleep(sleep_time)
    
    except Exception as e:
        logger.error(f"❌ Streaming error: {e}")
        return False
    
    logger.info(f"✅ Streaming complete: {command_count} commands sent")
    return True


async def test_streaming_mode(robot: RobotController, args):
    """Test streaming command mode."""
    logger.info("=" * 60)
    logger.info("CONTINUOUS COMMAND STREAMING TEST")
    logger.info("=" * 60)
    
    # Get current FSM state
    await asyncio.sleep(0.5)  # Let state update
    fsm_id = robot.state_monitor.current_fsm_state
    logger.info(f"Current FSM state: {fsm_id}")
    
    # Optionally switch to DAMP mode first
    if args.damp_first:
        logger.info("🔧 Switching to DAMP mode first...")
        damp_result = await robot.send_api_command(7101, {"fsm_id": 600})
        if damp_result and damp_result.get("code") == 0:
            logger.info("✅ Switched to DAMP mode (600)")
            await asyncio.sleep(1.0)
        else:
            logger.warning(f"⚠️ DAMP mode switch result: {damp_result}")
    
    # Stream commands
    logger.info("")
    logger.info("📡 Starting command stream...")
    success = await stream_arm_commands(
        robot, 
        target_angle=args.angle,
        frequency=args.frequency,
        duration=args.duration
    )
    
    if success:
        logger.info("")
        logger.info("🔄 Returning to zero position...")
        zero_command = {
            "enable_arm_sdk": True,
            "topic": "rt/arm_sdk",
            "joints": [
                {"index": 15, "q": 0.0, "kp": 60.0, "kd": 1.5},
            ]
        }
        # Stream zero position briefly
        start_time = time.time()
        while (time.time() - start_time) < 1.0:
            robot.executor.send_lowcmd_arm_command(zero_command)
            await asyncio.sleep(1.0 / args.frequency)
        
        logger.info("✅ Test complete")
    
    return success


async def main():
    parser = argparse.ArgumentParser(description="Test continuous rt/arm_sdk streaming")
    parser.add_argument("--robot_ip", default="192.168.86.11", help="Robot IP address")
    parser.add_argument("--angle", type=float, default=0.3, help="Target angle in radians")
    parser.add_argument("--frequency", type=float, default=50.0, help="Command frequency (Hz)")
    parser.add_argument("--duration", type=float, default=5.0, help="Hold duration (seconds)")
    parser.add_argument("--damp_first", action="store_true", help="Switch to DAMP mode first")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    args = parser.parse_args()
    
    # Setup logging
    log_level = logging.DEBUG if args.debug else logging.INFO
    logging.getLogger().setLevel(log_level)
    
    logger.info("🤖 G1 Continuous Command Streaming Test")
    logger.info(f"Robot IP: {args.robot_ip}")
    logger.info(f"Target: {args.angle} rad @ {args.frequency}Hz for {args.duration}s")
    if args.damp_first:
        logger.info("Mode: DAMP mode first, then stream")
    logger.info("")
    
    # Create robot controller
    robot = RobotController(robot_ip=args.robot_ip, robot_sn="G1_6937")
    
    try:
        # Connect to robot
        logger.info("📡 Connecting to robot...")
        await robot.connect()
        
        logger.info("✅ Connected!")
        logger.info("")
        
        # Wait for state updates
        await asyncio.sleep(2.0)
        
        # Run streaming test
        success = await test_streaming_mode(robot, args)
        
        # Cleanup
        await asyncio.sleep(1.0)
        await robot.disconnect()
        
        return 0 if success else 1
        
    except KeyboardInterrupt:
        logger.info("\n⚠️ Interrupted by user")
        await robot.disconnect()
        return 130
    except Exception as e:
        logger.error(f"❌ Error: {e}", exc_info=True)
        await robot.disconnect()
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
