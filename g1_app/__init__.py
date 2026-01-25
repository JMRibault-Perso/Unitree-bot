"""
G1 Robot Control Application

A comprehensive Python application for controlling Unitree G1 humanoid robot
with support for locomotion, arm control, voice interface, and sensor data.
"""

__version__ = '1.0.0'
__author__ = 'G1 Control Team'

from .core import (
    EventBus,
    Events,
    StateMachine,
    RobotState,
    CommandExecutor,
    RobotController,
)

from .api import (
    Service,
    LocoAPI,
    ArmAPI,
    FSMState,
    LEDColor,
    ArmGesture,
    ArmTask,
    Topic,
)

from .sensors import (
    OdometryManager,
    LiDARManager,
    VUIManager,
    VideoManager,
)

from .utils import (
    Config,
    config,
    setup_app_logging,
)

__all__ = [
    # Core
    'EventBus',
    'Events',
    'StateMachine',
    'RobotState',
    'CommandExecutor',
    'RobotController',
    
    # API
    'Service',
    'LocoAPI',
    'ArmAPI',
    'FSMState',
    'LEDColor',
    'ArmGesture',
    'ArmTask',
    'Topic',
    
    # Sensors
    'OdometryManager',
    'LiDARManager',
    'VUIManager',
    'VideoManager',
    
    # Utils
    'Config',
    'config',
    'setup_app_logging',
]
