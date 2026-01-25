#!/bin/bash
# Capture traffic between Android app and G1 robot

ANDROID_IP="192.168.86.10"
ROBOT_IP="192.168.86.3"

echo "======================================"
echo "  Capturing Android <-> Robot Traffic"
echo "======================================"
echo "Android: $ANDROID_IP"
echo "Robot:   $ROBOT_IP"
echo ""
echo "Now use your Android app to control the robot..."
echo "Press Ctrl+C when done"
echo ""

# Capture traffic between the two devices
sudo tcpdump -i eth1 -n -v \
  "(host $ANDROID_IP and host $ROBOT_IP)" \
  2>&1 | tee robot_capture.log
