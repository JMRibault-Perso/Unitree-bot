"""
Command Executor - Builds API payloads and executes commands
"""

import json
from typing import Optional, List
import logging

from ..api.constants import (
    LocoAPI, ArmAPI, Service, FSMState, ArmGesture, ArmTask,
    VelocityLimits, SpeedMode, TTSSpeaker
)

logger = logging.getLogger(__name__)


class CommandExecutor:
    """
    Builds correct API payloads and manages command execution
    """
    
    def __init__(self, datachannel):
        """
        Args:
            datachannel: WebRTC datachannel for sending commands
        """
        self.datachannel = datachannel
    
    # ========================================================================
    # Locomotion Commands (Sport Service)
    # ========================================================================
    
    async def set_fsm_state(self, state: FSMState) -> dict:
        """
        Change FSM state
        
        Args:
            state: Target FSM state
            
        Returns:
            Command payload
        """
        payload = {
            "api_id": LocoAPI.SET_FSM_ID,
            "parameter": json.dumps({"data": int(state)})
        }
        logger.info(f"Setting FSM state to {state.name} ({state})")
        return await self._send_command(payload)
    
    async def set_velocity(self, vx: float = 0.0, vy: float = 0.0, omega: float = 0.0,
                     duration: float = 1.0, continuous: bool = False) -> dict:
        """
        Set robot velocity using wireless controller topic (joystick emulation)
        
        This is how the Android app controls the robot - via rt/wirelesscontroller topic
        NOT via API 7105 (SET_VELOCITY)
        
        Wireless controller expects NORMALIZED joystick values (-1.0 to 1.0), not m/s!
        
        Args:
            vx: Forward/backward speed (m/s), positive = forward
            vy: Left/right strafe (m/s), positive = left  
            omega: Rotation speed (rad/s), positive = CCW
            duration: Ignored (wireless controller uses continuous mode)
            continuous: Ignored (wireless controller is always continuous)
            
        Returns:
            Command payload
        """
        # Apply safety limits (m/s and rad/s)
        vx = max(-VelocityLimits.MAX_LINEAR, min(VelocityLimits.MAX_LINEAR, vx))
        vy = max(-VelocityLimits.MAX_STRAFE, min(VelocityLimits.MAX_STRAFE, vy))
        omega = max(-VelocityLimits.MAX_ANGULAR, min(VelocityLimits.MAX_ANGULAR, omega))
        
        # Normalize to joystick range (-1.0 to 1.0)
        # Joystick values are stick positions, not actual speeds
        ly_normalized = vx / VelocityLimits.MAX_LINEAR   # Forward: -1.0 to 1.0
        lx_normalized = vy / VelocityLimits.MAX_STRAFE   # Strafe: -1.0 to 1.0
        rx_normalized = omega / VelocityLimits.MAX_ANGULAR  # Rotation: -1.0 to 1.0
        
        # Wireless controller uses joystick mapping:
        # ly = forward/back (normalized vx)
        # lx = strafe left/right (normalized vy)  
        # rx = rotation (normalized omega)
        # ry = unused
        payload = {
            "lx": lx_normalized,
            "ly": ly_normalized,
            "rx": rx_normalized,
            "ry": 0.0,
            "keys": 0
        }
        
        logger.info(f"🎮 Wireless controller: vx={vx:.2f}m/s → ly={ly_normalized:.2f}, vy={vy:.2f}m/s → lx={lx_normalized:.2f}, omega={omega:.2f}rad/s → rx={rx_normalized:.2f}")
        
        # NOTE: publish_without_callback is SYNCHRONOUS, not async
        # Send via wireless controller topic (not API request)
        self.datachannel.pub_sub.publish_without_callback(
            "rt/wirelesscontroller",
            payload
        )
        
        logger.info(f"✅ Sent wireless controller command")
        
        return payload
    
    async def stop_motion(self) -> dict:
        """Stop all motion"""
        logger.info("Stopping motion")
        return await self.set_velocity(0, 0, 0)
    
    async def get_fsm_mode(self) -> Optional[dict]:
        """
        Query current FSM state from robot
        
        Returns:
            Dict with 'data' key containing FSM ID, or None if failed
        """
        try:
            payload = {
                "api_id": LocoAPI.GET_FSM_ID,  # Use GET_FSM_ID (7001) not GET_FSM_MODE (7002)
                "parameter": "{}"
            }
            
            # Send request
            topic = f"rt/api/{Service.SPORT}/request"
            response_topic = f"rt/api/{Service.SPORT}/response"
            
            # Create a simple promise to wait for response
            response_data = None
            
            def on_response(data: dict):
                nonlocal response_data
                # Response structure: {type: 'res', topic: '...', data: {header: {...}, data: '{"data": X}'}}
                if isinstance(data, dict) and data.get('type') == 'res':
                    inner_data = data.get('data', {})
                    if isinstance(inner_data, dict):
                        header = inner_data.get('header', {})
                        identity = header.get('identity', {})
                        if identity.get('api_id') == LocoAPI.GET_FSM_ID:  # Match GET_FSM_ID
                            # Parse the nested JSON string
                            data_str = inner_data.get('data', '{}')
                            try:
                                parsed = json.loads(data_str) if isinstance(data_str, str) else data_str
                                response_data = parsed
                            except:
                                response_data = inner_data
            
            # Subscribe to response temporarily
            self.datachannel.pub_sub.subscribe(response_topic, on_response)
            
            # Send request
            await self.datachannel.pub_sub.publish_request_new(topic, payload)
            
            # Wait briefly for response
            import asyncio
            for _ in range(20):  # Wait up to 2 seconds
                if response_data:
                    break
                await asyncio.sleep(0.1)
            
            logger.info(f"📋 FSM mode query response: {response_data}")
            return response_data
            
        except Exception as e:
            logger.error(f"Failed to query FSM mode: {e}")
            return None
    
    def set_arm_task(self, task: ArmTask) -> dict:
        """
        Execute simple arm gesture via LocoClient
        
        Args:
            task: Arm task ID (wave, shake hand)
            
        Returns:
            Command payload
        """
        payload = {
            "api_id": LocoAPI.SET_ARM_TASK,
            "parameter": json.dumps({"data": int(task)})
        }
        logger.info(f"Setting arm task: {task.name}")
        return self._send_command(payload)
    
    def wave_hand(self, turn: bool = False) -> dict:
        """Wave hand gesture"""
        task = ArmTask.WAVE_HAND_TURN if turn else ArmTask.WAVE_HAND
        return self.set_arm_task(task)
    
    def shake_hand(self, stage: int = 1) -> dict:
        """Shake hand gesture (2-stage)"""
        task = ArmTask.SHAKE_HAND_STAGE_1 if stage == 1 else ArmTask.SHAKE_HAND_STAGE_2
        return self.set_arm_task(task)
    
    # ========================================================================
    # Arm Action Commands (Arm Service)
    # ========================================================================
    
    def execute_gesture(self, gesture: ArmGesture) -> dict:
        """
        Execute pre-programmed arm gesture
        
        Args:
            gesture: Gesture ID from ArmGesture enum
            
        Returns:
            Command payload
        """
        payload = {
            "api_id": ArmAPI.EXECUTE_ACTION,
            "parameter": json.dumps({"action_id": int(gesture)})
        }
        logger.info(f"Executing gesture: {gesture.name}")
        return self._send_command(payload, service=Service.ARM)
    
    def release_arm(self) -> dict:
        """Release arm from held position"""
        return self.execute_gesture(ArmGesture.RELEASE_ARM)
    
    def get_gesture_list(self) -> dict:
        """Get list of available gestures from robot"""
        payload = {
            "api_id": ArmAPI.GET_ACTION_LIST,
            "parameter": "{}"
        }
        logger.info("Requesting gesture list")
        return self._send_command(payload, service=Service.ARM)
    
    def execute_custom_action(self, action_name: str) -> dict:
        """
        Play custom teach mode recording
        
        Args:
            action_name: Name of recorded action
            
        Returns:
            Command payload
        """
        payload = {
            "api_id": ArmAPI.EXECUTE_CUSTOM_ACTION,
            "parameter": json.dumps({"action_name": action_name})
        }
        logger.info(f"Playing custom action: {action_name}")
        return self._send_command(payload, service=Service.ARM)
    
    def stop_custom_action(self) -> dict:
        """Stop custom action playback"""
        payload = {
            "api_id": ArmAPI.STOP_CUSTOM_ACTION,
            "parameter": "{}"
        }
        logger.info("Stopping custom action")
        return self._send_command(payload, service=Service.ARM)
    
    # ========================================================================
    # High-Level Convenience Methods
    # ========================================================================
    
    def go_to_damp_mode(self) -> dict:
        """Safe emergency stop - go to damp mode"""
        return self.set_fsm_state(FSMState.DAMP)
    
    def go_to_ready(self) -> dict:
        """Go to ready mode (preparatory posture)"""
        return self.set_fsm_state(FSMState.START)
    
    def sit_down(self) -> dict:
        """Sit down from standing"""
        return self.set_fsm_state(FSMState.SIT)
    
    def stand_up_from_sit(self) -> dict:
        """Stand up from seated position"""
        return self.set_fsm_state(FSMState.STAND_UP)
    
    def squat_down(self) -> dict:
        """Squat down from standing"""
        return self.set_fsm_state(FSMState.STAND_TO_SQUAT)
    
    def stand_up_from_squat(self) -> dict:
        """Stand up from squat"""
        return self.set_fsm_state(FSMState.SQUAT_TO_STAND)
    
    def stand_up_from_lying(self) -> dict:
        """Stand up from lying position"""
        return self.set_fsm_state(FSMState.STAND_UP)
    
    def walk_forward(self, speed: float = 0.3) -> dict:
        """Walk forward at specified speed"""
        return self.set_velocity(vx=speed, vy=0, omega=0, continuous=True)
    
    def walk_backward(self, speed: float = 0.3) -> dict:
        """Walk backward at specified speed"""
        return self.set_velocity(vx=-speed, vy=0, omega=0, continuous=True)
    
    def strafe_left(self, speed: float = 0.2) -> dict:
        """Strafe left at specified speed"""
        return self.set_velocity(vx=0, vy=speed, omega=0, continuous=True)
    
    def strafe_right(self, speed: float = 0.2) -> dict:
        """Strafe right at specified speed"""
        return self.set_velocity(vx=0, vy=-speed, omega=0, continuous=True)
    
    def turn_left(self, speed: float = 0.5) -> dict:
        """Turn left at specified angular speed"""
        return self.set_velocity(vx=0, vy=0, omega=speed, continuous=True)
    
    def turn_right(self, speed: float = 0.5) -> dict:
        """Turn right at specified angular speed"""
        return self.set_velocity(vx=0, vy=0, omega=-speed, continuous=True)
    
    # ========================================================================
    # Internal Methods
    # ========================================================================
    
    async def _send_command(self, payload: dict, service: str = Service.SPORT) -> dict:
        """
        Send command via WebRTC datachannel
        
        Args:
            payload: Command payload
            service: Target service (sport or arm)
            
        Returns:
            Payload that was sent
        """
        try:
            # Determine topic based on service
            topic = f"rt/api/{service}/request"
            
            # Send via WebRTC datachannel (async method)
            await self.datachannel.pub_sub.publish_request_new(topic, payload)
            
            logger.info(f"✅ Sent to {topic}: {payload}")
            return payload
            
        except Exception as e:
            logger.error(f"Failed to send command: {e}")
            raise
