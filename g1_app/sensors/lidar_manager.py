"""LiDAR Manager - Processes Mid-360 LiDAR point cloud data"""

import logging
import numpy as np
from dataclasses import dataclass
from typing import Optional, List

from g1_app.core import EventBus, Events
from g1_app.api import Topic

logger = logging.getLogger(__name__)


@dataclass
class LiDARPoint:
    """Single LiDAR point"""
    x: float
    y: float
    z: float
    intensity: float
    reflectivity: int
    tag: int


@dataclass
class PointCloudData:
    """LiDAR point cloud with metadata"""
    points: List[LiDARPoint]
    timestamp: float
    frame_id: str
    point_count: int


class LiDARManager:
    """Manages LiDAR point cloud from Mid-360"""
    
    def __init__(self, datachannel):
        self.datachannel = datachannel
        self.current_cloud: Optional[PointCloudData] = None
        
        # LiDAR specs (from official docs)
        self.fov_horizontal = (0, 360)  # degrees
        self.fov_vertical = (-7, 52)    # degrees
        self.range = (0.05, 70.0)       # meters
        self.accuracy = 0.02            # meters (2cm)
        
        # Mounting info (from docs)
        self.mount_position = {
            'x': 0.017,      # meters forward from center
            'y': 0.0,        # centered
            'z': 0.5,        # ~50cm height
            'pitch': -2.3    # degrees (inverted mount)
        }
    
    def start(self):
        """Subscribe to LiDAR topics"""
        # Point cloud (10Hz)
        self.datachannel.subscribe(Topic.LIDAR_CLOUD, self._on_cloud_message)
        
        # IMU data (200Hz) - optional for stability
        self.datachannel.subscribe(Topic.LIDAR_IMU, self._on_imu_message)
        
        logger.info("LiDARManager started")
    
    def _on_cloud_message(self, msg: dict):
        """Process PointCloud2 message (10Hz)"""
        try:
            # Parse PointCloud2 format
            header = msg.get('header', {})
            fields = msg.get('fields', [])
            data = msg.get('data', [])
            
            # Extract points (format: x, y, z, intensity, reflectivity, tag)
            points = []
            point_step = msg.get('point_step', 18)  # 18 bytes per point
            
            for i in range(0, len(data), point_step):
                chunk = data[i:i+point_step]
                if len(chunk) < point_step:
                    break
                
                # Parse binary data (assuming little-endian floats)
                point = LiDARPoint(
                    x=self._bytes_to_float(chunk[0:4]),
                    y=self._bytes_to_float(chunk[4:8]),
                    z=self._bytes_to_float(chunk[8:12]),
                    intensity=self._bytes_to_float(chunk[12:16]),
                    reflectivity=chunk[16],
                    tag=chunk[17]
                )
                points.append(point)
            
            cloud = PointCloudData(
                points=points,
                timestamp=header.get('stamp', 0.0),
                frame_id=header.get('frame_id', 'lidar_frame'),
                point_count=len(points)
            )
            
            self.current_cloud = cloud
            EventBus.emit(Events.LIDAR_CLOUD, cloud)
            
            logger.debug(f"Received point cloud: {len(points)} points")
            
        except Exception as e:
            logger.error(f"Error processing point cloud: {e}")
    
    def _on_imu_message(self, msg: dict):
        """Process LiDAR IMU message (200Hz)"""
        try:
            # Extract IMU data for sensor fusion
            accel = msg.get('linear_acceleration', {})
            gyro = msg.get('angular_velocity', {})
            
            imu_data = {
                'accel': (accel.get('x', 0), accel.get('y', 0), accel.get('z', 0)),
                'gyro': (gyro.get('x', 0), gyro.get('y', 0), gyro.get('z', 0)),
                'timestamp': msg.get('header', {}).get('stamp', 0.0)
            }
            
            EventBus.emit(Events.LIDAR_IMU, imu_data)
            
        except Exception as e:
            logger.error(f"Error processing LiDAR IMU: {e}")
    
    def _bytes_to_float(self, bytes_data: bytes) -> float:
        """Convert byte array to float (little-endian)"""
        import struct
        return struct.unpack('<f', bytes(bytes_data))[0]
    
    def get_current_cloud(self) -> Optional[PointCloudData]:
        """Get current point cloud"""
        return self.current_cloud
    
    def apply_mount_transform(self, points: List[LiDARPoint]) -> List[LiDARPoint]:
        """Transform points from LiDAR frame to robot base frame"""
        # Apply rotation for inverted mount (-2.3° pitch)
        pitch_rad = np.radians(self.mount_position['pitch'])
        cos_p = np.cos(pitch_rad)
        sin_p = np.sin(pitch_rad)
        
        transformed = []
        for p in points:
            # Rotation around Y axis (pitch)
            x_rot = p.x * cos_p - p.z * sin_p
            z_rot = p.x * sin_p + p.z * cos_p
            
            # Translation to robot center
            x_final = x_rot + self.mount_position['x']
            y_final = p.y + self.mount_position['y']
            z_final = z_rot + self.mount_position['z']
            
            transformed.append(LiDARPoint(
                x=x_final,
                y=y_final,
                z=z_final,
                intensity=p.intensity,
                reflectivity=p.reflectivity,
                tag=p.tag
            ))
        
        return transformed
