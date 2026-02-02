#!/usr/bin/env python3
"""
Simple ARP-based robot discovery helper
Uses MAC address fc:23:cd:92:60:02 to find G1_6937
"""
import subprocess
import platform
import re
import logging

logger = logging.getLogger(__name__)

G1_MAC = "fc:23:cd:92:60:02"

def discover_robot_ip(target_mac: str = G1_MAC, timeout: int = 10) -> str:
    """
    Discover robot IP by scanning ARP table for known MAC address.
    
    Args:
        target_mac: MAC address to search for (default: G1_6937)
        timeout: How long to retry (not used, kept for compatibility)
    
    Returns:
        IP address string or raises RuntimeError if not found
    """
    target_mac = target_mac.lower().replace("-", ":").replace(".", ":")
    
    logger.info(f"Scanning ARP table for MAC {target_mac}...")
    
    # First, trigger ARP cache population with broadcast ping
    system = platform.system().lower()
    try:
        if system == "windows":
            subprocess.run(['ping', '-n', '2', '192.168.86.255'], 
                         capture_output=True, timeout=3)
        else:
            subprocess.run(['ping', '-c', '2', '-b', '192.168.86.255'], 
                         capture_output=True, timeout=3)
    except:
        pass  # Ignore errors, this is just to populate cache
    
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
                        logger.info(f"✅ Found robot at {ip} (MAC: {mac})")
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
                        logger.info(f"✅ Found robot at {ip} (MAC: {mac})")
                        return ip
    
    except Exception as e:
        logger.error(f"ARP scan failed: {e}")
    
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
    
    raise RuntimeError(f"Robot with MAC {target_mac} not found in ARP table or network scan. "
                      "Ensure robot is powered on and connected to network.")


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
