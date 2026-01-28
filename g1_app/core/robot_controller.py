"""
Robot Controller - Main orchestrator for G1 robot control
"""

import asyncio
import sys
import logging
from typing import Optional

# Add WebRTC library to path
sys.path.insert(0, '/root/G1/go2_webrtc_connect')

from unitree_webrtc_connect.webrtc_driver import UnitreeWebRTCConnection
from unitree_webrtc_connect.constants import WebRTCConnectionMethod

from ..core.state_machine import StateMachine, FSMState
from ..core.command_executor import CommandExecutor
from ..core.event_bus import EventBus, Events
from ..api.constants import Topic, SpeedMode, VelocityLimits

logger = logging.getLogger(__name__)


class RobotController:
    """
    Main robot controller - manages connection, state, and commands
    """
    
    def __init__(self, robot_ip: str, robot_sn: str):
        """
        Args:
            robot_ip: Robot IP address (discovered dynamically)
            robot_sn: Robot serial number (e.g., "E21D1000PAHBMB06")
        """
        self.robot_ip = robot_ip
        self.robot_sn = robot_sn
        self.serial_number = robot_sn  # Alias for compatibility
        
        # Core components
        self.state_machine = StateMachine()
        self.conn: Optional[UnitreeWebRTCConnection] = None
        self.executor: Optional[CommandExecutor] = None
        
        # Connection state
        self.connected = False
        
        # Speed mode tracking (for RUN mode)
        self.current_speed_mode = SpeedMode.LOW
        
        # Track first FSM state received after connection
        self._first_state_logged = False
        
        logger.info(f"Initialized RobotController for {robot_sn} @ {robot_ip}")
    
    async def connect(self) -> None:
        """Establish WebRTC connection to robot"""
        if self.connected:
            logger.warning("Already connected")
            return
        
        logger.info(f"Connecting to G1 at {self.robot_ip}...")
        
        try:
            # Create WebRTC connection
            self.conn = UnitreeWebRTCConnection(
                WebRTCConnectionMethod.LocalSTA,
                ip=self.robot_ip,
                serialNumber=self.robot_sn
            )
            
            try:
                await self.conn.connect()
            except SystemExit:
                # WebRTC driver calls sys.exit(1) on failure - catch it
                raise ConnectionError(f"Failed to establish WebRTC connection to {self.robot_ip}. Check if robot is powered on and ports 8081/9991 are accessible.")
            
            # Create command executor
            self.executor = CommandExecutor(self.conn.datachannel)
            
            # Subscribe to robot state topic
            self._subscribe_to_state()
            
            # Subscribe to battery updates
            self._subscribe_to_battery()
            
            # NOTE: GET_FSM_ID and GET_FSM_MODE APIs don't return reliable state
            # API 7001 returns unknown values (e.g., 801)
            # API 7002 returns mode (0) not actual FSM state
            # We track state by monitoring commands we send
            logger.info("⚠️  Initial state unknown - assuming ZERO_TORQUE. Send DAMP command to sync.")
            
            self.connected = True
            EventBus.emit(Events.CONNECTION_CHANGED, {"connected": True})
            
            logger.info("✅ Connected to robot")
            
        except Exception as e:
            logger.error(f"Connection failed: {e}")
            EventBus.emit(Events.CONNECTION_CHANGED, {"connected": False, "error": str(e)})
            raise
    
    async def disconnect(self) -> None:
        """Close connection to robot"""
        if not self.connected:
            return
        
        logger.info("Disconnecting from robot...")
        
        if self.conn:
            await self.conn.disconnect()
        
        self.connected = False
        EventBus.emit(Events.CONNECTION_CHANGED, {"connected": False})
        
        logger.info("Disconnected")
    
    def _subscribe_to_state(self) -> None:
        """Subscribe to robot state topic for FSM tracking"""
        def on_state_update(data: dict):
            """Handle sport mode state updates"""
            try:
                if isinstance(data, dict) and 'data' in data:
                    state_data = data['data']
                    
                    # Extract FSM info from SportModeState message
                    # Fields: fsm_id (actual FSM state), fsm_mode (sub-mode), task_id, task_id_time
                    fsm_id = state_data.get('fsm_id')
                    fsm_mode = state_data.get('fsm_mode')
                    task_id = state_data.get('task_id')
                    
                    # 🎯 SPECIAL: Log first FSM state after connection
                    if not self._first_state_logged:
                        logger.warning("=" * 80)
                        logger.warning(f"🎯🎯🎯 FIRST FSM STATE ON CONNECTION 🎯🎯🎯")
                        logger.warning(f"FSM ID: {fsm_id}")
                        logger.warning(f"FSM MODE: {fsm_mode}")
                        logger.warning(f"TASK ID: {task_id}")
                        logger.warning("=" * 80)
                        self._first_state_logged = True
                    
                    # Debug logging (disabled - too verbose)
                    logger.info(f"🤖 Robot state update: fsm_id={fsm_id}, fsm_mode={fsm_mode}, task_id={task_id}")
                    
                    # Update state machine with actual FSM state
                    if fsm_id is not None:
                        try:
                            reported_state = FSMState(fsm_id)
                            current_state = self.state_machine.fsm_state
                            
                            # Only update if state actually changed
                            if reported_state != current_state:
                                logger.info(f"🔄 Robot state changed: {current_state.name} → {reported_state.name}")
                                self.state_machine.update_state(reported_state, fsm_mode=fsm_mode, task_id=task_id)
                                EventBus.emit(Events.STATE_CHANGED, {
                                    "fsm_state": reported_state.value,
                                    "fsm_state_name": reported_state.name,
                                    "fsm_mode": fsm_mode,
                                    "task_id": task_id
                                })
                        except ValueError:
                            # fsm_id doesn't match a known FSM state
                            logger.warning(f"Unknown FSM state: {fsm_id}")
            except Exception as e:
                logger.error(f"Error processing state update: {e}")
        
        try:
            # Subscribe to low-frequency sportmodestate (20Hz)
            # This is more reliable than high-frequency version
            self.conn.datachannel.pub_sub.subscribe(
                Topic.SPORT_MODE_STATE_LF,  # rt/lf/sportmodestate
                on_state_update
            )
            logger.info(f"✅ Subscribed to {Topic.SPORT_MODE_STATE_LF}")
        except Exception as e:
            logger.warning(f"Could not subscribe to state topic: {e}")
    
    def _subscribe_to_battery(self) -> None:
        """Subscribe to battery state updates
        
        G1 has BmsState_ message type with soc_, current_, temperature_, bmsvoltage_ fields.
        Trying rt/lf/bmsstate and other common patterns.
        """
        def on_bms_update(data: dict):
            """Handle BMS state updates"""
            logger.info(f"🔋 BMS CALLBACK! Topic: {data.get('topic', 'unknown')}")
            try:
                if isinstance(data, dict) and 'data' in data:
                    bms_data = data['data']
                    logger.info(f"🔋 BMS Keys: {list(bms_data.keys())[:30]}")
                    
                    # BmsState_ fields from SDK: soc_, current_, temperature_, bmsvoltage_
                    soc = bms_data.get('soc', bms_data.get('soc_', bms_data.get('battery_percentage', 0)))
                    current = bms_data.get('current', bms_data.get('current_', 0))
                    temperature = bms_data.get('temperature', bms_data.get('temperature_', [0]))
                    voltage = bms_data.get('bmsvoltage', bms_data.get('bmsvoltage_', [0]))
                    
                    # Temperature is array, take first one
                    temp_value = temperature[0] if isinstance(temperature, (list, tuple)) and len(temperature) > 0 else temperature
                    # Voltage is array, sum or take first
                    voltage_value = sum(voltage) / 1000.0 if isinstance(voltage, (list, tuple)) else voltage / 1000.0
                    
                    logger.info(f"🔋 Battery: {soc}% | {voltage_value}V | {current}mA | {temp_value}°C")
                    
                    EventBus.emit(Events.BATTERY_UPDATED, {
                        "soc": soc,
                        "voltage": voltage_value,
                        "current": current / 1000.0,  # mA to A
                        "temperature": temp_value
                    })
            except Exception as e:
                logger.error(f"Error processing BMS update: {e}", exc_info=True)
        
        try:
            # Try all possible BMS topic patterns
            potential_topics = [
                "rt/lf/bmsstate",     # Most likely based on lowstate pattern
                "rt/bmsstate",
                "rt/lf/agvbmsstate",
                "rt/agvbmsstate", 
                "rt/lf/bms",
                "rt/bms",
                "rt/battery",
                "rt/lf/battery",
                "rt/sensor/bms"       # Sensor data pattern
            ]
            
            for topic in potential_topics:
                try:
                    self.conn.datachannel.pub_sub.subscribe(topic, on_bms_update)
                    logger.info(f"✅ Subscribed to {topic} for BMS data")
                except Exception as sub_err:
                    logger.debug(f"Could not subscribe to {topic}: {sub_err}")
            
        except Exception as e:
            logger.warning(f"Could not subscribe to lowstate topic: {e}")
    
    # ========================================================================
    # Command Methods (delegate to executor)
    # ========================================================================
    
    async def set_speed_mode(self, speed_mode: SpeedMode) -> bool:
        """Set speed mode (RUN mode only)"""
        if not self.connected or not self.executor:
            return False
        
        # Only valid in RUN mode
        if self.state_machine.fsm_state != FSMState.RUN:
            logger.warning(f"Speed mode can only be set in RUN mode (current: {self.state_machine.fsm_state.name})")
            return False
        
        try:
            await self.executor.set_speed_mode(speed_mode)
            self.current_speed_mode = speed_mode
            logger.info(f"Set speed mode to {speed_mode.name} ({speed_mode.value})")
            return True
        except Exception as e:
            logger.error(f"Set speed mode failed: {e}")
            return False
    
    def get_max_speeds(self) -> dict:
        """Get current max speeds based on FSM state and speed mode"""
        fsm_state = self.state_machine.fsm_state
        return {
            'max_linear': VelocityLimits.get_max_linear(fsm_state, self.current_speed_mode),
            'max_strafe': VelocityLimits.get_max_strafe(fsm_state),
            'max_angular': VelocityLimits.get_max_angular(fsm_state),
            'speed_mode': self.current_speed_mode.value if fsm_state == FSMState.RUN else None
        }
    
    async def set_fsm_state(self, state: FSMState) -> bool:
        """
        Change FSM state with validation
        
        Args:
            state: Target FSM state
            
        Returns:
            True if command sent successfully
        """
        if not self.connected or not self.executor:
            logger.error("Not connected")
            return False
        
        # Validate transition (allow emergency transitions)
        if not self.state_machine.can_transition(state):
            # Allow DAMP and ZERO_TORQUE as emergency transitions
            if state not in [FSMState.DAMP, FSMState.ZERO_TORQUE]:
                current = self.state_machine.fsm_state
                logger.warning(f"Forcing transition: {current.name} → {state.name}")
        
        try:
            await self.executor.set_fsm_state(state)
            
            # Update state machine (optimistic)
            self.state_machine.update_state(state)
            
            # Give command time to be processed
            await asyncio.sleep(0.3)
            
            return True
            
        except Exception as e:
            logger.error(f"Command failed: {e}")
            return False
    
    async def set_velocity(self, vx: float = 0, vy: float = 0, omega: float = 0,
                          continuous: bool = True) -> bool:
        """Send velocity command"""
        if not self.connected or not self.executor:
            logger.error("Not connected")
            return False
        
        # Check if in motion-ready state
        if not self.state_machine.is_ready_for_motion():
            logger.error(f"Cannot move in state {self.state_machine.fsm_state.name}")
            return False
        
        try:
            await self.executor.set_velocity(vx, vy, omega, continuous=continuous)
            return True
        except Exception as e:
            logger.error(f"Velocity command failed: {e}")
            return False
    
    async def execute_gesture(self, gesture_name: str) -> dict:
        """Execute pre-programmed gesture by name"""
        if not self.connected or not self.executor:
            return {"success": False, "message": "Not connected"}
        
        try:
            from ..api.constants import ArmGesture, ArmTask
            
            # Try ArmGesture first
            gesture = getattr(ArmGesture, gesture_name.upper(), None)
            if gesture is not None:
                await self.executor.execute_gesture(gesture)
                return {"success": True, "message": f"Executing {gesture_name}"}
            
            # Try ArmTask second
            task = getattr(ArmTask, gesture_name.upper(), None)
            if task is not None:
                await self.executor.set_arm_task(task)
                return {"success": True, "message": f"Executing task {gesture_name}"}
            
            # Not found in either enum
            logger.error(f"Unknown gesture or task: {gesture_name}")
            return {"success": False, "message": f"Unknown gesture or task: {gesture_name}"}
            
        except Exception as e:
            logger.error(f"Gesture failed: {e}")
            return {"success": False, "message": str(e)}
    
    async def emergency_stop(self) -> bool:
        """Emergency stop - go to damp mode"""
        logger.warning("EMERGENCY STOP")
        if self.connected and self.executor:
            self.executor.go_to_damp_mode()
            self.state_machine.update_state(FSMState.DAMP)
            return True
        return False
    
    # Convenience methods
    # ⚠️⚠️⚠️ SAFETY: damp() disables motors - robot may fall. NEVER call programmatically! ⚠️⚠️⚠️
    # AI AGENTS: ONLY call when user explicitly clicks "Damp" button. Can cause injury.
    async def damp(self): return await self.set_fsm_state(FSMState.DAMP)
    async def ready(self): return await self.set_fsm_state(FSMState.START)
    async def sit(self): return await self.set_fsm_state(FSMState.SIT)
    async def squat_to_stand(self): return await self.set_fsm_state(FSMState.SQUAT_TO_STAND)
    
    async def stop(self): return await self.set_velocity(0, 0, 0)
    async def forward(self, speed=0.3): return await self.set_velocity(vx=speed)
    async def backward(self, speed=0.3): return await self.set_velocity(vx=-speed)
    async def left(self, speed=0.2): return await self.set_velocity(vy=speed)
    async def right(self, speed=0.2): return await self.set_velocity(vy=-speed)
    async def turn_left(self, speed=0.5): return await self.set_velocity(omega=speed)
    async def turn_right(self, speed=0.5): return await self.set_velocity(omega=-speed)
    
    async def get_custom_action_list(self) -> dict:
        """Get list of custom taught actions via API 7107"""
        if not self.connected or not self.executor:
            return {"success": False, "error": "Not connected"}
        
        try:
            result = await self.executor.send_api_request(7107, {})
            return {"success": True, "data": result}
        except Exception as e:
            logger.error(f"GetActionList failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def send_api_command(self, api_id: int, parameter: dict = None) -> dict:
        """Send raw API command to robot
        
        Args:
            api_id: API command ID (e.g., 7109, 7110, etc.)
            parameter: Command parameters as dict
        
        Returns:
            dict with success status and response data
        """
        if not self.connected or not self.executor:
            return {"success": False, "error": "Not connected"}
        
        try:
            result = await self.executor.send_api_request(api_id, parameter or {})
            return {"success": True, "data": result}
        except Exception as e:
            logger.error(f"API {api_id} failed: {e}")
            return {"success": False, "error": str(e)}
    
    # Properties
    @property
    def current_state(self):
        return self.state_machine.current_state
    
    @property
    def is_connected(self):
        return self.connected
