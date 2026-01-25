"""Configuration Management"""

import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class RobotConfig:
    """Robot connection configuration"""
    ip: str
    serial_number: str
    timeout: float = 10.0
    
    @classmethod
    def from_env(cls) -> 'RobotConfig':
        """Load configuration from environment variables"""
        ip = os.getenv('G1_ROBOT_IP', None)  # No default IP - must be discovered
        sn = os.getenv('G1_ROBOT_SN', 'E21D1000PAHBMB06')
        timeout = float(os.getenv('G1_TIMEOUT', '10.0'))
        
        return cls(ip=ip, serial_number=sn, timeout=timeout)


@dataclass
class SensorConfig:
    """Sensor configuration"""
    enable_odometry: bool = True
    enable_lidar: bool = True
    enable_vui: bool = True
    enable_video: bool = True
    
    # Odometry settings
    odom_rate: str = 'high'  # 'high' (500Hz) or 'low' (20Hz)
    
    # LiDAR settings
    lidar_transform: bool = True  # Apply mount transform
    lidar_max_range: float = 70.0  # meters
    lidar_min_range: float = 0.05  # meters
    
    # Video settings
    video_fps: int = 30
    video_format: str = 'H264'
    
    @classmethod
    def from_env(cls) -> 'SensorConfig':
        """Load sensor config from environment"""
        return cls(
            enable_odometry=os.getenv('G1_ENABLE_ODOM', 'true').lower() == 'true',
            enable_lidar=os.getenv('G1_ENABLE_LIDAR', 'true').lower() == 'true',
            enable_vui=os.getenv('G1_ENABLE_VUI', 'true').lower() == 'true',
            enable_video=os.getenv('G1_ENABLE_VIDEO', 'true').lower() == 'true',
        )


@dataclass
class UIConfig:
    """UI configuration"""
    type: str = 'web'  # 'web' or 'desktop'
    host: str = '0.0.0.0'
    port: int = 8000
    websocket_port: int = 8001
    
    @classmethod
    def from_env(cls) -> 'UIConfig':
        """Load UI config from environment"""
        return cls(
            type=os.getenv('G1_UI_TYPE', 'web'),
            host=os.getenv('G1_UI_HOST', '0.0.0.0'),
            port=int(os.getenv('G1_UI_PORT', '8000')),
            websocket_port=int(os.getenv('G1_UI_WS_PORT', '8001')),
        )


class Config:
    """Global configuration"""
    
    def __init__(
        self,
        robot: Optional[RobotConfig] = None,
        sensors: Optional[SensorConfig] = None,
        ui: Optional[UIConfig] = None
    ):
        self.robot = robot or RobotConfig.from_env()
        self.sensors = sensors or SensorConfig.from_env()
        self.ui = ui or UIConfig.from_env()
    
    @classmethod
    def from_env(cls) -> 'Config':
        """Load all configuration from environment"""
        return cls()
    
    def __repr__(self) -> str:
        return (
            f"Config(\n"
            f"  robot={self.robot},\n"
            f"  sensors={self.sensors},\n"
            f"  ui={self.ui}\n"
            f")"
        )


# Global config instance
config = Config.from_env()
