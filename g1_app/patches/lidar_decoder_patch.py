#!/usr/bin/env python3
"""
Patch the WebRTC LiDAR decoder to handle G1 SLAM format.
G1 uses LibVoxel compression but with different metadata (xmin/xmax instead of origin/resolution).
"""

import sys
import logging
import struct
import json
sys.path.insert(0, '/root/G1/go2_webrtc_connect')

from unitree_webrtc_connect.webrtc_datachannel import WebRTCDataChannel

logger = logging.getLogger(__name__)

# Store original method
_original_deal_array_buffer_for_lidar = WebRTCDataChannel.deal_array_buffer_for_lidar

def patched_deal_array_buffer_for_lidar(self, buffer):
    """
    G1 SLAM format:
    - Header: [json_len (4 bytes), binary_len (4 bytes)]
    - JSON metadata: {"type": "msg", "data": {"xmin", "xmax", "ymin", "ymax", "zmin", "zmax", ...}}
    - Binary data: LibVoxel compressed voxel grid
    
    We need to convert G1 bounding box format to GO2 origin/resolution format for LibVoxel decoder.
    """
    try:
        # Parse header
        json_len = struct.unpack('<I', buffer[0:4])[0]
        binary_len = struct.unpack('<I', buffer[4:8])[0]
        
        # Extract JSON metadata
        json_start = 8
        json_end = json_start + json_len
        json_str = buffer[json_start:json_end].decode('utf-8')
        message = json.loads(json_str)
        
        # Extract binary compressed data
        binary_data = buffer[json_end:]
        
        # Convert G1 metadata format to GO2 format
        data = message.get('data', {})
        
        # Calculate origin and resolution from bounding box
        # Origin is the minimum corner
        origin_x = data.get('xmin', 0.0)
        origin_y = data.get('ymin', 0.0)
        origin_z = data.get('zmin', 0.0)
        
        # Calculate range
        range_x = data.get('xmax', 0.0) - origin_x
        range_y = data.get('ymax', 0.0) - origin_y
        range_z = data.get('zmax', 0.0) - origin_z
        
        # Estimate resolution (assume typical voxel grid size)
        # LibVoxel typically uses 128x128x128 or similar
        resolution = max(range_x, range_y, range_z) / 128.0  # Reasonable estimate
        
        # Build GO2-style metadata
        go2_metadata = {
            'origin': [origin_x, origin_y, origin_z],
            'resolution': resolution,
            'frame_id': data.get('header', {}).get('frame_id', 'map'),
            # Pass through original metadata for reference
            'g1_bounds': {
                'xmin': data.get('xmin'),
                'xmax': data.get('xmax'),
                'ymin': data.get('ymin'),
                'ymax': data.get('ymax'),
                'zmin': data.get('zmin'),
                'zmax': data.get('zmax')
            }
        }
        
        logger.debug(f"📦 G1 SLAM Point Cloud: {len(binary_data)} bytes compressed data")
        logger.debug(f"   Bounds: X[{origin_x:.2f}, {data.get('xmax'):.2f}] "
                    f"Y[{origin_y:.2f}, {data.get('ymax'):.2f}] "
                    f"Z[{origin_z:.2f}, {data.get('zmax'):.2f}]")
        
        # Decode using LibVoxel
        try:
            decoded_data = self.decoder.decode(binary_data, go2_metadata)
            logger.debug(f"✅ Successfully decoded {len(decoded_data.get('points', []))} points")
            return decoded_data
        except Exception as decode_error:
            logger.error(f"LibVoxel decode error: {decode_error}")
            # Fall back to returning raw data
            return {
                'type': 'lidar_pointcloud',
                'binary_data': binary_data,
                'metadata': go2_metadata,
                'size': len(binary_data)
            }
        
    except Exception as e:
        logger.error(f"Error in patched lidar handler: {e}", exc_info=True)
        # Return empty data rather than crashing
        return {
            'type': 'lidar_pointcloud',
            'binary_data': b'',
            'metadata': {},
            'size': 0
        }

# Apply the patch
WebRTCDataChannel.deal_array_buffer_for_lidar = patched_deal_array_buffer_for_lidar

logger.info("✅ Applied LiDAR decoder patch for G1 SLAM point clouds")
