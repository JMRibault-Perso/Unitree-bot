#!/usr/bin/env python3
"""
SLAM Mapper with Odometry - Accumulate point clouds into a global map using robot pose

This script:
1. Subscribes to point cloud and odometry topics
2. Transforms point clouds using robot pose
3. Accumulates into a global voxel map
4. Saves map to PCD file periodically
5. Provides real-time mapping visualization

Usage:
    python3 slam_mapper.py [--output-dir ./maps] [--voxel-size 0.05] [--max-points 1000000]
"""

import asyncio
import json
import sys
import os
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional, List, Tuple
import numpy as np
from collections import deque

# Add SDK paths
sys.path.insert(0, '/root/G1/go2_webrtc_connect')
from unitree_webrtc_connect.webrtc_driver import UnitreeWebRTCConnection, WebRTCConnectionMethod

# Optional: for visualization and map saving
try:
    import open3d as o3d
    HAS_O3D = True
except ImportError:
    HAS_O3D = False
    print("⚠️  Open3D not available - visualization disabled (pip install open3d)")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("SLAMMapper")


class SLAMMapper:
    """Accumulate SLAM point clouds with odometry into a persistent global map"""
    
    def __init__(self, 
                 output_dir: str = "./maps",
                 voxel_size: float = 0.05,
                 max_points: int = 1_000_000,
                 save_interval: int = 100):
        """
        Initialize mapper
        
        Args:
            output_dir: Directory to save maps
            voxel_size: Voxel grid size for downsampling (meters)
            max_points: Maximum points in accumulated map
            save_interval: Save map every N point clouds
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.voxel_size = voxel_size
        self.max_points = max_points
        self.save_interval = save_interval
        
        # Map accumulation
        self.global_points: List[np.ndarray] = []
        self.global_colors: List[np.ndarray] = []
        self.total_points = 0
        
        # Odometry tracking
        self.current_pose = None  # (x, y, z, qx, qy, qz, qw)
        self.pose_history: deque = deque(maxlen=1000)
        
        # Statistics
        self.cloud_count = 0
        self.odom_count = 0
        self.skipped_clouds = 0
        
        # Open3D objects
        self.pcd = o3d.geometry.PointCloud() if HAS_O3D else None
        
        logger.info(f"📊 Mapper initialized (voxel_size={voxel_size}m, max_points={max_points:,})")
    
    def quaternion_to_rotation_matrix(self, qx: float, qy: float, qz: float, qw: float) -> np.ndarray:
        """Convert quaternion to 4x4 transformation matrix"""
        # Normalized quaternion
        q = np.array([qx, qy, qz, qw])
        q = q / np.linalg.norm(q)
        qx, qy, qz, qw = q
        
        # Rotation matrix
        R = np.array([
            [1 - 2*(qy**2 + qz**2),     2*(qx*qy - qz*qw),     2*(qx*qz + qy*qw)],
            [    2*(qx*qy + qz*qw), 1 - 2*(qx**2 + qz**2),     2*(qy*qz - qx*qw)],
            [    2*(qx*qz - qy*qw),     2*(qy*qz + qx*qw), 1 - 2*(qx**2 + qy**2)]
        ])
        return R
    
    def pose_to_transform(self, x: float, y: float, z: float, 
                         qx: float, qy: float, qz: float, qw: float) -> np.ndarray:
        """Convert pose (position + quaternion) to 4x4 transformation matrix"""
        T = np.eye(4)
        T[:3, :3] = self.quaternion_to_rotation_matrix(qx, qy, qz, qw)
        T[0, 3] = x
        T[1, 3] = y
        T[2, 3] = z
        return T
    
    def on_point_cloud(self, msg: Dict) -> None:
        """Callback for point cloud messages"""
        self.cloud_count += 1
        
        try:
            # Try both message formats:
            # Format 1: Direct 'points' at root (from lidar_decoder_patch)
            if 'points' in msg:
                points = msg['points']
            # Format 2: Nested in 'data' key
            elif 'data' in msg and isinstance(msg.get('data'), dict) and 'points' in msg['data']:
                points = msg['data']['points']
            else:
                return
            
            if not isinstance(points, np.ndarray):
                try:
                    points = np.array(points)
                except:
                    return
            
            # Skip if no valid pose yet
            if self.current_pose is None:
                self.skipped_clouds += 1
                if self.skipped_clouds == 1:
                    logger.warning("⏳ Waiting for odometry data...")
                return
            
            # Transform points to global frame using current pose
            x, y, z, qx, qy, qz, qw = self.current_pose
            T = self.pose_to_transform(x, y, z, qx, qy, qz, qw)
            
            # Apply transformation
            if points.shape[1] >= 3:
                points_3d = points[:, :3]
                ones = np.ones((points_3d.shape[0], 1))
                points_homogeneous = np.hstack([points_3d, ones])
                
                transformed = (T @ points_homogeneous.T).T
                global_points = transformed[:, :3]
                
                # Store in global map
                self.global_points.append(global_points)
                self.total_points += len(global_points)
                
                # Color by height (Z) for visualization
                colors = np.tile([0.5, 0.5, 1.0], (len(global_points), 1))  # Blue
                if global_points.shape[0] > 0:
                    z_min, z_max = global_points[:, 2].min(), global_points[:, 2].max()
                    if z_max > z_min:
                        z_norm = (global_points[:, 2] - z_min) / (z_max - z_min)
                        colors = np.column_stack([z_norm, np.ones_like(z_norm) * 0.5, 1 - z_norm])
                
                self.global_colors.append(colors)
                
                # Check if we should save
                if self.cloud_count % self.save_interval == 0:
                    self._save_map()
                    self._update_visualization()
                
                if self.cloud_count % 10 == 0:
                    logger.info(f"☁️  Cloud #{self.cloud_count}: {len(global_points)} points "
                              f"(total: {self.total_points:,} points, "
                              f"pose: [{x:.2f}, {y:.2f}, {z:.2f}])")
        
        except Exception as e:
            logger.error(f"❌ Error processing point cloud: {e}")
    
    def on_odometry(self, msg: Dict) -> None:
        """Callback for odometry messages"""
        self.odom_count += 1
        
        try:
            if not isinstance(msg, dict):
                return
            
            # Extract pose from odometry message
            if 'pose' in msg:
                pose_data = msg['pose']
            elif 'data' in msg and 'pose' in msg['data']:
                pose_data = msg['data']['pose']
            else:
                return
            
            # Extract position
            if 'position' in pose_data:
                pos = pose_data['position']
                x, y, z = float(pos.get('x', 0)), float(pos.get('y', 0)), float(pos.get('z', 0))
            else:
                return
            
            # Extract orientation (quaternion)
            if 'orientation' in pose_data:
                ori = pose_data['orientation']
                qx = float(ori.get('x', 0))
                qy = float(ori.get('y', 0))
                qz = float(ori.get('z', 0))
                qw = float(ori.get('w', 1))
            else:
                qx, qy, qz, qw = 0, 0, 0, 1
            
            # Update current pose
            self.current_pose = (x, y, z, qx, qy, qz, qw)
            self.pose_history.append((self.odom_count, self.current_pose))
            
            if self.odom_count == 1:
                logger.info(f"✅ Odometry received! Robot at [{x:.2f}, {y:.2f}, {z:.2f}]")
        
        except Exception as e:
            logger.error(f"❌ Error processing odometry: {e}")
    
    def on_slam_info(self, msg: Dict) -> None:
        """Callback for SLAM status messages"""
        try:
            if isinstance(msg, dict):
                if 'data' in msg:
                    status = msg['data'].get('status', 'unknown')
                    logger.debug(f"📊 SLAM status: {status}")
        except:
            pass
    
    def _save_map(self) -> None:
        """Save accumulated map to PCD file"""
        if not self.global_points:
            return
        
        try:
            # Combine all points
            combined_points = np.vstack(self.global_points)
            combined_colors = np.vstack(self.global_colors)
            
            # Limit to max_points
            if len(combined_points) > self.max_points:
                indices = np.random.choice(len(combined_points), self.max_points, replace=False)
                combined_points = combined_points[indices]
                combined_colors = combined_colors[indices]
                logger.info(f"🔍 Downsampled to {self.max_points:,} points")
            
            if HAS_O3D:
                # Create Point Cloud
                pcd = o3d.geometry.PointCloud()
                pcd.points = o3d.utility.Vector3dVector(combined_points)
                pcd.colors = o3d.utility.Vector3dVector(combined_colors)
                
                # Voxel downsampling
                pcd_down = pcd.voxel_down_sample(self.voxel_size)
                
                # Save PCD
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = self.output_dir / f"map_{timestamp}_{self.cloud_count:06d}.pcd"
                o3d.io.write_point_cloud(str(filename), pcd_down)
                
                logger.info(f"💾 Saved map: {filename} ({len(pcd_down.points):,} points after voxel filter)")
            else:
                # Save as simple text format
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = self.output_dir / f"map_{timestamp}_{self.cloud_count:06d}.txt"
                
                # Stack points and colors
                data = np.hstack([combined_points, combined_colors])
                np.savetxt(filename, data, fmt='%.6f', header='x y z r g b')
                
                logger.info(f"💾 Saved map: {filename} ({len(combined_points):,} points)")
        
        except Exception as e:
            logger.error(f"❌ Error saving map: {e}")
    
    def _update_visualization(self) -> None:
        """Update Open3D visualization"""
        if not HAS_O3D or not self.global_points:
            return
        
        try:
            # Combine all points for visualization
            combined_points = np.vstack(self.global_points)
            combined_colors = np.vstack(self.global_colors)
            
            # Update point cloud
            self.pcd.points = o3d.utility.Vector3dVector(combined_points)
            self.pcd.colors = o3d.utility.Vector3dVector(combined_colors)
        
        except Exception as e:
            logger.error(f"❌ Error updating visualization: {e}")
    
    def get_statistics(self) -> Dict:
        """Get current mapping statistics"""
        return {
            'cloud_count': self.cloud_count,
            'odom_count': self.odom_count,
            'total_points': self.total_points,
            'skipped_clouds': self.skipped_clouds,
            'current_pose': self.current_pose,
            'pose_history_length': len(self.pose_history),
        }


async def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='SLAM Mapper with Odometry')
    parser.add_argument('--output-dir', default='./maps', help='Output directory for maps')
    parser.add_argument('--voxel-size', type=float, default=0.05, help='Voxel size in meters')
    parser.add_argument('--max-points', type=int, default=1_000_000, help='Max points per map')
    parser.add_argument('--save-interval', type=int, default=100, help='Save every N clouds')
    args = parser.parse_args()
    
    logger.info("=" * 70)
    logger.info("🗺️  SLAM MAPPER WITH ODOMETRY")
    logger.info("=" * 70)
    logger.info(f"Output: {args.output_dir}")
    logger.info(f"Voxel size: {args.voxel_size}m")
    logger.info(f"Max points: {args.max_points:,}")
    logger.info(f"Save interval: every {args.save_interval} clouds")
    
    # Discover robot using ARP
    logger.info("🔍 Discovering robot...")
    import subprocess
    try:
        result = subprocess.run(['arp', '-n'], capture_output=True, text=True, timeout=5)
        for line in result.stdout.split('\n'):
            if 'fc:23:cd:92:60:02' in line.lower():  # Unitree MAC prefix
                robot_ip = line.split()[0]
                logger.info(f"✅ Found robot at {robot_ip}")
                break
        else:
            # Fallback to default
            robot_ip = "192.168.86.3"
            logger.warning(f"⚠️  Using fallback IP: {robot_ip}")
    except Exception as e:
        logger.warning(f"⚠️  Discovery failed: {e}, using fallback IP")
        robot_ip = "192.168.86.3"
    
    logger.info(f"Connecting to: {robot_ip}")
    
    # Initialize mapper
    mapper = SLAMMapper(
        output_dir=args.output_dir,
        voxel_size=args.voxel_size,
        max_points=args.max_points,
        save_interval=args.save_interval
    )
    
    # Apply decoder patch
    from g1_app.patches import lidar_decoder_patch
    logger.info("🔧 Applying decoder patch...")
    
    # Connect to robot
    logger.info(f"🔗 Connecting to {robot_ip}...")
    max_retries = 30
    conn = None
    
    for attempt in range(max_retries):
        try:
            conn = UnitreeWebRTCConnection(WebRTCConnectionMethod.LocalSTA, ip=robot_ip)
            await conn.connect()
            logger.info(f"✅ Connected!")
            break
        except Exception as e:
            if attempt < max_retries - 1:
                logger.warning(f"⏳ Connection attempt {attempt + 1}/{max_retries} failed: {e}")
                await asyncio.sleep(5)
            else:
                logger.error(f"❌ Failed to connect after {max_retries} attempts")
                return
    
    if not conn:
        logger.error("❌ Could not establish connection")
        return
    
    try:
        # Disable traffic saving for better performance
        await conn.datachannel.disableTrafficSaving(True)
        
        # Subscribe to topics
        logger.info("📡 Subscribing to topics...")
        conn.datachannel.pub_sub.subscribe('rt/unitree/slam_mapping/points', mapper.on_point_cloud)
        conn.datachannel.pub_sub.subscribe('rt/unitree/slam_mapping/odom', mapper.on_odometry)
        conn.datachannel.pub_sub.subscribe('rt/slam_info', mapper.on_slam_info)
        logger.info("✅ Subscribed!")
        
        # Start SLAM mapping
        logger.info("🚀 Starting SLAM mapping...")
        result = await conn.datachannel.pub_sub.publish_request_new(
            'rt/api/slam_operate/request',
            {
                'api_id': 1801,  # START_MAPPING
                'parameter': json.dumps({
                    'data': {'slam_type': 'indoor'}
                })
            }
        )
        
        if result and result.get('status') == 200:
            logger.info("✅ SLAM mapping started!")
        else:
            logger.warning(f"⚠️  SLAM start returned: {result}")
        
        # Run mapping
        logger.info("=" * 70)
        logger.info("📊 MAPPING IN PROGRESS - Press Ctrl+C to stop")
        logger.info("=" * 70)
        
        last_stats_time = asyncio.get_event_loop().time()
        
        while True:
            await asyncio.sleep(1)
            
            # Print statistics every 30 seconds
            now = asyncio.get_event_loop().time()
            if now - last_stats_time > 30:
                stats = mapper.get_statistics()
                logger.info(f"\n📊 Statistics:")
                logger.info(f"   Clouds received: {stats['cloud_count']}")
                logger.info(f"   Odometry messages: {stats['odom_count']}")
                logger.info(f"   Total points accumulated: {stats['total_points']:,}")
                logger.info(f"   Pose history: {stats['pose_history_length']}")
                if stats['current_pose']:
                    x, y, z = stats['current_pose'][:3]
                    logger.info(f"   Current pose: [{x:.2f}, {y:.2f}, {z:.2f}]")
                logger.info()
                last_stats_time = now
    
    except KeyboardInterrupt:
        logger.info("\n⛔ Stopping mapper...")
    
    finally:
        # Stop SLAM
        try:
            logger.info("🛑 Stopping SLAM mapping...")
            await conn.datachannel.pub_sub.publish_request_new(
                'rt/api/slam_operate/request',
                {'api_id': 1901}  # CLOSE_SLAM
            )
            logger.info("✅ SLAM stopped")
        except:
            pass
        
        # Final save
        mapper._save_map()
        
        # Final statistics
        stats = mapper.get_statistics()
        logger.info("\n" + "=" * 70)
        logger.info("📊 FINAL STATISTICS")
        logger.info("=" * 70)
        logger.info(f"Point clouds processed: {stats['cloud_count']}")
        logger.info(f"Odometry messages: {stats['odom_count']}")
        logger.info(f"Total points accumulated: {stats['total_points']:,}")
        logger.info(f"Clouds skipped (no odometry): {stats['skipped_clouds']}")
        logger.info(f"Maps saved to: {mapper.output_dir.absolute()}")
        logger.info("=" * 70)
        
        # Close connection
        await conn.close()


if __name__ == '__main__':
    asyncio.run(main())
