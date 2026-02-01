#!/usr/bin/env python3
"""
Helper function to discover Unitree robot on network
Uses multicast discovery (231.1.1.2:10134) to find robot IP automatically
"""
import socket
import struct
import json
import logging
import time

logger = logging.getLogger(__name__)

MCAST_GRP = '231.1.1.2'
MCAST_PORT = 10134
TARGET_MAC = 'fc:23:cd:92:60:02'  # G1_6937 MAC address

def discover_robot_ip(timeout=10, target_mac=TARGET_MAC):
    """
    Discover Unitree robot IP address via multicast discovery.
    
    Args:
        timeout: Seconds to wait for discovery broadcast
        target_mac: Optional MAC address to filter specific robot
    
    Returns:
        Robot IP address string, or None if not found
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.settimeout(timeout)
    
    # Bind to multicast port
    sock.bind(('', MCAST_PORT))
    
    # Join multicast group
    mreq = struct.pack("4sl", socket.inet_aton(MCAST_GRP), socket.INADDR_ANY)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
    
    logger.info(f"Listening for robot discovery on {MCAST_GRP}:{MCAST_PORT} (timeout: {timeout}s)...")
    
    start_time = time.time()
    try:
        while time.time() - start_time < timeout:
            try:
                data, addr = sock.recvfrom(1024)
                robot_info = json.loads(data.decode('utf-8'))
                
                robot_ip = robot_info.get('ip')
                robot_name = robot_info.get('name', 'Unknown')
                robot_sn = robot_info.get('sn', 'Unknown')
                
                logger.info(f"Found robot: {robot_name} (SN: {robot_sn}, IP: {robot_ip})")
                
                # If target MAC not specified, return first robot found
                if target_mac is None:
                    sock.close()
                    return robot_ip
                
                # Otherwise filter by MAC (if available in broadcast)
                # Note: Current G1 broadcasts don't include MAC, so we return first match
                sock.close()
                return robot_ip
                
            except socket.timeout:
                continue
            except json.JSONDecodeError:
                logger.warning(f"Invalid JSON from {addr}")
                continue
        
        logger.warning(f"No robot found after {timeout}s")
        return None
        
    except Exception as e:
        logger.error(f"Discovery error: {e}")
        return None
    finally:
        sock.close()


def discover_or_fallback(fallback_ip='192.168.86.8', timeout=5):
    """
    Try to discover robot IP, fall back to known IP if discovery fails.
    
    Args:
        fallback_ip: IP to use if discovery fails
        timeout: Discovery timeout in seconds
    
    Returns:
        Robot IP address string
    """
    logger.info("Attempting robot discovery...")
    robot_ip = discover_robot_ip(timeout=timeout)
    
    if robot_ip:
        logger.info(f"✅ Robot discovered at {robot_ip}")
        return robot_ip
    else:
        logger.warning(f"⚠️  Discovery failed, using fallback IP: {fallback_ip}")
        return fallback_ip


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    
    print("=" * 60)
    print("Unitree Robot Discovery")
    print("=" * 60)
    
    ip = discover_robot_ip(timeout=15)
    
    if ip:
        print(f"\n✅ Robot IP: {ip}")
    else:
        print(f"\n❌ No robot found")
    
    print("=" * 60)
