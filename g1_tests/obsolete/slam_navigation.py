#!/usr/bin/env python3
"""
G1 SLAM Navigation Controller
Load saved maps on the robot and navigate to goal positions.
"""

import sys
import asyncio
import json
import logging
import argparse
from typing import Optional, Tuple

sys.path.insert(0, '.')
from g1_app.utils.arp_discovery import discover_robot_ip

sys.path.insert(0, '/root/G1/go2_webrtc_connect')
from unitree_webrtc_connect.webrtc_driver import UnitreeWebRTCConnection, WebRTCConnectionMethod

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("SLAMNav")


class SLAMNavigator:
    """SLAM Navigation Controller for G1"""
    
    def __init__(self, robot_ip: str):
        self.robot_ip = robot_ip
        self.conn: Optional[UnitreeWebRTCConnection] = None
        self.current_pose = None
        self.nav_status = "idle"
        
    async def connect(self):
        """Connect to robot via WebRTC"""
        logger.info(f"🔌 Connecting to robot at {self.robot_ip}...")
        
        self.conn = UnitreeWebRTCConnection(
            self.robot_ip,
            WebRTCConnectionMethod.LocalSTA
        )
        
        await self.conn.connect()
        logger.info("✅ Connected!")
        
        # Subscribe to odometry for pose updates
        self.conn.datachannel.pub_sub.subscribe('rt/unitree/slam_mapping/odom', self._on_odom)
        await asyncio.sleep(1)
        
    def _on_odom(self, msg):
        """Handle odometry updates"""
        if 'data' in msg and 'pose' in msg['data']:
            pose = msg['data']['pose']['pose']
            pos = pose['position']
            self.current_pose = (pos['x'], pos['y'], pos['z'])
            
    async def load_map(self, map_path: str, init_x: float = 0, init_y: float = 0, init_yaw: float = 0):
        """
        Load a saved map on the robot and set initial pose.
        
        API 1804: Initialize pose and load map
        
        Args:
            map_path: Path to PCD map file on robot (e.g., /home/unitree/my_map.pcd)
            init_x, init_y: Initial position in meters
            init_yaw: Initial yaw angle in radians
        """
        logger.info(f"📂 Loading map: {map_path}")
        logger.info(f"   Initial pose: x={init_x:.2f}, y={init_y:.2f}, yaw={init_yaw:.2f}")
        
        # Normalize path
        if not map_path.startswith('/'):
            map_path = f'/home/unitree/{map_path}'
        
        payload = {
            'api_id': 1804,
            'parameter': json.dumps({
                'data': {
                    'slam_type': 'indoor',
                    'map_path': map_path,
                    'init_pose': {
                        'x': init_x,
                        'y': init_y,
                        'z': 0.0,
                        'yaw': init_yaw
                    }
                }
            })
        }
        
        response = await self.conn.datachannel.pub_sub.publish_request_new(
            'rt/api/slam_operate/request',
            payload,
            response_topic='rt/api/slam_operate/response'
        )
        
        if response and 'data' in response:
            data = json.loads(response['data']) if isinstance(response['data'], str) else response['data']
            if data.get('succeed'):
                logger.info("✅ Map loaded successfully!")
                return True
            else:
                error_code = data.get('errorCode', 'unknown')
                error_info = data.get('info', 'No error info')
                logger.error(f"❌ Failed to load map: {error_info} (code: {error_code})")
                return False
        else:
            logger.error("❌ No response from robot")
            return False
    
    async def set_goal(self, x: float, y: float, yaw: float = 0.0):
        """
        Navigate to a goal position on the loaded map.
        
        API 1805: Set navigation goal
        
        Args:
            x, y: Goal position in meters (relative to map origin)
            yaw: Goal orientation in radians
        """
        logger.info(f"🎯 Setting navigation goal: x={x:.2f}, y={y:.2f}, yaw={yaw:.2f}")
        
        payload = {
            'api_id': 1805,
            'parameter': json.dumps({
                'data': {
                    'goal_pose': {
                        'x': x,
                        'y': y,
                        'z': 0.0,
                        'yaw': yaw
                    }
                }
            })
        }
        
        response = await self.conn.datachannel.pub_sub.publish_request_new(
            'rt/api/slam_operate/request',
            payload,
            response_topic='rt/api/slam_operate/response'
        )
        
        if response and 'data' in response:
            data = json.loads(response['data']) if isinstance(response['data'], str) else response['data']
            if data.get('succeed'):
                logger.info("✅ Navigation started!")
                self.nav_status = "navigating"
                return True
            else:
                error_code = data.get('errorCode', 'unknown')
                error_info = data.get('info', 'No error info')
                logger.error(f"❌ Navigation failed: {error_info} (code: {error_code})")
                return False
        else:
            logger.error("❌ No response from robot")
            return False
    
    async def cancel_navigation(self):
        """Cancel current navigation goal"""
        logger.info("🛑 Canceling navigation...")
        
        payload = {
            'api_id': 1806,
            'parameter': json.dumps({'data': {}})
        }
        
        response = await self.conn.datachannel.pub_sub.publish_request_new(
            'rt/api/slam_operate/request',
            payload,
            response_topic='rt/api/slam_operate/response'
        )
        
        if response and 'data' in response:
            data = json.loads(response['data']) if isinstance(response['data'], str) else response['data']
            if data.get('succeed'):
                logger.info("✅ Navigation canceled")
                self.nav_status = "idle"
                return True
        
        logger.error("❌ Failed to cancel navigation")
        return False
    
    async def get_current_pose(self) -> Optional[Tuple[float, float, float]]:
        """Get current robot pose (x, y, z)"""
        return self.current_pose
    
    async def close(self):
        """Close connection"""
        if self.conn:
            try:
                await self.conn.close()
            except:
                pass
        logger.info("🔌 Connection closed")


async def interactive_mode(navigator: SLAMNavigator):
    """Interactive navigation mode"""
    print("\n" + "=" * 70)
    print("G1 SLAM Navigation - Interactive Mode")
    print("=" * 70)
    print("\nCommands:")
    print("  load <map_path> [x] [y] [yaw]  - Load map and set initial pose")
    print("  goto <x> <y> [yaw]             - Navigate to position")
    print("  cancel                         - Cancel navigation")
    print("  pose                           - Show current pose")
    print("  quit                           - Exit")
    print("=" * 70)
    
    while True:
        try:
            cmd = input("\n> ").strip().split()
            if not cmd:
                continue
            
            action = cmd[0].lower()
            
            if action == 'quit':
                break
            
            elif action == 'load':
                if len(cmd) < 2:
                    print("Usage: load <map_path> [x] [y] [yaw]")
                    continue
                map_path = cmd[1]
                init_x = float(cmd[2]) if len(cmd) > 2 else 0.0
                init_y = float(cmd[3]) if len(cmd) > 3 else 0.0
                init_yaw = float(cmd[4]) if len(cmd) > 4 else 0.0
                await navigator.load_map(map_path, init_x, init_y, init_yaw)
            
            elif action == 'goto':
                if len(cmd) < 3:
                    print("Usage: goto <x> <y> [yaw]")
                    continue
                x = float(cmd[1])
                y = float(cmd[2])
                yaw = float(cmd[3]) if len(cmd) > 3 else 0.0
                await navigator.set_goal(x, y, yaw)
            
            elif action == 'cancel':
                await navigator.cancel_navigation()
            
            elif action == 'pose':
                pose = await navigator.get_current_pose()
                if pose:
                    print(f"Current pose: x={pose[0]:.3f}, y={pose[1]:.3f}, z={pose[2]:.3f}")
                else:
                    print("No pose available yet")
            
            else:
                print(f"Unknown command: {action}")
        
        except KeyboardInterrupt:
            print("\nInterrupted")
            break
        except Exception as e:
            print(f"Error: {e}")
    
    await navigator.close()


async def main():
    parser = argparse.ArgumentParser(description="G1 SLAM Navigation Controller")
    parser.add_argument('--robot-ip', help='Robot IP address (auto-discovered if not provided)')
    parser.add_argument('--load-map', help='Map file path on robot (e.g., /home/unitree/test.pcd)')
    parser.add_argument('--init-x', type=float, default=0.0, help='Initial X position')
    parser.add_argument('--init-y', type=float, default=0.0, help='Initial Y position')
    parser.add_argument('--init-yaw', type=float, default=0.0, help='Initial yaw (radians)')
    parser.add_argument('--goto-x', type=float, help='Navigate to X position')
    parser.add_argument('--goto-y', type=float, help='Navigate to Y position')
    parser.add_argument('--goto-yaw', type=float, default=0.0, help='Navigate to yaw')
    args = parser.parse_args()
    
    # Discover robot if IP not provided
    robot_ip = args.robot_ip
    if not robot_ip:
        logger.info("🔍 Auto-discovering robot...")
        robot_ip = discover_robot_ip()
        if not robot_ip:
            logger.error("❌ Robot not found. Please specify --robot-ip")
            return
        logger.info(f"✅ Found robot at {robot_ip}")
    
    # Create navigator
    navigator = SLAMNavigator(robot_ip)
    
    try:
        # Connect
        await navigator.connect()
        
        # Load map if specified
        if args.load_map:
            success = await navigator.load_map(
                args.load_map,
                args.init_x,
                args.init_y,
                args.init_yaw
            )
            if not success:
                logger.error("Failed to load map")
                return
            
            await asyncio.sleep(2)
        
        # Navigate if goal specified
        if args.goto_x is not None and args.goto_y is not None:
            await navigator.set_goal(args.goto_x, args.goto_y, args.goto_yaw)
            
            # Monitor navigation
            logger.info("🚶 Navigating... Press Ctrl+C to cancel")
            while navigator.nav_status == "navigating":
                await asyncio.sleep(1)
                pose = await navigator.get_current_pose()
                if pose:
                    logger.info(f"   Position: x={pose[0]:.3f}, y={pose[1]:.3f}, z={pose[2]:.3f}")
        else:
            # Interactive mode
            await interactive_mode(navigator)
    
    except KeyboardInterrupt:
        logger.info("\n⚠️  Interrupted by user")
        await navigator.cancel_navigation()
    
    finally:
        await navigator.close()


if __name__ == "__main__":
    asyncio.run(main())
