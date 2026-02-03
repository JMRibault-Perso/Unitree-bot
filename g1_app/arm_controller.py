"""
Arm Controller for Unitree G1 Robot
Handles coordinate-based arm motion teaching and playback
Based on findings from Sentdex's unitree_g1_vibes repository
"""

import asyncio
import json
import math
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict
import logging

logger = logging.getLogger(__name__)


@dataclass
class JointCommand:
    """Single joint command for arm control"""
    index: int  # Motor index (15-21 for left, 22-28 for right)
    q: float    # Target position (radians)
    dq: float = 0.0   # Target velocity
    tau: float = 0.0  # Feed-forward torque
    kp: float = 60.0  # Position gain (stiffness)
    kd: float = 1.5   # Damping gain


@dataclass
class ArmPose:
    """Complete arm pose with all 7 joints"""
    arm: str  # 'left' or 'right'
    joints: List[float]  # 7 joint angles in radians
    timestamp: Optional[str] = None


class ArmController:
    """
    Controls G1 robot arm using joint coordinates
    
    Based on rt/arm_sdk topic from Unitree SDK2:
    - Left arm: Motor indices 15-21 (7 DOF)
    - Right arm: Motor indices 22-28 (7 DOF)
    - Motor 29 must be set to q=1 to enable arm SDK
    - Commands sent at 50 Hz (20ms intervals)
    """
    
    # Motor indices for each arm
    LEFT_ARM_JOINTS = list(range(15, 22))   # [15, 16, 17, 18, 19, 20, 21]
    RIGHT_ARM_JOINTS = list(range(22, 29))  # [22, 23, 24, 25, 26, 27, 28]
    ENABLE_ARM_SDK_IDX = 29
    
    # Joint limits (radians) - approximate safe ranges
    JOINT_LIMITS = {
        'shoulder_pitch': (-math.pi, math.pi),
        'shoulder_roll': (-math.pi, math.pi),
        'shoulder_yaw': (-math.pi, math.pi),
        'elbow': (0, math.pi),
        'wrist_roll': (-math.pi, math.pi),
        'wrist_pitch': (-math.pi, math.pi),
        'wrist_yaw': (-math.pi, math.pi),
    }
    
    def __init__(self, robot_controller=None):
        """
        Initialize arm controller
        
        Args:
            robot_controller: Reference to main RobotController for sending commands
        """
        self.robot = robot_controller
        self.current_left_pose: Optional[List[float]] = None
        self.current_right_pose: Optional[List[float]] = None
        self._command_rate = 0.02  # 50 Hz = 20ms intervals
        
    def get_joint_indices(self, arm: str) -> List[int]:
        """Get motor indices for specified arm"""
        if arm == 'left':
            return self.LEFT_ARM_JOINTS
        elif arm == 'right':
            return self.RIGHT_ARM_JOINTS
        else:
            raise ValueError(f"Invalid arm: {arm}. Must be 'left' or 'right'")
    
    def clamp_joint_angle(self, joint_idx: int, angle: float) -> float:
        """Clamp joint angle to safe limits"""
        joint_names = list(self.JOINT_LIMITS.keys())
        joint_name = joint_names[joint_idx % 7]  # Works for both arms
        min_angle, max_angle = self.JOINT_LIMITS[joint_name]
        return max(min_angle, min(max_angle, angle))
    
    def validate_pose(self, joints: List[float]) -> List[float]:
        """Validate and clamp all joint angles in a pose"""
        if len(joints) != 7:
            raise ValueError(f"Pose must have 7 joints, got {len(joints)}")
        
        return [self.clamp_joint_angle(i, angle) for i, angle in enumerate(joints)]
    
    async def send_arm_command(self, arm: str, joints: List[float], 
                               kp: float = 60.0, kd: float = 1.5) -> bool:
        """
        Send arm command to robot via WebRTC datachannel
        
        Args:
            arm: 'left' or 'right'
            joints: List of 7 joint angles in radians
            kp: Position gain (stiffness)
            kd: Damping gain
            
        Returns:
            True if command sent successfully
        """
        logger.debug(f"=== send_arm_command START ===")
        logger.debug(f"Arm: {arm}")
        logger.debug(f"Input joints (rad): {joints}")
        logger.debug(f"Input joints (deg): {[f'{j*180/3.14159:.1f}°' for j in joints]}")
        logger.debug(f"kp={kp}, kd={kd}")
        
        try:
            # Validate inputs
            logger.debug("Validating pose...")
            joints = self.validate_pose(joints)
            logger.debug(f"Validated joints: {joints}")
            
            joint_indices = self.get_joint_indices(arm)
            logger.debug(f"Motor indices for {arm} arm: {joint_indices}")
            
            # Build command structure (will be sent via WebRTC)
            # This matches the LowCmd_ structure from Unitree SDK2
            command = {
                'type': 'arm_command',
                'arm': arm,
                'enable_arm_sdk': True,  # Sets motor 29 to q=1
                'joints': []
            }
            
            # Add each joint command
            logger.debug("Building joint commands...")
            for idx, (motor_idx, angle) in enumerate(zip(joint_indices, joints)):
                joint_cmd = {
                    'motor_index': motor_idx,
                    'q': angle,      # Position (radians)
                    'dq': 0.0,       # Velocity
                    'tau': 0.0,      # Torque
                    'kp': kp,        # Position gain
                    'kd': kd         # Damping gain
                }
                command['joints'].append(joint_cmd)
                logger.debug(f"  Joint {idx}: motor={motor_idx}, q={angle:.3f}rad ({angle*180/3.14159:.1f}°)")
            
            logger.debug(f"Complete command structure: {command}")
            
            # Send via robot controller (WebRTC datachannel)
            if self.robot:
                logger.debug("Robot controller available, sending command...")
                success = await self.robot.send_command(command)
                logger.debug(f"send_command() returned: {success}")
                
                if success:
                    # Update current pose cache
                    if arm == 'left':
                        self.current_left_pose = joints
                    else:
                        self.current_right_pose = joints
                    logger.info(f"✅ Sent {arm} arm command: {[f'{j:.2f}rad' for j in joints]}")
                    logger.debug(f"=== send_arm_command SUCCESS ===")
                else:
                    logger.warning(f"⚠️ send_command() failed")
                return success
            else:
                logger.warning("❌ No robot controller connected")
                logger.debug(f"=== send_arm_command FAILED (no robot) ===")
                return False
                
        except Exception as e:
            logger.error(f"❌ Failed to send arm command: {e}", exc_info=True)
            logger.debug(f"=== send_arm_command EXCEPTION ===")
            return False
    
    async def move_to_pose(self, arm: str, joints: List[float], 
                          duration: float = 2.0, kp: float = 60.0) -> bool:
        """
        Smoothly move arm to target pose over specified duration
        
        Args:
            arm: 'left' or 'right'
            joints: Target joint angles (radians)
            duration: Movement duration in seconds
            kp: Position gain (lower = smoother, higher = stiffer)
            
        Returns:
            True if movement completed successfully
        """
        logger.debug(f"=== move_to_pose START ===")
        logger.debug(f"Arm: {arm}, Duration: {duration}s, kp: {kp}")
        
        try:
            # Get current pose
            current = self.current_left_pose if arm == 'left' else self.current_right_pose
            if current is None:
                # If no current pose, use zero position
                logger.debug("No cached pose, using zero position as start")
                current = [0.0] * 7
            else:
                logger.debug(f"Current pose: {current}")
            
            target = self.validate_pose(joints)
            logger.debug(f"Target pose: {target}")
            
            # Calculate number of steps based on duration and command rate
            num_steps = int(duration / self._command_rate)
            if num_steps < 1:
                num_steps = 1
            logger.debug(f"Will interpolate over {num_steps} steps ({self._command_rate*1000}ms each)")
            
            # Interpolate between current and target
            for step in range(num_steps + 1):
                alpha = step / num_steps  # 0.0 to 1.0
                
                # Linear interpolation
                interpolated = [
                    current[i] + alpha * (target[i] - current[i])
                    for i in range(7)
                ]
                
                logger.debug(f"Step {step}/{num_steps} (α={alpha:.2f}): {[f'{j:.3f}' for j in interpolated]}")
                
                # Send command
                success = await self.send_arm_command(arm, interpolated, kp=kp)
                if not success:
                    logger.error(f"❌ Failed to send command at step {step}/{num_steps}")
                    return False
                
                # Wait for next command cycle
                if step < num_steps:
                    await asyncio.sleep(self._command_rate)
            
            logger.info(f"✅ Completed smooth movement to pose in {duration}s")
            logger.debug(f"=== move_to_pose SUCCESS ===")
            return True
            
        except Exception as e:
            logger.error(f"Error during smooth movement: {e}")
            return False
    
    async def play_sequence(self, waypoints: List[Dict], speed: float = 1.0) -> bool:
        """
        Play back a sequence of waypoints
        
        Args:
            waypoints: List of waypoint dictionaries with 'arm' and 'joints'
            speed: Playback speed multiplier (1.0 = normal)
            
        Returns:
            True if sequence completed successfully
        """
        try:
            logger.info(f"Playing sequence with {len(waypoints)} waypoints at {speed}x speed")
            
            # Default transition time between waypoints
            transition_time = 1.0 / speed
            
            for i, waypoint in enumerate(waypoints):
                arm = waypoint['arm']
                joints = waypoint['joints']
                
                logger.info(f"Waypoint {i+1}/{len(waypoints)}: {arm} arm")
                
                # Move to waypoint
                success = await self.move_to_pose(
                    arm=arm,
                    joints=joints,
                    duration=transition_time,
                    kp=50.0  # Slightly softer for smooth trajectories
                )
                
                if not success:
                    logger.error(f"Failed at waypoint {i+1}")
                    return False
                
                # Small pause at waypoint
                await asyncio.sleep(0.1)
            
            logger.info("Sequence playback completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error during sequence playback: {e}")
            return False
    
    async def read_current_pose(self, arm: str) -> Optional[List[float]]:
        """
        Read current joint angles from robot
        
        Args:
            arm: 'left' or 'right'
            
        Returns:
            List of 7 joint angles or None if read failed
        """
        try:
            if self.robot:
                # Request current state from robot
                result = await self.robot.request_arm_state(arm)
                if result and 'joints' in result:
                    joints = result['joints']
                    
                    # Update cache
                    if arm == 'left':
                        self.current_left_pose = joints
                    else:
                        self.current_right_pose = joints
                    
                    return joints
            
            # Fall back to cached value
            return self.current_left_pose if arm == 'left' else self.current_right_pose
            
        except Exception as e:
            logger.error(f"Failed to read current pose: {e}")
            return None
    
    def preset_poses(self, arm: str) -> Dict[str, List[float]]:
        """
        Get preset poses for common positions
        
        Returns:
            Dictionary of pose names to joint angles
        """
        # Example preset poses (in radians)
        # These are approximate and should be tuned for your robot
        presets = {
            'rest': [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            'forward_reach': [0.8, 0.0, 0.0, 1.2, 0.0, -0.3, 0.0],
            'side_reach': [0.5, 0.7 if arm == 'left' else -0.7, 0.0, 1.0, 0.0, 0.0, 0.0],
            'up_reach': [1.2, 0.0, 0.0, 0.8, 0.0, 0.5, 0.0],
            'button_push': [0.6, 0.2, 0.0, 1.4, 0.0, -0.4, 0.0],  # Arm extended for pushing
        }
        
        return presets
    
    async def go_to_preset(self, arm: str, preset_name: str, duration: float = 2.0) -> bool:
        """
        Move arm to a preset pose
        
        Args:
            arm: 'left' or 'right'
            preset_name: Name of preset pose
            duration: Movement duration
            
        Returns:
            True if successful
        """
        presets = self.preset_poses(arm)
        
        if preset_name not in presets:
            logger.error(f"Unknown preset: {preset_name}")
            return False
        
        return await self.move_to_pose(arm, presets[preset_name], duration)
