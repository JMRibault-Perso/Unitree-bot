"""
API Constants - All API IDs, FSM states, and enums from Unitree SDK
"""

from enum import IntEnum, Enum


# ============================================================================
# DDS Topics
# ============================================================================
class Topic:
    """DDS topic names for subscriptions"""
    SPORT_MODE_STATE = "rt/sportmodestate"       # High-frequency (~100Hz) state
    SPORT_MODE_STATE_LF = "rt/lf/sportmodestate"  # Low-frequency (~20Hz) state
    LOW_STATE = "rt/lowstate"                     # Motor/sensor state
    LOW_CMD = "rt/lowcmd"                         # Motor commands
    BMS_STATE = "rt/lf/bms"                       # Battery management system
    
    # Multimedia topics  
    AUDIO_MSG = "rt/audio_msg"                    # ASR (speech recognition) messages
    
    # LiDAR topics
    LIDAR_CLOUD = "rt/utlidar/cloud_livox_mid360"  # Point cloud data (10Hz)
    LIDAR_IMU = "rt/utlidar/imu_livox_mid360"      # LiDAR IMU data (200Hz)


# ============================================================================
# Service Names
# ============================================================================
class Service:
    SPORT = "sport"  # Locomotion (LocoClient uses this confusingly)
    ARM = "arm"      # Arm actions and gestures
    ROBOT_STATE = "robot_state"  # Robot state management (RobotStateClient)
    SLAM = "slam_operate"  # SLAM and navigation service


# ============================================================================
# System Service Names (for ServiceSwitch API)
# ============================================================================
class SystemService:
    """Service names for RobotStateClient.ServiceSwitch()"""
    AI_SPORT = "ai_sport"              # Main motion control service
    BASIC_SERVICE = "basic_service"    # Basic service
    ARM_EXAMPLE = "g1_arm_example"     # Upper limb motion service
    VUI_SERVICE = "vui_service"        # Audio and lighting control
    UNITREE_SLAM = "unitree_slam"      # Navigation service
    LIDAR_DRIVER = "lidar_driver"      # LiDAR driver (not in official list but used in SLAM docs)


# ============================================================================
# Robot State API IDs (robot_state Service)
# ============================================================================
class RobotStateAPI(IntEnum):
    """RobotStateClient API IDs for service management"""
    SERVICE_SWITCH = 5001  # Enable/disable services
    SET_REPORT_FREQ = 5002  # Set service status reporting frequency
    # Error codes: 5201 (switch execution error), 5202 (service protected)


# ============================================================================
# Locomotion API IDs (Sport Service)
# ============================================================================
class LocoAPI(IntEnum):
    """Locomotion/LocoClient API IDs"""
    # Getters
    GET_FSM_ID = 7001
    GET_FSM_MODE = 7002
    GET_BALANCE_MODE = 7003
    GET_SWING_HEIGHT = 7004
    GET_STAND_HEIGHT = 7005
    
    # Setters
    SET_FSM_ID = 7101           # Change FSM state
    SET_BALANCE_MODE = 7102
    SET_SWING_HEIGHT = 7103
    SET_STAND_HEIGHT = 7104
    SET_VELOCITY = 7105         # Movement control
    SET_ARM_TASK = 7106         # Arm gestures (wave, shake hand)
    SET_SPEED_MODE = 7107


# ============================================================================
# Arm Action API IDs (Arm Service)
# ============================================================================
class ArmAPI(IntEnum):
    """Arm action client API IDs"""
    EXECUTE_ACTION = 7106           # Execute pre-programmed gesture
    GET_ACTION_LIST = 7107          # Retrieve available gestures
    EXECUTE_CUSTOM_ACTION = 7108    # Play teach mode recording
    
    # Undocumented APIs (gaps in numbering - likely recording APIs)
    START_RECORD_ACTION = 7109      # EXPERIMENTAL: Start recording teach action
    STOP_RECORD_ACTION = 7110       # EXPERIMENTAL: Stop recording
    SAVE_RECORDED_ACTION = 7111     # EXPERIMENTAL: Save recording with name
    DELETE_ACTION = 7112            # EXPERIMENTAL: Delete saved action
    
    STOP_CUSTOM_ACTION = 7113       # Stop teach playback


# ============================================================================
# SLAM API IDs (SLAM Service)
# ============================================================================
class SlamAPI(IntEnum):
    """SLAM and navigation service API IDs"""
    START_MAPPING = 1801      # Start SLAM mapping (enables LiDAR)
    END_MAPPING = 1802        # End mapping and save map
    INITIALIZE_POSE = 1804    # Load map and start relocation
    POSE_NAVIGATION = 1102    # Navigate to target pose
    PAUSE_NAVIGATION = 1201   # Pause navigation
    RESUME_NAVIGATION = 1202  # Resume navigation
    CLOSE_SLAM = 1901         # Close SLAM (disables LiDAR)


# ============================================================================
# FSM States and Modes
# ============================================================================
class FSMState(IntEnum):
    """Finite State Machine states for G1 locomotion"""
    ZERO_TORQUE = 0         # All motors passive, no damping
    DAMP = 1                # Damping mode, can enter ready
    SQUAT = 2               # Squat position
    SIT = 3                 # Seated mode
    LOCK_STANDING = 4       # Lock standing position (no balance control)
    
    # Main motion states
    START = 200             # Ready mode (preparatory posture)
    LOCK_STAND = 500        # Standing with balance (basic) - GESTURES ALLOWED
    LOCK_STAND_ADV = 501    # Standing with balance + 3DOF waist - GESTURES ALLOWED
    
    # Recovery states (available in DAMP and ZERO_TORQUE modes)
    STAND_UP = 702          # Stand up from lying position
    SQUAT_TO_STAND = 706    # Squat/stand toggle (bidirectional)
    
    # Motion modes (with balance control)
    RUN = 801               # Run mode (faster speeds) - GESTURES ALLOWED when fsm_mode ∈ {0, 3}


class FSMMode(IntEnum):
    """
    FSM sub-modes within FSM states
    
    CRITICAL: In RUN mode (FSM state 801), gestures ONLY work when fsm_mode is 0 or 3
    SDK error code 7404 (UT_ROBOT_ARM_ACTION_ERR_INVALID_FSM_ID) returned if invalid
    """
    MODE_0 = 0  # Gesture-compatible mode in RUN
    MODE_1 = 1  # Gesture-incompatible
    MODE_2 = 2  # Gesture-incompatible
    MODE_3 = 3  # Gesture-compatible mode in RUN


# Gesture-compatible FSM states
GESTURE_COMPATIBLE_STATES = {
    FSMState.LOCK_STAND,      # 500 - Always allows gestures
    FSMState.LOCK_STAND_ADV,  # 501 - Always allows gestures
    FSMState.RUN              # 801 - Requires fsm_mode ∈ {0, 3}
}

# Valid fsm_modes for gestures in RUN mode (801)
GESTURE_COMPATIBLE_RUN_MODES = {FSMMode.MODE_0, FSMMode.MODE_3}


# ============================================================================
# LED Colors (mapped to FSM states)
# ============================================================================
class LEDColor(Enum):
    """LED strip colors indicating robot state"""
    BLUE = "blue"           # Normal operation
    ORANGE = "orange"       # Damp mode
    GREEN = "green"         # Seated mode
    YELLOW = "yellow"       # Debug mode
    PURPLE = "purple"       # Zero torque mode
    DARK_BLUE = "darkblue"  # Standby mode
    RED = "red"             # Error state


# Map FSM states to LED colors
FSM_TO_LED = {
    FSMState.ZERO_TORQUE: LEDColor.PURPLE,
    FSMState.DAMP: LEDColor.ORANGE,
    FSMState.SIT: LEDColor.GREEN,
    FSMState.START: LEDColor.BLUE,
    FSMState.LOCK_STAND: LEDColor.BLUE,        # Walk mode
    FSMState.LOCK_STAND_ADV: LEDColor.BLUE,    # Walk mode with 3DOF waist (motion recording)
    FSMState.RUN: LEDColor.DARK_BLUE,          # Run mode (faster)
}


# ============================================================================
# Arm Gesture IDs
# ============================================================================
class ArmGesture(IntEnum):
    """Pre-programmed arm gestures"""
    RELEASE_ARM = 99        # Stop gesture / release hold
    
    # Gestures
    TWO_HAND_KISS = 11
    LEFT_KISS = 12
    RIGHT_KISS = 12  # Same as left
    HANDS_UP = 15
    CLAP = 17
    HIGH_FIVE = 18
    HUG = 19
    HEART = 20          # Two hands
    RIGHT_HEART = 21    # One hand
    REJECT = 22
    RIGHT_HAND_UP = 23
    X_RAY = 24
    FACE_WAVE = 25
    HIGH_WAVE = 26
    SHAKE_HAND = 27


# ============================================================================
# Arm Task IDs (for simple gestures via SET_ARM_TASK)
# ============================================================================
class ArmTask(IntEnum):
    """Simple arm tasks via LocoClient SetTaskId"""
    WAVE_HAND = 0
    WAVE_HAND_TURN = 1
    SHAKE_HAND_STAGE_1 = 2
    SHAKE_HAND_STAGE_2 = 3


# ============================================================================
# DDS Topics
# ============================================================================
class Topic:
    """DDS topic names"""
    # State
    SPORT_MODE_STATE = "rt/sportmodestate"
    SPORT_MODE_STATE_LF = "rt/lf/sportmodestate"  # Low-frequency
    
    # Commands
    API_SPORT_REQUEST = "rt/api/sport/request"
    API_ARM_REQUEST = "rt/api/arm/request"
    
    # Odometry
    ODOM_STATE = "rt/odommodestate"           # 500Hz
    ODOM_STATE_LF = "rt/lf/odommodestate"     # 20Hz
    
    # LiDAR
    LIDAR_CLOUD = "rt/utlidar/cloud_livox_mid360"   # 10Hz PointCloud2
    LIDAR_IMU = "rt/utlidar/imu_livox_mid360"       # 200Hz IMU
    
    # Audio/VUI
    AUDIO_MSG = "rt/audio_msg"  # ASR results
    
    # Battery
    BMS_STATE = "rt/lf/bms"  # Battery management system
    
    # Low-level (for reference, not used in high-level control)
    LOW_STATE = "rt/lowstate"
    LOW_CMD = "rt/lowcmd"


# ============================================================================
# Speed Modes (RUN mode only)
# ============================================================================
class SpeedMode(IntEnum):
    """Speed levels for RUN mode (FSM 801)"""
    LOW = 0      # 1.0 m/s
    MEDIUM = 1   # 2.0 m/s
    HIGH = 2     # 2.7 m/s
    ULTRA = 3    # 3.0 m/s

# Speed mode to max speed mapping (m/s)
SPEED_MODE_LIMITS = {
    SpeedMode.LOW: 1.0,
    SpeedMode.MEDIUM: 2.0,
    SpeedMode.HIGH: 2.7,
    SpeedMode.ULTRA: 3.0,
}


# ============================================================================
# TTS Speaker IDs
# ============================================================================
class TTSSpeaker(IntEnum):
    """Text-to-speech speaker selection"""
    CHINESE = 0
    ENGLISH = 1


# ============================================================================
# Velocity Limits and Thresholds
# ============================================================================
class VelocityLimits:
    """
    Velocity limits and thresholds for movement control
    
    Mode-based maximum speeds:
    - WALK mode (500/501): 1.0 m/s linear, 1.0 rad/s angular
    - RUN mode (801): Depends on SpeedMode setting (1.0 - 3.0 m/s)
    
    Normalization:
    - Commands sent as percentage of max speed for current mode
    - value / get_max_speed(fsm_state, speed_mode)
    
    Minimum thresholds (dead zone):
    - Below MIN, command is set to 0 to prevent unintentional drift
    - Applied regardless of mode (WALK/RUN)
    """
    # WALK mode limits
    WALK_MAX_LINEAR = 1.0    # m/s
    WALK_MAX_STRAFE = 1.0    # m/s
    WALK_MAX_ANGULAR = 1.0   # rad/s
    
    # RUN mode limits (varies by SpeedMode setting)
    # See SPEED_MODE_LIMITS for linear speed
    RUN_MAX_STRAFE = 1.0     # m/s (strafe limited in RUN)
    RUN_MAX_ANGULAR = 1.5    # rad/s (faster turns in RUN)
    
    # Minimum speed thresholds (dead zone)
    MIN_LINEAR = 0.05   # m/s - minimum forward/backward before stopping
    MIN_STRAFE = 0.5    # m/s - minimum strafe before stopping
    MIN_ANGULAR = 0.05  # rad/s - minimum rotation before stopping
    
    @staticmethod
    def get_max_linear(fsm_state: 'FSMState', speed_mode: SpeedMode = SpeedMode.LOW) -> float:
        """Get max linear speed based on FSM state and speed mode"""
        if fsm_state == FSMState.RUN:
            return SPEED_MODE_LIMITS.get(speed_mode, 1.0)
        return VelocityLimits.WALK_MAX_LINEAR
    
    @staticmethod
    def get_max_strafe(fsm_state: 'FSMState') -> float:
        """Get max strafe speed based on FSM state"""
        if fsm_state == FSMState.RUN:
            return VelocityLimits.RUN_MAX_STRAFE
        return VelocityLimits.WALK_MAX_STRAFE
    
    @staticmethod
    def get_max_angular(fsm_state: 'FSMState') -> float:
        """Get max angular speed based on FSM state"""
        if fsm_state == FSMState.RUN:
            return VelocityLimits.RUN_MAX_ANGULAR
        return VelocityLimits.WALK_MAX_ANGULAR

    DEFAULT_LINEAR = 0.5
    DEFAULT_STRAFE = 0.5
    DEFAULT_ANGULAR = 0.5
