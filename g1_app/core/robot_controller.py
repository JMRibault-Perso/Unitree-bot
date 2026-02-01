"""
Robot Controller - Main orchestrator for G1 robot control
"""

import asyncio
import sys
import logging
import struct
from typing import Optional

# Add WebRTC library to path
sys.path.insert(0, '/root/G1/go2_webrtc_connect')

from unitree_webrtc_connect.webrtc_driver import UnitreeWebRTCConnection
from unitree_webrtc_connect.constants import WebRTCConnectionMethod

from ..core.state_machine import StateMachine, FSMState
from ..core.command_executor import CommandExecutor
from ..core.event_bus import EventBus, Events
from ..api.constants import Topic, SpeedMode, VelocityLimits
from ..core.lidar_handler import LiDARPointCloudHandler

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
        
        # Video frame storage
        self.latest_frame = None
        
        # LiDAR point cloud storage and handler
        self.latest_lidar_points = []
        self.lidar_handler = LiDARPointCloudHandler()
        
        # Register callback to update latest_lidar_points when new data arrives
        def on_point_cloud_update(binary_data: bytes, metadata: dict):
            try:
                # Parse binary data to XYZ points
                points = self._parse_slam_point_cloud(binary_data)
                
                # Downsample for web display (every 10th point)
                self.latest_lidar_points = points[::10]
                
                logger.debug(f"📊 Point cloud updated: {len(points)} points -> {len(self.latest_lidar_points)} downsampled")
                
                # Emit event for real-time UI updates
                event_bus.emit(Events.LIDAR_CLOUD, {'points': self.latest_lidar_points})
            except Exception as e:
                logger.error(f"Error updating point cloud display: {e}")
        
        self.lidar_handler.subscribe(on_point_cloud_update)
        
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
            
            # Subscribe to video frames
            self._subscribe_to_video()
            
            # Subscribe to SLAM feedback topics
            self._subscribe_to_slam_feedback()
            
            # DEBUG: Subscribe to ALL topics to see what's available
            self._debug_all_topics()
            
            # COMPREHENSIVE MESSAGE LOGGING - catch EVERYTHING
            self._log_all_datachannel_messages()
            
            # Subscribe to LiDAR point cloud
            self._subscribe_to_lidar()
            
            # Enable LiDAR driver service (required for LiDAR data to publish)
            await self._enable_lidar_service()
            
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
    
    def _subscribe_to_video(self) -> None:
        """Capture video frames from WebRTC video track"""
        try:
            import cv2
            import asyncio
            from aiortc import MediaStreamTrack
            
            # Check if WebRTC connection has video support
            if not hasattr(self.conn, 'video'):
                logger.warning("No video channel available from WebRTC connection")
                return
            
            # Enable video channel
            self.conn.video.switchVideoChannel(True)
            logger.info("✅ Video channel enabled")
            
            async def recv_video_frames(track: MediaStreamTrack):
                """Async callback to receive video frames"""
                logger.info("📹 Starting video frame reception")
                while True:
                    try:
                        # Receive frame from WebRTC track
                        frame = await track.recv()
                        
                        # Convert to numpy array
                        img = frame.to_ndarray(format="bgr24")
                        
                        # Encode to JPEG for streaming
                        _, buffer = cv2.imencode('.jpg', img, [cv2.IMWRITE_JPEG_QUALITY, 80])
                        self.latest_frame = buffer.tobytes()
                        
                    except Exception as e:
                        logger.error(f"Error receiving video frame: {e}")
                        break
            
            # Register video track callback
            self.conn.video.add_track_callback(recv_video_frames)
            logger.info("✅ Subscribed to video stream")
            
        except Exception as e:
            logger.warning(f"Could not subscribe to video: {e}")
            import traceback
            traceback.print_exc()
    
    def _subscribe_to_lidar(self) -> None:
        """Subscribe to SLAM mapping point clouds during active mapping
        
        Point clouds ONLY available during active SLAM mapping:
        1. Start mapping: API 1801 (START_MAPPING)
        2. Subscribe to rt/unitree/slam_mapping/points for real-time point clouds
        3. Subscribe to rt/unitree/slam_mapping/odom for odometry
        4. End mapping: API 1802 (END_MAPPING) to save map
        """
        try:
            # Enable LibVoxel decoder (patched to bypass for G1 SLAM)
            self.conn.datachannel.set_decoder(decoder_type='libvoxel')
            logger.info("✅ LibVoxel decoder enabled (with G1 SLAM bypass patch)")
            
            def on_slam_point_cloud(data: dict):
                """Handle SLAM mapping point cloud messages
                
                Patched decoder returns:
                {
                    'type': 'lidar_pointcloud',
                    'binary_data': bytes,  # Raw point cloud
                    'metadata': dict,      # JSON metadata
                    'size': int            # Binary data size
                }
                """
                try:
                    if isinstance(data, dict) and data.get('type') == 'lidar_pointcloud':
                        binary_data = data.get('binary_data')
                        metadata = data.get('metadata', {})
                        
                        if binary_data:
                            # Pass to LiDAR handler (triggers callbacks)
                            self.lidar_handler.set_raw_point_cloud(binary_data, metadata)
                            
                            logger.debug(f"📦 SLAM point cloud: {len(binary_data)} bytes, metadata: {list(metadata.keys())}")
                    else:
                        logger.warning(f"Unexpected point cloud data format: {type(data)}")
                        
                except Exception as e:
                    logger.error(f"Error processing SLAM point cloud: {e}")
                    import traceback
                    traceback.print_exc()
            
            def on_slam_odometry(data: dict):
                """Handle SLAM odometry updates"""
                try:
                    logger.debug(f"🧭 SLAM odometry update: {list(data.keys()) if isinstance(data, dict) else type(data)}")
                except Exception as e:
                    logger.error(f"Error processing odometry: {e}")
            
            # Subscribe to SLAM mapping topics
            # NOTE: These topics only publish data during ACTIVE SLAM mapping (API 1801)
            self.conn.datachannel.pub_sub.subscribe("rt/unitree/slam_mapping/points", on_slam_point_cloud)
            self.conn.datachannel.pub_sub.subscribe("rt/unitree/slam_mapping/odom", on_slam_odometry)
            
            logger.info("📡 Subscribed to SLAM mapping topics (rt/unitree/slam_mapping/*)")
            logger.info("ℹ️  Point clouds will only flow during active SLAM mapping (use /api/slam/start)")
            
        except Exception as e:
            logger.warning(f"Could not subscribe to SLAM mapping topics: {e}")
            import traceback
            traceback.print_exc()

    
    def _subscribe_to_slam_feedback(self) -> None:
        """Subscribe to SLAM feedback topics to monitor SLAM status"""
        try:
            # Initialize trajectory storage
            self.slam_trajectory = []  # List of {x, y, z, timestamp} pose points
            self.slam_active = False
            self.slam_last_pose = None  # Track last position for deduplication
            
            # rt/slam_info - Real-time broadcast info (robot data, pos info, ctrl info)
            def slam_info_callback(data: dict):
                try:
                    if isinstance(data, dict) and 'data' in data:
                        import json
                        import math
                        slam_data = json.loads(data['data']) if isinstance(data['data'], str) else data['data']
                        
                        # Collect trajectory points during mapping (with deduplication)
                        if slam_data.get('type') in ['mapping_info', 'pos_info']:
                            pose = slam_data.get('data', {}).get('currentPose')
                            if pose and self.slam_active:
                                # Only add point if robot moved > 5cm from last position
                                should_add = True
                                if self.slam_last_pose:
                                    dx = pose['x'] - self.slam_last_pose['x']
                                    dy = pose['y'] - self.slam_last_pose['y']
                                    dz = pose['z'] - self.slam_last_pose['z']
                                    distance = math.sqrt(dx*dx + dy*dy + dz*dz)
                                    should_add = distance > 0.05  # 5cm threshold
                                
                                if should_add:
                                    self.slam_trajectory.append({
                                        'x': pose['x'],
                                        'y': pose['y'],
                                        'z': pose['z'],
                                        'timestamp': slam_data.get('sec', 0)
                                    })
                                    self.slam_last_pose = pose
                                    
                                    # Limit to last 1000 points
                                    if len(self.slam_trajectory) > 1000:
                                        self.slam_trajectory = self.slam_trajectory[-1000:]
                                    
                                    logger.debug(f"📍 Trajectory point {len(self.slam_trajectory)}: ({pose['x']:.2f}, {pose['y']:.2f}, {pose['z']:.2f})")
                        
                except Exception as e:
                    logger.error(f"Error processing SLAM info: {e}")
            
            # rt/slam_key_info - Execution status feedback (task results)
            def slam_key_info_callback(data: dict):
                import json
                logger.info(f"🗺️  SLAM KEY INFO FULL: {json.dumps(data, indent=2)[:5000]}")
            
            # rt/api/slam_operate/response - API responses
            def slam_api_response_callback(data: dict):
                try:
                    if isinstance(data, dict) and 'data' in data:
                        response_data = data['data']
                        api_id = response_data.get('header', {}).get('identity', {}).get('api_id')
                        
                        # Track SLAM state
                        if api_id == 1801:  # START_MAPPING
                            self.slam_active = True
                            self.slam_trajectory = []  # Reset trajectory
                            logger.info("🗺️  SLAM mapping STARTED - trajectory collection enabled")
                        elif api_id in [1802, 1901]:  # END_MAPPING or CLOSE_SLAM
                            self.slam_active = False
                            logger.info(f"🗺️  SLAM mapping STOPPED - collected {len(self.slam_trajectory)} points")
                        
                        logger.info(f"🗺️  SLAM API RESPONSE: api_id={api_id}")
                except Exception as e:
                    logger.error(f"Error processing SLAM response: {e}")
            
            self.conn.datachannel.pub_sub.subscribe("rt/slam_info", slam_info_callback)
            self.conn.datachannel.pub_sub.subscribe("rt/slam_key_info", slam_key_info_callback)
            self.conn.datachannel.pub_sub.subscribe("rt/api/slam_operate/response", slam_api_response_callback)
            
            logger.info("📡 Subscribed to SLAM feedback topics")
            
        except Exception as e:
            logger.warning(f"Could not subscribe to SLAM feedback: {e}")
    
    def _debug_all_topics(self) -> None:
        """Subscribe to common topics to see what's available"""
        debug_topics = [
            "rt/utlidar/cloud_livox_mid360",
            "rt/lidar/cloud",
            "rt/pointcloud",
            "rt/cloud",
        ]
        
        def debug_callback(topic_name):
            def callback(data: dict):
                logger.warning(f"🔍 DEBUG MESSAGE on {topic_name}: {type(data)} keys={list(data.keys()) if isinstance(data, dict) else 'not dict'}")
            return callback
        
        for topic in debug_topics:
            try:
                self.conn.datachannel.pub_sub.subscribe(topic, debug_callback(topic))
                logger.info(f"📡 Debug subscribed to: {topic}")
            except Exception as e:
                logger.debug(f"Could not subscribe to {topic}: {e}")
    
    def _log_all_datachannel_messages(self) -> None:
        """Patch datachannel to log ALL incoming messages"""
        try:
            original_dispatch = self.conn.datachannel.pub_sub._dispatch_message
            message_count = [0]
            seen_topics = set()
            
            def logging_dispatch(topic: str, message: any):
                """Intercept all messages before dispatch"""
                message_count[0] += 1
                
                # Log new topics
                if topic not in seen_topics:
                    seen_topics.add(topic)
                    logger.warning(f"🆕 NEW DATACHANNEL TOPIC: '{topic}'")
                
                # Log every 10th message for active monitoring
                if message_count[0] % 10 == 0:
                    msg_type = type(message).__name__
                    msg_size = len(str(message)) if hasattr(message, '__len__') else 'N/A'
                    logger.info(f"📨 [{message_count[0]}] {topic}: type={msg_type}, size={msg_size}")
                
                # Log ALL utlidar/lidar/slam messages
                if any(keyword in topic.lower() for keyword in ['utlidar', 'lidar', 'slam', 'voxel', 'cloud', 'point']):
                    logger.warning(f"🔶 LIDAR/SLAM MSG: topic='{topic}', type={type(message)}, size={len(str(message)) if hasattr(message, '__len__') else 'N/A'}")
                    if isinstance(message, dict):
                        logger.warning(f"🔶   Keys: {list(message.keys())}")
                
                # Call original dispatch
                return original_dispatch(topic, message)
            
            # Monkey-patch the dispatch method
            self.conn.datachannel.pub_sub._dispatch_message = logging_dispatch
            logger.warning("🔧 PATCHED datachannel to log ALL messages!")
            
        except Exception as e:
            logger.error(f"Failed to patch datachannel logging: {e}")
    
    async def _enable_lidar_service(self) -> None:
        """Enable LiDAR driver service to publish point cloud data"""
        try:
            from ..api.constants import SystemService
            
            # Subscribe to response topic to see what robot says
            def on_robot_state_response(data: dict):
                logger.warning(f"🔧 ROBOT_STATE RESPONSE: {data}")
            
            self.conn.datachannel.pub_sub.subscribe("rt/api/robot_state/response", on_robot_state_response)
            
            logger.info("Enabling lidar_driver service...")
            response = await self.executor.service_switch(
                service_name=SystemService.LIDAR_DRIVER,
                enable=True
            )
            
            # Wait a moment for response
            await asyncio.sleep(0.5)
            
            logger.info(f"LiDAR service command sent: {response}")
                
        except Exception as e:
            logger.warning(f"Could not enable LiDAR service: {e}")
    
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
    
    def _parse_slam_point_cloud(self, binary_data: bytes) -> list:
        """Parse SLAM point cloud binary data to XYZ coordinates
        
        G1 SLAM point cloud format appears to be:
        - Array of float32 values
        - Structure: [x1, y1, z1, x2, y2, z2, ...]
        
        Args:
            binary_data: Raw binary point cloud from rt/unitree/slam_mapping/points
            
        Returns:
            List of [x, y, z] coordinates
        """
        try:
            # Calculate number of floats (4 bytes each)
            num_floats = len(binary_data) // 4
            
            # Must be divisible by 3 for XYZ triplets
            if num_floats % 3 != 0:
                logger.warning(f"Point cloud data not divisible by 3: {num_floats} floats")
                # Truncate to nearest multiple of 3
                num_floats = (num_floats // 3) * 3
            
            points = []
            for i in range(0, num_floats, 3):
                offset = i * 4
                try:
                    # Unpack 3 consecutive float32 values (little-endian)
                    x, y, z = struct.unpack('<fff', binary_data[offset:offset+12])
                    points.append([x, y, z])
                except struct.error:
                    break
            
            logger.debug(f"📐 Parsed {len(points)} points from {len(binary_data)} bytes")
            return points
            
        except Exception as e:
            logger.error(f"Error parsing point cloud: {e}")
            return []
