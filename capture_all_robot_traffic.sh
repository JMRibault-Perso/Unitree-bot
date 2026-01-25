#!/bin/bash
# Capture ALL traffic to/from robot to analyze what the Android app actually uses
# This helps determine if the robot uses DDS or a proprietary protocol

ROBOT_IP="192.168.86.3"
IFACE="eth1"
OUTPUT_FILE="robot_all_traffic_$(date +%Y%m%d_%H%M%S).pcap"

echo "=========================================="
echo "  Full Robot Traffic Capture"
echo "=========================================="
echo "Robot IP: $ROBOT_IP"
echo "Interface: $IFACE"
echo "Output: $OUTPUT_FILE"
echo ""
echo "This will capture ALL traffic to/from the robot."
echo "Use your Android app while this runs to see what it actually uses."
echo ""
echo "Instructions:"
echo "  1. Start this capture (press Enter)"
echo "  2. Use Android app to control robot"
echo "  3. Press Ctrl+C when done"
echo "  4. Analyze the output"
echo ""
read -p "Press Enter to start..."

echo ""
echo "Capturing... (Press Ctrl+C to stop)"
echo ""

sudo tcpdump -i $IFACE -n -s 0 -w "$OUTPUT_FILE" "host $ROBOT_IP"

echo ""
echo "=========================================="
echo "Capture saved to: $OUTPUT_FILE"
echo ""
echo "Quick analysis:"
echo ""

echo "=== Port Summary ==="
sudo tcpdump -r "$OUTPUT_FILE" -n 2>/dev/null | \
  awk '{print $3, $5}' | \
  sed 's/.*\.\([0-9]*\):.*/\1/' | \
  sort | uniq -c | sort -rn | head -20

echo ""
echo "=== Protocol Summary ==="
sudo tcpdump -r "$OUTPUT_FILE" -n 2>/dev/null | \
  awk '{print $1, $2, $3, $4, $5}' | head -50

echo ""
echo "=== DDS-specific ports (7400-7430) ==="
sudo tcpdump -r "$OUTPUT_FILE" -n 'udp and (port >= 7400 and port <= 7430)' 2>/dev/null | wc -l
echo "packets found"

echo ""
echo "To analyze in Wireshark:"
echo "  wireshark $OUTPUT_FILE"
echo ""
echo "To see if it's using DDS:"
echo "  sudo tcpdump -r $OUTPUT_FILE -n 'udp and (port >= 7400 and port <= 7430)' | head -20"
echo ""
