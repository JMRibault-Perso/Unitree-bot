#!/usr/bin/env bash
# RELOCALIZATION TEST - QUICK START
# ==================================
# Run this when the robot is powered on and connected to WiFi

echo "=========================================="
echo "SLAM RELOCALIZATION DETECTION TEST"
echo "=========================================="
echo ""
echo "Prerequisites:"
echo "  ✓ Robot is powered on"
echo "  ✓ Robot is on WiFi (192.168.86.3)"
echo "  ✓ You have the room.pcd map built"
echo ""
echo "Step 1: Start the web server (if not running)..."
echo "  Terminal 1: python3 g1_app/__main__.py"
echo ""
echo "Step 2: Run the relocation test..."
echo "  Terminal 2: python3 test_relocation_detection.py --map room"
echo ""
echo "Step 3: Follow the prompts:"
echo "  1. Test will load map and monitor baseline position (10s)"
echo "  2. Test will STOP SLAM service"
echo "  3. Test will PAUSE and wait for you to move robot"
echo "  4. YOU MOVE THE ROBOT (at least 0.5-1.0m away)"
echo "  5. Press ENTER to restart SLAM and detect relocalization"
echo "  6. Test monitors position for 10s"
echo ""
echo "=========================================="
echo "Starting test..."
echo "=========================================="
echo ""

cd /root/G1/unitree_sdk2
python3 test_relocation_detection.py --map room --robot-ip 192.168.86.3 --robot-sn G1_6937
