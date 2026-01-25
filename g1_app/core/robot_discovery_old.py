"""
Robot Discovery - Listen for Unitree robot announcements
"""
import socket
import struct
import json
import asyncio
import logging
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

MCAST_GRP = '231.1.1.2'
MCAST_PORT = 10134

@dataclass
class RobotInfo:
    """Discovered robot information"""
    serial_number: str
    name: str
    ip: str
    key: Optional[str] = None
    last_seen: datetime = None
    
    def to_dict(self) -> dict:
        return {
            "serial_number": self.serial_number,
            "name": self.name,
            "ip": self.ip,
            "key": self.key,
            "last_seen": self.last_seen.isoformat() if self.last_seen else None
        }


class RobotDiscovery:
    """
    Discovers Unitree robots on the local network via multicast
    Robots broadcast their info to 231.1.1.2:10134 periodically
    """
    
    def __init__(self):
        self._robots: Dict[str, RobotInfo] = {}  # key: serial_number
        self._sock = None
        self._running = False
        self._listener_task = None
        
    def start(self):
        """Start listening for robot announcements"""
        if self._running:
            return
            
        logger.info(f"Starting robot discovery on {MCAST_GRP}:{MCAST_PORT}")
        
        try:
            self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
            self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self._sock.settimeout(1.0)  # Non-blocking with timeout
            
            # Bind to the multicast port
            self._sock.bind(('', MCAST_PORT))
            
            # Join multicast group
            mreq = struct.pack("4sl", socket.inet_aton(MCAST_GRP), socket.INADDR_ANY)
            self._sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
            
            self._running = True
            self._listener_task = asyncio.create_task(self._listen_loop())
            logger.info("Robot discovery started")
            
        except Exception as e:
            logger.error(f"Failed to start discovery: {e}")
            self.stop()
            
    def stop(self):
        """Stop listening for robot announcements"""
        self._running = False
        
        if self._listener_task:
            self._listener_task.cancel()
            self._listener_task = None
            
        if self._sock:
            try:
                self._sock.close()
            except:
                pass
            self._sock = None
            
        logger.info("Robot discovery stopped")
        
    async def _listen_loop(self):
        """Async loop to receive robot announcements"""
        logger.info("Discovery listener started")
        
        while self._running:
            try:
                # Use asyncio to run blocking socket recv in executor
                data, addr = await asyncio.get_event_loop().run_in_executor(
                    None, self._recv_with_timeout
                )
                
                if data:
                    self._process_announcement(data, addr)
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                if self._running:  # Only log if not shutting down
                    logger.debug(f"Discovery loop error: {e}")
                await asyncio.sleep(0.1)
                
        logger.info("Discovery listener stopped")
        
    def _recv_with_timeout(self):
        """Blocking recv with timeout (called in executor)"""
        try:
            return self._sock.recvfrom(1024)
        except socket.timeout:
            return None, None
        except:
            return None, None
            
    def _process_announcement(self, data: bytes, addr: tuple):
        """Process robot announcement packet"""
        try:
            robot_data = json.loads(data.decode('utf-8'))
            
            serial = robot_data.get('sn', robot_data.get('serial_number', 'UNKNOWN'))
            name = robot_data.get('name', f'Robot_{serial}')
            ip = robot_data.get('ip', addr[0])
            key = robot_data.get('key')
            
            robot = RobotInfo(
                serial_number=serial,
                name=name,
                ip=ip,
                key=key,
                last_seen=datetime.now()
            )
            
            if serial not in self._robots:
                logger.info(f"🤖 Discovered robot: {name} ({serial}) at {ip}")
            
            self._robots[serial] = robot
            
        except json.JSONDecodeError:
            logger.debug(f"Non-JSON data from {addr}: {data[:50]}")
        except Exception as e:
            logger.error(f"Error processing announcement: {e}")
            
    def get_robots(self, max_age_seconds: int = 60) -> List[RobotInfo]:
        """
        Get list of discovered robots
        
        Args:
            max_age_seconds: Only return robots seen within this many seconds
        """
        cutoff = datetime.now() - timedelta(seconds=max_age_seconds)
        
        active_robots = [
            robot for robot in self._robots.values()
            if robot.last_seen and robot.last_seen > cutoff
        ]
        
        # If no robots discovered via multicast, try active scanning
        if not active_robots:
            logger.info("No multicast announcements, trying active scan...")
            # This will be handled by web_server with fallback IPs
        
        return active_robots
        
    def get_robot(self, serial_number: str) -> Optional[RobotInfo]:
        """Get specific robot by serial number"""
        return self._robots.get(serial_number)
        
    def clear_stale_robots(self, max_age_seconds: int = 300):
        """Remove robots not seen in a while"""
        cutoff = datetime.now() - timedelta(seconds=max_age_seconds)
        
        stale = [
            sn for sn, robot in self._robots.items()
            if robot.last_seen and robot.last_seen < cutoff
        ]
        
        for sn in stale:
            logger.info(f"Removing stale robot: {self._robots[sn].name}")
            del self._robots[sn]


# Global discovery instance
_discovery = None

def get_discovery() -> RobotDiscovery:
    """Get global discovery instance"""
    global _discovery
    if _discovery is None:
        _discovery = RobotDiscovery()
    return _discovery
