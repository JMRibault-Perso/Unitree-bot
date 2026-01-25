#!/bin/bash
# G1 Robot SDK Quick Test Script
# Use this on a native Linux PC connected to the same WiFi as the G1 robot

echo "======================================"
echo "  Unitree G1 Robot SDK Test"
echo "======================================"
echo ""

# Set environment
export CYCLONEDDS_URI=file://$(pwd)/cyclonedds.xml
export LD_LIBRARY_PATH=$(pwd)/thirdparty/lib/x86_64:$LD_LIBRARY_PATH

# Get robot IP (default for G1_6937)
read -p "Enter robot IP address [192.168.86.3]: " ROBOT_IP
ROBOT_IP=${ROBOT_IP:-192.168.86.3}

echo ""
echo "Testing connectivity to robot at $ROBOT_IP..."
ping -c 2 $ROBOT_IP

if [ $? -ne 0 ]; then
    echo "ERROR: Cannot ping robot. Check WiFi connection."
    exit 1
fi

echo ""
echo "✓ Robot is reachable"
echo ""
echo "Testing DDS subscriber (listening for 10 seconds)..."
echo "If you see messages, DDS is working!"
echo ""

timeout 10 ./build/bin/test_subscriber

echo ""
echo "======================================"
echo "If no messages appeared above, check:"
echo "  1. Robot is powered on and standing"
echo "  2. You're on the same WiFi network"
echo "  3. Firewall allows UDP ports 7400-7430"
echo ""
echo "Try an action example:"
echo "  export CYCLONEDDS_URI=file://$(pwd)/cyclonedds.xml"
echo "  ./build/bin/g1_arm_action_example -n <interface> -l"
echo ""
echo "Replace <interface> with: wlan0, eth0, etc."
echo "======================================"
