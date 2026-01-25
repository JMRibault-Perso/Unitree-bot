#!/bin/bash
# Complete robot boot and connection capture
# This will capture everything to understand the Android app protocol

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
CAPTURE_FILE="robot_boot_complete_${TIMESTAMP}.pcap"

echo "═══════════════════════════════════════════════════════════════"
echo "G1 Robot Boot & Android App Connection Capture"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "Output file: $CAPTURE_FILE"
echo ""
echo "INSTRUCTIONS:"
echo "─────────────────────────────────────────────────────────────"
echo "1. Make sure robot is POWERED OFF now"
echo "2. Press Enter to start capture"
echo "3. Then POWER ON the robot"
echo "4. Wait for robot to fully boot (LEDs stable)"
echo "5. Open Android app and connect to G1_6937"
echo "6. Try a few commands (wave, walk, etc.)"
echo "7. Press Ctrl+C here when done"
echo "─────────────────────────────────────────────────────────────"
echo ""
read -p "Ready? Press Enter to start capturing..."

echo ""
echo "🔴 CAPTURING - Do the following:"
echo "   1. Power on robot now"
echo "   2. Wait for boot complete"
echo "   3. Open Android app"
echo "   4. Connect to G1_6937"
echo "   5. Send some commands"
echo "   6. Press Ctrl+C when done"
echo ""

# Capture everything on the network interface
sudo tcpdump -i eth1 -w "$CAPTURE_FILE" -v 2>&1 &
TCPDUMP_PID=$!

# Wait for Ctrl+C
trap "echo ''; echo 'Stopping capture...'; sudo kill $TCPDUMP_PID 2>/dev/null; sleep 2" INT

wait $TCPDUMP_PID 2>/dev/null

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "✓ Capture complete!"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "File: $CAPTURE_FILE"
echo "Size: $(ls -lh "$CAPTURE_FILE" | awk '{print $5}')"
echo ""
echo "Quick analysis:"
echo "─────────────────────────────────────────────────────────────"

# Show robot IP
echo "Robot IP addresses seen:"
tcpdump -r "$CAPTURE_FILE" -n 2>/dev/null | grep -oE '192\.168\.[0-9]+\.[0-9]+' | sort -u | grep -v "$(hostname -I | awk '{print $1}')"

echo ""
echo "Ports used by robot:"
tcpdump -r "$CAPTURE_FILE" -n 'host 192.168.86.3' 2>/dev/null | grep -oE '(UDP|TCP).* [0-9]+' | awk '{print $2}' | sort -u | head -20

echo ""
echo "DNS queries:"
tcpdump -r "$CAPTURE_FILE" 'port 53' 2>/dev/null | grep -E "A\?|AAAA\?" | awk '{print $NF}' | sort -u

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "Run detailed analysis:"
echo "  ./analyze_capture.sh $CAPTURE_FILE"
echo "═══════════════════════════════════════════════════════════════"
