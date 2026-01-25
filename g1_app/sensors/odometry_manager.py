"""Odometry Manager - Processes robot position and velocity data"""

import logging
from dataclasses import dataclass
from typing import Optional

from g1_app.core import EventBus, Events
from g1_app.api import Topic

logger = logging.getLogger(__name__)


@dataclass
class OdometryData:
    """Robot odometry state"""
    # Position (meters)
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0
    
    # Orientation (radians)
    roll: float = 0.0
    pitch: float = 0.0
    yaw: float = 0.0
    
    # Linear velocity (m/s)
    vx: float = 0.0
    vy: float = 0.0
    vz: float = 0.0
    
    # Angular velocity (rad/s)
    wx: float = 0.0
    wy: float = 0.0
    wz: float = 0.0
    
    timestamp: float = 0.0


class OdometryManager:
    """Manages odometry data from robot"""
    
    def __init__(self, datachannel):
        self.datachannel = datachannel
        self.current_odom: Optional[OdometryData] = None
        
    def start(self):
        """Subscribe to odometry topics"""
        # High-frequency odometry (500Hz)
        self.datachannel.subscribe(Topic.ODOM_STATE, self._on_odom_message)
        
        # Low-frequency odometry (20Hz) - fallback
        self.datachannel.subscribe(Topic.ODOM_STATE_LF, self._on_odom_lf_message)
        
        logger.info("OdometryManager started")
    
    def _on_odom_message(self, msg: dict):
        """Process high-frequency odometry message (500Hz)"""
        try:
            # Parse position
            pos = msg.get('position', {})
            # Parse orientation (quaternion or euler)
            orient = msg.get('orientation', {})
            # Parse velocity
            vel = msg.get('velocity', {})
            ang_vel = msg.get('angular_velocity', {})
            
            odom = OdometryData(
                x=pos.get('x', 0.0),
                y=pos.get('y', 0.0),
                z=pos.get('z', 0.0),
                roll=orient.get('roll', 0.0),
                pitch=orient.get('pitch', 0.0),
                yaw=orient.get('yaw', 0.0),
                vx=vel.get('x', 0.0),
                vy=vel.get('y', 0.0),
                vz=vel.get('z', 0.0),
                wx=ang_vel.get('x', 0.0),
                wy=ang_vel.get('y', 0.0),
                wz=ang_vel.get('z', 0.0),
                timestamp=msg.get('timestamp', 0.0)
            )
            
            self.current_odom = odom
            EventBus.emit(Events.ODOMETRY, odom)
            
        except Exception as e:
            logger.error(f"Error processing odometry: {e}")
    
    def _on_odom_lf_message(self, msg: dict):
        """Process low-frequency odometry message (20Hz)"""
        # Same parsing as high-frequency
        self._on_odom_message(msg)
    
    def get_current(self) -> Optional[OdometryData]:
        """Get current odometry data"""
        return self.current_odom
