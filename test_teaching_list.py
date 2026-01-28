#!/usr/bin/env python3
"""
Test teaching mode protocol - Get action list using port 49504
Based on TEACHING_MODE_PROTOCOL_COMPLETE.md reverse engineering
"""

import socket
import struct
import zlib
import time
import logging

logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)


class UnitreeTeachingProtocol:
    """Unitree teaching mode protocol (port 49504)"""
    
    # Packet structure constants
    HEADER_TYPE = 0x17
    MAGIC = bytes([0xFE, 0xFD, 0x00])
    FLAGS = bytes([0x01, 0x00])
    RESERVED1 = bytes([0x00, 0x00])
    RESERVED2 = bytes([0x00, 0x01])
    
    # Command IDs
    CMD_CONTROL_MODE = 0x09
    CMD_PARAM_SYNC = 0x0A
    CMD_STATUS_SUB = 0x0B
    CMD_READY = 0x0C
    CMD_LIST_ACTIONS = 0x1A
    CMD_ENTER_DAMP = 0x0D
    CMD_EXIT_DAMP = 0x0E
    
    def __init__(self, robot_ip, robot_port=49504):
        self.robot_ip = robot_ip
        self.robot_port = robot_port
        self.sequence = 0
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.settimeout(2.0)
    
    def _build_packet(self, cmd_id, payload_data=None):
        """Build complete packet with proper structure"""
        # Use 44-byte standard payload if none provided
        if payload_data is None:
            payload_data = bytes(44)
        
        packet = bytearray()
        
        # Header (13 bytes)
        packet.append(self.HEADER_TYPE)        # 0x17
        packet.extend(self.MAGIC)               # 0xFE 0xFD 0x00
        packet.extend(self.FLAGS)               # 0x01 0x00
        packet.extend(struct.pack('>H', self.sequence))  # Big-endian sequence (offset 2-3)
        packet.extend(self.RESERVED1)           # 0x00 0x00
        packet.extend(self.RESERVED2)           # 0x00 0x01
        packet.append(cmd_id)                   # Command ID
        packet.extend(struct.pack('>H', len(payload_data)))  # Payload length
        
        # Payload
        packet.extend(payload_data)
        
        # CRC32 checksum (big-endian, last 4 bytes)
        crc = zlib.crc32(packet) & 0xFFFFFFFF
        packet.extend(struct.pack('>I', crc))
        
        self.sequence += 1
        
        return bytes(packet)
    
    def _send_command(self, cmd_id, payload_data=None, expect_response=True):
        """Send command and optionally wait for response"""
        packet = self._build_packet(cmd_id, payload_data)
        
        logger.info(f"→ Sending command 0x{cmd_id:02X} ({len(packet)} bytes)")
        logger.debug(f"  Packet: {packet.hex()}")
        
        self.socket.sendto(packet, (self.robot_ip, self.robot_port))
        
        if expect_response:
            try:
                response, addr = self.socket.recvfrom(1024)
                logger.info(f"← Received response from {addr}: {len(response)} bytes")
                logger.debug(f"  Data: {response.hex()}")
                return response
            except socket.timeout:
                logger.warning(f"✗ No response (timeout after 2s)")
                return None
        
        return None
    
    def initialize(self):
        """Send initialization sequence (0x09-0x0C)"""
        logger.info("=" * 60)
        logger.info("INITIALIZATION SEQUENCE (0x09-0x0C)")
        logger.info("=" * 60)
        
        payload = bytes(44)
        
        # 0x09 - Control mode set
        self._send_command(self.CMD_CONTROL_MODE, payload, expect_response=True)
        time.sleep(0.5)
        
        # 0x0A - Parameter sync
        self._send_command(self.CMD_PARAM_SYNC, payload, expect_response=True)
        time.sleep(0.5)
        
        # 0x0B - Status subscription
        self._send_command(self.CMD_STATUS_SUB, payload, expect_response=True)
        time.sleep(0.5)
        
        # 0x0C - Ready signal
        self._send_command(self.CMD_READY, payload, expect_response=True)
        time.sleep(0.5)
    
    def list_actions(self):
        """Query robot for list of teaching actions (0x1A)"""
        logger.info("=" * 60)
        logger.info("QUERY TEACHING ACTIONS (0x1A)")
        logger.info("=" * 60)
        
        payload = bytes(44)  # Standard 44-byte payload
        response = self._send_command(self.CMD_LIST_ACTIONS, payload, expect_response=True)
        
        if response:
            logger.info("✓ Received action list response")
            self._parse_action_list(response)
            return response
        else:
            logger.error("✗ Failed to get action list")
            return None
    
    def _parse_action_list(self, response):
        """Parse action list from response"""
        if len(response) < 17:
            logger.error(f"Response too short: {len(response)} bytes")
            return
        
        # Skip header (13 bytes), parse payload
        header = response[:13]
        payload = response[13:-4]  # Exclude last 4 CRC bytes
        crc_bytes = response[-4:]
        
        logger.info(f"\nResponse structure:")
        logger.info(f"  Header: {header.hex()}")
        logger.info(f"  Payload ({len(payload)} bytes): {payload.hex()}")
        logger.info(f"  CRC32: {crc_bytes.hex()}")
        
        # Try to parse action count (first 4 bytes of payload)
        if len(payload) >= 4:
            action_count = struct.unpack('>I', payload[0:4])[0]
            logger.info(f"\nActions available: {action_count}")
            
            # Try to extract action names
            offset = 4
            for i in range(min(action_count, 15)):  # Max 15 actions
                if offset + 32 <= len(payload):
                    action_name_bytes = payload[offset:offset+32]
                    # Find null terminator
                    null_pos = action_name_bytes.find(b'\x00')
                    if null_pos > 0:
                        action_name = action_name_bytes[:null_pos].decode('utf-8', errors='ignore')
                        logger.info(f"  [{i}] {action_name}")
                    else:
                        logger.info(f"  [{i}] (encrypted/binary data)")
                    offset += 32
    
    def close(self):
        """Close socket"""
        self.socket.close()


def discover_robot_ip():
    """Discover robot IP by MAC address or return default"""
    import subprocess
    
    # Try to find robot by MAC address (fc:23:cd:92:60:02 from PCAP)
    try:
        result = subprocess.run(
            ["arp", "-n"],
            capture_output=True,
            text=True,
            timeout=5
        )
        for line in result.stdout.split('\n'):
            if 'fc:23:cd' in line.lower():
                parts = line.split()
                if parts:
                    logger.info(f"✓ Found robot via ARP: {parts[0]}")
                    return parts[0]
    except Exception as e:
        logger.warning(f"ARP discovery failed: {e}")
    
    # Try default IPs
    defaults = ["192.168.137.164", "192.168.86.2", "192.168.86.3"]
    for ip in defaults:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(0.5)
            sock.sendto(b'\x00', (ip, 49504))
            logger.info(f"✓ Robot found at: {ip}")
            sock.close()
            return ip
        except:
            pass
    
    return None


if __name__ == "__main__":
    logger.info("\n" + "=" * 60)
    logger.info("UNITREE TEACHING MODE PROTOCOL TEST")
    logger.info("=" * 60 + "\n")
    
    # Discover robot
    robot_ip = discover_robot_ip()
    
    if not robot_ip:
        logger.error("✗ Could not find robot on network")
        logger.info("\nTrying with default IP: 192.168.137.164")
        robot_ip = "192.168.137.164"
    
    logger.info(f"Robot IP: {robot_ip}")
    logger.info(f"Port: 49504\n")
    
    # Create protocol handler
    protocol = UnitreeTeachingProtocol(robot_ip)
    
    try:
        # Step 1: Initialize
        protocol.initialize()
        time.sleep(1)
        
        # Step 2: List actions
        protocol.list_actions()
        
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
    finally:
        protocol.close()
        logger.info("\n✓ Done")
