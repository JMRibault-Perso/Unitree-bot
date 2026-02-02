#!/bin/bash
# Restart web server with clean state and auto-start SLAM

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

if ps -p $SERVER_PID > /dev/null; then
    echo "✅ Server running (PID: $SERVER_PID)"
    echo ""
    echo "🤖 Connecting to robot G1_6937..."
    ROBOT_IP="192.168.86.18"
    ROBOT_SN="E21D1000PAHBMB06"
    
    CONNECT_RESULT=$(curl -s -X POST "http://localhost:9000/api/connect?ip=$ROBOT_IP&serial_number=$ROBOT_SN")
    if echo "$CONNECT_RESULT" | grep -q '"success":true'; then
        echo "   ✅ Robot connected"
    else
        echo "   ⚠️  Connection failed: $CONNECT_RESULT"
        exit 1
    fi
    
    sleep 3
    echo ""
    echo "🗺️  Auto-starting SLAM..."
    SLAM_RESULT=$(curl -s -X POST http://localhost:9000/api/slam/start)
    if echo "$SLAM_RESULT" | grep -q '"success":true'; then
        echo "   ✅ SLAM started"
    else
        echo "   ⚠️  SLAM start failed: $SLAM_RESULT"
    fi
    
    sleep 3
    echo ""
    echo "🧪 Testing point cloud data..."
    python3 test_lidar_storage.py
else
    echo "❌ Server failed to start"
    tail -20 /tmp/web_server.log
fi
