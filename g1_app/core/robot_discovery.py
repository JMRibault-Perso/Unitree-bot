"""
Robot Discovery - MAC-based ARP table lookup (Windows/Linux compatible)
Uses MAC addresses from bindings file to find robot IPs via ARP cache
"""
import asyncio
import logging
import platform
import subprocess
import json
import socket
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime

logger = logging.getLogger(__name__)

# Path to robot bindings file
BINDINGS_FILE = Path.home() / ".unitree_robot_bindings.json"

# Known Unitree MAC address prefixes (OUI - Organizationally Unique Identifier)
UNITREE_MAC_PREFIXES = [
    'fc:23:cd',  # Unitree Robotics MAC prefix
]

@dataclass
class RobotInfo:
    """Information about a discovered robot"""
    serial_number: str
    name: str
    ip: Optional[str] = None
    key: Optional[str] = None
    mac_address: Optional[str] = None
    last_seen: Optional[datetime] = None
    is_online: bool = False
    
    def to_dict(self):
        d = asdict(self)
        if self.last_seen:
            d['last_seen'] = self.last_seen.isoformat()
        return d
    
    @classmethod
    def from_dict(cls, d: dict):
        if 'last_seen' in d and d['last_seen']:
            d['last_seen'] = datetime.fromisoformat(d['last_seen'])
        return cls(**d)


class RobotDiscovery:
    """Discovers Unitree robots via ARP table scanning"""
    
    def __init__(self):
        self._robots: Dict[str, RobotInfo] = {}
        self._running = False
        self._scan_task: Optional[asyncio.Task] = None
        self._load_bindings()  # Load saved bindings on startup
        
    def _load_bindings(self):
        """Load robot bindings from file"""
        if not BINDINGS_FILE.exists():
            logger.info("No bindings file found")
            return
            
        try:
            with open(BINDINGS_FILE, 'r') as f:
                bindings = json.load(f)
                
            for mac, data in bindings.items():
                robot = RobotInfo(
                    serial_number=data.get("serial_number", ""),
                    name=data.get("name", ""),
                    ip=None,  # IP will be discovered via ARP
                    mac_address=mac.lower(),
                    last_seen=None,
                    is_online=False  # Will be updated by ARP scan
                )
                self._robots[robot.name] = robot
                logger.info(f"Loaded bound robot: {robot.name} (MAC: {mac})")
                
        except Exception as e:
            logger.error(f"Failed to load bindings: {e}")
        
    def _get_arp_table(self) -> List[Tuple[str, str]]:
        """Get ARP table - returns list of (IP, MAC) tuples for ALL entries"""
        arp_entries = []
        
        try:
            system = platform.system().lower()
            
            if system == "windows":
                result = subprocess.run(['arp', '-a'], capture_output=True, text=True, timeout=2)
                for line in result.stdout.split('\n'):
                    line = line.strip()
                    if not line:
                        continue
                    parts = line.split()
                    # Windows format: IP MAC TYPE
                    # Example: "192.168.86.11         fc-23-cd-92-60-02     dynamic"
                    if len(parts) >= 2:
                        # Check if first part looks like an IP address
                        ip = parts[0].strip()
                        if '.' in ip and len(ip.split('.')) == 4:
                            mac = parts[1].strip().replace('-', ':').lower()
                            # Validate MAC format (should have colons or dashes)
                            if ':' in mac or len(mac.replace(':', '')) == 12:
                                arp_entries.append((ip, mac))
                                logger.debug(f"ARP entry: {ip} -> {mac}")
            else:
                # Linux/Mac
                result = subprocess.run(['arp', '-n'], capture_output=True, text=True, timeout=2)
                for line in result.stdout.split('\n'):
                    parts = line.split()
                    if len(parts) >= 3:
                        ip = parts[0]
                        mac = parts[2].lower()
                        # Get all entries, will match against bound MACs
                        arp_entries.append((ip, mac))
                            
        except Exception as e:
            logger.error(f"Failed to read ARP table: {e}")
            
        return arp_entries
    
    def _ping_ok(self, ip: str) -> bool:
        """Quick ping test"""
        system = platform.system().lower()
        param = '-n' if system == "windows" else '-c'
        
        try:
            result = subprocess.run(
                ['ping', param, '1', '-W', '2', ip],
                capture_output=True,
                timeout=3
            )
            return result.returncode == 0
        except:
            return False
    
    async def _scan_loop(self):
        """Scan ARP table every 5 seconds to find bound robots by MAC"""
        while self._running:
            try:
                # Just scan the existing ARP table - no need for broadcast
                # The robot should already be in ARP from normal network activity
                entries = self._get_arp_table()
                logger.debug(f"ARP scan found {len(entries)} total entries")
                
                # First, check for any Unitree robots by MAC prefix (auto-discovery)
                for ip, mac in entries:
                    mac_prefix = ':'.join(mac.split(':')[:3])
                    if mac_prefix in UNITREE_MAC_PREFIXES:
                        # Check if this MAC already exists in bound robots (avoid duplicates)
                        existing_robot = None
                        for robot in self._robots.values():
                            if robot.mac_address and robot.mac_address.lower() == mac.lower():
                                existing_robot = robot
                                break
                        
                        if existing_robot:
                            # Update existing bound robot's IP if changed
                            if existing_robot.ip != ip:
                                logger.info(f"🔄 Robot {existing_robot.name} IP changed: {existing_robot.ip} -> {ip}")
                                existing_robot.ip = ip
                            existing_robot.last_seen = datetime.now()
                            existing_robot.is_online = True
                        else:
                            # Auto-discover new robot not in bindings
                            robot_name = f"G1_{mac.replace(':', '')[-4:]}"  # Use last 4 chars of MAC as ID
                            
                            if robot_name not in self._robots:
                                logger.info(f"🤖 Auto-discovered Unitree robot at {ip} (MAC: {mac})")
                                robot = RobotInfo(
                                    serial_number="",
                                    name=robot_name,
                                    ip=ip,
                                    mac_address=mac,
                                    last_seen=datetime.now(),
                                    is_online=True
                                )
                                self._robots[robot_name] = robot
                
                # Then check bound robots (if any)
                for robot_name, robot in list(self._robots.items()):
                    if not robot.mac_address:
                        logger.debug(f"Robot {robot_name} has no MAC address configured")
                        continue
                    
                    target_mac = robot.mac_address.lower()
                    
                    # Search ARP table for this MAC
                    found = False
                    for ip, mac in entries:
                        if mac == target_mac:
                            logger.debug(f"✓ Found {robot_name} at {ip} (MAC: {mac})")
                            if robot.ip != ip:
                                logger.info(f"🔄 Robot {robot_name} IP changed: {robot.ip} -> {ip}")
                            robot.ip = ip
                            robot.is_online = True
                            robot.last_seen = datetime.now()
                            found = True
                            break
                    
                    if not found:
                        # MAC not in ARP cache - robot might be offline
                        if robot.is_online:
                            logger.warning(f"✗ Robot {robot_name} is now OFFLINE (MAC {target_mac} not in ARP)")
                        robot.is_online = False
                        robot.ip = None
                
            except Exception as e:
                logger.error(f"ARP scan error: {e}")
                import traceback
                traceback.print_exc()
            
            await asyncio.sleep(5)
    
    async def start(self):
        """Start ARP-based discovery"""
        if self._running:
            return
        self._running = True
        logger.info("Starting robot discovery via ARP table...")
        self._scan_task = asyncio.create_task(self._scan_loop())
    
    async def stop(self, clear: bool = True):
        """Stop discovery

        Args:
            clear: Whether to clear cached robots (default True)
        """
        if not self._running:
            return
        self._running = False
        logger.info("Stopping robot discovery...")
        if self._scan_task:
            self._scan_task.cancel()
            try:
                await self._scan_task
            except asyncio.CancelledError:
                pass
        if clear:
            self._robots.clear()
    
    def get_robots(self) -> List[RobotInfo]:
        """Get list of discovered robots"""
        return list(self._robots.values())


_discovery_instance = None

def get_discovery() -> RobotDiscovery:
    """Get the singleton discovery instance"""
    global _discovery_instance
    if _discovery_instance is None:
        _discovery_instance = RobotDiscovery()
    return _discovery_instance
