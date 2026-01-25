#!/usr/bin/env python3
"""
DDS-based robot discovery - listens to DDS topics to find robots
This is how the Android app likely discovers robots (via DDS participant discovery)
"""
import asyncio
import subprocess
import re
import json
from typing import Dict, Optional, Set
from datetime import datetime
from dataclasses import dataclass, asdict

@dataclass
class DiscoveredRobot:
    """Robot discovered via DDS"""
    name: str
    serial_number: Optional[str] = None
    ip: Optional[str] = None
    last_seen: Optional[datetime] = None
    dds_participant_guid: Optional[str] = None
    
    def to_dict(self):
        return {
            'name': self.name,
            'serial_number': self.serial_number or '',
            'ip': self.ip,
            'last_seen': self.last_seen.isoformat() if self.last_seen else None,
            'dds_participant_guid': self.dds_participant_guid
        }

class DDSDiscovery:
    """Discover robots via DDS participant discovery"""
    
    def __init__(self):
        self._robots: Dict[str, DiscoveredRobot] = {}
        self._running = False
        self._discovery_task = None
        
    async def start(self):
        """Start DDS discovery"""
        if self._running:
            return
            
        self._running = True
        self._discovery_task = asyncio.create_task(self._discovery_loop())
        print("DDS Discovery: Started listening for robots...")
    
    async def stop(self):
        """Stop DDS discovery"""
        self._running = False
        if self._discovery_task:
            self._discovery_task.cancel()
            try:
                await self._discovery_task
            except asyncio.CancelledError:
                pass
    
    async def _discovery_loop(self):
        """Main discovery loop - uses ddsls to find DDS participants"""
        while self._running:
            try:
                # Use ddsls to discover DDS participants
                # This shows all DDS participants on the network
                proc = await asyncio.create_subprocess_exec(
                    'timeout', '2', 'ddsls', '-a',
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    env={'CYCLONEDDS_URI': 'file:///root/G1/unitree_sdk2/cyclonedds.xml'}
                )
                
                stdout, stderr = await proc.communicate()
                
                if stdout:
                    await self._parse_ddsls_output(stdout.decode())
                    
            except FileNotFoundError:
                # ddsls not found, try alternative method
                await self._discover_via_topic_listening()
                
            except Exception as e:
                print(f"DDS Discovery error: {e}")
            
            await asyncio.sleep(5)  # Check every 5 seconds
    
    async def _parse_ddsls_output(self, output: str):
        """Parse ddsls output to find robot participants"""
        # Look for patterns like:
        # Participant (1.f.1.2.3.4.5.6.7.8.9.a.b.c.d.e|0.0.0.0)
        #   Topic: rt/lowstate
        
        lines = output.split('\n')
        current_participant = None
        current_ip = None
        has_robot_topics = False
        
        for line in lines:
            # Extract participant GUID and IP
            if 'Participant' in line:
                match = re.search(r'Participant.*?\|([0-9.]+)', line)
                if match:
                    current_ip = match.group(1)
                    current_participant = line
                    has_robot_topics = False
            
            # Check for robot-specific topics
            elif 'rt/lowstate' in line or 'rt/lowcmd' in line:
                if current_ip and current_ip != '0.0.0.0':
                    has_robot_topics = True
                    # Extract robot name from participant info or hostname
                    robot_name = await self._get_robot_name(current_ip)
                    if robot_name:
                        robot = DiscoveredRobot(
                            name=robot_name,
                            ip=current_ip,
                            last_seen=datetime.now(),
                            dds_participant_guid=current_participant
                        )
                        self._robots[robot_name] = robot
                        print(f"DDS Discovery: Found robot {robot_name} at {current_ip}")
    
    async def _get_robot_name(self, ip: str) -> Optional[str]:
        """Try to get robot name from hostname or reverse DNS"""
        try:
            # Try reverse DNS lookup
            proc = await asyncio.create_subprocess_exec(
                'nslookup', ip,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, _ = await proc.communicate()
            
            if stdout:
                output = stdout.decode()
                # Look for name like "name = G1_6937.local" or similar
                match = re.search(r'name\s*=\s*([^.\s]+)', output)
                if match:
                    return match.group(1)
                    
        except:
            pass
        
        # Fallback: create name from IP
        return f"Robot_{ip.replace('.', '_')}"
    
    async def _discover_via_topic_listening(self):
        """Alternative: Listen to rt/lowstate and extract sender info"""
        # This would require C++ integration with test_robot_listener
        # For now, fall back to periodic ping sweep
        pass
    
    def get_robots(self) -> Dict[str, DiscoveredRobot]:
        """Get all discovered robots"""
        return self._robots.copy()
    
    def get_robot(self, name: str) -> Optional[DiscoveredRobot]:
        """Get specific robot by name"""
        return self._robots.get(name)


# Global singleton
_discovery_instance = None

def get_discovery() -> DDSDiscovery:
    """Get global discovery instance"""
    global _discovery_instance
    if _discovery_instance is None:
        _discovery_instance = DDSDiscovery()
    return _discovery_instance
