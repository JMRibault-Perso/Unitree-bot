#!/bin/bash
# Capture Android app traffic when phone is connected to PC's WiFi hotspot
# The Android app talks to robot, we want to see that communication

echo "================================================"
echo "Android App → Robot Traffic Capture (via Hotspot)"
echo "================================================"
echo ""
echo "Network Setup:"
echo "  - Your PC WiFi Hotspot: 192.168.137.x"
echo "  - Android Phone: connects to hotspot (gets 192.168.137.x IP)"
echo "  - Robot: 192.168.86.2 (on different network)"
echo ""
echo "Note: This capture may not work if robot is on different network!"
echo "      For best results:"
echo "      1. Connect PC to same WiFi as robot (192.168.86.x)"
echo "      2. OR use Wireshark on Windows directly"
echo "      3. OR capture on Android phone itself using tcpdump"
echo ""
echo "Looking for WiFi hotspot interface..."

# Find hotspot interface (usually has 192.168.137.1 as gateway)
HOTSPOT_IF=$(ip a | grep -B2 "192.168.137" | grep "state UP" | awk '{print $2}' | tr -d ':' | head -1)

if [ -z "$HOTSPOT_IF" ]; then
    echo "ERROR: Could not find hotspot interface!"
    echo "Available interfaces:"
    ip a | grep "state UP" | awk '{print "  - " $2}'
    exit 1
fi

echo "Found hotspot interface: $HOTSPOT_IF"
echo ""

# List connected devices on hotspot
echo "Devices on hotspot (192.168.137.x):"
arp -n | grep "192.168.137" | grep -v "incomplete" || echo "  None found"
echo ""

CAPTURE_FILE="/tmp/android_hotspot_$(date +%Y%m%d_%H%M%S).pcap"

echo "Starting capture on $HOTSPOT_IF..."
echo "Output: $CAPTURE_FILE"
echo ""
echo "Now use Android app to control robot for 60 seconds..."
echo "Press Ctrl+C to stop early"
echo ""

# Capture all traffic on hotspot interface
sudo timeout 60 tcpdump -i $HOTSPOT_IF -nn -s0 -w $CAPTURE_FILE 2>&1 | grep -E "(listening|packet)"

echo ""
echo "Capture saved to: $CAPTURE_FILE"
echo ""

# Analysis
echo "Quick analysis:"
echo "1. Total packets:"
sudo tcpdump -r $CAPTURE_FILE 2>/dev/null | wc -l

echo ""
echo "2. Unique IP conversations:"
sudo tcpdump -nn -r $CAPTURE_FILE 2>/dev/null | awk '{print $3, $5}' | sort -u | head -20

echo ""
echo "To analyze: wireshark $CAPTURE_FILE"
