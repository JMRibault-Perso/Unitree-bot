#!/usr/bin/env python3
"""
Full G1 SLAM Mapper with Map Save/Load
- Accumulates SLAM point clouds using odometry
- Saves maps to PCD format (API 1802)
- Loads maps with initial pose (API 1804)
- Tracks complete odometry history
- Builds 3D global map
"""

import sys
import asyncio
import json
import logging
import time
import argparse
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

repo_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(repo_root))
sys.path.insert(0, str(repo_root / 'deps' / 'g1_webrtc_connect'))

from g1_app.utils.arp_discovery import discover_robot_ip
from unitree_webrtc_connect.webrtc_driver import UnitreeWebRTCConnection, WebRTCConnectionMethod

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("SLAMMapper")


@dataclass
class RobotPose:
    """Robot pose with timestamp"""
    timestamp: float
    x: float
    y: float
    z: float
    qx: float
    qy: float
    qz: float
    qw: float


class SLAMMapper:
    """Complete SLAM mapper with save/load capability"""
    
    def __init__(self, output_dir: str = "./maps", map_name: str = "slam_map"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.map_name = map_name
        
        # Point cloud accumulation
        self.global_points: List[np.ndarray] = []
        self.global_colors: List[np.ndarray] = []
        self.pose_history: List[RobotPose] = []
        
        # Current state
        self.current_pose: Optional[Tuple[float, ...]] = None
        self.conn: Optional[UnitreeWebRTCConnection] = None
        self.mapping_active = False
        
        # Statistics
        self.cloud_count = 0
        self.odom_count = 0
        self.total_points = 0
        self.start_time = time.time()
        self.last_save_time = time.time()
        
        # Settings
        self.save_interval_clouds = 100  # Save every N clouds
        self.save_interval_seconds = 60  # Save every N seconds
        self.voxel_size = 0.05  # Downsample to 5cm voxels
        
        logger.info(f"🗺️  SLAM Mapper initialized")
        logger.info(f"   Output: {self.output_dir / self.map_name}.pcd")

    def _normalize_robot_pcd_path(self, pcd_path: str) -> str:
        """Ensure robot PCD path is under /home/unitree/ if not absolute."""
        if not pcd_path:
            return "/home/unitree/test.pcd"
        if pcd_path.startswith("/"):
            return pcd_path
        return f"/home/unitree/{pcd_path}"

    def _parse_slam_response(self, response: Optional[dict]) -> Optional[dict]:
        """Parse SLAM API response data field (JSON string) into dict."""
        if not response or not isinstance(response, dict):
            return None
        data = response.get("data")
        if isinstance(data, str):
            try:
                return json.loads(data)
            except Exception:
                return None
        if isinstance(data, dict):
            return data
        return None
    
    def quaternion_to_rotation_matrix(self, qx: float, qy: float, qz: float, qw: float) -> np.ndarray:
        """Convert quaternion to 3x3 rotation matrix"""
        # Normalize quaternion
        norm = np.sqrt(qw**2 + qx**2 + qy**2 + qz**2)
        qw, qx, qy, qz = qw/norm, qx/norm, qy/norm, qz/norm
        
        # Compute rotation matrix elements
        R = np.array([
            [1 - 2*(qy**2 + qz**2), 2*(qx*qy - qw*qz), 2*(qx*qz + qw*qy)],
            [2*(qx*qy + qw*qz), 1 - 2*(qx**2 + qz**2), 2*(qy*qz - qw*qx)],
            [2*(qx*qz - qw*qy), 2*(qy*qz + qw*qx), 1 - 2*(qx**2 + qy**2)]
        ])
        return R
    
    def pose_to_transform(self, x: float, y: float, z: float, 
                         qx: float, qy: float, qz: float, qw: float) -> np.ndarray:
        """Create 4x4 homogeneous transformation matrix from pose"""
        R = self.quaternion_to_rotation_matrix(qx, qy, qz, qw)
        T = np.eye(4)
        T[:3, :3] = R
        T[0, 3] = x
        T[1, 3] = y
        T[2, 3] = z
        return T
    
    def on_point_cloud(self, msg: Dict) -> None:
        """Callback for SLAM point cloud messages"""
        self.cloud_count += 1
        
        try:
            # Extract points from decoder patch format
            if 'points' in msg:
                points = msg['points']
            elif 'data' in msg and isinstance(msg.get('data'), dict):
                data_block = msg['data']
                if 'points' in data_block:
                    points = data_block['points']
                elif 'data' in data_block and isinstance(data_block.get('data'), dict) and 'points' in data_block['data']:
                    points = data_block['data']['points']
                else:
                    return
            else:
                return
            
            if not isinstance(points, np.ndarray):
                try:
                    points = np.array(points)
                except:
                    return
            
            if len(points) == 0 or points.shape[1] != 3:
                return
            
            # Wait for first odometry
            if self.current_pose is None:
                return
            
            # Transform to global frame
            x, y, z, qx, qy, qz, qw = self.current_pose
            T = self.pose_to_transform(x, y, z, qx, qy, qz, qw)
            
            # Apply transformation
            points_homo = np.hstack([points, np.ones((len(points), 1))])
            global_points = (T @ points_homo.T).T[:, :3]
            
            # Store
            self.global_points.append(global_points)
            self.total_points += len(global_points)
            
            # Color by height
            colors = self._compute_height_colors(global_points)
            self.global_colors.append(colors)
            
            # Periodic save
            time_since_save = time.time() - self.last_save_time
            if (self.cloud_count % self.save_interval_clouds == 0 or 
                time_since_save > self.save_interval_seconds):
                self._save_map()
                self.last_save_time = time.time()
            
            # Log progress
            if self.cloud_count % 20 == 0:
                elapsed = time.time() - self.start_time
                rate = self.cloud_count / elapsed if elapsed > 0 else 0
                logger.info(f"☁️  Cloud #{self.cloud_count}: {len(global_points)} pts "
                          f"(total: {self.total_points:,}, rate: {rate:.1f} Hz, "
                          f"pose: [{x:.2f}, {y:.2f}, {z:.2f}])")
        
        except Exception as e:
            logger.error(f"❌ Point cloud error: {e}", exc_info=True)
    
    def on_odometry(self, msg: Dict) -> None:
        """Callback for odometry messages"""
        self.odom_count += 1
        
        try:
            if not isinstance(msg, dict):
                return
            
            # Extract pose
            if 'pose' in msg:
                pose_data = msg['pose']
            elif 'data' in msg and isinstance(msg.get('data'), dict) and 'pose' in msg['data']:
                pose_data = msg['data']['pose']
            else:
                return

            # Handle PoseWithCovariance nesting
            if isinstance(pose_data, dict) and 'pose' in pose_data and isinstance(pose_data.get('pose'), dict):
                pose_data = pose_data['pose']
            
            # Position
            if 'position' in pose_data:
                pos = pose_data['position']
                x = float(pos.get('x', 0))
                y = float(pos.get('y', 0))
                z = float(pos.get('z', 0))
            else:
                return
            
            # Orientation (quaternion)
            if 'orientation' in pose_data:
                ori = pose_data['orientation']
                qx = float(ori.get('x', 0))
                qy = float(ori.get('y', 0))
                qz = float(ori.get('z', 0))
                qw = float(ori.get('w', 1))
            else:
                return
            
            # Update current pose
            self.current_pose = (x, y, z, qx, qy, qz, qw)
            
            # Store in history
            pose = RobotPose(
                timestamp=time.time(),
                x=x, y=y, z=z,
                qx=qx, qy=qy, qz=qz, qw=qw
            )
            self.pose_history.append(pose)
            
        except Exception as e:
            logger.error(f"❌ Odometry error: {e}")
    
    def _compute_height_colors(self, points: np.ndarray) -> np.ndarray:
        """Color points by height (Z coordinate)"""
        colors = np.tile([0.5, 0.5, 1.0], (len(points), 1))
        if points.shape[0] > 0:
            z_min, z_max = points[:, 2].min(), points[:, 2].max()
            if z_max > z_min:
                z_norm = (points[:, 2] - z_min) / (z_max - z_min)
                # Red (low) -> Yellow -> Green (high)
                colors = np.column_stack([
                    z_norm,                    # R
                    np.ones_like(z_norm) * 0.5,  # G
                    1 - z_norm                 # B
                ])
        return colors
    
    def _voxel_downsample(self, points: np.ndarray, colors: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """Simple voxel downsampling"""
        if len(points) == 0:
            return points, colors
        
        # Compute voxel indices
        voxel_indices = np.floor(points / self.voxel_size).astype(int)
        
        # Find unique voxels
        _, unique_idx = np.unique(voxel_indices, axis=0, return_index=True)
        
        return points[unique_idx], colors[unique_idx]
    
    def _save_map(self, filename: Optional[str] = None) -> None:
        """Save accumulated map to PCD file"""
        if self.total_points == 0:
            logger.warning("⚠️  No points to save")
            return
        
        try:
            # Concatenate all points
            all_points = np.vstack(self.global_points)
            all_colors = np.vstack(self.global_colors)
            
            # Downsample
            logger.info(f"🔽 Downsampling {len(all_points):,} points (voxel={self.voxel_size}m)...")
            all_points, all_colors = self._voxel_downsample(all_points, all_colors)
            logger.info(f"   → {len(all_points):,} points after downsampling")
            
            # Save
            if filename is None:
                filename = f"{self.map_name}_{self.cloud_count:06d}.pcd"
            
            filepath = self.output_dir / filename
            self._write_pcd(filepath, all_points, all_colors)
            
            # Also save latest
            latest_path = self.output_dir / f"{self.map_name}_latest.pcd"
            self._write_pcd(latest_path, all_points, all_colors)
            
            logger.info(f"💾 Saved map: {filepath} ({len(all_points):,} points)")
            
        except Exception as e:
            logger.error(f"❌ Save failed: {e}", exc_info=True)
    
    def _write_pcd(self, filepath: Path, points: np.ndarray, colors: np.ndarray) -> None:
        """Write PCD file"""
        try:
            # Try Open3D first
            import open3d as o3d
            pcd = o3d.geometry.PointCloud()
            pcd.points = o3d.utility.Vector3dVector(points)
            pcd.colors = o3d.utility.Vector3dVector(colors)
            o3d.io.write_point_cloud(str(filepath), pcd)
        except ImportError:
            # Fallback to ASCII PCD
            logger.info("   Using ASCII PCD format (Open3D not available)")
            with open(filepath, 'w') as f:
                f.write("# .PCD v0.7 - Point Cloud Data file format\n")
                f.write("VERSION 0.7\n")
                f.write("FIELDS x y z rgb\n")
                f.write("SIZE 4 4 4 4\n")
                f.write("TYPE F F F F\n")
                f.write("COUNT 1 1 1 1\n")
                f.write(f"WIDTH {len(points)}\n")
                f.write("HEIGHT 1\n")
                f.write("VIEWPOINT 0 0 0 1 0 0 0\n")
                f.write(f"POINTS {len(points)}\n")
                f.write("DATA ascii\n")
                
                for (x, y, z), (r, g, b) in zip(points, colors):
                    # Pack RGB into uint32
                    rgb = (int(r*255) << 16) | (int(g*255) << 8) | int(b*255)
                    f.write(f"{x:.6f} {y:.6f} {z:.6f} {rgb}\n")
    
    def save_final_map(self) -> None:
        """Save final map with trajectory"""
        logger.info("=" * 70)
        logger.info("💾 SAVING FINAL MAP")
        logger.info("=" * 70)
        
        # Save point cloud
        self._save_map(f"{self.map_name}_final.pcd")
        
        # Save trajectory
        if len(self.pose_history) > 0:
            traj_path = self.output_dir / f"{self.map_name}_trajectory.txt"
            with open(traj_path, 'w') as f:
                f.write("# timestamp x y z qx qy qz qw\n")
                for pose in self.pose_history:
                    f.write(f"{pose.timestamp:.6f} {pose.x:.6f} {pose.y:.6f} {pose.z:.6f} "
                           f"{pose.qx:.6f} {pose.qy:.6f} {pose.qz:.6f} {pose.qw:.6f}\n")
            logger.info(f"📍 Saved trajectory: {traj_path} ({len(self.pose_history)} poses)")
        
        # Print statistics
        elapsed = time.time() - self.start_time
        logger.info(f"\n📊 MAPPING STATISTICS:")
        logger.info(f"   Duration: {elapsed:.1f}s")
        logger.info(f"   Clouds received: {self.cloud_count}")
        logger.info(f"   Odometry updates: {self.odom_count}")
        logger.info(f"   Total points: {self.total_points:,}")
        logger.info(f"   Average rate: {self.cloud_count/elapsed:.1f} Hz")
        logger.info(f"   Trajectory length: {len(self.pose_history)} poses")
        
        if len(self.pose_history) > 1:
            # Calculate path length
            path_length = 0.0
            for i in range(1, len(self.pose_history)):
                p1 = self.pose_history[i-1]
                p2 = self.pose_history[i]
                dx = p2.x - p1.x
                dy = p2.y - p1.y
                dz = p2.z - p1.z
                path_length += np.sqrt(dx**2 + dy**2 + dz**2)
            logger.info(f"   Path length: {path_length:.2f}m")
    
    async def start_mapping(self) -> None:
        """Start SLAM mapping (API 1801)"""
        logger.info("🚀 Starting SLAM mapping...")
        response = await self.conn.datachannel.pub_sub.publish_request_new(
            'rt/api/slam_operate/request',
            {
                'api_id': 1801,
                'parameter': json.dumps({
                    'data': {'slam_type': 'indoor'}
                })
            }
        )
        
        parsed = self._parse_slam_response(response)
        if parsed and parsed.get('succeed'):
            self.mapping_active = True
            logger.info("✅ SLAM mapping started!")
        else:
            error = (parsed or {}).get('info', 'Unknown error') if response else 'No response'
            code = (parsed or {}).get('errorCode')
            logger.error(f"❌ Failed to start mapping: {error} (code={code})")
    
    async def stop_mapping_and_save(self, pcd_path: str = "/home/unitree/test.pcd") -> None:
        """End mapping and save map to robot (API 1802)"""
        pcd_path = self._normalize_robot_pcd_path(pcd_path)
        logger.info(f"🛑 Stopping mapping and saving to {pcd_path}...")
        response = await self.conn.datachannel.pub_sub.publish_request_new(
            'rt/api/slam_operate/request',
            {
                'api_id': 1802,
                'parameter': json.dumps({
                    'data': {'address': pcd_path}
                })
            }
        )
        
        parsed = self._parse_slam_response(response)
        if parsed and parsed.get('succeed'):
            self.mapping_active = False
            logger.info(f"✅ Map saved to robot: {pcd_path}")
        else:
            error = (parsed or {}).get('info', 'Unknown error') if response else 'No response'
            code = (parsed or {}).get('errorCode')
            logger.error(f"❌ Failed to save map: {error} (code={code})")
    
    async def load_map(self, pcd_path: str, x: float = 0, y: float = 0, z: float = 0,
                      qx: float = 0, qy: float = 0, qz: float = 0, qw: float = 1) -> None:
        """Load map and initialize pose (API 1804)"""
        pcd_path = self._normalize_robot_pcd_path(pcd_path)
        logger.info(f"📂 Loading map from {pcd_path}...")
        logger.info(f"   Initial pose: [{x:.2f}, {y:.2f}, {z:.2f}], "
                   f"quat: [{qx:.3f}, {qy:.3f}, {qz:.3f}, {qw:.3f}]")
        
        response = await self.conn.datachannel.pub_sub.publish_request_new(
            'rt/api/slam_operate/request',
            {
                'api_id': 1804,
                'parameter': json.dumps({
                    'data': {
                        'x': x, 'y': y, 'z': z,
                        'q_x': qx, 'q_y': qy, 'q_z': qz, 'q_w': qw,
                        'address': pcd_path
                    }
                })
            }
        )
        
        parsed = self._parse_slam_response(response)
        if parsed and parsed.get('succeed'):
            logger.info("✅ Map loaded and pose initialized!")
        else:
            error = (parsed or {}).get('info', 'Unknown error') if response else 'No response'
            code = (parsed or {}).get('errorCode')
            logger.error(f"❌ Failed to load map: {error} (code={code})")
    
    async def close_slam(self) -> None:
        """Close SLAM service (API 1901)"""
        logger.info("🔒 Closing SLAM...")
        response = await self.conn.datachannel.pub_sub.publish_request_new(
            'rt/api/slam_operate/request',
            {
                'api_id': 1901,
                'parameter': json.dumps({
                    'data': {}
                })
            }
        )
        
        parsed = self._parse_slam_response(response)
        if parsed and parsed.get('succeed'):
            logger.info("✅ SLAM closed")
        else:
            error = (parsed or {}).get('info', 'Unknown error') if response else 'No response'
            code = (parsed or {}).get('errorCode')
            logger.warning(f"⚠️  SLAM close response: {error} (code={code})")


async def main():
    parser = argparse.ArgumentParser(description='G1 SLAM Mapper with Save/Load')
    parser.add_argument('--output-dir', default='./maps', help='Output directory for maps')
    parser.add_argument('--map-name', default='slam_map', help='Map filename prefix')
    parser.add_argument('--duration', type=int, default=60, help='Mapping duration (seconds)')
    parser.add_argument('--save-interval', type=int, default=100, help='Save every N clouds')
    parser.add_argument('--robot-ip', default=None, help='Robot IP address (auto-discover if omitted)')
    parser.add_argument('--load-map', type=str, help='Load existing map (PCD path on robot)')
    parser.add_argument('--robot-pcd-path', default='/home/unitree/test.pcd',
                        help='PCD path on robot for save/load')
    args = parser.parse_args()
    
    logger.info("=" * 70)
    logger.info("🗺️  G1 SLAM MAPPER - Full Map Save/Load System")
    logger.info("=" * 70)
    logger.info(f"Output: {args.output_dir}")
    logger.info(f"Duration: {args.duration}s")
    logger.info(f"Save interval: every {args.save_interval} clouds")
    if args.load_map:
        logger.info(f"Loading map: {args.load_map}")
    logger.info(f"Robot PCD path: {args.robot_pcd_path}")
    logger.info("=" * 70)
    
    # Create mapper
    mapper = SLAMMapper(output_dir=args.output_dir, map_name=args.map_name)
    mapper.save_interval_clouds = args.save_interval
    
    # Connect to robot
    # Discover robot IP if not provided
    robot_ip = args.robot_ip
    if not robot_ip:
        logger.info("🔎 Discovering robot IP via ARP...")
        robot_ip = discover_robot_ip()
        logger.info(f"✅ Robot found at {robot_ip}")
    
    logger.info(f"🔌 Connecting to robot at {robot_ip}...")
    conn = UnitreeWebRTCConnection(
        WebRTCConnectionMethod.LocalSTA,
        ip=robot_ip
    )
    mapper.conn = conn
    
    # Connect with retry
    max_retries = 10
    for attempt in range(max_retries):
        try:
            await conn.connect()
            logger.info(f"✅ Connected! (attempt {attempt + 1})")
            break
        except Exception as e:
            if attempt < max_retries - 1:
                logger.warning(f"⚠️  Connection failed, retrying in 3s... ({attempt + 1}/{max_retries})")
                await asyncio.sleep(3)
            else:
                logger.error(f"❌ Connection failed after {max_retries} attempts: {e}")
                return
    
    # Subscribe to topics
    logger.info("📡 Subscribing to SLAM topics...")
    conn.datachannel.pub_sub.subscribe('rt/unitree/slam_mapping/points', mapper.on_point_cloud)
    conn.datachannel.pub_sub.subscribe('rt/unitree/slam_mapping/odom', mapper.on_odometry)
    
    await asyncio.sleep(2)
    
    try:
        if args.load_map:
            # Load existing map
            await mapper.load_map(args.load_map)
            await asyncio.sleep(2)
        else:
            # Start new mapping
            await mapper.start_mapping()
            await asyncio.sleep(2)
        
        # Map for specified duration
        logger.info(f"⏱️  Mapping for {args.duration} seconds...")
        logger.info("   Press Ctrl+C to stop early\n")
        
        await asyncio.sleep(args.duration)
        
    except KeyboardInterrupt:
        logger.info("\n⚠️  Interrupted by user")
    
    finally:
        # Save final map
        mapper.save_final_map()
        
        # Stop SLAM
        if mapper.mapping_active:
            try:
                await mapper.stop_mapping_and_save(args.robot_pcd_path)
            except Exception as e:
                logger.warning(f"⚠️  Stop/save skipped (datachannel closed?): {e}")
        
        try:
            await mapper.close_slam()
        except Exception as e:
            logger.warning(f"⚠️  SLAM close skipped (datachannel closed?): {e}")
        
        # Close WebRTC connection
        try:
            await conn.close()
            logger.info("🔌 Connection closed")
        except Exception as e:
            logger.warning(f"⚠️  Connection close warning: {e}")
        
        logger.info("=" * 70)
        logger.info("✅ MAPPING SESSION COMPLETE")
        logger.info("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
