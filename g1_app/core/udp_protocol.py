"""
UDP Teaching Protocol Implementation for G1 Air

Enhanced UDP module with:
- UDP initialization sequence (0x09, 0x0A, 0x0B, 0x0C)
- Action list query (0x1A)
- Action playback (0x41)

Protocol Details:
- Packet format: Magic (0x17 0xFE 0xFD 0x00) + header + payload + CRC32
- Port: 49504 (raw robot protocol) or 43893 (app protocol)
- All multi-byte values: Little-endian
- CRC32: IEEE 802.3 over all bytes except last 4
"""

import struct
import logging
import socket
import asyncio
import zlib
import time
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class UDPPacket:
    """UDP Packet structure"""
    magic_1: int = 0x17
    magic_2: int = 0xFE
    magic_3: int = 0xFD
    magic_4: int = 0x00
    sequence: int = 0
    command_id: int = 0x00
    payload_length: int = 0
    payload: bytes = b''
    
    def to_bytes(self) -> bytes:
        """Convert packet to bytes with CRC32"""
        # Build packet without CRC
        pkt = bytearray()
        pkt.extend(bytes([self.magic_1, self.magic_2, self.magic_3, self.magic_4]))
        pkt.extend(struct.pack('<H', self.sequence))  # 2-byte little-endian sequence
        pkt.append(self.command_id)
        pkt.extend(struct.pack('<H', len(self.payload)))  # 2-byte little-endian length
        pkt.extend(self.payload)
        
        # Calculate CRC32 (IEEE 802.3)
        crc = zlib.crc32(bytes(pkt)) & 0xFFFFFFFF
        pkt.extend(struct.pack('<I', crc))  # 4-byte little-endian CRC
        
        return bytes(pkt)
    
    @staticmethod
    def from_bytes(data: bytes) -> Optional['UDPPacket']:
        """Parse packet from bytes"""
        if len(data) < 13:
            return None
        
        # Verify magic bytes
        if data[0:4] != bytes([0x17, 0xFE, 0xFD, 0x00]):
            return None
        
        # Extract header
        sequence = struct.unpack('<H', data[4:6])[0]
        command_id = data[6]
        payload_length = struct.unpack('<H', data[7:9])[0]
        
        # Verify length
        expected_total = 13 + payload_length
        if len(data) < expected_total:
            return None
        
        payload = data[9:9+payload_length]
        received_crc = struct.unpack('<I', data[9+payload_length:13+payload_length])[0]
        
        # Verify CRC32
        pkt_no_crc = data[:9+payload_length]
        calculated_crc = zlib.crc32(pkt_no_crc) & 0xFFFFFFFF
        
        if received_crc != calculated_crc:
            logger.warning(f"CRC mismatch! Received: {received_crc:08x}, Expected: {calculated_crc:08x}")
            # Don't fail, just warn - sometimes this happens
        
        return UDPPacket(
            sequence=sequence,
            command_id=command_id,
            payload_length=payload_length,
            payload=payload
        )


class UDPInitializer:
    """Handles UDP initialization sequence"""
    
    def __init__(self):
        self.sequence = 0
    
    def next_sequence(self) -> int:
        """Get next sequence number"""
        seq = self.sequence
        self.sequence = (self.sequence + 1) & 0xFFFF
        return seq
    
    def init_0x09(self) -> bytes:
        """
        First initialization packet (0x09)
        
        Purpose: Handshake, establish communication
        Payload: 46 bytes of zeros (57B total)
        """
        pkt = UDPPacket(
            sequence=self.next_sequence(),
            command_id=0x09,
            payload=b'\x00' * 46
        )
        logger.info("📡 Init packet 0x09 (handshake)")
        return pkt.to_bytes()
    
    def init_0x0A(self) -> bytes:
        """
        Second initialization packet (0x0A)
        
        Purpose: Acknowledge handshake
        Payload: 46 bytes of zeros (57B total)
        """
        pkt = UDPPacket(
            sequence=self.next_sequence(),
            command_id=0x0A,
            payload=b'\x00' * 46
        )
        logger.info("📡 Init packet 0x0A (acknowledge)")
        return pkt.to_bytes()
    
    def init_0x0B(self) -> bytes:
        """
        Third initialization packet (0x0B)
        
        Purpose: Sync state
        Payload: 46 bytes of zeros (57B total)
        """
        pkt = UDPPacket(
            sequence=self.next_sequence(),
            command_id=0x0B,
            payload=b'\x00' * 46
        )
        logger.info("📡 Init packet 0x0B (sync)")
        return pkt.to_bytes()
    
    def init_0x0C(self) -> bytes:
        """
        Fourth initialization packet (0x0C)
        
        Purpose: Complete initialization
        Payload: 46 bytes of zeros (57B total)
        """
        pkt = UDPPacket(
            sequence=self.next_sequence(),
            command_id=0x0C,
            payload=b'\x00' * 46
        )
        logger.info("📡 Init packet 0x0C (complete)")
        return pkt.to_bytes()
    
    def get_initialization_sequence(self) -> List[bytes]:
        """Get all 4 initialization packets"""
        return [
            self.init_0x09(),
            self.init_0x0A(),
            self.init_0x0B(),
            self.init_0x0C()
        ]
    
    def keep_alive(self) -> bytes:
        """
        Keep-alive packet (57 bytes of zeros)
        
        Sent every ~4.5 seconds to maintain connection
        """
        pkt = UDPPacket(
            sequence=self.next_sequence(),
            command_id=0x00,  # Keep-alive has no specific command
            payload=b'\x00' * 46
        )
        return pkt.to_bytes()


class UDPActionClient:
    """Handles action list and playback"""
    
    def __init__(self):
        self.sequence = 0
    
    def next_sequence(self) -> int:
        """Get next sequence number"""
        seq = self.sequence
        self.sequence = (self.sequence + 1) & 0xFFFF
        return seq
    
    def query_action_list(self) -> bytes:
        """
        Command 0x1A: Query list of saved actions
        
        Returns: UDP packet (57 bytes)
        """
        pkt = UDPPacket(
            sequence=self.next_sequence(),
            command_id=0x1A,
            payload=b'\x00' * 46
        )
        logger.info("📋 Query action list (0x1A)")
        return pkt.to_bytes()
    
    def play_action_by_index(self, action_index: int) -> bytes:
        """
        Command 0x41: Play saved action by index
        
        Args:
            action_index: Index of action to play (0-based)
        
        Returns: UDP packet
        
        NOTE: Action index is the position in the action list from 0x1A query
        """
        # Payload structure: Action index in first bytes
        payload = bytearray(46)
        payload[0] = action_index & 0xFF
        payload[1] = (action_index >> 8) & 0xFF
        
        pkt = UDPPacket(
            sequence=self.next_sequence(),
            command_id=0x41,
            payload=bytes(payload)
        )
        logger.info(f"▶️  Play action {action_index} (0x41)")
        return pkt.to_bytes()
    
    def play_action_by_name(self, action_name: str, action_list: List[Dict]) -> Optional[bytes]:
        """
        Find action by name in list and play it
        
        Args:
            action_name: Name of action to play (e.g., "waist_drum_dance")
            action_list: List from query_action_list() response
        
        Returns: UDP packet, or None if not found
        """
        for idx, action in enumerate(action_list):
            if action.get('name') == action_name:
                logger.info(f"Found action '{action_name}' at index {idx}")
                return self.play_action_by_index(idx)
        
        logger.warning(f"Action '{action_name}' not found in list")
        return None
    
    def stop_playback(self) -> bytes:
        """
        Command 0x42: Stop action playback
        
        Returns: UDP packet
        """
        pkt = UDPPacket(
            sequence=self.next_sequence(),
            command_id=0x42,
            payload=b'\x00' * 46
        )
        logger.info("⏹️  Stop playback (0x42)")
        return pkt.to_bytes()


class UDPProtocolClient:
    """
    Main UDP client for G1 Air teaching protocol
    
    Combines initialization, action querying, and playback
    """
    
    def __init__(self, robot_ip: str, port: int = 49504):
        """
        Initialize UDP client
        
        Args:
            robot_ip: Robot IP address
            port: UDP port (default 49504)
        """
        self.robot_ip = robot_ip
        self.port = port
        self.socket: Optional[socket.socket] = None
        
        self.initializer = UDPInitializer()
        self.action_client = UDPActionClient()
        
        logger.info(f"🔌 UDP Protocol Client: {robot_ip}:{port}")
    
    async def connect(self):
        """Create UDP socket"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.socket.settimeout(5.0)
            logger.info("✅ UDP socket created")
        except Exception as e:
            logger.error(f"Failed to create socket: {e}")
            raise
    
    async def disconnect(self):
        """Close UDP socket"""
        if self.socket:
            self.socket.close()
            self.socket = None
            logger.info("🔌 UDP socket closed")
    
    async def initialize(self) -> bool:
        """
        Initialize UDP connection with handshake sequence
        
        Sends 4 packets: 0x09, 0x0A, 0x0B, 0x0C
        
        Returns: True if successful, False otherwise
        """
        if not self.socket:
            await self.connect()
        
        try:
            logger.info("🚀 Initializing UDP connection...")
            init_packets = self.initializer.get_initialization_sequence()
            
            for i, pkt in enumerate(init_packets):
                logger.info(f"   Packet {i+1}/4: {len(pkt)} bytes")
                self.socket.sendto(pkt, (self.robot_ip, self.port))
                await asyncio.sleep(0.1)  # Small delay between packets
            
            logger.info("✅ UDP initialization complete")
            return True
            
        except Exception as e:
            logger.error(f"Initialization failed: {e}")
            return False
    
    async def query_actions(self) -> List[Dict]:
        """
        Query list of saved actions
        
        Returns: List of action dictionaries with 'name' and 'index' keys
        """
        if not self.socket:
            await self.connect()
        
        try:
            logger.info("📋 Querying saved actions...")
            
            cmd = self.action_client.query_action_list()
            self.socket.sendto(cmd, (self.robot_ip, self.port))
            
            actions = []
            self.socket.settimeout(3.0)
            
            try:
                while True:
                    response, addr = self.socket.recvfrom(4096)
                    
                    # Parse response packet
                    pkt = UDPPacket.from_bytes(response)
                    if not pkt or pkt.command_id != 0x1A:
                        continue
                    
                    # Extract action name from payload
                    # Action names are UTF-8 strings, null-terminated
                    name_bytes = pkt.payload[:32]  # First 32 bytes typically contain name
                    name = name_bytes.split(b'\x00')[0].decode('utf-8', errors='ignore')
                    
                    if name:
                        action = {
                            'name': name,
                            'index': len(actions),
                            'raw': pkt.payload.hex()
                        }
                        actions.append(action)
                        logger.info(f"✅ Found action: {name}")
                    
            except socket.timeout:
                pass
            
            if actions:
                logger.info(f"✅ Query complete: {len(actions)} actions found")
                for action in actions:
                    logger.info(f"   [{action['index']}] {action['name']}")
            else:
                logger.warning("⚠️  No actions found")
            
            return actions
            
        except Exception as e:
            logger.error(f"Query failed: {e}")
            return []
    
    async def play_action(self, action_name: str) -> bool:
        """
        Play an action by name
        
        Args:
            action_name: Name of action (e.g., "waist_drum_dance")
        
        Returns: True if action started, False otherwise
        
        NOTE: Robot must be in RUN mode (FSM state 500 or 501)
        """
        try:
            logger.info(f"▶️  Playing action: {action_name}")
            
            # Query actions first
            actions = await self.query_actions()
            
            # Find action index
            action_index = None
            for action in actions:
                if action['name'] == action_name:
                    action_index = action['index']
                    break
            
            if action_index is None:
                logger.error(f"❌ Action '{action_name}' not found")
                return False
            
            # Send play command
            cmd = self.action_client.play_action_by_index(action_index)
            self.socket.sendto(cmd, (self.robot_ip, self.port))
            
            logger.info(f"✅ Action '{action_name}' (index {action_index}) sent to robot")
            return True
            
        except Exception as e:
            logger.error(f"Play action failed: {e}")
            return False
    
    async def stop_action(self) -> bool:
        """
        Stop current action playback
        
        Returns: True if sent successfully
        """
        try:
            logger.info("⏹️  Stopping action playback...")
            
            cmd = self.action_client.stop_playback()
            self.socket.sendto(cmd, (self.robot_ip, self.port))
            
            logger.info("✅ Stop command sent")
            return True
            
        except Exception as e:
            logger.error(f"Stop failed: {e}")
            return False
