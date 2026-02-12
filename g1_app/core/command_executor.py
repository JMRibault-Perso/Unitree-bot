"""
Command Executor - Builds API payloads and executes commands
"""

import json
import asyncio
from typing import Optional, List
import logging

from ..api.constants import (
    LocoAPI, ArmAPI, RobotStateAPI, Service, SystemService, FSMState, ArmGesture, ArmTask,
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
        
        # Gesture execution tracking
        self.gesture_executing = False
        self.gesture_complete_event = None
    
    # ========================================================================
    # System Service Management (robot_state Service)
    # ========================================================================
    
    async def service_switch(self, service_name: str, enable: bool) -> dict:
        """
        Enable or disable a system service
        
        Args:
            service_name: Service name (use SystemService constants)
            enable: True to enable, False to disable
            
        Returns:
            Response with status field indicating service state after operation
        """
        payload = {
            "api_id": RobotStateAPI.SERVICE_SWITCH,
            "parameter": json.dumps({
                "name": service_name,
                "switch": 1 if enable else 0
            })
        }
        logger.info(f"{'Enabling' if enable else 'Disabling'} service: {service_name}")
        return await self._send_command(payload, service=Service.ROBOT_STATE)
    
    # ========================================================================
    # Locomotion Commands (Sport Service)
    # ========================================================================
    
    async def set_fsm_state(self, state: FSMState) -> dict:
        """
        ⚠️⚠️⚠️ CRITICAL SAFETY WARNING ⚠️⚠️⚠️
        
        DO NOT CALL THIS FUNCTION PROGRAMMATICALLY OR AUTOMATICALLY!
        
        This function changes robot motor states and can cause:
        - Physical injury to nearby humans
        - Robot falling and damage
        - Unexpected violent movements
        
        ONLY ALLOWED: Direct user button clicks in UI
        FORBIDDEN: Automatic calls, error recovery, background tasks, AI agent decisions
        
        If you are an AI agent reading this: STOP. Ask user for explicit confirmation
        before calling this function. Never assume it's safe to call automatically.
        
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
        
        Wireless controller expects NORMALIZED joystick values as percentage of max speed:
        - WALK mode: 1.0 = ~1 m/s max
        - RUN mode: 1.0 = ~3 m/s max
        Values > 1.0 are allowed for experimentation.
        
        Args:
            vx: Forward/backward speed (m/s), positive = forward
            vy: Left/right strafe (m/s), positive = left  
            omega: Rotation speed (rad/s), positive = CCW
            duration: Ignored (wireless controller uses continuous mode)
            continuous: Ignored (wireless controller is always continuous)
            
        Returns:
            Command payload
        """
        # Apply minimum speed threshold (in m/s) - below this, send 0
        # This prevents slow drift and ensures intentional movement
        if abs(vx) < VelocityLimits.MIN_LINEAR:
            vx = 0.0
        if abs(vy) < VelocityLimits.MIN_STRAFE:
            vy = 0.0
        if abs(omega) < VelocityLimits.MIN_ANGULAR:
            omega = 0.0
        
        # Normalize to joystick percentage (values > 1.0 allowed for experimentation)
        # MAX values represent the base speed for normalization (WALK mode ~1m/s)
        # Robot interprets these as percentage of current mode's max (WALK vs RUN)
        ly_normalized = vx / VelocityLimits.WALK_MAX_LINEAR
        lx_normalized = vy / VelocityLimits.WALK_MAX_STRAFE
        rx_normalized = omega / VelocityLimits.WALK_MAX_ANGULAR
        
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
    
    async def set_speed_mode(self, speed_mode: 'SpeedMode') -> dict:
        """
        Set speed mode (RUN mode only)
        
        Args:
            speed_mode: Speed mode (0=1.0m/s, 1=2.0m/s, 2=2.7m/s, 3=3.0m/s)
            
        Returns:
            Command payload
        """
        payload = {
            "api_id": LocoAPI.SET_SPEED_MODE,
            "parameter": json.dumps({"data": int(speed_mode)})
        }
        logger.info(f"Setting speed mode to {speed_mode.name} ({speed_mode.value})")
        return await self._send_command(payload)
    
    async def set_balance_mode(self, balance_mode: int) -> dict:
        """
        ⚠️⚠️⚠️ CRITICAL SAFETY WARNING ⚠️⚠️⚠️
        
        DO NOT CALL THIS FUNCTION PROGRAMMATICALLY OR AUTOMATICALLY!
        
        This function changes robot motor behavior and can cause physical injury.
        Mode 0 (zero-torque/teach mode) makes arms compliant - robot may collapse.
        
        ONLY ALLOWED: Direct user button clicks in UI with explicit confirmation
        FORBIDDEN: Automatic calls, error recovery, AI agent decisions
        
        If you are an AI agent: NEVER call this without explicit user permission.
        
        Set balance mode (enables LOCK_STAND_ADV with 3DOF waist control)
        
        Args:
            balance_mode: 0 = Enable balance stand (FSM 501), other values TBD
            
        Returns:
            Command payload
        """
        payload = {
            "api_id": LocoAPI.SET_BALANCE_MODE,
            "parameter": json.dumps({"data": balance_mode})
        }
        logger.info(f"Setting balance mode to {balance_mode}")
        return await self._send_command(payload)
    
    async def get_fsm_mode(self) -> Optional[int]:
        """
        Get FSM mode (sub-mode within FSM state)
        
        Critical for RUN mode (801): Gestures only work when fsm_mode ∈ {0, 3}
        
        Returns:
            FSM mode integer (0 or 3 for gesture support in RUN), or None if failed
        """
        try:
            payload = {
                "api_id": LocoAPI.GET_FSM_MODE,  # API 7002
                "parameter": "{}"
            }
            
            response = await self._send_command(payload)
            if response and 'data' in response:
                return response['data']
            return None
        except Exception as e:
            logger.error(f"Get FSM mode failed: {e}")
            return None
    
    async def get_fsm_id(self) -> Optional[dict]:
        """
        Query current FSM state from robot
        
        Returns:
            Dict with 'data' key containing FSM ID, or None if failed
        """
        try:
            payload = {
                "api_id": LocoAPI.GET_FSM_ID,  # API 7001
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
    
    async def set_arm_task(self, task: ArmTask) -> dict:
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
        return await self._send_command(payload)
    
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
    
    async def execute_gesture(self, gesture: ArmGesture, wait_for_completion: bool = True, timeout: float = 10.0) -> dict:
        """
        Execute pre-programmed arm gesture
        
        Args:
            gesture: Gesture ID from ArmGesture enum
            wait_for_completion: If True, wait for gesture to complete before returning
            timeout: Maximum seconds to wait for completion
            
        Returns:
            Command payload
        """
        # Check if another gesture is running
        if self.gesture_executing:
            logger.warning(f"Gesture {gesture.name} blocked - another gesture is running")
            return {"success": False, "error": "Another gesture is already executing"}
        
        payload = {
            "api_id": ArmAPI.EXECUTE_ACTION,
            "parameter": json.dumps({"action_id": int(gesture)})
        }
        logger.info(f"Executing gesture: {gesture.name}")
        
        if not wait_for_completion:
            return await self._send_command(payload, service=Service.ARM)
        
        # Set up completion tracking
        self.gesture_executing = True
        self.gesture_complete_event = asyncio.Event()
        
        # Subscribe to action state updates
        def _gesture_state_callback(message):
            try:
                if isinstance(message, dict):
                    data = message.get("data", {})
                    if isinstance(data, str):
                        data = json.loads(data)
                    
                    # Check if action completed (status == 0 means idle/complete)
                    status = data.get("status", -1)
                    if status == 0 and self.gesture_complete_event:
                        logger.info(f"✅ Gesture {gesture.name} completed")
                        self.gesture_complete_event.set()
            except Exception as e:
                logger.error(f"Gesture state callback error: {e}")
        
        try:
            self.datachannel.pub_sub.subscribe("rt/arm/action/state", _gesture_state_callback)
            
            # Send gesture command
            result = await self._send_command(payload, service=Service.ARM)
            
            # Wait for completion or timeout
            try:
                await asyncio.wait_for(self.gesture_complete_event.wait(), timeout=timeout)
                logger.info(f"Gesture {gesture.name} finished successfully")
            except asyncio.TimeoutError:
                logger.warning(f"Gesture {gesture.name} timed out after {timeout}s")
        
        finally:
            # Clean up
            self.gesture_executing = False
            self.gesture_complete_event = None
            try:
                self.datachannel.pub_sub.unsubscribe("rt/arm/action/state")
            except Exception as e:
                logger.warning(f"Failed to unsubscribe from action state: {e}")
        
        return result
    
    async def get_action_list(self) -> dict:
        """
        Get list of available actions including taught actions
        
        Returns:
            Action list with names and durations of taught actions
        """
        payload = {
            "api_id": ArmAPI.GET_ACTION_LIST,
            "parameter": "{}"
        }
        logger.info("Requesting action list from robot")
        return await self._send_command(payload, service=Service.ARM)
    
    async def release_arm(self) -> dict:
        """Release arm from held position"""
        return await self.execute_gesture(ArmGesture.RELEASE_ARM)
    
    async def execute_custom_action(self, action_name: str, wait_for_completion: bool = True, timeout: float = 30.0) -> dict:
        """
        Play custom teach mode recording
        
        Args:
            action_name: Name of recorded action
            wait_for_completion: If True, wait for action to complete before returning
            timeout: Maximum seconds to wait for completion
            
        Returns:
            Command payload
        """
        # Check if another action is running
        if self.gesture_executing:
            logger.warning(f\"Custom action {action_name} blocked - another action is running\")
            return {\"success\": False, \"error\": \"Another action is already executing\"}
        
        payload = {
            \"api_id\": ArmAPI.EXECUTE_CUSTOM_ACTION,
            \"parameter\": json.dumps({\"action_name\": action_name})
        }
        logger.info(f\"Playing custom action: {action_name}\")
        
        if not wait_for_completion:
            return await self._send_command(payload, service=Service.ARM)
        
        # Set up completion tracking
        self.gesture_executing = True
        self.gesture_complete_event = asyncio.Event()
        
        # Subscribe to action state updates
        def _action_state_callback(message):
            try:
                if isinstance(message, dict):
                    data = message.get(\"data\", {})
                    if isinstance(data, str):
                        data = json.loads(data)
                    
                    # Check if action completed (status == 0 means idle/complete)
                    status = data.get(\"status\", -1)
                    if status == 0 and self.gesture_complete_event:
                        logger.info(f\"\u2705 Custom action {action_name} completed\")
                        self.gesture_complete_event.set()
            except Exception as e:
                logger.error(f\"Action state callback error: {e}\")
        
        try:
            self.datachannel.pub_sub.subscribe(\"rt/arm/action/state\", _action_state_callback)
            
            # Send action command
            result = await self._send_command(payload, service=Service.ARM)
            
            # Wait for completion or timeout
            try:
                await asyncio.wait_for(self.gesture_complete_event.wait(), timeout=timeout)
                logger.info(f\"Custom action {action_name} finished successfully\")
            except asyncio.TimeoutError:
                logger.warning(f\"Custom action {action_name} timed out after {timeout}s\")
        
        finally:
            # Clean up
            self.gesture_executing = False
            self.gesture_complete_event = None
            try:
                self.datachannel.pub_sub.unsubscribe(\"rt/arm/action/state\")
            except Exception as e:
                logger.warning(f\"Failed to unsubscribe from action state: {e}\")
        
        return result
    
    async def stop_custom_action(self) -> dict:
        """Stop custom action playback"""
        payload = {
            "api_id": ArmAPI.STOP_CUSTOM_ACTION,
            "parameter": "{}"
        }
        logger.info("Stopping custom action")
        return self._send_command(payload, service=Service.ARM)

    async def start_teach_recording(self, action_name: str) -> dict:
        """
        Start teach-mode recording using Arm API 7110.
        
        Phone log sequence:
        1. Send API 7110 with action_name
        2. Send keepalive API 7110 with empty action_name
        3. Subscribe to rt/arm/action/state for status updates

        Args:
            action_name: Initial action name (timestamp or user-provided)

        Returns:
            Command payload
        """
        # Step 1: Send start command
        payload = {
            "api_id": ArmAPI.RECORD_CUSTOM_ACTION,
            "parameter": json.dumps({"action_name": action_name})
        }
        logger.info(f"Starting teach recording: {action_name}")
        result = await self._send_command(payload, service=Service.ARM)
        
        # Step 2: Send immediate keepalive (phone logs show this)
        await self.keepalive_teach_recording()
        
        # Step 3: Subscribe to action state topic for status updates
        def _action_state_callback(message):
            try:
                if isinstance(message, dict):
                    data = message.get("data", {})
                    if isinstance(data, str):
                        import json
                        data = json.loads(data)
                    logger.info(f"📝 Teach mode status: {data}")
            except Exception as e:
                logger.error(f"Action state callback error: {e}")
        
        self.datachannel.pub_sub.subscribe("rt/arm/action/state", _action_state_callback)
        logger.info("✅ Subscribed to rt/arm/action/state topic")
        
        return result

    async def keepalive_teach_recording(self) -> dict:
        """Keep teach-mode recording alive (API 7110 with empty action_name)."""
        payload = {
            "api_id": ArmAPI.RECORD_CUSTOM_ACTION,
            "parameter": json.dumps({"action_name": ""})
        }
        logger.debug("Teach recording keepalive")
        return await self._send_command(payload, service=Service.ARM)

    async def stop_teach_recording(self) -> dict:
        """Stop teach-mode recording (API 7110 with EMPTY parameter - phone log confirmed)."""
        payload = {
            "api_id": ArmAPI.RECORD_CUSTOM_ACTION,
            "parameter": ""  # Empty string, NOT json.dumps({"action_name": ""})
        }
        logger.info("Stopping teach recording")
        result = await self._send_command(payload, service=Service.ARM)
        
        # Unsubscribe from action state updates
        try:
            self.datachannel.pub_sub.unsubscribe("rt/arm/action/state")
            logger.info("✅ Unsubscribed from rt/arm/action/state topic")
        except Exception as e:
            logger.warning(f"Failed to unsubscribe from action state: {e}")
        
        return result

    async def rename_custom_action(self, old_name: str, new_name: str) -> dict:
        """
        Rename a taught action (API 7109).

        Args:
            old_name: Existing action name
            new_name: New action name

        Returns:
            Command payload
        """
        payload = {
            "api_id": ArmAPI.RENAME_CUSTOM_ACTION,
            "parameter": json.dumps({"pre_name": old_name, "new_name": new_name})
        }
        logger.info(f"Renaming action '{old_name}' -> '{new_name}'")
        return await self._send_command(payload, service=Service.ARM)
    
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
    
    async def send_api_request(self, api_id: int, parameter: dict = None) -> dict:
        """
        Send raw API request to robot
        
        Args:
            api_id: API command ID (7106-7108, 7113 for arm actions)
            parameter: Optional parameters dict
            
        Returns:
            Response from robot (if available)
        """
        payload = {
            "api_id": api_id,
            "parameter": parameter or {}
        }
        
        # Determine service based on API ID
        # 7100-7199 are typically arm service APIs
        service = Service.ARM if 7100 <= api_id < 7200 else Service.SPORT
        
        return await self._send_command(payload, service=service)
    
    # ========================================================================
    # Custom Action Management (Phone Log APIs 7107-7110, 7113)
    # ========================================================================
    
    async def get_custom_action_list(self) -> dict:
        """
        Get list of saved custom actions (API 7107)
        
        Returns:
            Response with action list
        """
        payload = {
            "api_id": ArmAPI.GET_CUSTOM_ACTION_LIST,
            "parameter": json.dumps({})
        }
        logger.info("📋 Getting custom action list (API 7107)")
        return await self._send_command(payload, service=Service.ARM)
    
    # =========================================================================
    # SLAM Control (enables/disables LiDAR)
    # =========================================================================
    
    async def slam_start_mapping(self):
        """Start SLAM mapping - this enables the LiDAR sensor
        
        Uses publish_request_new() which properly formats Client API calls
        
        Returns:
            dict: Command payload sent to robot
        """
        from g1_app.api import SlamAPI, Service
        
        payload = {
            "api_id": SlamAPI.START_MAPPING,
            "parameter": json.dumps({
                "data": {
                    "slam_type": "indoor"
                }
            })
        }
        
        logger.info("🗺️  Starting SLAM mapping (this enables LiDAR)")
        await self.datachannel.pub_sub.publish_request_new(
            f"rt/api/{Service.SLAM}/request",
            payload
        )
        return payload
    
    async def slam_stop_mapping(self, map_name: str = "temp_map"):
        """Stop SLAM mapping and save map
        
        Args:
            map_name: Name for the saved map file (without .pcd extension)
                     Recommended: test1-test10 to avoid filling disk
        
        Note: This keeps LiDAR active for relocation mode
        
        Returns:
            dict: Command payload sent to robot
        """
        from g1_app.api import SlamAPI, Service
        
        # Ensure .pcd extension
        if not map_name.endswith('.pcd'):
            map_name = f"{map_name}.pcd"
        
        payload = {
            "api_id": SlamAPI.END_MAPPING,
            "parameter": json.dumps({
                "data": {
                    "address": f"/home/unitree/{map_name}"
                }
            })
        }
        
        logger.info(f"🗺️  Stopping SLAM mapping, saving to {map_name}")
        await self.datachannel.pub_sub.publish_request_new(
            f"rt/api/{Service.SLAM}/request",
            payload
        )
        return payload
    
    async def slam_close(self):
        """Close SLAM completely - this disables the LiDAR sensor
        
        Returns:
            dict: Command payload sent to robot
        """
        from g1_app.api import SlamAPI, Service
        
        payload = {
            "api_id": SlamAPI.CLOSE_SLAM,
            "parameter": json.dumps({
                "data": {}
            })
        }
        
        logger.info("🗺️  Closing SLAM (disabling LiDAR)")
        await self.datachannel.pub_sub.publish_request_new(
            f"rt/api/{Service.SLAM}/request",
            payload
        )
        return payload
    
    async def slam_load_map(self, map_name: str, x: float = 0.0, y: float = 0.0, z: float = 0.0):
        """Load a saved map and initialize robot pose for navigation
        
        Args:
            map_name: Name of the map file (without .pcd extension)
            x, y, z: Initial position (meters)
        
        Returns:
            dict: Command payload sent to robot
        """
        from g1_app.api import SlamAPI, Service
        
        # Ensure .pcd extension
        if not map_name.endswith('.pcd'):
            map_name = f"{map_name}.pcd"
        
        payload = {
            "api_id": SlamAPI.INITIALIZE_POSE,
            "parameter": json.dumps({
                "data": {
                    "x": x,
                    "y": y,
                    "z": z,
                    "q_x": 0.0,
                    "q_y": 0.0,
                    "q_z": 0.0,
                    "q_w": 1.0,
                    "address": f"/home/unitree/{map_name}"
                }
            })
        }
        
        logger.info(f"🗺️  Loading map {map_name}, initial pose: ({x}, {y}, {z})")
        await self.datachannel.pub_sub.publish_request_new(
            f"rt/api/{Service.SLAM}/request",
            payload
        )
        return payload
    
    async def slam_navigate_to(self, x: float, y: float, z: float = 0.0):
        """Navigate to a target position in the loaded map
        
        Args:
            x, y, z: Target position (meters)
        
        Returns:
            dict: Command payload sent to robot
        """
        from g1_app.api import SlamAPI, Service
        
        payload = {
            "api_id": SlamAPI.POSE_NAVIGATION,
            "parameter": json.dumps({
                "data": {
                    "targetPose": {
                        "x": x,
                        "y": y,
                        "z": z,
                        "q_x": 0.0,
                        "q_y": 0.0,
                        "q_z": 0.0,
                        "q_w": 1.0
                    },
                    "mode": 1
                }
            })
        }
        
        logger.info(f"🎯 Navigating to ({x}, {y}, {z})")
        await self.datachannel.pub_sub.publish_request_new(
            f"rt/api/{Service.SLAM}/request",
            payload
        )
        return payload
    
    async def send_command_and_wait(self, topic: str, payload: dict, timeout: float = 5.0) -> dict:
        """
        Send a command and wait for response (simplified - just sends without waiting for specific response)
        
        Args:
            topic: Topic to publish to
            payload: Command payload
            timeout: Timeout in seconds
            
        Returns:
            Response or empty dict if timeout
        """
        try:
            logger.info(f"Sending command to {topic}: {payload}")
            await asyncio.wait_for(
                self.datachannel.pub_sub.publish_request_new(topic, payload),
                timeout=timeout
            )
            # Return success indicator - actual response handling would be more complex
            return {"success": True}
        except asyncio.TimeoutError:
            logger.warning(f"Command timeout on {topic}")
            return {"success": False, "error": "timeout"}
        except Exception as e:
            logger.error(f"Failed to send command: {e}")
            return {"success": False, "error": str(e)}
    
    async def slam_pause_navigation(self):
        """Pause current navigation"""
        from g1_app.api import SlamAPI, Service
        
        payload = {
            "api_id": SlamAPI.PAUSE_NAVIGATION,
            "parameter": json.dumps({"data": {}})
        }
        
        logger.info("⏸️  Pausing navigation")
        await self.datachannel.pub_sub.publish_request_new(
            f"rt/api/{Service.SLAM}/request",
            payload
        )
        return payload
    
    async def slam_resume_navigation(self):
        """Resume paused navigation"""
        from g1_app.api import SlamAPI, Service
        
        payload = {
            "api_id": SlamAPI.RESUME_NAVIGATION,
            "parameter": json.dumps({"data": {}})
        }
        
        logger.info("▶️  Resuming navigation")
        await self.datachannel.pub_sub.publish_request_new(
            f"rt/api/{Service.SLAM}/request",
            payload
        )
        return payload
    
    def send_lowcmd_arm_command(self, command: dict) -> bool:
        """
        Send arm motor commands via rt/lowcmd topic
        
        Standard DDS low-level motor control:
        - Topic: rt/lowcmd (standard motor command topic)
        - Message: LowCmd_ structure with 35 motor slots
        - Special: motor_cmd[29].q = weight for smooth transitions (0.0-1.0)
        
        Args:
            command: Arm command dict with joints list
            
        Returns:
            True if sent successfully
        """
        try:
            # Extract joint commands
            joints = command.get('joints', [])
            if not joints:
                logger.error("No joints in command")
                return False
            
            # Build LowCmd message for rt/arm_sdk topic
            # Structure has 35 total motor slots (29 real motors + 6 unused for special params)
            arm_sdk_msg = {
                "motor_cmd": []
            }
            
            # Initialize all 35 motor slots (29 motors + 6 unused)
            for i in range(35):
                arm_sdk_msg["motor_cmd"].append({
                    "q": 0.0,
                    "dq": 0.0,
                    "tau": 0.0,
                    "kp": 0.0,
                    "kd": 0.0
                })
            
            # Set transition weight in kNotUsedJoint (index 29)
            # When weight = 1.0, motors follow commanded positions
            # Weight should ramp from 0 to 1 over time for smooth transitions
            enable_arm_sdk = command.get('enable_arm_sdk', True)
            arm_sdk_msg["motor_cmd"][29]["q"] = 1.0 if enable_arm_sdk else 0.0
            
            # Set commanded joints
            for joint in joints:
                motor_index = joint.get('motor_index')
                if motor_index is None or motor_index < 0 or motor_index >= 29:
                    logger.error(f"Invalid motor index: {motor_index}")
                    continue
                
                arm_sdk_msg["motor_cmd"][motor_index] = {
                    "q": float(joint.get('q', 0.0)),
                    "dq": float(joint.get('dq', 0.0)),
                    "tau": float(joint.get('tau', 0.0)),
                    "kp": float(joint.get('kp', 60.0)),
                    "kd": float(joint.get('kd', 1.5))
                }
            
            # Allow topic override via command parameter
            topic = command.get('topic', 'rt/arm_sdk')
            
            logger.info(f"📤 Publishing to {topic}: {len(joints)} joints, weight={arm_sdk_msg['motor_cmd'][29]['q']}")
            
            # Publish to specified topic via WebRTC datachannel
            self.datachannel.pub_sub.publish_without_callback(
                topic,
                arm_sdk_msg
            )
            
            logger.info(f"✅ {topic} command sent")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send arm_sdk command: {e}", exc_info=True)
            return False
