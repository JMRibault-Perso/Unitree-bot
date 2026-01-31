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
    
    async def execute_gesture(self, gesture: ArmGesture) -> dict:
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
        return await self._send_command(payload, service=Service.ARM)
    
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
    
    async def execute_custom_action(self, action_name: str) -> dict:
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
    
    async def start_record_action(self) -> dict:
        """
        EXPERIMENTAL: Start recording a teach mode action
        
        Returns:
            Command payload
        """
        payload = {
            "api_id": ArmAPI.START_RECORD_ACTION,
            "parameter": "{}"
        }
        logger.info("EXPERIMENTAL: Starting action recording (API 7109)")
        return await self._send_command(payload, service=Service.ARM)
    
    async def stop_record_action(self) -> dict:
        """
        EXPERIMENTAL: Stop recording teach mode action
        
        Returns:
            Command payload
        """
        payload = {
            "api_id": ArmAPI.STOP_RECORD_ACTION,
            "parameter": "{}"
        }
        logger.info("EXPERIMENTAL: Stopping action recording (API 7110)")
        return await self._send_command(payload, service=Service.ARM)
    
    async def save_recorded_action(self, action_name: str) -> dict:
        """
        EXPERIMENTAL: Save recorded action with a name
        
        Args:
            action_name: Name to save the action under
            
        Returns:
            Command payload
        """
        payload = {
            "api_id": ArmAPI.SAVE_RECORDED_ACTION,
            "parameter": json.dumps({"action_name": action_name})
        }
        logger.info(f"EXPERIMENTAL: Saving recorded action as '{action_name}' (API 7111)")
        return await self._send_command(payload, service=Service.ARM)
    
    async def delete_action(self, action_name: str) -> dict:
        """
        EXPERIMENTAL: Delete a saved action
        
        Args:
            action_name: Name of action to delete
            
        Returns:
            Command payload
        """
        payload = {
            "api_id": ArmAPI.DELETE_ACTION,
            "parameter": json.dumps({"action_name": action_name})
        }
        logger.info(f"EXPERIMENTAL: Deleting action '{action_name}' (API 7112)")
        return await self._send_command(payload, service=Service.ARM)
    
    async def rename_action(self, old_name: str, new_name: str) -> dict:
        """
        EXPERIMENTAL: Rename a saved action
        
        Args:
            old_name: Current name of the action
            new_name: New name for the action
            
        Returns:
            Command payload
        """
        payload = {
            "api_id": ArmAPI.RENAME_ACTION,
            "parameter": json.dumps({"old_name": old_name, "new_name": new_name})
        }
        logger.info(f"EXPERIMENTAL: Renaming action '{old_name}' to '{new_name}' (API 7113)")
        return await self._send_command(payload, service=Service.ARM)
    
    async def stop_custom_action(self) -> dict:
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
    
    async def send_api_request(self, api_id: int, parameter: dict = None) -> dict:
        """
        Send raw API request to robot
        
        Args:
            api_id: API command ID (e.g., 7107 for GetActionList, 7109-7112 for recording)
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
    # Teaching Mode Commands (WebRTC Datachannel Protocol)
    # ========================================================================
    
    async def list_teaching_actions(self) -> dict:
        """
        Query robot for list of saved teaching actions
        
        Uses WebRTC datachannel to send teaching protocol command 0x1A
        
        Returns:
            Response with action list
        """
        logger.info("📋 Querying teaching actions...")
        
        # Send raw teaching protocol packet via WebRTC
        # Teaching mode uses datachannel directly with binary protocol
        return await self._send_teaching_command(cmd_id=0x1A)
    
    async def enter_teaching_mode(self) -> dict:
        """
        Enter damping/teaching mode (command 0x0D)
        
        Puts robot into compliant state for manual manipulation
        
        Returns:
            Response from robot
        """
        logger.warning("⚠️  ENTERING TEACHING MODE - Robot will become compliant!")
        return await self._send_teaching_command(cmd_id=0x0D, extended_payload=True)
    
    async def exit_teaching_mode(self) -> dict:
        """
        Exit damping/teaching mode (command 0x0E)
        
        Returns robot to normal control
        
        Returns:
            Response from robot
        """
        logger.info("Exiting teaching mode...")
        return await self._send_teaching_command(cmd_id=0x0E)
    
    async def start_recording(self) -> dict:
        """
        Start recording trajectory (command 0x0F)
        
        Must be in teaching mode first
        
        Returns:
            Response from robot
        """
        logger.info("▶️  Starting trajectory recording...")
        return await self._send_teaching_command(cmd_id=0x0F, payload_data=bytes([0x01]) + bytes(43))
    
    async def stop_recording(self) -> dict:
        """
        Stop recording trajectory (command 0x0F toggle)
        
        Returns:
            Response from robot
        """
        logger.info("⏹️  Stopping trajectory recording...")
        return await self._send_teaching_command(cmd_id=0x0F, payload_data=bytes([0x00]) + bytes(43))
    
    async def save_teaching_action(self, action_name: str, duration_ms: int = 0) -> dict:
        """
        Save recorded teaching action (command 0x2B)
        
        Args:
            action_name: Name for the saved action
            duration_ms: Duration in milliseconds
            
        Returns:
            Response from robot
        """
        logger.info(f"💾 Saving teaching action: {action_name}")
        
        # Build payload with action name and duration
        import struct
        payload = bytearray(144)
        
        # Action name (32 bytes, null-terminated)
        name_bytes = action_name.encode('utf-8')[:31]
        payload[0:len(name_bytes)] = name_bytes
        
        # Duration (4 bytes at offset 32)
        struct.pack_into('>I', payload, 32, duration_ms)
        
        return await self._send_teaching_command(cmd_id=0x2B, payload_data=bytes(payload))
    
    async def play_teaching_action(self, action_id: int = 1) -> dict:
        """
        Play recorded teaching action (command 0x41)
        
        Args:
            action_id: ID of the action to play
            
        Returns:
            Response from robot
        """
        logger.info(f"▶️  Playing teaching action {action_id}...")
        
        # Build playback payload
        import struct
        payload = bytearray(144)
        struct.pack_into('>I', payload, 0, action_id)
        
        return await self._send_teaching_command(cmd_id=0x41, payload_data=bytes(payload))
    
    async def _send_teaching_command(self, cmd_id: int, payload_data: bytes = None, extended_payload: bool = False) -> dict:
        """
        Send teaching mode command via WebRTC datachannel
        
        Teaching protocol (reverse-engineered from PCAP):
        - Port: 49504 (but via WebRTC datachannel in this case)
        - Format: Type 0x17, magic 0xFE 0xFD 0x00, CRC32 checksum
        
        Args:
            cmd_id: Command ID (0x1A, 0x0D, 0x0E, 0x0F, 0x2B, 0x41)
            payload_data: Optional custom payload (44 or 144 bytes)
            extended_payload: If True, use 144-byte payload for extended state
            
        Returns:
            Command sent status
        """
        import struct
        import zlib
        
        # Build packet
        packet = bytearray()
        
        # Header (13 bytes)
        packet.append(0x17)                    # Message type
        packet.extend([0xFE, 0xFD, 0x00])     # Magic
        packet.extend([0x01, 0x00])            # Flags
        packet.extend([0x00, 0x00])            # Sequence (will be updated)
        packet.extend([0x00, 0x00])            # Reserved
        packet.extend([0x00, 0x01])            # Reserved
        packet.append(cmd_id)                   # Command ID
        
        # Payload (44 or 144 bytes)
        if payload_data:
            payload = payload_data
        elif extended_payload:
            payload = bytes(144)  # Full state packet
        else:
            payload = bytes(44)   # Standard packet
        
        packet.extend(struct.pack('>H', len(payload)))  # Payload length
        packet.extend(payload)
        
        # CRC32 checksum
        crc = zlib.crc32(packet) & 0xFFFFFFFF
        packet.extend(struct.pack('>I', crc))
        
        logger.info(f"📤 Teaching command 0x{cmd_id:02X}: {len(packet)} bytes")
        logger.debug(f"   Packet: {packet.hex()}")
        
        # Send via WebRTC datachannel
        try:
            # Use publish without callback for teaching commands
            self.datachannel.pub_sub.publish_without_callback(
                "rt/teaching_cmd",
                bytes(packet)
            )
            logger.info(f"✅ Teaching command sent")
            return {"status": "sent", "cmd_id": cmd_id, "packet_size": len(packet)}
        except Exception as e:
            logger.error(f"❌ Failed to send teaching command: {e}")
            return {"status": "error", "error": str(e)}
