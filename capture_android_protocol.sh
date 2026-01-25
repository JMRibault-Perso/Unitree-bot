#!/bin/bash
# Monitor traffic between Android app and G1 robot
# This will help identify what protocol the app uses

ROBOT_IP="192.168.86.3"
IFACE="eth1"
DURATION=120
OUTPUT_FILE="android_robot_traffic_$(date +%Y%m%d_%H%M%S).pcap"

echo "=========================================="
echo "  Android App Protocol Analysis"
echo "=========================================="
echo ""
echo "Robot IP: $ROBOT_IP"
echo "Network: $IFACE"
echo "Output: $OUTPUT_FILE"
echo "Duration: $DURATION seconds (or Ctrl+C to stop)"
echo ""
echo "INSTRUCTIONS:"
echo "  1. Make sure your Android phone is on same WiFi (192.168.86.x)"
echo "  2. Press Enter to start capture"
echo "  3. Use your Android app to:"
echo "     - Connect to robot"
echo "     - Send commands (walk, arm movements, etc.)"
echo "     - View status information"
echo "     - Stream video"
echo "  4. Wait for capture to complete or press Ctrl+C"
echo ""
read -p "Press Enter to start capture..."

echo ""
echo "===== CAPTURING - USE YOUR ANDROID APP NOW ====="
echo ""

# Capture all traffic to/from robot
sudo tcpdump -i $IFACE -n -s 0 -w "$OUTPUT_FILE" "host $ROBOT_IP" &
TCPDUMP_PID=$!

echo "Capture running (PID: $TCPDUMP_PID)"
echo "Press Ctrl+C to stop early, or wait $DURATION seconds..."
echo ""

# Wait for duration or until user stops
sleep $DURATION 2>/dev/null || true

# Stop capture
sudo kill $TCPDUMP_PID 2>/dev/null
wait $TCPDUMP_PID 2>/dev/null

echo ""
echo "=========================================="
echo "Capture Complete: $OUTPUT_FILE"
echo "=========================================="
echo ""

# Quick analysis
echo "=== Quick Analysis ==="
echo ""

PACKET_COUNT=$(sudo tcpdump -r "$OUTPUT_FILE" 2>/dev/null | wc -l)
echo "Total packets captured: $PACKET_COUNT"
echo ""

if [ $PACKET_COUNT -eq 0 ]; then
    echo "⚠ WARNING: No packets captured!"
    echo "Check:"
    echo "  - Is Android phone on same WiFi network?"
    echo "  - Did you use the app during capture?"
    echo "  - Is robot IP correct: $ROBOT_IP"
    exit 1
fi

echo "=== Top 10 Ports Used ==="
sudo tcpdump -r "$OUTPUT_FILE" -n 2>/dev/null | \
    grep -oP '\.\K[0-9]+(?=:)' | sort | uniq -c | sort -rn | head -10
echo ""

echo "=== Protocol Distribution ==="
sudo tcpdump -r "$OUTPUT_FILE" -n 2>/dev/null | \
    awk '{for(i=1;i<=NF;i++) if($i~/^(TCP|UDP|ICMP)$/) print $i}' | \
    sort | uniq -c
echo ""

echo "=== First 20 Packets ==="
sudo tcpdump -r "$OUTPUT_FILE" -n -c 20 2>/dev/null
echo ""

echo "=== Check for Specific Protocols ==="
echo ""

echo "DDS ports (7400-7430):"
DDS_COUNT=$(sudo tcpdump -r "$OUTPUT_FILE" -n 'udp and (portrange 7400-7430)' 2>/dev/null | wc -l)
echo "  $DDS_COUNT packets"

echo "HTTP/HTTPS (80/443):"
HTTP_COUNT=$(sudo tcpdump -r "$OUTPUT_FILE" -n 'tcp port 80 or tcp port 443' 2>/dev/null | wc -l)
echo "  $HTTP_COUNT packets"

echo "Custom high ports (>10000):"
HIGH_COUNT=$(sudo tcpdump -r "$OUTPUT_FILE" -n 'portrange 10000-65535' 2>/dev/null | wc -l)
echo "  $HIGH_COUNT packets"

echo ""
echo "=== Next Steps ==="
echo ""
echo "1. Open in Wireshark for detailed analysis:"
echo "   wireshark $OUTPUT_FILE"
echo ""
echo "2. Look for repeating patterns in packet data:"
echo "   sudo tcpdump -r $OUTPUT_FILE -X | less"
echo ""
echo "3. Find command packets (look for packets when you pressed buttons):"
echo "   - Note the timestamp when you pressed a button"
echo "   - Find packets near that time"
echo "   - Compare hex dumps to identify command structure"
echo ""
echo "4. Export interesting packets as hex:"
echo "   sudo tcpdump -r $OUTPUT_FILE -XX -n > packet_dump.txt"
echo ""
echo "5. If you see a specific port being used heavily, filter it:"
echo "   sudo tcpdump -r $OUTPUT_FILE -n 'port XXXX' -X"
echo ""
