#!/usr/bin/env python3
"""
Discover Unitree G1 robot on network after reboot.
Scans for MAC address fc:23:cd:92:60:02 (G1_6937)
"""

import subprocess
import re
import sys

ROBOT_MAC = "fc:23:cd:92:60:02"
ROBOT_NAME = "G1_6937"

def scan_arp_cache():
    """Check ARP cache for robot MAC"""
    print("🔍 Checking ARP cache...")
    try:
        result = subprocess.run(['arp', '-n'], capture_output=True, text=True)
        for line in result.stdout.split('\n'):
            if ROBOT_MAC.lower() in line.lower():
                # Extract IP address (first field)
                match = re.search(r'(\d+\.\d+\.\d+\.\d+)', line)
                if match:
                    ip = match.group(1)
                    print(f"✅ Found in ARP cache: {ip} ({ROBOT_MAC})")
                    return ip
    except Exception as e:
        print(f"⚠️  ARP cache check failed: {e}")
    return None

def scan_network(interface='eth1', subnet='192.168.86.0/24'):
    """Scan network for robot MAC using arp-scan"""
    print(f"🔍 Scanning network {subnet} on {interface}...")
    print(f"   Looking for MAC: {ROBOT_MAC}")
    
    try:
        # Try arp-scan first (requires sudo)
        result = subprocess.run(
            ['sudo', 'arp-scan', '-I', interface, '--localnet'],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        for line in result.stdout.split('\n'):
            if ROBOT_MAC.lower() in line.lower():
                match = re.search(r'(\d+\.\d+\.\d+\.\d+)', line)
                if match:
                    ip = match.group(1)
                    print(f"✅ FOUND: {ip} - {ROBOT_MAC}")
                    return ip
        
        print("❌ Robot not found with arp-scan")
        
    except FileNotFoundError:
        print("⚠️  arp-scan not installed, trying nmap...")
        
        # Fallback to nmap
        try:
            result = subprocess.run(
                ['nmap', '-sn', subnet],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            # Parse nmap output for MAC
            current_ip = None
            for line in result.stdout.split('\n'):
                ip_match = re.search(r'Nmap scan report for (\d+\.\d+\.\d+\.\d+)', line)
                if ip_match:
                    current_ip = ip_match.group(1)
                
                if current_ip and ROBOT_MAC.upper() in line.upper():
                    print(f"✅ FOUND: {current_ip} - {ROBOT_MAC}")
                    return current_ip
            
            print("❌ Robot not found with nmap")
            
        except Exception as e:
            print(f"⚠️  nmap scan failed: {e}")
    
    except Exception as e:
        print(f"⚠️  Network scan failed: {e}")
    
    return None

def ping_test(ip):
    """Test if robot is reachable"""
    print(f"🏓 Testing connectivity to {ip}...")
    try:
        result = subprocess.run(
            ['ping', '-c', '3', ip],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            print(f"✅ Robot is reachable at {ip}")
            return True
        else:
            print(f"❌ Robot not responding at {ip}")
            return False
    except Exception as e:
        print(f"⚠️  Ping failed: {e}")
        return False

def main():
    print("="*70)
    print(f"🤖 Unitree {ROBOT_NAME} Discovery")
    print(f"   MAC Address: {ROBOT_MAC}")
    print("="*70)
    
    # Method 1: Check ARP cache (fastest)
    ip = scan_arp_cache()
    
    # Method 2: Scan network
    if not ip:
        print("\n⚠️  Not in ARP cache, scanning network...")
        ip = scan_network()
    
    if ip:
        print("\n" + "="*70)
        print(f"🎯 ROBOT DISCOVERED!")
        print(f"   Name: {ROBOT_NAME}")
        print(f"   IP:   {ip}")
        print(f"   MAC:  {ROBOT_MAC}")
        print("="*70)
        
        # Test connectivity
        ping_test(ip)
        
        print(f"\n💡 Update robot IP in your code:")
        print(f'   ROBOT_IP = "{ip}"')
        
        return ip
    else:
        print("\n" + "="*70)
        print("❌ ROBOT NOT FOUND")
        print("="*70)
        print("Troubleshooting:")
        print("1. Ensure robot is powered on and WiFi connected")
        print("2. Check your computer is on the same network")
        print("3. Try pinging the old IP: ping 192.168.86.18")
        print("4. Check router DHCP leases for 'unitree' or 'g1'")
        return None

if __name__ == "__main__":
    discovered_ip = main()
    sys.exit(0 if discovered_ip else 1)
