#!/bin/bash

# Test script for G1 Air robot connection
export CYCLONEDDS_URI=file:///root/G1/unitree_sdk2/cyclonedds.xml

echo "=== Testing G1 Air Robot Connection ==="
echo "Robot IP: 192.168.86.3"
echo "Network Interface: eth1"
echo ""

echo "1. Ping test..."
ping -c 2 192.168.86.3 && echo "✓ Ping successful" || echo "✗ Ping failed"
echo ""

echo "2. Testing G1 Arm Action Client..."
cd /root/G1/unitree_sdk2
./build/bin/g1_arm_action_example -n eth1 -l
echo ""

echo "3. Testing G1 Loco Client..."
timeout 3 ./build/bin/g1_loco_client --network_interface=eth1 --get_state
echo ""

echo "=== Test Complete ==="
echo "If you see error 3104, the robot may need to be in a specific mode."
echo "Check the Unitree app to ensure the robot is ready for SDK control."
