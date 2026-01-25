#!/bin/bash
# Capture Android app WebRTC/MQTT traffic for protocol analysis
# Run this BEFORE opening the Android app

ROBOT_IP="192.168.86.3"
CAPTURE_FILE="webrtc_app_$(date +%Y%m%d_%H%M%S).pcap"

echo "========================================="
echo "WebRTC/MQTT Protocol Capture"
echo "========================================="
echo "Robot IP: $ROBOT_IP"
echo "Capture file: $CAPTURE_FILE"
echo ""
echo "Instructions:"
echo "1. This script will start capturing traffic"
echo "2. Open the Unitree Android app"
echo "3. Control the robot (walk, move arms, etc.)"
echo "4. Press Ctrl+C when done"
echo ""
echo "What to look for in Wireshark:"
echo "  - MQTT topics (port 1883/8883)"
echo "  - STUN/TURN (ports 3478, 5349)"
echo "  - WebRTC (look for DTLS/SRTP)"
echo "  - Custom TCP/UDP ports"
echo ""
echo "Press Enter to start capture..."
read

echo "Starting capture on eth1..."
echo "(Press Ctrl+C to stop)"
sudo tcpdump -i eth1 host $ROBOT_IP -w $CAPTURE_FILE -v

echo ""
echo "Capture saved to: $CAPTURE_FILE"
echo ""
echo "Analyze with:"
echo "  wireshark $CAPTURE_FILE"
echo ""
echo "Quick analysis commands:"
echo "  # Show conversation statistics"
echo "  tshark -r $CAPTURE_FILE -q -z conv,tcp"
echo "  tshark -r $CAPTURE_FILE -q -z conv,udp"
echo ""
echo "  # Extract MQTT topics"
echo "  tshark -r $CAPTURE_FILE -Y 'mqtt' -T fields -e mqtt.topic"
echo ""
echo "  # Find WebRTC signaling"
echo "  tshark -r $CAPTURE_FILE -Y 'stun or dtls or srtp'"
