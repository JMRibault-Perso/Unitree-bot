#!/bin/bash
ROBOT_IP="192.168.86.18"

echo "Testing HTTP endpoints for map data..."
for port in 8000 8080 9000 7001; do
    for path in slam/map slam/grid slam/points map/data lidar/cloud api/slam/stream; do
        url="http://$ROBOT_IP:$port/$path"
        response=$(curl -s -m 1 "$url" 2>&1)
        if [ -n "$response" ] && [ "$response" != "curl: (28) Connection timed out"* ]; then
            echo "✅ $url"
            echo "   Response (first 100 chars): ${response:0:100}"
        fi
    done
done
