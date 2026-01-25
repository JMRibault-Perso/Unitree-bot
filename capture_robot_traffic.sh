#!/bin/bash
# Capture network traffic between Android app and G1 robot
# This will help identify what protocol/ports the app uses

ROBOT_IP="192.168.86.3"
DURATION=60
OUTPUT_FILE="robot_traffic_$(date +%Y%m%d_%H%M%S).pcap"

echo "======================================"
echo "  G1 Robot Network Traffic Capture"
echo "======================================"
echo ""
echo "Robot IP: $ROBOT_IP"
echo "Duration: $DURATION seconds"
echo "Output: $OUTPUT_FILE"
echo ""
echo "Instructions:"
echo "  1. Start this capture"
echo "  2. Use your Android app to connect/control the robot"
echo "  3. Wait for capture to complete"
echo "  4. Analyze the pcap file"
echo ""
read -p "Press Enter to start capture..."

echo ""
echo "Capturing traffic..."
echo "(Use Ctrl+C to stop early)"
echo ""

sudo tcpdump -i eth1 -w "$OUTPUT_FILE" \
  "host $ROBOT_IP" \
  -n -s 0 &

TCPDUMP_PID=$!

sleep $DURATION

sudo kill $TCPDUMP_PID 2>/dev/null

echo ""
echo "Capture complete: $OUTPUT_FILE"
echo ""
echo "Quick analysis:"
sudo tcpdump -r "$OUTPUT_FILE" -n | head -50

echo ""
echo "To see port summary:"
echo "  sudo tcpdump -r $OUTPUT_FILE -n | awk '{print \$5}' | cut -d. -f5 | sort | uniq -c | sort -rn"
echo ""
echo "To open in Wireshark (if installed):"
echo "  wireshark $OUTPUT_FILE"
