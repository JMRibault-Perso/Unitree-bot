"""
Robot Discovery - mDNS/Bonjour discovery with persistent bindings
"""
import asyncio
import socket
import json
import logging
import os
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
from zeroconf import ServiceBrowser, ServiceListener, Zeroconf
from zeroconf.asyncio import AsyncZeroconf

logger = logging.getLogger(__name__)

@dataclass
class RobotInfo:
    """Information about a discovered robot"""
    serial_number: str
    name: str
    ip: Optional[str] = None
    key: Optional[str] = None
    mac_address: Optional[str] = None  # Store MAC address for discovery
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


class UnitreeServiceListener(ServiceListener):
    """Listens for Unitree robot mDNS services"""
    
    def __init__(self, discovery: 'RobotDiscovery'):
        self.discovery = discovery
        
    def add_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        info = zc.get_service_info(type_, name)
        if info:
            # Extract robot info from mDNS service
            addresses = [socket.inet_ntoa(addr) for addr in info.addresses]
            ip = addresses[0] if addresses else None
            
            # Robot name from service name (e.g., "G1_6937._unitree._tcp.local.")
            robot_name = name.split('.')[0]
            
            # Get serial from TXT record if available
            props = {}
            if info.properties:
                props = {k.decode('utf-8'): v.decode('utf-8') for k, v in info.properties.items()}
            serial = props.get('serial', robot_name)
            
            if ip:
                robot_info = RobotInfo(
                    serial_number=serial,
                    name=robot_name,
                    ip=ip,
                    key=props.get('key'),
                    last_seen=datetime.now()
                )
                self.discovery._add_robot(robot_info)
                logger.info(f"mDNS: Discovered {robot_name} at {ip}")
                
    def remove_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        robot_name = name.split('.')[0]
        logger.info(f"mDNS: Robot {robot_name} offline")
        
    def update_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        self.add_service(zc, type_, name)


class RobotDiscovery:
    """Discovers Unitree robots via multicast UDP (231.1.1.2:10134) and maintains persistent bindings"""
    
    STORAGE_FILE = "/tmp/unitree_robots.json"
    MCAST_GRP = '231.1.1.2'
    MCAST_PORT = 10134
    
    def __init__(self):
        self._robots: Dict[str, RobotInfo] = {}
        self._bound_robots: Dict[str, RobotInfo] = {}  # Persistent bindings
        self._running = False
        self._aiozc: Optional[AsyncZeroconf] = None
        self._browser: Optional[ServiceBrowser] = None
        self._multicast_task: Optional[asyncio.Task] = None
        self._timeout_task: Optional[asyncio.Task] = None
        self._load_bound_robots()
        
    async def _check_robot_port(self, ip: str, mac: str) -> Tuple[bool, str]:
        """Check if port 8081 is open on given IP and MAC matches"""
        try:
            # Fast TCP connection test to port 8081
            conn = asyncio.open_connection(ip, 8081)
            reader, writer = await asyncio.wait_for(conn, timeout=0.5)
            writer.close()
            await writer.wait_closed()
            # Port is open, now verify MAC address via ARP
            proc = await asyncio.create_subprocess_exec(
                'arp', '-n', ip,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.DEVNULL
            )
            stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=0.5)
            if mac.lower() in stdout.decode('utf-8').lower():
                return (True, ip)
        except:
            pass
        return (False, None)
    
    def _load_bound_robots(self):
        """Load previously bound robots from storage"""
        if os.path.exists(self.STORAGE_FILE):
            try:
                with open(self.STORAGE_FILE, 'r') as f:
                    data = json.load(f)
                    for robot_dict in data.get('robots', []):
                        robot = RobotInfo.from_dict(robot_dict)
                        self._bound_robots[robot.name] = robot
                logger.info(f"Loaded {len(self._bound_robots)} bound robots")
            except Exception as e:
                logger.error(f"Failed to load bound robots: {e}")
                
    def _save_bound_robots(self):
        """Save bound robots to storage"""
        try:
            data = {
                'robots': [robot.to_dict() for robot in self._bound_robots.values()]
            }
            with open(self.STORAGE_FILE, 'w') as f:
                json.dump(data, f, indent=2)
            logger.info(f"Saved {len(self._bound_robots)} bound robots")
        except Exception as e:
            logger.error(f"Failed to save bound robots: {e}")
            
    def bind_robot(self, robot: RobotInfo):
        """Bind to a robot (save for future auto-discovery)"""
        self._bound_robots[robot.name] = robot
        self._save_bound_robots()
        logger.info(f"Bound to robot: {robot.name}")
        
    def unbind_robot(self, name: str):
        """Remove robot binding"""
        if name in self._bound_robots:
            del self._bound_robots[name]
            self._save_bound_robots()
            logger.info(f"Unbound robot: {name}")
            
    def _add_robot(self, robot: RobotInfo):
        """Add/update discovered robot"""
        robot.is_online = True
        self._robots[robot.name] = robot
        
        # Update bound robot IP if it changed
        if robot.name in self._bound_robots:
            bound = self._bound_robots[robot.name]
            if bound.ip != robot.ip:
                logger.info(f"Robot {robot.name} IP changed: {bound.ip} -> {robot.ip}")
                bound.ip = robot.ip
                bound.last_seen = robot.last_seen
                bound.is_online = True
                self._save_bound_robots()
        
    async def start(self):
        """Start multicast UDP discovery (231.1.1.2:10134)"""
        if self._running:
            return
            
        self._running = True
        logger.info("Starting robot discovery via multicast UDP...")
        
        # Start multicast listener for Unitree robot broadcasts
        self._multicast_task = asyncio.create_task(self._listen_multicast())
        
        # Also try mDNS as fallback (for newer robots)
        try:
            self._aiozc = AsyncZeroconf()
            await self._aiozc.zeroconf.async_wait_for_start()
            
            listener = UnitreeServiceListener(self)
            service_types = ["_unitree._tcp.local.", "_http._tcp.local.", "_Unitree._tcp.local."]
            
            for service_type in service_types:
                try:
                    ServiceBrowser(self._aiozc.zeroconf, service_type, listener)
                except Exception as e:
                    logger.warning(f"Failed to browse {service_type}: {e}")
        except Exception as e:
            logger.warning(f"mDNS init failed (expected for G1 Air): {e}")
        
        # NO PING MONITORING - rely only on multicast discovery
        
        # Start timeout monitoring for robots that stop broadcasting
        self._timeout_task = asyncio.create_task(self._monitor_broadcast_timeouts())
    
    async def _listen_multicast(self):
        """Listen for robot multicast discovery broadcasts on 231.1.1.2:10134"""
        import socket
        import struct
        import select
        import subprocess
        
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.bind(('', self.MCAST_PORT))
            
            # Auto-detect local IP for multicast interface
            try:
                result = subprocess.run(['ip', 'route', 'get', self.MCAST_GRP], 
                                      capture_output=True, text=True, timeout=1)
                # Parse: "multicast 231.1.1.2 dev eth1 src 192.168.86.10"
                for word in result.stdout.split():
                    if '192.168.' in word or '10.' in word or '172.' in word:
                        local_ip = word
                        break
                else:
                    local_ip = None
            except:
                local_ip = None
            
            # Join multicast group on specific interface (or ANY if auto-detect failed)
            if local_ip:
                mreq = struct.pack("4s4s", socket.inet_aton(self.MCAST_GRP), socket.inet_aton(local_ip))
                logger.info(f"Joining multicast group {self.MCAST_GRP} on {local_ip}")
            else:
                mreq = struct.pack("4sl", socket.inet_aton(self.MCAST_GRP), socket.INADDR_ANY)
                logger.info(f"Joining multicast group {self.MCAST_GRP} on ANY interface")
            
            sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
            
            # Enable multicast loopback
            sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_LOOP, 1)
            sock.settimeout(1.0)  # 1 second timeout
            
            logger.info(f"Listening for robot broadcasts on {self.MCAST_GRP}:{self.MCAST_PORT}")
            
            while self._running:
                try:
                    # Use select with timeout
                    ready = select.select([sock], [], [], 1.0)
                    if ready[0]:
                        data, addr = sock.recvfrom(1024)
                        
                        try:
                            robot_data = json.loads(data.decode('utf-8'))
                            serial = robot_data.get('sn', '')
                            name = robot_data.get('name', '')
                            ip = robot_data.get('ip', '')
                            key = robot_data.get('key', '')
                            
                            if serial and ip:
                                logger.info(f"✓ Multicast: Found robot SN={serial}, name={name}, ip={ip}")
                                
                                robot = RobotInfo(
                                    serial_number=serial,
                                    name=name or serial,  # Use serial if no name
                                    ip=ip,
                                    key=key if key else None,
                                    last_seen=datetime.now(),
                                    is_online=True
                                )
                                
                                # Add to discovered robots
                                self._robots[robot.name] = robot
                                
                                # Update bound robot if it matches
                                for bound_name, bound_robot in list(self._bound_robots.items()):
                                    if bound_robot.serial_number == serial:
                                        logger.info(f"✓ Live broadcast: {bound_name} is online at {ip}")
                                        # Don't save IP to persistent storage - only use for live status
                                        bound_robot.last_seen = datetime.now()
                                        bound_robot.is_online = True
                                        if not bound_robot.name or bound_robot.name == bound_robot.serial_number:
                                            bound_robot.name = name if name else serial
                                        # No _save_bound_robots() call - don't persist IP
                                        break
                                
                        except json.JSONDecodeError:
                            logger.debug(f"Non-JSON multicast packet from {addr}")
                        except Exception as e:
                            logger.error(f"Error parsing multicast packet: {e}")
                    else:
                        # Timeout, just loop again
                        await asyncio.sleep(0.1)
                        
                except socket.timeout:
                    await asyncio.sleep(0.1)
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    if self._running:
                        logger.error(f"Multicast listener error: {e}")
                    await asyncio.sleep(1)
                    
        except Exception as e:
            logger.error(f"Failed to start multicast listener: {e}")
        finally:
            try:
                sock.close()
            except:
                pass
    
    # NO PING MONITORING - Robot status determined purely by multicast discovery
    
    async def _monitor_broadcast_timeouts(self):
        """Mark robots as offline if they haven't broadcast in 30 seconds"""
        while self._running:
            try:
                current_time = datetime.now()
                
                for robot in list(self._robots.values()):
                    if robot.last_seen:
                        time_since_last_seen = (current_time - robot.last_seen).total_seconds()
                        if time_since_last_seen > 30 and robot.is_online:  # 30 second timeout
                            logger.info(f"✗ {robot.name} broadcast timeout - marking offline")
                            robot.is_online = False
                            
                            # Update bound robot too
                            if robot.name in self._bound_robots:
                                self._bound_robots[robot.name].is_online = False
                
                await asyncio.sleep(10)  # Check every 10 seconds
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in broadcast timeout monitor: {e}")
                await asyncio.sleep(5)
    
    async def _find_robot_on_subnet(self, robot_name: str) -> Optional[str]:
        """Scan local subnet to find a specific robot"""
        try:
            # Get local IP to determine subnet
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()
            
            subnet = '.'.join(local_ip.split('.')[:-1])
            
            # Scan common IPs first (.2, .3, .16)
            priority_ips = [f"{subnet}.{i}" for i in [2, 3, 16]]
            
            for ip in priority_ips:
                try:
                    # Use ping instead of TCP connection
                    proc = await asyncio.create_subprocess_exec(
                        'ping', '-c', '1', '-W', '1', ip,
                        stdout=asyncio.subprocess.DEVNULL,
                        stderr=asyncio.subprocess.DEVNULL
                    )
                    returncode = await proc.wait()
                    
                    if returncode == 0:
                        return ip
                except Exception:
                    continue
                    
        except Exception as e:
            logger.error(f"Subnet scan failed: {e}")
            
        return None
                
    async def stop(self):
        """Stop discovery"""
        self._running = False
        
        if self._multicast_task:
            self._multicast_task.cancel()
            try:
                await self._multicast_task
            except asyncio.CancelledError:
                pass
        
        if self._timeout_task:
            self._timeout_task.cancel()
            try:
                await self._timeout_task
            except asyncio.CancelledError:
                pass
        
        print(f"Robot discovery stopped. Discovered {len(self._robots)} robots, bound {len(self._bound_robots)} robots.")
    
    def get_bound_robots(self) -> List[RobotInfo]:
        """Get list of bound robots only"""
        return list(self._bound_robots.values())

    async def get_robots(self) -> List[RobotInfo]:
        """Get list of all robots (bound robots with live IP from broadcasts)"""
        all_robots = {}
        
        # Start with bound robots (no stored IP)
        for name, robot in self._bound_robots.items():
            all_robots[name] = robot
            
        # Update with live broadcast information (IP only from live broadcasts)
        for name, discovered_robot in self._robots.items():
            if name in all_robots:
                # Update bound robot with live broadcast info (but don't persist it)
                bound_robot = all_robots[name]
                bound_robot.ip = discovered_robot.ip  # Live IP only
                bound_robot.last_seen = discovered_robot.last_seen  
                bound_robot.is_online = discovered_robot.is_online
            else:
                # Add newly discovered robot (not bound)
                all_robots[name] = discovered_robot
                
        # Real-time robot reachability check via network scanning (NO hardcoded IPs)
        for name, robot in all_robots.items():
            if robot.mac_address:
                # Discover robot IP by MAC address scan (fully dynamic)
                from datetime import datetime
                
                is_reachable = False
                discovered_ip = None
                
                try:
                    # If we have a stored IP, test it first (quick ping)
                    if robot.ip:
                        proc = await asyncio.create_subprocess_exec(
                            'ping', '-c', '1', '-W', '1', robot.ip,
                            stdout=asyncio.subprocess.DEVNULL,
                            stderr=asyncio.subprocess.DEVNULL
                        )
                        try:
                            returncode = await asyncio.wait_for(proc.wait(), timeout=2)
                            if returncode == 0:
                                robot.is_online = True
                                robot.last_seen = datetime.now()
                                is_reachable = True
                                logger.debug(f"✓ Ping: {name} online at {robot.ip}")
                        except asyncio.TimeoutError:
                            proc.kill()
                            await proc.wait()
                    
                    # If no IP or ping failed, scan for MAC address
                    if not is_reachable:
                        # Try fast arp cache lookup first (no network scan needed)
                        proc = await asyncio.create_subprocess_exec(
                            'arp', '-n',
                            stdout=asyncio.subprocess.PIPE,
                            stderr=asyncio.subprocess.DEVNULL
                        )
                        try:
                            stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=1)
                            arp_output = stdout.decode('utf-8')
                            for line in arp_output.split('\n'):
                                if robot.mac_address.lower() in line.lower():
                                    parts = line.split()
                                    if len(parts) >= 1:
                                        discovered_ip = parts[0].strip().rstrip(')')
                                        # Verify with quick ping
                                        ping_proc = await asyncio.create_subprocess_exec(
                                            'ping', '-c', '1', '-W', '1', discovered_ip,
                                            stdout=asyncio.subprocess.DEVNULL,
                                            stderr=asyncio.subprocess.DEVNULL
                                        )
                                        try:
                                            ping_return = await asyncio.wait_for(ping_proc.wait(), timeout=1)
                                            if ping_return == 0:
                                                robot.ip = discovered_ip
                                                robot.is_online = True
                                                robot.last_seen = datetime.now()
                                                is_reachable = True
                                                logger.info(f"✓ Discovered (ARP cache): {name} at {discovered_ip}")
                                                break
                                        except asyncio.TimeoutError:
                                            ping_proc.kill()
                                            await ping_proc.wait()
                        except asyncio.TimeoutError:
                            proc.kill()
                            await proc.wait()
                        
                        # If not in cache, scan subnet for port 8081 (WebRTC signaling server)
                        if not is_reachable:
                            # Get subnet from local IP
                            route_proc = await asyncio.create_subprocess_exec(
                                'ip', 'route', 'get', '8.8.8.8',
                                stdout=asyncio.subprocess.PIPE,
                                stderr=asyncio.subprocess.DEVNULL
                            )
                            try:
                                route_stdout, _ = await asyncio.wait_for(route_proc.communicate(), timeout=1)
                                route_output = route_stdout.decode('utf-8')
                                subnet_base = None
                                for word in route_output.split():
                                    if '192.168.' in word or '10.' in word or '172.' in word:
                                        # Extract subnet (e.g., 192.168.86.10 -> 192.168.86)
                                        parts = word.split('.')
                                        if len(parts) == 4:
                                            subnet_base = f"{parts[0]}.{parts[1]}.{parts[2]}"
                                            break
                                
                                if subnet_base:
                                    logger.debug(f"Scanning {subnet_base}.0/24 for port 8081...")
                                    # Fast parallel port scan
                                    tasks = [self._check_robot_port(f"{subnet_base}.{i}", robot.mac_address) for i in range(1, 255)]
                                    try:
                                        results = await asyncio.wait_for(asyncio.gather(*tasks, return_exceptions=True), timeout=5)
                                        for result in results:
                                            if isinstance(result, tuple) and result[0]:
                                                discovered_ip = result[1]
                                                robot.ip = discovered_ip
                                                robot.is_online = True
                                                robot.last_seen = datetime.now()
                                                is_reachable = True
                                                logger.info(f"✓ Discovered (port 8081): {name} at {discovered_ip}")
                                                break
                                    except asyncio.TimeoutError:
                                        logger.warning(f"Port scan timed out for {subnet_base}.0/24")
                            except asyncio.TimeoutError:
                                route_proc.kill()
                                await route_proc.wait()
                except Exception as e:
                    logger.debug(f"Discovery failed for {name}: {e}")
                
                # If robot is not reachable, mark offline
                if not is_reachable:
                    robot.is_online = False
                    # Keep last known IP for reference
                    logger.debug(f"✗ Robot offline: {name} not reachable")
        
        return list(all_robots.values())

# Singleton instance
_discovery_instance = None

def get_discovery() -> RobotDiscovery:
    """Get the singleton discovery instance"""
    global _discovery_instance
    if _discovery_instance is None:
        _discovery_instance = RobotDiscovery()
    return _discovery_instance
