"""
API Constants - All API IDs, FSM states, and enums from Unitree SDK
"""

from enum import IntEnum, Enum


# ============================================================================
# Service Names
# ============================================================================
class Service:
    SPORT = "sport"  # Locomotion (LocoClient uses this confusingly)
    ARM = "arm"      # Arm actions and gestures


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
    STOP_CUSTOM_ACTION = 7113       # Stop teach playback


# ============================================================================
# FSM States
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
    LOCK_STAND = 500        # Standing with balance (basic)
    LOCK_STAND_ADV = 501    # Standing with balance + 3DOF waist (motion recording mode)
    
    # Recovery states (available in DAMP and ZERO_TORQUE modes)
    STAND_UP = 702          # Stand up from lying position
    SQUAT_TO_STAND = 706    # Squat/stand toggle (bidirectional)
    
    # Motion modes (with balance control)
    RUN = 801               # Run mode (faster speeds, supports arm actions)


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
    
    # Low-level (for reference, not used in high-level control)
    LOW_STATE = "rt/lowstate"
    LOW_CMD = "rt/lowcmd"


# ============================================================================
# Speed Modes
# ============================================================================
class SpeedMode(IntEnum):
    """Walking/running speed levels"""
    LOW = 0
    MEDIUM = 1
    HIGH = 2


# ============================================================================
# TTS Speaker IDs
# ============================================================================
class TTSSpeaker(IntEnum):
    """Text-to-speech speaker selection"""
    CHINESE = 0
    ENGLISH = 1


# ============================================================================
# Velocity Limits (safety)
# ============================================================================
class VelocityLimits:
    """Safe velocity limits for movement"""
    MAX_LINEAR = 0.8    # m/s
    MAX_STRAFE = 0.5    # m/s  
    MAX_ANGULAR = 1.0   # rad/s
    
    DEFAULT_LINEAR = 0.3
    DEFAULT_STRAFE = 0.2
    DEFAULT_ANGULAR = 0.5
