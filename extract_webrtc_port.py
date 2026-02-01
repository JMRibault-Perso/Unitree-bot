#!/usr/bin/env python3
"""
Extract Remote Port from WebRTC Connection

This script demonstrates how to extract the remote UDP port from an established
WebRTC peer connection. The port is negotiated during ICE (STUN) handshake and
is available in the remote ICE candidates.

Based on PCAP analysis:
- STUN negotiates port (e.g., 51639 in our capture)
- DTLS handshake establishes encrypted channel on that port
- Teaching protocol runs as DTLS Application Data on this port
"""

import asyncio
import sys
import logging
import re
from datetime import datetime

# Add WebRTC library to path
sys.path.insert(0, '/root/G1/go2_webrtc_connect')

from unitree_webrtc_connect.webrtc_driver import UnitreeWebRTCConnection
from unitree_webrtc_connect.constants import WebRTCConnectionMethod

# Robot details
ROBOT_IP = "192.168.86.3"
ROBOT_SN = "E21D1000PAHBMB06"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def extract_remote_port():
    """Extract remote port from WebRTC connection"""
    
    logger.info("=" * 80)
    logger.info("WebRTC Remote Port Extraction Test")
    logger.info("=" * 80)
    
    try:
        # Step 1: Connect to robot via WebRTC
        logger.info(f"Step 1: Connecting to robot at {ROBOT_IP}...")
        webrtc = UnitreeWebRTCConnection(
            WebRTCConnectionMethod.LocalSTA,
            ip=ROBOT_IP,
            serialNumber=ROBOT_SN
        )
        
        await webrtc.connect()
        logger.info("✅ WebRTC connection established")
        
        # Step 2: Wait for ICE to complete
        await asyncio.sleep(2)
        
        # Step 3: Extract port information from peer connection
        if hasattr(webrtc, 'peer_connection') and webrtc.peer_connection:
            pc = webrtc.peer_connection
            
            logger.info("\n" + "=" * 80)
            logger.info("PEER CONNECTION DETAILS")
            logger.info("=" * 80)
            
            # Connection state
            logger.info(f"Connection State: {pc.connectionState}")
            logger.info(f"ICE Connection State: {pc.iceConnectionState}")
            logger.info(f"ICE Gathering State: {pc.iceGatheringState}")
            
            # Method 1: Get remote description (SDP contains port)
            if hasattr(pc, 'remoteDescription') and pc.remoteDescription:
                sdp = pc.remoteDescription.sdp
                logger.info("\n--- Method 1: Parse Remote SDP ---")
                
                # Extract candidate lines from SDP
                candidate_lines = [line for line in sdp.split('\n') if 'candidate:' in line]
                
                if candidate_lines:
                    logger.info(f"Found {len(candidate_lines)} ICE candidates in remote SDP:")
                    
                    for i, line in enumerate(candidate_lines, 1):
                        # Parse candidate: a=candidate:1 1 udp 2130706431 192.168.86.3 51639 typ host
                        match = re.search(r'candidate:\S+\s+\S+\s+udp\s+\S+\s+(\S+)\s+(\d+)', line)
                        if match:
                            remote_ip = match.group(1)
                            remote_port = match.group(2)
                            logger.info(f"  Candidate {i}: {remote_ip}:{remote_port}")
                            
                            # Check if this is the robot's IP
                            if remote_ip == ROBOT_IP:
                                logger.info(f"  ✅ TEACHING PORT FOUND: {remote_port}")
                else:
                    logger.warning("No ICE candidates found in remote SDP")
                    
            else:
                logger.warning("No remote description available")
            
            # Method 2: Get SCTP port (data channel transport)
            if hasattr(pc, 'sctp') and pc.sctp:
                logger.info("\n--- Method 2: SCTP Transport ---")
                logger.info(f"SCTP Port: {pc.sctp.port}")
                
                # Get transport info
                if hasattr(pc.sctp, 'transport'):
                    transport = pc.sctp.transport
                    logger.info(f"Transport State: {transport.state}")
                    
                    # DTLS transport details
                    if hasattr(transport, 'transport') and transport.transport:
                        dtls_transport = transport.transport
                        logger.info(f"DTLS State: {dtls_transport.state}")
                        
                        # ICE transport (contains remote candidate)
                        if hasattr(dtls_transport, 'transport') and dtls_transport.transport:
                            ice_transport = dtls_transport.transport
                            logger.info(f"ICE Role: {ice_transport.role}")
                            
                            # Get selected candidate pair
                            if hasattr(ice_transport, 'getSelectedCandidatePair'):
                                try:
                                    pair = ice_transport.getSelectedCandidatePair()
                                    if pair:
                                        logger.info("\n--- Selected ICE Candidate Pair ---")
                                        logger.info(f"Local: {pair[0]}")
                                        logger.info(f"Remote: {pair[1]}")
                                        
                                        # Parse remote candidate
                                        remote = pair[1]
                                        if hasattr(remote, 'ip') and hasattr(remote, 'port'):
                                            logger.info(f"\n✅ TEACHING PORT: {remote.ip}:{remote.port}")
                                        elif isinstance(remote, str):
                                            # Parse string format
                                            match = re.search(r'(\d+\.\d+\.\d+\.\d+):(\d+)', remote)
                                            if match:
                                                remote_ip = match.group(1)
                                                remote_port = match.group(2)
                                                logger.info(f"\n✅ TEACHING PORT: {remote_ip}:{remote_port}")
                                except Exception as e:
                                    logger.warning(f"Could not get selected candidate pair: {e}")
            
            # Method 3: Access underlying aiortc objects
            logger.info("\n--- Method 3: Direct Attribute Inspection ---")
            logger.info("Available peer_connection attributes:")
            attrs = [attr for attr in dir(pc) if not attr.startswith('_')]
            for attr in attrs:
                try:
                    value = getattr(pc, attr)
                    # Skip methods
                    if not callable(value):
                        logger.info(f"  {attr}: {type(value).__name__}")
                except:
                    pass
            
            # Keep connection alive for monitoring
            logger.info("\nMonitoring connection for 5 seconds...")
            await asyncio.sleep(5)
            
            # Disconnect
            logger.info("Disconnecting...")
            await webrtc.disconnect()
            
            logger.info("\n" + "=" * 80)
            logger.info("Port extraction complete")
            logger.info("=" * 80)
            
        else:
            logger.error("❌ No peer connection available")
            
    except Exception as e:
        logger.error(f"Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(extract_remote_port())
