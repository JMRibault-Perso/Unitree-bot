"""
LiDAR point cloud handler for G1 SLAM mapping.
Captures binary point cloud data and makes it available for web visualization.
"""
import asyncio
import struct
from typing import Optional, Callable
import logging

logger = logging.getLogger(__name__)

class LiDARPointCloudHandler:
    """Handles LiDAR point cloud data from SLAM mapping"""
    
    def __init__(self):
        self.latest_point_cloud: Optional[bytes] = None
        self.point_cloud_count = 0
        self.callbacks = []
        
    def set_raw_point_cloud(self, binary_data: bytes, metadata: dict):
        """Store raw point cloud binary data
        
        Args:
            binary_data: Raw binary point cloud data from robot
            metadata: Metadata dict (may not have all fields for G1)
        """
        self.latest_point_cloud = binary_data
        self.point_cloud_count += 1
        
        # Notify callbacks
        for callback in self.callbacks:
            try:
                callback(binary_data, metadata)
            except Exception as e:
                logger.error(f"Error in point cloud callback: {e}")
    
    def subscribe(self, callback: Callable):
        """Subscribe to point cloud updates
        
        Args:
            callback: Function to call with (binary_data, metadata)
        """
        self.callbacks.append(callback)
    
    def get_latest_cloud(self) -> Optional[bytes]:
        """Get the most recent point cloud binary data"""
        return self.latest_point_cloud
    
    def get_stats(self) -> dict:
        """Get statistics about point cloud reception"""
        return {
            "total_clouds": self.point_cloud_count,
            "has_data": self.latest_point_cloud is not None,
            "latest_size": len(self.latest_point_cloud) if self.latest_point_cloud else 0
        }
    
    def parse_point_cloud_simple(self, binary_data: bytes) -> list:
        """Simple parser to extract XYZ points from binary data
        
        Assumes binary data is array of float32 values: [x, y, z, x, y, z, ...]
        This is a best-guess format - may need adjustment based on actual format.
        
        Returns:
            List of [x, y, z] points
        """
        try:
            # Try to parse as float32 array
            num_floats = len(binary_data) // 4
            if num_floats % 3 != 0:
                logger.warning(f"Binary data size {len(binary_data)} not divisible by 12 (3 floats)")
                # Try anyway, truncate to nearest multiple of 3
                num_floats = (num_floats // 3) * 3
            
            points = []
            for i in range(0, num_floats, 3):
                offset = i * 4
                if offset + 12 <= len(binary_data):
                    x, y, z = struct.unpack('<fff', binary_data[offset:offset+12])
                    points.append([x, y, z])
            
            logger.info(f"Parsed {len(points)} points from {len(binary_data)} bytes")
            return points
            
        except Exception as e:
            logger.error(f"Error parsing point cloud: {e}")
            return []
