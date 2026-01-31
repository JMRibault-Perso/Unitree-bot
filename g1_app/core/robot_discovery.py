"""
Robot Discovery - ARP table scanning (Windows/Linux compatible)
"""
import asyncio
import logging
import platform
import subprocess
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime

logger = logging.getLogger(__name__)

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
    
    # Known Unitree G1 MAC prefix
    UNITREE_MAC_PREFIX = "fc:23:cd"
    
    def __init__(self):
        self._robots: Dict[str, RobotInfo] = {}
        self._running = False
        self._scan_task: Optional[asyncio.Task] = None
        
    def _get_arp_table(self) -> List[Tuple[str, str]]:
        """Get ARP table - returns list of (IP, MAC) tuples"""
        arp_entries = []
        
        try:
            system = platform.system().lower()
            
            if system == "windows":
                result = subprocess.run(['arp', '-a'], capture_output=True, text=True, timeout=2)
                for line in result.stdout.split('\n'):
                    parts = line.split()
                    if len(parts) >= 2:
                        ip = parts[0].strip()
                        mac = parts[1].strip().replace('-', ':')
                        if mac.lower().startswith(self.UNITREE_MAC_PREFIX):
                            arp_entries.append((ip, mac))
            else:
                # Linux/Mac
                result = subprocess.run(['arp', '-n'], capture_output=True, text=True, timeout=2)
                for line in result.stdout.split('\n'):
                    parts = line.split()
                    if len(parts) >= 3:
                        ip = parts[0]
                        mac = parts[2]
                        if mac.lower().startswith(self.UNITREE_MAC_PREFIX):
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
                ['ping', param, '1', '-w', '500' if system == "windows" else '0.5', ip],
                capture_output=True,
                timeout=1
            )
            return result.returncode == 0
        except:
            return False
    
    async def _scan_loop(self):
        """Scan ARP table every 5 seconds"""
        while self._running:
            try:
                entries = self._get_arp_table()
                current_robots = {}
                
                for ip, mac in entries:
                    if self._ping_ok(ip):
                        robot_name = f"Robot_{ip.replace('.', '_')}"
                        robot = RobotInfo(
                            serial_number="E21D1000PAHBMB06",
                            name=robot_name,
                            ip=ip,
                            mac_address=mac,
                            last_seen=datetime.now(),
                            is_online=True
                        )
                        current_robots[robot_name] = robot
                        if robot_name not in self._robots:
                            logger.info(f"ARP: Found new robot {robot_name} at {ip} (MAC: {mac})")
                
                self._robots = current_robots
                
            except Exception as e:
                logger.error(f"ARP scan error: {e}")
            
            await asyncio.sleep(5)
    
    async def start(self):
        """Start ARP-based discovery"""
        if self._running:
            return
        self._running = True
        logger.info("Starting robot discovery via ARP table...")
        self._scan_task = asyncio.create_task(self._scan_loop())
    
    async def stop(self):
        """Stop discovery"""
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
