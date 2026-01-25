#!/bin/bash
# Run the G1 Web UI Server

cd /root/G1/unitree_sdk2

# Install dependencies if needed
pip3 install -q fastapi uvicorn websockets 2>/dev/null || true

# Run the server
echo "Starting G1 Web UI Server..."
echo "Open http://localhost:8000 in your browser"
echo ""

python3 -m g1_app.ui.web_server
