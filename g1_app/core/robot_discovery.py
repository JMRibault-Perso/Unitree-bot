"""Robot Discovery - Active MAC-based discovery for Unitree robots
Dynamically finds robot by MAC address on any network without fixed IPs

Enhanced with Android app protocol insights:
- Multicast discovery (231.1.1.2:7400)
- Network mode detection (AP/STA-L/STA-T)
- Multiple discovery methods (multicast, broadcast, ARP, nmap)
- Fast initial discovery with fallback to thorough scans
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

# Import enhanced discovery functions
try:
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from utils.arp_discovery import (
        try_multicast_discovery,
        get_network_interfaces as get_enhanced_interfaces,
        detect_network_mode,
        G1_AP_IP
    )
    ENHANCED_DISCOVERY = True
except ImportError:
    logger.warning("Enhanced discovery functions not available")
    ENHANCED_DISCOVERY = False

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
    network_mode: Optional[str] = None  # "AP", "STA-L", or "STA-T" (from phone logs)
    missed_scans: int = 0  # Track consecutive failed detections for offline detection
    
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
    """Discovers Unitree robots by active MAC-based network scanning"""
    
    def __init__(self):
        self._robots: Dict[str, RobotInfo] = {}
        self._running = False
        self._scan_task: Optional[asyncio.Task] = None
        self._load_bindings()
        
    def _load_bindings(self):
        """Load robot bindings from file - MAC only, IP will be discovered"""
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
                    ip=None,  # DO NOT load cached IP - discover fresh
                    mac_address=mac.lower(),
                    last_seen=None,
                    is_online=False
                )
                self._robots[robot.name] = robot
                logger.info(f"Loaded bound robot: {robot.name} (MAC: {mac}) - IP will be discovered")
                
        except Exception as e:
            logger.error(f"Failed to load bindings: {e}")
    
    def _update_bindings_with_ip(self, robot_name: str, ip: str):
        """Update bindings file with discovered robot IP"""
        try:
            bindings = {}
            if BINDINGS_FILE.exists():
                with open(BINDINGS_FILE, 'r') as f:
                    bindings = json.load(f)
            
            for mac, data in bindings.items():
                if data.get("name") == robot_name:
                    data["ip"] = ip
                    logger.debug(f"Updated IP for {robot_name}: {ip}")
                    break
            
            with open(BINDINGS_FILE, 'w') as f:
                json.dump(bindings, f, indent=2)
                
        except Exception as e:
            logger.warning(f"Failed to update bindings file: {e}")
    
    def _get_network_interfaces(self) -> List[Tuple[str, str]]:
        """Get all network interfaces and their subnets"""
        interfaces = []
        try:
            # Use timeout to avoid hanging
            result = subprocess.run(['ip', 'route'], capture_output=True, text=True, timeout=1)
            for line in result.stdout.split('\n'):
                if 'dev' in line:
                    parts = line.split()
                    if len(parts) >= 1:
                        network = parts[0]
                        try:
                            dev_idx = parts.index('dev')
                            if dev_idx + 1 < len(parts):
                                iface = parts[dev_idx + 1]
                                if network and iface:
                                    interfaces.append((network, iface))
                                    logger.debug(f"Found network: {network} on {iface}")
                        except (ValueError, IndexError):
                            continue
        except subprocess.TimeoutExpired:
            logger.warning("ip route command timed out - skipping network interface detection")
        except Exception as e:
            logger.debug(f"Failed to get network interfaces: {e}")
        
        # Fallback: if no interfaces found, try eth0/eth1 with common subnets
        if not interfaces:
            logger.debug("No interfaces found via ip route, using fallback")
            interfaces = [
                ("192.168.0.0/16", "eth0"),
                ("192.168.86.0/22", "eth1"),
                ("10.0.0.0/8", "eth0"),
            ]
        
        return interfaces
    
    def _get_arp_table(self) -> List[Tuple[str, str]]:
        """Get ARP table - returns list of (IP, MAC) tuples"""
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
                    if len(parts) >= 2:
                        ip = parts[0].strip()
                        if '.' in ip and len(ip.split('.')) == 4:
                            mac = parts[1].strip().replace('-', ':').lower()
                            if ':' in mac or len(mac.replace(':', '')) == 12:
                                arp_entries.append((ip, mac))
                                logger.debug(f"ARP: {ip} -> {mac}")
            else:
                # Linux/Mac: parse arp -n output
                result = subprocess.run(['arp', '-n'], capture_output=True, text=True, timeout=2)
                for line in result.stdout.split('\n'):
                    line = line.strip()
                    if not line or line.startswith('Address'):
                        continue
                    
                    parts = line.split()
                    if len(parts) < 3:
                        continue
                    
                    ip = parts[0]
                    if not ('.' in ip and len(ip.split('.')) == 4):
                        continue
                    
                    # Column 2 is either MAC or (incomplete) or interface name
                    if len(parts) >= 3:
                        candidate = parts[2].lower()
                        if ':' in candidate or '-' in candidate:
                            arp_entries.append((ip, candidate))
                            logger.debug(f"ARP: {ip} -> {candidate}")
                        elif candidate == "(incomplete)":
                            logger.debug(f"Skip incomplete: {ip}")
                            
        except Exception as e:
            logger.error(f"Failed to read ARP table: {e}")
        
        logger.info(f"ARP scan found {len(arp_entries)} entries total")
        return arp_entries
    
    def _nmap_scan(self, subnet: str = "192.168.86.0/24") -> List[Tuple[str, str]]:
        """Use nmap to find active hosts and try to get MACs via ARP"""
        import time
        results = []
        try:
            start = time.time()
            logger.info(f"Running nmap scan on {subnet}...")
            result = subprocess.run(
                ['nmap', '-sn', subnet],
                capture_output=True, text=True, timeout=20
            )
            
            if result.returncode == 0:
                import re
                host_count = len(re.findall(r'Nmap scan report for', result.stdout))
                logger.info(f"nmap found {host_count} hosts in {time.time() - start:.1f}s")
                
                for line in result.stdout.split('\n'):
                    match = re.search(r'Nmap scan report for (\d+\.\d+\.\d+\.\d+)', line)
                    if match:
                        ip = match.group(1)
                        # After nmap pings it, try to get MAC from ARP
                        try:
                            arp_result = subprocess.run(
                                ['arp', '-n', ip], capture_output=True, text=True, timeout=1
                            )
                            mac = None
                            for arp_line in arp_result.stdout.split('\n'):
                                parts = arp_line.split()
                                if len(parts) >= 3 and parts[0] == ip:
                                    candidate = parts[2].lower()
                                    if ':' in candidate or '-' in candidate:
                                        mac = candidate
                                        break
                            
                            if mac:
                                results.append((ip, mac))
                                logger.debug(f"nmap found: {ip} -> {mac}")
                            else:
                                # Just add the IP without MAC
                                results.append((ip, "unknown"))
                        except:
                            results.append((ip, "unknown"))
                
                logger.info(f"nmap complete: {len(results)} hosts analyzed in {time.time() - start:.1f}s total")
        except subprocess.TimeoutExpired:
            logger.warning(f"nmap scan timeout on {subnet}")
        except FileNotFoundError:
            logger.debug("nmap not installed - skipping nmap scan")
        except Exception as e:
            logger.warning(f"nmap scan failed: {e}")
        
        return results
    
    async def _broadcast_arp_scan(self, network: str, interface: str):
        """Send ARP broadcast to wake up devices on network"""
        try:
            import ipaddress
            net = ipaddress.ip_network(network, strict=False)
            broadcast_ip = str(net.broadcast_address)
            logger.debug(f"Broadcast ping to {broadcast_ip} on {interface}")
            
            subprocess.run(['ping', '-c', '1', '-W', '1', broadcast_ip], 
                         capture_output=True, timeout=2)
        except Exception as e:
            logger.debug(f"Broadcast scan skipped: {e}")
    
    async def _scan_loop(self):
        """Scan networks for robots by MAC address"""
        import time
        while self._running:
            try:
                scan_start = time.time()
                logger.debug("=" * 70)
                logger.debug("DISCOVERY SCAN START")
                logger.debug("=" * 70)
                
                # STEP 1: Try multicast discovery (fastest when robot broadcasts)
                multicast_found = set()
                if ENHANCED_DISCOVERY:
                    logger.debug("Listening for robot multicast broadcasts...")
                    multicast_ip = try_multicast_discovery(timeout=0.5)
                    
                    if multicast_ip:
                        # Get MAC for the multicast responder
                        try:
                            result = subprocess.run(['arp', '-n', multicast_ip], 
                                                   capture_output=True, text=True, timeout=1)
                            for line in result.stdout.split('\n'):
                                if multicast_ip in line:
                                    parts = line.split()
                                    if len(parts) >= 3 and parts[2] != '<incomplete>':
                                        multicast_mac = parts[2].lower()
                                        
                                        # Find which robot this is
                                        for robot_name, robot in list(self._robots.items()):
                                            if robot.mac_address and robot.mac_address.lower() == multicast_mac:
                                                mode = detect_network_mode(multicast_ip)
                                                if not robot.is_online:
                                                    logger.info(f"✓ {robot_name} ONLINE via multicast: {multicast_ip} ({mode})")
                                                
                                                robot.ip = multicast_ip
                                                robot.network_mode = mode
                                                robot.is_online = True
                                                robot.last_seen = datetime.now()
                                                robot.missed_scans = 0
                                                multicast_found.add(robot_name)
                                                break
                                        break
                        except Exception as e:
                            logger.debug(f"Failed to get MAC for {multicast_ip}: {e}")
                
                # STEP 2: ARP fallback for robots not found via multicast
                robots_to_check = [name for name in self._robots.keys() if name not in multicast_found]
                
                if robots_to_check:
                    # Quick ARP scan for bound robots only
                    try:
                        result = subprocess.run(['arp', '-n'], capture_output=True, text=True, timeout=1)
                        for robot_name in robots_to_check:
                            robot = self._robots[robot_name]
                            if not robot.mac_address:
                                continue
                            
                            target_mac = robot.mac_address.lower()
                            found = False
                            
                            # Search ARP table for this specific MAC
                            for line in result.stdout.split('\n')[1:]:
                                parts = line.split()
                                if len(parts) >= 3 and parts[2].lower() == target_mac:
                                    ip = parts[0]
                                    
                                    # ALWAYS verify with ping - ARP cache can be stale
                                    try:
                                        ping_result = subprocess.run(
                                            ['ping', '-c', '1', '-W', '1', ip],
                                            capture_output=True,
                                            timeout=1.5  # Quick timeout
                                        )
                                        if ping_result.returncode != 0:
                                            logger.debug(f"⚠️  {robot_name} in ARP but not responding to ping")
                                            continue
                                    except:
                                        logger.debug(f"⚠️  {robot_name} ping failed")
                                        continue
                                    
                                    mode = detect_network_mode(ip) if ENHANCED_DISCOVERY else None
                                    
                                    if not robot.is_online:
                                        logger.info(f"✓ {robot_name} ONLINE via ARP: {ip} ({mode})")
                                    
                                    robot.ip = ip
                                    robot.network_mode = mode
                                    robot.is_online = True
                                    robot.last_seen = datetime.now()
                                    robot.missed_scans = 0
                                    found = True
                                    break
                            
                            if not found:
                                robot.missed_scans += 1
                                # Mark offline after 1 missed scan (2s with 2s intervals)
                                if robot.missed_scans >= 1:
                                    if robot.is_online:
                                        logger.warning(f"✗ {robot_name} OFFLINE (not responding to ping)")
                                    robot.is_online = False
                    except Exception as e:
                        logger.error(f"ARP scan failed: {e}")
                
                scan_duration = time.time() - scan_start
                logger.info(f"DISCOVERY SCAN COMPLETE in {scan_duration:.2f}s total")
                
            except Exception as e:
                logger.error(f"Error in discovery scan: {e}", exc_info=True)
            
            await asyncio.sleep(2)  # Scan every 2 seconds (fast like Android app)
    
    async def start(self):
        """Start robot discovery"""
        if self._running:
            return
        self._running = True
        logger.info("Starting active MAC-based robot discovery...")
        self._scan_task = asyncio.create_task(self._scan_loop())
    
    async def stop(self, clear: bool = True):
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
        if clear:
            self._robots.clear()
    
    def get_robots(self) -> List[RobotInfo]:
        """Get list of discovered robots"""
        return list(self._robots.values())


_discovery_instance = None

def get_discovery() -> RobotDiscovery:
    """Get singleton discovery instance"""
    global _discovery_instance
    if _discovery_instance is None:
        _discovery_instance = RobotDiscovery()
    return _discovery_instance
