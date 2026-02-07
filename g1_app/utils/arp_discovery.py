#!/usr/bin/env python3
"""
Robot Discovery - Enhanced with insights from Android app protocol analysis
Supports: MAC-based ARP, multicast discovery, multiple network modes (AP/STA-L/STA-T)

Phone log insights:
- Robot broadcasts on multicast 231.1.1.2 (discovered from logs)
- Network modes: AP (192.168.12.1), STA-L (local network), STA-T (remote/cloud)
- WiFi interface MAC: fc:23:cd:92:60:02 (WiFi), fe:23:cd:92:60:02 (BLE)
- Link-local addresses (169.254.x.x) also available
"""
import subprocess
import platform
import re
import logging
import socket
import ipaddress
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

# G1_6937 known addresses
G1_MAC = "fc:23:cd:92:60:02"  # WiFi MAC address
G1_BLE_MAC = "fe:23:cd:92:60:02"  # BLE MAC address (phone logs)
G1_AP_IP = "192.168.12.1"  # AP mode default IP (phone logs)

# Network discovery parameters (from phone logs)
MULTICAST_GROUP = "231.1.1.2"  # Robot multicast group (discovered in logs)
MULTICAST_PORT = 7400  # DDS discovery port
BROADCAST_PORT = 7400  # UDP broadcast port

def try_multicast_discovery(timeout: float = 2.0) -> Optional[str]:
    """
    Attempt robot discovery via multicast (as Android app does).
    Phone logs show: "收到组播ip:timeout" (multicast discovery attempt)
    
    Args:
        timeout: How long to wait for response
    
    Returns:
        Robot IP address if discovered, None otherwise
    """
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.settimeout(timeout)
        
        # Join multicast group
        mreq = socket.inet_aton(MULTICAST_GROUP) + socket.inet_aton('0.0.0.0')
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
        
        # Bind to multicast port
        sock.bind(('', MULTICAST_PORT))
        
        logger.debug(f"Listening for multicast on {MULTICAST_GROUP}:{MULTICAST_PORT}")
        
        # Wait for any multicast message from robot
        try:
            data, addr = sock.recvfrom(1024)
            robot_ip = addr[0]
            logger.info(f"✅ Multicast discovery: robot at {robot_ip}")
            sock.close()
            return robot_ip
        except socket.timeout:
            logger.debug("Multicast discovery timeout (expected if robot on different network)")
            sock.close()
            return None
            
    except Exception as e:
        logger.debug(f"Multicast discovery failed: {e}")
        return None


def get_network_interfaces() -> list:
    """
    Get all active network interfaces with their IP addresses.
    Phone logs show app detects: type 0=connection, 1=local IP, 2=cloud, 3=AP
    
    Returns:
        List of (interface_name, ip_address, subnet) tuples
    """
    interfaces = []
    try:
        # Method 1: Parse ip addr show for all interfaces with IPs
        result = subprocess.run(['ip', 'addr', 'show'], capture_output=True, text=True, timeout=2)
        current_iface = None
        for line in result.stdout.split('\n'):
            # Interface line: "2: eth0: <BROADCAST,MULTICAST,UP,LOWER_UP>"
            if not line.startswith(' '):
                parts = line.split(':')
                if len(parts) >= 2:
                    current_iface = parts[1].strip()
            # IP line: "    inet 192.168.86.12/22 brd 192.168.87.255 scope global"
            elif 'inet ' in line and current_iface:
                parts = line.split()
                if 'inet' in parts:
                    idx = parts.index('inet')
                    if idx + 1 < len(parts):
                        ip_cidr = parts[idx + 1]
                        if '/' in ip_cidr:
                            ip_addr = ip_cidr.split('/')[0]
                            # Skip loopback
                            if not ip_addr.startswith('127.'):
                                interfaces.append((current_iface, ip_addr, ip_cidr))
                                logger.debug(f"Network interface: {current_iface} -> {ip_addr} ({ip_cidr})")
    except Exception as e:
        logger.debug(f"Failed to get network interfaces: {e}")
    
    return interfaces


def detect_network_mode(robot_ip: str) -> str:
    """
    Detect which network mode robot is in (from phone logs).
    
    Args:
        robot_ip: Robot's IP address
    
    Returns:
        "AP" (robot hotspot), "STA-L" (same network), or "STA-T" (different network)
    """
    # AP mode detection
    if robot_ip == G1_AP_IP or robot_ip.startswith("192.168.12."):
        return "AP"
    
    # Check if on same local network
    interfaces = get_network_interfaces()
    for iface, local_ip, network in interfaces:
        try:
            net = ipaddress.ip_network(network, strict=False)
            robot_addr = ipaddress.ip_address(robot_ip)
            local_addr = ipaddress.ip_address(local_ip)
            
            if robot_addr in net and local_addr in net:
                logger.debug(f"Robot on same network {network} via {iface}")
                return "STA-L"  # Station mode - Local network
        except:
            continue
    
    # If not on same network, must be STA-T (remote)
    return "STA-T"


def discover_robot_ip(target_mac: str = G1_MAC, timeout: int = 10, fast: bool = True) -> str:
    """
    Discover robot IP using multiple methods (fastest to slowest).
    Enhanced with Android app protocol insights from phone logs.
    
    Discovery order (if fast=True):
    1. Multicast discovery (231.1.1.2) - Android app uses this
    2. AP mode check (192.168.12.1) - Default when robot is hotspot
    3. ARP table scan - Fast if cache populated
    4. Network broadcast + ARP rescan
    5. Full nmap scan (slowest, most thorough)
    
    Args:
        target_mac: MAC address to search for (default: G1_6937)
        timeout: Maximum time to spend on slow methods (seconds)
        fast: If True, try quick methods first before slow scans
    
    Returns:
        IP address string or raises RuntimeError if not found
    """
    target_mac = target_mac.lower().replace("-", ":").replace(".", ":")
    
    logger.info(f"🔍 Discovering robot (MAC: {target_mac})...")
    
    # FAST METHOD 1: Try multicast discovery (Android app does this)
    if fast:
        logger.debug("Trying multicast discovery...")
        ip = try_multicast_discovery(timeout=1.0)
        if ip:
            mode = detect_network_mode(ip)
            logger.info(f"✅ Found via multicast: {ip} (mode: {mode})")
            return ip
    
    # FAST METHOD 2: Check if robot is in AP mode
    if fast and ping_test(G1_AP_IP):
        logger.info(f"✅ Found in AP mode: {G1_AP_IP}")
        return G1_AP_IP
    
    # FAST METHOD 3: Check ARP cache (no network traffic)
    logger.debug("Checking ARP cache...")
    system = platform.system().lower()
    
    # Scan existing ARP cache first (no network traffic)
    def scan_arp_cache():
        try:
            if system == "windows":
                # Windows: arp -a
                output = subprocess.check_output(['arp', '-a'], text=True)
                # Format: 192.168.86.8         fc-23-cd-92-60-02     dynamic
                for line in output.split('\n'):
                    parts = line.split()
                    if len(parts) >= 2:
                        ip = parts[0]
                        mac = parts[1].lower().replace("-", ":")
                        if mac == target_mac:
                            return ip
            else:
                # Linux: arp -n or ip neigh
                try:
                    output = subprocess.check_output(['arp', '-n'], text=True)
                except FileNotFoundError:
                    output = subprocess.check_output(['ip', 'neigh'], text=True)
                
                # Format: 192.168.86.8 ether fc:23:cd:92:60:02 ...
                for line in output.split('\n'):
                    parts = line.split()
                    if len(parts) >= 3:
                        ip = parts[0]
                        mac = parts[2].lower() if 'ether' in parts[1] else parts[1].lower()
                        mac = mac.replace("-", ":")
                        if mac == target_mac:
                            return ip
        except Exception as e:
            logger.debug(f"ARP cache scan failed: {e}")
        return None
    
    # Try ARP cache first
    ip = scan_arp_cache()
    if ip:
        mode = detect_network_mode(ip)
        logger.info(f"✅ Found in ARP cache: {ip} (mode: {mode})")
        return ip
    
    # Not in cache - trigger network broadcast to populate ARP
    logger.debug("Robot not in ARP cache, triggering broadcast ping...")
    interfaces = get_network_interfaces()
    for iface, local_ip, network in interfaces:
        try:
            net = ipaddress.ip_network(network, strict=False)
            broadcast_ip = str(net.broadcast_address)
            logger.debug(f"Broadcast ping to {broadcast_ip}")
            
            if system == "windows":
                subprocess.run(['ping', '-n', '1', broadcast_ip],
                             capture_output=True, timeout=2)
            else:
                subprocess.run(['ping', '-c', '1', '-b', broadcast_ip],
                             capture_output=True, timeout=2)
        except:
            pass
    
    # Rescan ARP cache after broadcast
    ip = scan_arp_cache()
    if ip:
        mode = detect_network_mode(ip)
        logger.info(f"✅ Found after broadcast: {ip} (mode: {mode})")
        return ip
    
    # Fallback: Try nmap network scan
    logger.info("Not found in ARP cache, trying nmap scan...")
    try:
        output = subprocess.check_output(
            ['nmap', '-sn', '192.168.86.0/24'],
            text=True,
            stderr=subprocess.DEVNULL,
            timeout=40  # Increase timeout for network scan
        )
        
        lines = output.split('\n')
        for i, line in enumerate(lines):
            if target_mac in line.lower():
                # Look back for IP in "Nmap scan report for X.X.X.X"
                for j in range(i-1, max(i-5, -1), -1):
                    if 'Nmap scan report for' in lines[j]:
                        ip = lines[j].split()[-1]
                        logger.info(f"✅ Found robot at {ip} via nmap (MAC: {target_mac})")
                        return ip
    except Exception as e:
        logger.debug(f"Nmap scan failed: {e}")
    
    # Provide helpful error message based on network modes from phone logs
    raise RuntimeError(
        f"Robot with MAC {target_mac} not found.\n"
        f"Ensure robot is:\n"
        f"  1. Powered on\n"
        f"  2. In one of these network modes:\n"
        f"     - AP mode: Robot creates WiFi 'G1_6937' (should appear at {G1_AP_IP})\n"
        f"     - STA-L mode: Robot and PC on same WiFi network\n"
        f"     - STA-T mode: Robot on different network (requires cloud relay - not supported)\n"
        f"  3. Not blocked by firewall (needs UDP port {MULTICAST_PORT})\n"
        f"\nTry: Connect to robot's WiFi hotspot 'G1_6937' (password: 88888888)"
    )


def ping_test(ip: str) -> bool:
    """Quick ping test to verify connectivity"""
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


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    
    print("Scanning for G1_6937...")
    try:
        ip = discover_robot_ip()
        print(f"Robot IP: {ip}")
        
        if ping_test(ip):
            print(f"✅ Ping successful!")
        else:
            print(f"⚠️  Ping failed - robot may not be ready")
    except RuntimeError as e:
        print(f"❌ {e}")
