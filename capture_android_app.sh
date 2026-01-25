#!/bin/bash
# Capture Android app traffic to analyze robot control protocol

ROBOT_IP="192.168.86.2"
INTERFACE="eth1"
CAPTURE_FILE="/tmp/android_app_control_$(date +%Y%m%d_%H%M%S).pcap"

echo "================================================"
echo "Android App Traffic Capture"
echo "================================================"
echo "Robot IP: $ROBOT_IP"
echo "Interface: $INTERFACE"
echo "Output: $CAPTURE_FILE"
echo ""
echo "Instructions:"
echo "1. Start this script (it will capture for 60 seconds)"
echo "2. Use Android app to control robot movement:"
echo "   - Walk forward/backward"
echo "   - Turn left/right"
echo "   - Strafe left/right"
echo "   - Stop"
echo "3. Script will save capture and show analysis"
echo ""
echo "Press Ctrl+C to stop early"
echo "================================================"
echo ""

# Capture all traffic to/from robot for 60 seconds
echo "Starting capture..."
sudo timeout 60 tcpdump -i $INTERFACE -nn -v \
    "host $ROBOT_IP" \
    -w $CAPTURE_FILE 2>&1 | grep -E "(listening|packet)"

echo ""
echo "Capture complete: $CAPTURE_FILE"
echo ""

# Basic analysis
echo "================================================"
echo "Quick Analysis:"
echo "================================================"
echo ""

echo "1. Protocols used:"
sudo tcpdump -nn -r $CAPTURE_FILE 2>/dev/null | \
    awk '{print $3}' | cut -d. -f6 | sort | uniq -c | sort -rn | head -10

echo ""
echo "2. Ports used:"
sudo tcpdump -nn -r $CAPTURE_FILE 2>/dev/null | \
    grep -oE ":[0-9]+" | sort | uniq -c | sort -rn | head -10

echo ""
echo "3. Packet count by direction:"
echo "To robot ($ROBOT_IP):"
sudo tcpdump -nn -r $CAPTURE_FILE "dst host $ROBOT_IP" 2>/dev/null | wc -l
echo "From robot ($ROBOT_IP):"
sudo tcpdump -nn -r $CAPTURE_FILE "src host $ROBOT_IP" 2>/dev/null | wc -l

echo ""
echo "================================================"
echo "To analyze in Wireshark: wireshark $CAPTURE_FILE"
echo "To view UDP data: sudo tcpdump -nn -X -r $CAPTURE_FILE udp"
echo "To view specific port: sudo tcpdump -nn -X -r $CAPTURE_FILE 'port 8080'"
echo "================================================"
