"""
Centralized Robot Discovery - Single Source of Truth

This module provides the ONLY recommended way to discover Unitree robots.
All local scripts and utilities should use this module.

Architecture:
- Multicast discovery (231.1.1.2:7400) - fastest when robot broadcasts
- ARP scan with ping verification - reliable fallback
- Network mode detection (AP/STA-L/STA-T)

Usage:
    from g1_app.utils.robot_discovery import discover_robot
    
    robot = discover_robot()
    if robot:
        print(f"Robot: {robot['ip']} - {robot['mode']} - {'ONLINE' if robot['online'] else 'OFFLINE'}")
"""
import subprocess
import logging
from typing import Optional, Dict
from .arp_discovery import (
    try_multicast_discovery,
    detect_network_mode,
    discover_robot_ip as arp_discover_robot_ip,
    G1_MAC,
    G1_AP_IP
)

logger = logging.getLogger(__name__)


def _mac_for_ip(ip: str) -> Optional[str]:
    """Resolve MAC for a specific IP via ip neigh/arp."""
    try:
        result = subprocess.run(['ip', 'neigh', 'show', ip], capture_output=True, text=True, timeout=1)
        for line in result.stdout.split('\n'):
            if ip in line and 'lladdr' in line:
                parts = line.split()
                if 'lladdr' in parts:
                    return parts[parts.index('lladdr') + 1].lower()
    except Exception:
        pass

    try:
        result = subprocess.run(['arp', '-n', ip], capture_output=True, text=True, timeout=1)
        for line in result.stdout.split('\n'):
            if ip in line:
                parts = line.split()
                if len(parts) >= 3:
                    return parts[2].lower()
    except Exception:
        pass

    return None


def discover_robot(target_mac: str = G1_MAC, verify_with_ping: bool = True) -> Optional[Dict[str, any]]:
    """
    Discover robot using the same method as the web server.
    
    This is the RECOMMENDED way to discover robots in all scripts.
    Uses the proven multicast + ARP + ping verification approach.
    
    Args:
        target_mac: MAC address to find (default: G1_6937)
        verify_with_ping: If True, verify robot responds to ping (recommended)
    
    Returns:
        Dict with keys: ip, mac, mode, online
        None if robot not found
    
    Example:
        robot = discover_robot()
        if robot and robot['online']:
            print(f"Robot at {robot['ip']}")
        else:
            print("Robot offline or not found")
    """
    target_mac = target_mac.lower().replace("-", ":").replace(".", ":")
    
    # STEP 1: Try multicast discovery (fastest)
    logger.debug("Trying multicast discovery...")
    multicast_ip = try_multicast_discovery(timeout=0.5)
    
    if multicast_ip:
        resolved_mac = _mac_for_ip(multicast_ip)
        if resolved_mac and resolved_mac != target_mac:
            logger.debug(f"Multicast IP {multicast_ip} maps to {resolved_mac}, not target {target_mac}; continuing scan")
            multicast_ip = None

    if multicast_ip:
        # Verify MAC via ARP
        try:
            result = subprocess.run(['arp', '-n', multicast_ip],
                                   capture_output=True, text=True, timeout=1)
            for line in result.stdout.split('\n'):
                if multicast_ip in line:
                    parts = line.split()
                    if len(parts) >= 3 and parts[2].lower() == target_mac:
                        mode = detect_network_mode(multicast_ip)
                        logger.info(f"✓ Robot found via multicast: {multicast_ip} ({mode})")
                        return {
                            'ip': multicast_ip,
                            'mac': target_mac,
                            'mode': mode,
                            'online': True
                        }
        except Exception as e:
            logger.debug(f"Multicast MAC verification failed: {e}")
    
    # STEP 2: Full ARP/broadcast fallback (fast path)
    logger.debug("Trying ARP/broadcast scan...")
    try:
        ip = arp_discover_robot_ip(target_mac=target_mac, timeout=3, fast=True)
        if ip:
            online = True
            if verify_with_ping:
                try:
                    ping_result = subprocess.run(
                        ['ping', '-c', '1', '-W', '1', ip],
                        capture_output=True,
                        timeout=2
                    )
                    online = ping_result.returncode == 0
                except Exception:
                    online = False

            mode = detect_network_mode(ip)
            logger.info(f"✓ Robot found via scan: {ip} ({mode})")
            return {
                'ip': ip,
                'mac': target_mac,
                'mode': mode,
                'online': online
            }
    except Exception as e:
        logger.error(f"ARP/broadcast scan failed: {e}")

    # STEP 3: Full network scan fallback (slower)
    logger.debug("Trying full network scan...")
    try:
        ip = arp_discover_robot_ip(target_mac=target_mac, timeout=8, fast=False)
        if ip:
            online = True
            if verify_with_ping:
                try:
                    ping_result = subprocess.run(
                        ['ping', '-c', '1', '-W', '1', ip],
                        capture_output=True,
                        timeout=2
                    )
                    online = ping_result.returncode == 0
                except Exception:
                    online = False

            mode = detect_network_mode(ip)
            logger.info(f"✓ Robot found via full scan: {ip} ({mode})")
            return {
                'ip': ip,
                'mac': target_mac,
                'mode': mode,
                'online': online
            }
    except Exception as e:
        logger.error(f"Full scan failed: {e}")
    
    logger.warning(f"Robot not found (MAC: {target_mac})")
    return None


def wait_for_robot(target_mac: str = G1_MAC, timeout: int = 30, check_interval: int = 2) -> Optional[Dict[str, any]]:
    """
    Wait for robot to come online (useful for scripts that need to wait for boot).
    
    Args:
        target_mac: MAC address to find
        timeout: Maximum seconds to wait
        check_interval: Seconds between discovery attempts
    
    Returns:
        Robot info dict or None if timeout
    
    Example:
        print("Waiting for robot to boot...")
        robot = wait_for_robot(timeout=60)
        if robot:
            print(f"Robot online at {robot['ip']}")
    """
    import time
    elapsed = 0
    
    while elapsed < timeout:
        robot = discover_robot(target_mac, verify_with_ping=True)
        if robot and robot['online']:
            return robot
        
        time.sleep(check_interval)
        elapsed += check_interval
    
    return None


# Backward compatibility: provide simple IP discovery
def discover_robot_ip(target_mac: str = G1_MAC, timeout: int = 10, fast: bool = True) -> str:
    """
    DEPRECATED: Use discover_robot() instead for better info.
    
    Legacy function for backward compatibility.
    Returns IP string or raises RuntimeError.
    """
    robot = discover_robot(target_mac, verify_with_ping=fast)
    if robot and robot['ip']:
        return robot['ip']
    raise RuntimeError(f"Robot not found (MAC: {target_mac})")
