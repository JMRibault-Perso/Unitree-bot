#!/usr/bin/env python3
"""
Patch the WebRTC decoder to handle G1 SLAM PointCloud2 format.

G1 uses ROS2 sensor_msgs::PointCloud2 format (NOT LibVoxel compression like GO2).
Binary format:
- 8-byte header: [4 bytes json_len][4 bytes binary_len]
- JSON metadata with bounding box
- Binary PointCloud2 data
"""

import sys
import logging
import struct
import json
sys.path.insert(0, '/root/G1/go2_webrtc_connect')

from unitree_webrtc_connect.webrtc_datachannel import WebRTCDataChannel

# Import PointCloud2 decoder instead of LibVoxel
from .pointcloud2_decoder import PointCloud2Decoder

logger = logging.getLogger(__name__)

# Store original method
_original_deal_array_buffer_for_lidar = WebRTCDataChannel.deal_array_buffer_for_lidar

def patched_deal_array_buffer_for_lidar(self, buffer):
    """
    G1 SLAM PointCloud2 format handler.
    
    Format:
    - Header: [json_len (4 bytes), binary_len (4 bytes)]
    - JSON metadata: {"type": "msg", "data": {"xmin", "xmax", "ymin", "ymax", "zmin", "zmax", ...}}
    - Binary data: PointCloud2 point data
    
    Returns decoded point cloud with XYZ coordinates.
    """
    try:
        # Parse header
        json_len = struct.unpack('<I', buffer[0:4])[0]
        binary_len = struct.unpack('<I', buffer[4:8])[0]
        
        # Parse JSON metadata
        json_start = 8
        json_end = json_start + json_len
        json_str = buffer[json_start:json_end].decode('utf-8')
        message = json.loads(json_str)
        
        # Extract binary point cloud data
        binary_data = buffer[json_end:]
        
        # Get metadata
        data = message.get('data', {})
        
        logger.debug(f"📦 G1 SLAM PointCloud2: {len(binary_data)} bytes")
        logger.debug(f"   Bounds: X[{data.get('xmin', 0):.2f}, {data.get('xmax', 0):.2f}] "
                    f"Y[{data.get('ymin', 0):.2f}, {data.get('ymax', 0):.2f}] "
                    f"Z[{data.get('zmin', 0):.2f}, {data.get('zmax', 0):.2f}]")
        
        # Decode using PointCloud2 decoder (NOT LibVoxel!)
        if not hasattr(self, '_pointcloud2_decoder'):
            self._pointcloud2_decoder = PointCloud2Decoder()
        
        try:
            decoded_data = self._pointcloud2_decoder.decode(binary_data, data)
            point_count = decoded_data.get('point_count', 0)
            
            logger.info(f"🎯 PointCloud2 RESULT: {point_count} points")
            
            if point_count > 0:
                logger.info(f"   ✅ SUCCESS! Decoded {point_count} points from PointCloud2")
                # Add original metadata for reference
                decoded_data['metadata'] = data
            else:
                logger.warning(f"   ⚠️  PointCloud2 decoder returned 0 points")
            
            # CRITICAL FIX: Return data in WebRTC message format
            # The message structure must match what the original deal_array_buffer_for_lidar returns:
            # {'type': 'msg', 'data': {'data': decoded_data, ...other_fields}}
            message['data']['data'] = decoded_data
            return message
            
        except Exception as decode_error:
            logger.error(f"PointCloud2 decode error: {decode_error}")
            # Return raw data as fallback
            return {
                'type': 'lidar_pointcloud',
                'binary_data': binary_data,
                'metadata': data,
                'size': len(binary_data),
                'point_count': 0
            }
        
    except Exception as e:
        logger.error(f"Error in patched PointCloud2 handler: {e}", exc_info=True)
        # Return empty data rather than crashing
        return {
            'point_count': 0,
            'points': [],
            'error': str(e)
        }


# Apply the patch
WebRTCDataChannel.deal_array_buffer_for_lidar = patched_deal_array_buffer_for_lidar

logger.info("✅ G1 PointCloud2 decoder patch applied")
