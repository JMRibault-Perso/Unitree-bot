#!/bin/bash
# Complete automated restart: server + robot connection + SLAM

cd /root/G1/unitree_sdk2

echo "🛑 Stopping old server..."
pkill -9 -f "python.*web_server"
sleep 1

echo "🧹 Clearing Python cache..."
find g1_app -name "*.pyc" -delete 2>/dev/null
find g1_app -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null

echo "🚀 Starting web server..."
python3 -m g1_app.ui.web_server > /tmp/web_server.log 2>&1 &
SERVER_PID=$!
sleep 3

if ! ps -p $SERVER_PID > /dev/null; then
    echo "❌ Server failed to start"
    tail -20 /tmp/web_server.log
    exit 1
fi

echo "✅ Server running (PID: $SERVER_PID)"

echo "🔍 Discovering robot IP..."
ROBOT_IP=$(arp -n | grep -i 'fc:23:cd:92:60:02' | awk '{print $1}' | head -1)
if [ -z "$ROBOT_IP" ]; then
    echo "   ⚠️  Robot not in ARP cache, using last known IP..."
    ROBOT_IP="192.168.86.4"
fi
echo "   📍 Robot IP: $ROBOT_IP"

echo "📡 Connecting to robot..."
CONNECT_RESULT=$(curl -s -X POST "http://localhost:9000/api/connect?ip=$ROBOT_IP&serial_number=G1_6937")

if echo "$CONNECT_RESULT" | grep -q '"success":true'; then
    echo "   ✅ Robot connected"
    sleep 3
    
    echo "🗺️  Auto-starting SLAM..."
    SLAM_RESULT=$(curl -s -X POST http://localhost:9000/api/slam/start)
    if echo "$SLAM_RESULT" | grep -q '"success":true'; then
        echo "   ✅ SLAM started"
        sleep 2
        
        echo ""
        echo "🧪 Testing point cloud data..."
        python3 test_lidar_storage.py
    else
        echo "   ⚠️  SLAM start failed: $SLAM_RESULT"
    fi
else
    echo "   ❌ Robot connection failed: $CONNECT_RESULT"
    echo "   Try connecting manually at http://localhost:9000"
fi
