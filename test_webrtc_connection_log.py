#!/usr/bin/env python3
"""
WebRTC Connection Test - Generates detailed connection logs
Shows that the G1 robot WebRTC connection is working
"""

import asyncio
import logging
import sys
import subprocess
from datetime import datetime

# Add WebRTC library to path
sys.path.insert(0, '/root/G1/go2_webrtc_connect')

from unitree_webrtc_connect.webrtc_driver import UnitreeWebRTCConnection
from unitree_webrtc_connect.constants import WebRTCConnectionMethod

# Configure detailed logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

logger = logging.getLogger(__name__)

# Known G1 robot MAC address
ROBOT_MAC = "fc:23:cd:92:60:02"
ROBOT_NAME = "G1_6937"
ROBOT_SN = "E21D1000PAHBMB06"


def find_robot_ip_by_mac(mac_address: str) -> str:
    """Find robot IP using ARP cache lookup"""
    try:
        # Method 1: Check ARP cache
        result = subprocess.run(['arp', '-n'], capture_output=True, text=True)
        for line in result.stdout.split('\n'):
            if mac_address.lower() in line.lower():
                parts = line.split()
                if len(parts) >= 1:
                    ip = parts[0]
                    if ip.replace('.', '').isdigit():
                        return ip
        
        # Method 2: arp-scan (if available)
        try:
            result = subprocess.run(['arp-scan', '-I', 'eth1', '--localnet'], 
                                  capture_output=True, text=True, timeout=5)
            for line in result.stdout.split('\n'):
                if mac_address.lower() in line.lower():
                    parts = line.split()
                    if len(parts) >= 1:
                        return parts[0]
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass
            
    except Exception as e:
        logger.error(f"Error finding IP by MAC: {e}")
    
    return None


async def test_webrtc_connection():
    """Test WebRTC connection and log all steps"""
    
    print("=" * 80)
    print("G1 ROBOT WebRTC CONNECTION TEST")
    print("=" * 80)
    print(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("-" * 80)
    
    # Step 1: Discover robot by MAC address (ARP)
    logger.info(f"Step 1: Finding robot IP by MAC address {ROBOT_MAC}...")
    
    try:
        robot_ip = find_robot_ip_by_mac(ROBOT_MAC)
        
        if not robot_ip:
            logger.error("❌ Robot not found in ARP cache")
            logger.info("   Try pinging the robot first or check if it's on the network")
            print("\n" + "=" * 80)
            print("RESULT: FAILED - Robot not found via ARP")
            print("=" * 80)
            return False
        
        logger.info(f"✅ Robot discovered via ARP")
        logger.info(f"   Robot: {ROBOT_NAME}")
        logger.info(f"   IP Address: {robot_ip}")
        logger.info(f"   MAC Address: {ROBOT_MAC}")
        logger.info(f"   Serial: {ROBOT_SN}")
        print("-" * 80)
        
    except Exception as e:
        logger.error(f"❌ Discovery failed: {e}")
        print("\n" + "=" * 80)
        print(f"RESULT: FAILED - Discovery error: {e}")
        print("=" * 80)
        return False
    
    # Step 2: Initialize WebRTC Connection
    logger.info("Step 2: Initializing WebRTC Connection...")
    
    webrtc = UnitreeWebRTCConnection(
        WebRTCConnectionMethod.LocalSTA,
        ip=robot_ip,
        serialNumber=ROBOT_SN
    )
    
    # Step 3: Connect to robot
    logger.info(f"Step 3: Connecting to robot at {robot_ip}...")
    logger.info("   Creating WebRTC peer connection...")
    logger.info("   Negotiating ICE candidates...")
    logger.info("   Establishing data channel...")
    
    try:
        try:
            await webrtc.connect()
        except SystemExit as e:
            # WebRTC driver calls sys.exit(1) on failure - catch it
            raise ConnectionError(f"Failed to establish WebRTC connection to {robot_ip}. Check if robot is powered on and ports 8081/9991 are accessible.") from e
        
        logger.info("✅ WebRTC connection established successfully!")
        
        # Log connection details
        if hasattr(webrtc, 'peer_connection') and webrtc.peer_connection:
            pc = webrtc.peer_connection
            logger.info(f"   Peer connection state: {pc.connectionState}")
            logger.info(f"   ICE connection state: {pc.iceConnectionState}")
            logger.info(f"   Signaling state: {pc.signalingState}")
        
        if hasattr(webrtc, 'datachannel') and webrtc.datachannel:
            logger.info(f"   Data channel state: {webrtc.datachannel.readyState}")
            logger.info(f"   Data channel label: {webrtc.datachannel.label}")
        
        print("-" * 80)
            
        # Step 4: Verify connection is stable
        logger.info("Step 4: Verifying connection stability...")
        
        # Wait a moment for connection to stabilize
        await asyncio.sleep(2)
        
        # Check connection status
        if hasattr(webrtc, 'peer_connection') and webrtc.peer_connection:
            pc_state = webrtc.peer_connection.connectionState
            ice_state = webrtc.peer_connection.iceConnectionState
            
            logger.info(f"   Final connection state: {pc_state}")
            logger.info(f"   Final ICE state: {ice_state}")
            
            if pc_state in ["connected", "completed"] or ice_state in ["connected", "completed"]:
                logger.info("✅ Connection is stable")
                print("-" * 80)
                
                # Step 5: Log WebRTC ports and transport info
                logger.info("Step 5: WebRTC Transport Information...")
                
                # Get local/remote addresses from ICE candidates
                if hasattr(webrtc.peer_connection, 'sctp') and webrtc.peer_connection.sctp:
                    logger.info(f"   SCTP port: {webrtc.peer_connection.sctp.port}")
                
                # Check for video/audio tracks
                logger.info("Step 6: Checking media tracks...")
                has_video = False
                has_audio = False
                
                if hasattr(webrtc, 'video_track') and webrtc.video_track:
                    logger.info("✅ Video track available")
                    has_video = True
                
                if hasattr(webrtc, 'audio_track') and webrtc.audio_track:
                    logger.info("✅ Audio track available")
                    has_audio = True
                
                if not has_video and not has_audio:
                    logger.info("ℹ️  No media tracks (data channel only)")
                
                print("-" * 80)
                print("\n" + "=" * 80)
                print("RESULT: SUCCESS ✅")
                print("=" * 80)
                print("WebRTC connection to G1 robot is WORKING")
                print(f"Robot: {ROBOT_NAME}")
                print(f"IP: {robot_ip}")
                print(f"MAC: {ROBOT_MAC}")
                print(f"Serial: {ROBOT_SN}")
                print(f"Connection State: {pc_state}")
                print(f"ICE State: {ice_state}")
                print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                print("=" * 80)
                
                # Keep connection alive to monitor
                logger.info("\nMonitoring connection for 5 seconds...")
                await asyncio.sleep(5)
                
                # Disconnect gracefully
                logger.info("Disconnecting from robot...")
                await webrtc.disconnect()
                logger.info("Disconnected successfully")
                
                return True
            else:
                logger.error(f"❌ Connection not stable: {pc_state}/{ice_state}")
                print("\n" + "=" * 80)
                print("RESULT: FAILED - Connection unstable")
                print("=" * 80)
                return False
        else:
            logger.error("❌ No peer connection available")
            print("\n" + "=" * 80)
            print("RESULT: FAILED - No peer connection")
            print("=" * 80)
            return False
            
    except ConnectionError as e:
        logger.error(f"❌ Connection error: {e}", exc_info=True)
        print("\n" + "=" * 80)
        print(f"RESULT: FAILED - Error: {e}")
        print("=" * 80)
        return False
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}", exc_info=True)
        print("\n" + "=" * 80)
        print(f"RESULT: FAILED - Exception: {e}")
        print("=" * 80)
        try:
            await webrtc.disconnect()
        except:
            pass
        return False


async def main():
    """Main entry point"""
    try:
        success = await test_webrtc_connection()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.info("\nTest interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
