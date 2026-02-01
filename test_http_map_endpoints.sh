#!/bin/bash
# Test if robot serves map data via HTTP while SLAM is active

ROBOT_IP="192.168.86.18"

echo "====================================================================="
echo "Testing HTTP Endpoints for SLAM Map Data"
echo "====================================================================="
echo ""
echo "IMPORTANT: Start SLAM mapping in the web UI first!"
echo "Then run this script while the robot is mapping."
echo ""
echo "Press Enter when SLAM is active..."
read

echo "Testing possible map endpoints..."
echo ""

# Test common ports and paths
endpoints=(
    "http://$ROBOT_IP:8080/slam/map"
    "http://$ROBOT_IP:8080/slam/grid"
    "http://$ROBOT_IP:8080/slam/points"
    "http://$ROBOT_IP:8080/lidar/cloud"
    "http://$ROBOT_IP:9000/slam/data"
    "http://$ROBOT_IP:9000/map/grid"
    "http://$ROBOT_IP:9000/api/slam/realtime"
    "http://$ROBOT_IP:8000/slam/stream"
    "http://$ROBOT_IP:8000/map/occupancy"
    "http://$ROBOT_IP:7001/slam"
    "http://$ROBOT_IP:7001/map"
)

for url in "${endpoints[@]}"; do
    echo -n "Testing: $url ... "
    response=$(curl -s -m 2 "$url" 2>&1)
    status=$?
    
    if [ $status -eq 0 ] && [ -n "$response" ]; then
        echo "✅ RESPONSE!"
        echo "  First 200 chars: ${response:0:200}"
        echo ""
    else
        echo "❌ No response"
    fi
done

echo ""
echo "Port scan for HTTP servers..."
nmap -p 7000-9000 $ROBOT_IP 2>&1 | grep "open"

echo ""
echo "====================================================================="
echo "If you found any responses, check them carefully for map data!"
echo "====================================================================="
