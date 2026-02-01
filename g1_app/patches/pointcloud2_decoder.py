"""
PointCloud2 Decoder for G1 SLAM Point Clouds

G1 uses ROS2 sensor_msgs::msg::PointCloud2 format, NOT LibVoxel compression.
This decoder parses the PointCloud2 binary structure.
"""

import struct
import numpy as np
import logging

logger = logging.getLogger(__name__)


class PointCloud2Decoder:
    """
    Decodes ROS2 PointCloud2 binary data.
    
    PointCloud2 format:
    - Header (timestamp, frame_id)
    - height, width (uint32 each)
    - PointField[] fields (name, offset, datatype, count)
    - is_bigendian (bool)
    - point_step (uint32) - bytes per point
    - row_step (uint32) - bytes per row
    - data[] - actual point data
    - is_dense (bool)
    
    Common field layout for XYZ points:
    - field 0: x (FLOAT32 at offset 0)
    - field 1: y (FLOAT32 at offset 4)  
    - field 2: z (FLOAT32 at offset 8)
    - field 3: intensity (optional, FLOAT32 at offset 12)
    
    Point data is tightly packed according to point_step.
    """
    
    # PointField data types (from sensor_msgs/msg/PointField)
    DATATYPE_INT8    = 1
    DATATYPE_UINT8   = 2
    DATATYPE_INT16   = 3
    DATATYPE_UINT16  = 4
    DATATYPE_INT32   = 5
    DATATYPE_UINT32  = 6
    DATATYPE_FLOAT32 = 7
    DATATYPE_FLOAT64 = 8
    
    DATATYPE_SIZES = {
        1: 1,  # INT8
        2: 1,  # UINT8
        3: 2,  # INT16
        4: 2,  # UINT16
        5: 4,  # INT32
        6: 4,  # UINT32
        7: 4,  # FLOAT32
        8: 8,  # FLOAT64
    }
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def decode(self, binary_data, metadata=None):
        """
        Decode PointCloud2 binary data.
        
        Args:
            binary_data: Raw bytes from PointCloud2 message
            metadata: Optional metadata dict (we'll parse structure from binary)
        
        Returns:
            dict with:
                - point_count: number of points
                - points: numpy array of shape (N, 3) for XYZ
                - intensities: optional numpy array of shape (N,)
        """
        try:
            # PointCloud2 binary data is usually just the raw point data
            # The metadata (height, width, fields, etc.) comes in the JSON part
            
            # For Unitree's format, the binary appears to be compressed or encoded
            # Let's try to parse it as raw point data first
            
            # Common formats:
            # 1. XYZ as 3x float32 = 12 bytes per point
            # 2. XYZI as 4x float32 = 16 bytes per point
            # 3. Custom compressed format
            
            data_len = len(binary_data)
            self.logger.debug(f"Decoding {data_len} bytes of PointCloud2 data")
            
            # G1 SLAM uses specific 12-byte format - check first!
            if data_len % 12 == 0:
                return self._try_int16_12byte_format(binary_data)
            
            # Try 16 bytes per point (XYZI)
            elif data_len % 16 == 0:
                return self._decode_xyzi_float32(binary_data)
            
            # Try 6 bytes per point (compact XYZ)
            elif data_len % 6 == 0:
                return self._try_uint16_format(binary_data)
            
            # Unknown format
            else:
                return self._decode_variable_format(binary_data, metadata)
                
        except Exception as e:
            self.logger.error(f"PointCloud2 decode error: {e}", exc_info=True)
            return {
                'point_count': 0,
                'points': np.array([]),
                'error': str(e)
            }
    
    def _decode_xyz_float32(self, binary_data):
        """Decode as simple XYZ float32 points (12 bytes each)"""
        num_points = len(binary_data) // 12
        
        # Unpack as array of float32
        points = np.frombuffer(binary_data, dtype=np.float32)
        points = points.reshape((num_points, 3))
        
        self.logger.info(f"✅ Decoded {num_points} XYZ points (12 bytes/point)")
        
        return {
            'point_count': num_points,
            'points': points,
            'format': 'xyz_float32'
        }
    
    def _decode_xyzi_float32(self, binary_data):
        """Decode as XYZI float32 points (16 bytes each)"""
        num_points = len(binary_data) // 16
        
        # Unpack as array of float32
        data = np.frombuffer(binary_data, dtype=np.float32)
        data = data.reshape((num_points, 4))
        
        points = data[:, :3]  # XYZ
        intensities = data[:, 3]  # I
        
        self.logger.info(f"✅ Decoded {num_points} XYZI points (16 bytes/point)")
        
        return {
            'point_count': num_points,
            'points': points,
            'intensities': intensities,
            'format': 'xyzi_float32'
        }
    
    def _decode_variable_format(self, binary_data, metadata):
        """
        Decode variable format by analyzing the binary structure.
        
        G1 SLAM uses 12 bytes per point with 6 int16 values.
        """
        data_len = len(binary_data)
        
        self.logger.debug(f"Variable format: {data_len} bytes")
        
        # G1 SLAM uses 12 bytes per point
        return self._try_int16_12byte_format(binary_data)
    
    def _try_int16_12byte_format(self, binary_data):
        """
        G1 SLAM specific format: 12 bytes per point with 6 int16 values.
        First 3 values appear to be XYZ coordinates (scaled).
        """
        data_len = len(binary_data)
        
        if data_len % 12 != 0:
            self.logger.error(f"Data not aligned to 12 bytes: {data_len}")
            return {'point_count': 0, 'points': np.array([])}
        
        num_points = data_len // 12
        
        # Read as int16 (signed 16-bit integers)
        data_int16 = np.frombuffer(binary_data, dtype=np.int16)
        data_int16 = data_int16.reshape((num_points, 6))
        
        # Take first 3 values as XYZ coordinates
        xyz_raw = data_int16[:, :3].astype(np.float32)
        
        # Scale from int16 to meters (common: mm to m = / 1000)
        points = xyz_raw / 1000.0
        
        self.logger.info(f"✅ Decoded {num_points} points (G1 SLAM 12-byte int16 format)")
        self.logger.debug(f"Raw int16 range: X[{xyz_raw[:,0].min():.0f}, {xyz_raw[:,0].max():.0f}] "
                        f"Y[{xyz_raw[:,1].min():.0f}, {xyz_raw[:,1].max():.0f}] "
                        f"Z[{xyz_raw[:,2].min():.0f}, {xyz_raw[:,2].max():.0f}]")
        self.logger.debug(f"Scaled (m): X[{points[:,0].min():.3f}, {points[:,0].max():.3f}] "
                        f"Y[{points[:,1].min():.3f}, {points[:,1].max():.3f}] "
                        f"Z[{points[:,2].min():.3f}, {points[:,2].max():.3f}]")
        
        return {
            'point_count': num_points,
            'points': points,
            'format': 'g1_slam_int16_12byte'
        }
    
    def _try_uint16_format(self, binary_data):
        """
        Try decoding as uint16 coordinates.
        
        Some LiDAR formats use uint16 for efficiency:
        - Each coordinate is a uint16 scaled value
        - 3 uint16 = 6 bytes per point (XYZ)
        - 4 uint16 = 8 bytes per point (XYZI)
        """
        data_len = len(binary_data)
        
        # Try 6 bytes per point (XYZ as uint16)
        if data_len % 6 == 0:
            num_points = data_len // 6
            data_uint16 = np.frombuffer(binary_data, dtype=np.uint16)
            data_uint16 = data_uint16.reshape((num_points, 3))
            
            # Convert uint16 to float (typical scaling: divide by 1000 or use range)
            # Need to know the scaling factor from metadata
            # For now, try automatic scaling based on range
            points = data_uint16.astype(np.float32) / 1000.0  # Assume mm to meters
            
            self.logger.info(f"✅ Decoded {num_points} points as uint16 (6 bytes/point, scaled to meters)")
            self.logger.debug(f"Point range: X[{points[:,0].min():.2f}, {points[:,0].max():.2f}] "
                            f"Y[{points[:,1].min():.2f}, {points[:,1].max():.2f}] "
                            f"Z[{points[:,2].min():.2f}, {points[:,2].max():.2f}]")
            
            return {
                'point_count': num_points,
                'points': points,
                'format': 'xyz_uint16_scaled'
            }
        
        # Try 8 bytes per point (XYZI as uint16)
        elif data_len % 8 == 0:
            num_points = data_len // 8
            data_uint16 = np.frombuffer(binary_data, dtype=np.uint16)
            data_uint16 = data_uint16.reshape((num_points, 4))
            
            points = data_uint16[:, :3].astype(np.float32) / 1000.0
            intensities = data_uint16[:, 3].astype(np.float32) / 1000.0
            
            self.logger.info(f"✅ Decoded {num_points} points as uint16 (8 bytes/point, scaled to meters)")
            
            return {
                'point_count': num_points,
                'points': points,
                'intensities': intensities,
                'format': 'xyzi_uint16_scaled'
            }
        
        # Unknown format
        self.logger.error(f"❌ Could not determine point format: {data_len} bytes "
                         f"(not divisible by 6, 8, 12, or 16)")
        return {
            'point_count': 0,
            'points': np.array([]),
            'error': 'Unknown point format'
        }
