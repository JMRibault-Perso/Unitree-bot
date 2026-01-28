#!/bin/bash
# Capture Android app traffic to reverse-engineer teach mode recording protocol

ROBOT_IP="192.168.86.3"  # Your G1's IP
CAPTURE_FILE="/tmp/android_teachmode_$(date +%s).pcap"

echo "=== Android App Teach Mode Protocol Capture ==="
echo "Robot IP: $ROBOT_IP"
echo "Capture file: $CAPTURE_FILE"
echo ""
echo "Instructions:"
echo "1. This script will capture ALL traffic to/from the robot"
echo "2. Open the Unitree Android app"
echo "3. Enter teach mode and record a simple action"
echo "4. Save the action with a name"
echo "5. Press Ctrl+C here to stop capture"
echo "6. We'll analyze the capture to find recording APIs"
echo ""
echo "Starting capture in 5 seconds..."
sleep 5

sudo tcpdump -i any host $ROBOT_IP -w $CAPTURE_FILE -v

echo ""
echo "Capture saved to: $CAPTURE_FILE"
echo ""
echo "To analyze:"
echo "  wireshark $CAPTURE_FILE"
echo ""
echo "Look for:"
echo "  - HTTP POST requests with 'teach', 'record', 'save', or 'action' in URL"
echo "  - WebRTC datachannel messages with api_id in 7109-7112 range"
echo "  - Any new topics on rt/arm/*"
