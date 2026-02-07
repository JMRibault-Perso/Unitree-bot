#!/usr/bin/env python3
"""
Standard helper functions for all G1 robot test scripts.
Use these to ensure consistency and avoid repeating mistakes.

Uses centralized robot discovery - SINGLE SOURCE OF TRUTH
"""

import sys
import asyncio
import json
import logging
from pathlib import Path
from typing import Optional, Dict, Any

# Add repo root to path
repo_root = Path(__file__).resolve().parents[1]
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))
from g1_app.utils.robot_discovery import discover_robot, wait_for_robot

from g1_app.utils.pathing import get_webrtc_paths

for path in get_webrtc_paths():
    if path and path not in sys.path:
        sys.path.insert(0, path)
from unitree_webrtc_connect.webrtc_driver import UnitreeWebRTCConnection, WebRTCConnectionMethod

logger = logging.getLogger(__name__)


class RobotTestConnection:
    """Standard robot connection with ARP discovery and proper cleanup"""
    
    def __init__(self, robot_ip: Optional[str] = None):
        """
        Initialize connection. If robot_ip is None, will auto-discover via ARP.
        
        Args:
            robot_ip: Optional IP address. If None, uses ARP discovery.
        """
        self.robot_ip = robot_ip
        self.conn = None
    
    async def __aenter__(self):
        """Context manager entry - connect to robot"""
        # Discover robot if IP not provided
        if not self.robot_ip:
            logger.info("🔍 Discovering robot...")
            robot = discover_robot()
            if not robot or not robot['online']:
                raise RuntimeError("❌ Robot not found or offline")
            
            self.robot_ip = robot['ip']
            mode_desc = {
                "AP": "Access Point (robot WiFi hotspot)",
                "STA-L": "Station Local (same network)",
                "STA-T": "Station Remote (different network - may not work)"
            }.get(robot['mode'], "unknown")
            logger.info(f"✅ Found robot at {self.robot_ip} (mode: {robot['mode']} - {mode_desc})")
        else:
            logger.info(f"🔌 Using provided IP: {self.robot_ip}")
        
        # Connect
        logger.info(f"🔌 Connecting to {self.robot_ip}...")
        self.conn = UnitreeWebRTCConnection(
            WebRTCConnectionMethod.LocalSTA,
            ip=self.robot_ip
        )
        await self.conn.connect()
        logger.info("✅ Connected!")
        await asyncio.sleep(2)  # Brief settling time

        # Attach error listeners to prevent MediaStreamError from bubbling
        def _handle_error(exc: Exception, source: str = "unknown"):
            if exc and "MediaStreamError" in type(exc).__name__:
                logger.warning(f"⚠️  Ignored MediaStreamError from {source}")
                return
            logger.warning(f"⚠️  WebRTC error from {source}: {exc}")

        for source_name, obj in (
            ("conn", self.conn),
            ("datachannel", getattr(self.conn, "datachannel", None)),
            ("pub_sub", getattr(getattr(self.conn, "datachannel", None), "pub_sub", None)),
        ):
            try:
                if obj and hasattr(obj, "on"):
                    obj.on("error", lambda exc, src=source_name: _handle_error(exc, src))
            except Exception:
                pass
        
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - ALWAYS disconnect properly"""
        if self.conn:
            # Allow time for final messages to process before disconnecting
            await asyncio.sleep(0.2)
            
            logger.info("🔌 Disconnecting from robot...")
            try:
                await self.conn.disconnect()  # ⚠️ CRITICAL: Use disconnect(), NOT close()
                logger.info("✅ Disconnected")
            except Exception as e:
                # Don't log MediaStreamError - it's expected during WebRTC cleanup
                if 'MediaStreamError' not in str(type(e)):
                    logger.warning(f"⚠️  Disconnect error (non-fatal): {e}")
    
    def parse_response(self, response: Optional[dict]) -> Optional[dict]:
        """
        Parse API response data field (handles nested JSON strings).
        
        Args:
            response: Raw response from publish_request_new()
        
        Returns:
            Parsed data dict or None if parsing failed
        """
        if not response or not isinstance(response, dict):
            return None
        
        data = response.get("data")
        
        # Handle nested structure: response['data']['data'] is JSON string
        if isinstance(data, dict) and 'data' in data:
            inner_data = data['data']
            if isinstance(inner_data, str):
                try:
                    return json.loads(inner_data)
                except Exception:
                    return None
            return inner_data
        
        # Handle direct JSON string
        if isinstance(data, str):
            try:
                return json.loads(data)
            except Exception:
                return None
        
        return data
    
    async def send_slam_request(self, api_id: int, parameters: dict, timeout: Optional[float] = None) -> Optional[dict]:
        """
        Send SLAM API request with standard format.
        
        Args:
            api_id: API ID (1801, 1802, 1804, 1102, 1201, 1202, 1901)
            parameters: Parameter dict (will be wrapped in {'data': ...})
        
        Returns:
            Parsed response data or None
        """
        payload = {
            'api_id': api_id,
            'parameter': json.dumps({'data': parameters})
        }
        
        if timeout is None:
            response = await self.conn.datachannel.pub_sub.publish_request_new(
                'rt/api/slam_operate/request',
                payload
            )
        else:
            try:
                response = await asyncio.wait_for(
                    self.conn.datachannel.pub_sub.publish_request_new(
                        'rt/api/slam_operate/request',
                        payload
                    ),
                    timeout=timeout
                )
            except asyncio.TimeoutError:
                logger.warning(f"⏱️  SLAM request timed out (api_id={api_id})")
                return None
        
        # Brief delay to ensure response is fully processed
        await asyncio.sleep(0.1)
        
        return self.parse_response(response)
    
    def subscribe(self, topic: str, callback):
        """
        Subscribe to a topic with callback.
        
        Args:
            topic: Topic name (e.g., 'rt/unitree/slam_mapping/odom')
            callback: Callback function(msg: dict)
        """
        self.conn.datachannel.pub_sub.subscribe(topic, callback)


# SLAM API IDs (from SDK documentation)
SLAM_API = {
    'START_MAPPING': 1801,
    'END_MAPPING': 1802,
    'STOP_MAPPING': 1802,
    'SAVE_MAP': 1802,
    'LOAD_MAP': 1804,
    'INITIALIZE_POSE': 1804,
    'NAVIGATE': 1102,
    'PAUSE_NAV': 1201,
    'RESUME_NAV': 1202,
    'CLOSE_SLAM': 1901,
}


def check_slam_response(data: Optional[dict], operation: str) -> bool:
    """
    Check if SLAM response indicates success and log result.
    
    Args:
        data: Parsed response data
        operation: Operation name for logging
    
    Returns:
        True if successful, False otherwise
    """
    if data and data.get('succeed'):
        info = data.get('info', 'Success')
        logger.info(f"✅ {operation}: {info}")
        return True
    else:
        error = (data or {}).get('info', 'Unknown error')
        logger.error(f"❌ {operation} failed: {error}")
        return False


async def quick_connect(robot_ip: Optional[str] = None) -> UnitreeWebRTCConnection:
    """
    Quick connection helper for simple scripts.
    ⚠️ Remember to call await conn.disconnect() when done!
    
    Args:
        robot_ip: Optional IP. If None, uses ARP discovery.
    
    Returns:
        Connected WebRTC connection
    """
    if not robot_ip:
        logger.info("🔍 Discovering robot...")
        robot = discover_robot()
        if not robot or not robot['online']:
            raise RuntimeError("❌ Robot not found or offline")
        robot_ip = robot['ip']
        logger.info(f"✅ Found robot at {robot_ip} ({robot['mode']})")
    logger.info("✅ Connected!")
    await asyncio.sleep(2)
    
    return conn
