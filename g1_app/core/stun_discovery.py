#!/usr/bin/env python3
"""
STUN/WebRTC port discovery for Unitree teaching protocol
Based on PCAP analysis showing STUN negotiation before teaching protocol
"""

import socket
import struct
import secrets
import time
import logging
from typing import Optional, Tuple

logger = logging.getLogger(__name__)


class STUNClient:
    """
    STUN client for discovering teaching protocol port via WebRTC negotiation
    
    STUN message format (RFC 5389):
    0                   1                   2                   3
    0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
    +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
    |0 0|     STUN Message Type     |         Message Length        |
    +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
    |                         Magic Cookie                          |
    +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
    |                                                               |
    |                     Transaction ID (96 bits)                  |
    |                                                               |
    +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
    """
    
    MAGIC_COOKIE = 0x2112A442
    BINDING_REQUEST = 0x0001
    BINDING_RESPONSE = 0x0101
    
    # STUN attributes
    ATTR_MAPPED_ADDRESS = 0x0001
    ATTR_XOR_MAPPED_ADDRESS = 0x0020
    ATTR_USERNAME = 0x0006
    ATTR_MESSAGE_INTEGRITY = 0x0008
    ATTR_FINGERPRINT = 0x8028
    ATTR_SOFTWARE = 0x8022
    
    def __init__(self, robot_ip: str, timeout: float = 5.0):
        self.robot_ip = robot_ip
        self.timeout = timeout
        
    def create_binding_request(self, transaction_id: Optional[bytes] = None) -> bytes:
        """Create STUN Binding Request packet"""
        if transaction_id is None:
            transaction_id = secrets.token_bytes(12)
        
        # Build basic STUN header (no attributes for simple binding request)
        msg_type = self.BINDING_REQUEST
        msg_length = 0  # No attributes initially
        
        header = struct.pack('!HHI',
            msg_type,
            msg_length,
            self.MAGIC_COOKIE
        ) + transaction_id
        
        return header, transaction_id
    
    def create_binding_request_with_attrs(self, transaction_id: Optional[bytes] = None) -> bytes:
        """
        Create STUN Binding Request with attributes matching Android app
        From PCAP: includes USERNAME, FINGERPRINT, SOFTWARE attributes
        """
        if transaction_id is None:
            transaction_id = secrets.token_bytes(12)
        
        attributes = b''
        
        # Add USERNAME attribute (from PCAP: "n7Px:iq2R")
        username = b"n7Px:iq2R"
        username_len = len(username)
        # Pad to 4-byte boundary
        padding = (4 - (username_len % 4)) % 4
        attr_username = struct.pack('!HH', self.ATTR_USERNAME, username_len)
        attr_username += username + b'\x00' * padding
        attributes += attr_username
        
        # Add SOFTWARE attribute ("Unitree Explore")
        software = b"Unitree Explore"
        software_len = len(software)
        padding = (4 - (software_len % 4)) % 4
        attr_software = struct.pack('!HH', self.ATTR_SOFTWARE, software_len)
        attr_software += software + b'\x00' * padding
        attributes += attr_software
        
        # Build header
        msg_type = self.BINDING_REQUEST
        msg_length = len(attributes)
        
        header = struct.pack('!HHI',
            msg_type,
            msg_length,
            self.MAGIC_COOKIE
        ) + transaction_id
        
        packet = header + attributes
        
        return packet, transaction_id
    
    def parse_stun_response(self, data: bytes) -> Optional[Tuple[str, int]]:
        """
        Parse STUN Binding Response to extract mapped address/port
        Returns (ip, port) if successful, None otherwise
        """
        if len(data) < 20:
            return None
        
        # Parse header
        msg_type, msg_length, magic_cookie = struct.unpack('!HHI', data[0:8])
        transaction_id = data[8:20]
        
        if magic_cookie != self.MAGIC_COOKIE:
            logger.warning(f"Invalid STUN magic cookie: {magic_cookie:08x}")
            return None
        
        if msg_type != self.BINDING_RESPONSE:
            logger.warning(f"Not a binding response: {msg_type:04x}")
            return None
        
        # Parse attributes
        offset = 20
        while offset < len(data):
            if offset + 4 > len(data):
                break
            
            attr_type, attr_length = struct.unpack('!HH', data[offset:offset+4])
            offset += 4
            
            if offset + attr_length > len(data):
                break
            
            attr_data = data[offset:offset+attr_length]
            
            # XOR-MAPPED-ADDRESS (RFC 5389)
            if attr_type == self.ATTR_XOR_MAPPED_ADDRESS:
                if len(attr_data) >= 8:
                    family = struct.unpack('!H', attr_data[0:2])[0]
                    x_port = struct.unpack('!H', attr_data[2:4])[0]
                    x_addr = struct.unpack('!I', attr_data[4:8])[0]
                    
                    # XOR with magic cookie
                    port = x_port ^ (self.MAGIC_COOKIE >> 16)
                    addr = x_addr ^ self.MAGIC_COOKIE
                    
                    ip = socket.inet_ntoa(struct.pack('!I', addr))
                    logger.info(f"XOR-MAPPED-ADDRESS: {ip}:{port}")
                    return (ip, port)
            
            # MAPPED-ADDRESS (legacy)
            elif attr_type == self.ATTR_MAPPED_ADDRESS:
                if len(attr_data) >= 8:
                    family = struct.unpack('!H', attr_data[0:2])[0]
                    port = struct.unpack('!H', attr_data[2:4])[0]
                    addr = struct.unpack('!I', attr_data[4:8])[0]
                    
                    ip = socket.inet_ntoa(struct.pack('!I', addr))
                    logger.info(f"MAPPED-ADDRESS: {ip}:{port}")
                    return (ip, port)
            
            # Move to next attribute (pad to 4-byte boundary)
            offset += attr_length
            padding = (4 - (attr_length % 4)) % 4
            offset += padding
        
        return None
    
    def discover_teaching_port(self, known_ports: list = None) -> Optional[int]:
        """
        Discover teaching protocol port via STUN negotiation
        
        Strategy:
        1. Send STUN Binding Request to robot:51639 (WebRTC/ICE port)
        2. Parse XOR-MAPPED-ADDRESS from response to get teaching service port
        3. Fallback to hardcoded port 57006 if STUN fails (observed from PCAP)
        
        Args:
            known_ports: List of ports to try if STUN fails (default: [57006, 49504, 43893])
        
        Returns:
            Teaching service port number if discovered, None otherwise
        """
        if known_ports is None:
            # Port 57006 is the teaching service port discovered via STUN in PCAP analysis
            # Other ports are legacy/alternative ports from previous observations
            known_ports = [57006, 49504, 43893]
        
        logger.info(f"🔍 Discovering teaching protocol port for {self.robot_ip}")
        
        # Try STUN discovery first (proper method)
        port = self._stun_discovery()
        if port:
            logger.info(f"✅ STUN discovery found teaching port: {port}")
            return port
        
        # Fallback: try known ports (hardcoded from PCAP analysis)
        logger.warning("⚠️ STUN discovery failed, trying known ports...")
        port = self._scan_known_ports(known_ports)
        if port:
            logger.info(f"✅ Port scan found teaching port: {port}")
            return port
        
        logger.error("❌ Failed to discover teaching protocol port")
        return None
    
    def _stun_discovery(self) -> Optional[int]:
        """
        Attempt STUN discovery via WebRTC ICE port (51639)
        
        Discovery sequence (from PCAP analysis):
        1. Send STUN Binding Request to robot:51639 (WebRTC/ICE port)
        2. Robot responds with XOR-MAPPED-ADDRESS containing teaching service port
        3. Extract port from response (e.g., 57006)
        
        Returns teaching service port number if successful
        """
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(self.timeout)
        
        try:
            # CRITICAL: STUN request goes to WebRTC ICE port (51639)
            # This is where the robot's STUN server listens
            stun_port = 51639
            
            logger.info(f"🔍 Sending STUN request to {self.robot_ip}:{stun_port}")
            
            # Send binding request with attributes (like Android app)
            packet, transaction_id = self.create_binding_request_with_attrs()
            sock.sendto(packet, (self.robot_ip, stun_port))
            
            # Wait for response (may take a moment)
            try:
                data, addr = sock.recvfrom(2048)
                logger.info(f"📥 Received STUN response from {addr} ({len(data)} bytes)")
                
                # Parse response to extract teaching service port
                result = self.parse_stun_response(data)
                if result:
                    ip, teaching_port = result
                    logger.info(f"✅ STUN discovery: teaching service at {ip}:{teaching_port}")
                    
                    # The port from STUN response IS the teaching service port
                    # No need to verify - STUN told us where it is
                    return teaching_port
                else:
                    logger.warning("⚠️ STUN response received but could not parse XOR-MAPPED-ADDRESS")
            
            except socket.timeout:
                logger.warning(f"⏱️ STUN timeout waiting for response from {self.robot_ip}:{stun_port}")
        
        except Exception as e:
            logger.error(f"❌ STUN discovery error: {e}")
        
        finally:
            sock.close()
        
        return None
    
    def _scan_known_ports(self, ports: list) -> Optional[int]:
        """
        Scan known ports to find teaching protocol
        Returns port number if found
        """
        for port in ports:
            try:
                logger.debug(f"Testing port {port}...")
                if self._verify_teaching_port(port):
                    return port
            except Exception as e:
                logger.debug(f"Port {port} failed: {e}")
                continue
        
        return None
    
    def _verify_teaching_port(self, port: int) -> bool:
        """
        Verify if a port responds to teaching protocol
        Send init sequence and check for valid response
        """
        try:
            # Quick connection test with short timeout
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(1.0)
            
            # Send a simple teaching protocol packet to test
            # Use command 0x09 (init sequence start) from udp_protocol
            test_packet = b'\x17\xfe\xfd\x00\x01\x00\x00\x00\x00\x1d\x09\x00\x2c'
            test_packet += b'\x00' * (57 - len(test_packet))  # Pad to 57 bytes
            
            sock.sendto(test_packet, (self.robot_ip, port))
            
            # If we get ANY response, this port is likely correct
            data, addr = sock.recvfrom(2048)
            sock.close()
            
            if len(data) > 20 and data[0:4] == b'\x17\xfe\xfd\x00':
                logger.info(f"Port {port} responds to teaching protocol!")
                return True
            
        except socket.timeout:
            pass
        except Exception as e:
            logger.debug(f"Port verification error: {e}")
        
        return False


def discover_teaching_port(robot_ip: str, timeout: float = 5.0) -> Optional[int]:
    """
    Convenience function to discover teaching protocol port
    
    Args:
        robot_ip: Robot IP address
        timeout: Discovery timeout in seconds
    
    Returns:
        Port number if discovered, None otherwise
    """
    client = STUNClient(robot_ip, timeout)
    return client.discover_teaching_port()


if __name__ == '__main__':
    # Test discovery
    logging.basicConfig(level=logging.DEBUG)
    
    import sys
    if len(sys.argv) > 1:
        robot_ip = sys.argv[1]
    else:
        robot_ip = "192.168.86.3"
    
    print(f"Discovering teaching protocol port for {robot_ip}...")
    port = discover_teaching_port(robot_ip)
    
    if port:
        print(f"✅ Found teaching protocol port: {port}")
    else:
        print(f"❌ Failed to discover port")
