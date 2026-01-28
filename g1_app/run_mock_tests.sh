#!/bin/bash
# Test script for mock robot server

echo "=================================="
echo "🧪 MOCK ROBOT TEST SUITE"
echo "=================================="

# Start mock server in background
echo "Starting mock server on port 8080..."
cd /root/G1/unitree_sdk2/g1_app
nohup python3 test_mock_server.py > /tmp/mock_server.log 2>&1 &
MOCK_PID=$!

echo "Mock server PID: $MOCK_PID"
sleep 3

# Check if server started
if ps -p $MOCK_PID > /dev/null; then
    echo "✅ Mock server running"
else
    echo "❌ Mock server failed to start"
    cat /tmp/mock_server.log
    exit 1
fi

echo ""
echo "Testing API endpoints..."
echo ""

# Test 1: Connect
echo "TEST 1: Connect to mock robot"
CONNECT_RESULT=$(curl -s "http://localhost:8080/api/connect?ip=127.0.0.1&serial_number=MOCK_12345" -X POST)
echo "$CONNECT_RESULT" | python3 -m json.tool
if echo "$CONNECT_RESULT" | grep -q '"success": true'; then
    echo "✅ Connect successful"
else
    echo "❌ Connect failed"
fi
echo ""

# Test 2: Get initial state
echo "TEST 2: Get initial state (should be ZERO_TORQUE)"
STATE_RESULT=$(curl -s "http://localhost:8080/api/state")
echo "$STATE_RESULT" | python3 -m json.tool
if echo "$STATE_RESULT" | grep -q 'ZERO_TORQUE'; then
    echo "✅ Initial state is ZERO_TORQUE"
else
    echo "❌ Unexpected initial state"
fi
echo ""

# Test 3: Transition to DAMP
echo "TEST 3: Transition ZERO_TORQUE → DAMP"
DAMP_RESULT=$(curl -s "http://localhost:8080/api/set_state?state_name=DAMP" -X POST)
echo "$DAMP_RESULT" | python3 -m json.tool
if echo "$DAMP_RESULT" | grep -q '"success": true'; then
    echo "✅ Transition to DAMP successful"
else
    echo "❌ Transition to DAMP failed"
fi
echo ""

# Test 4: Verify allowed transitions from DAMP
echo "TEST 4: Check allowed transitions from DAMP"
STATE_RESULT=$(curl -s "http://localhost:8080/api/state")
echo "$STATE_RESULT" | python3 -m json.tool
if echo "$STATE_RESULT" | grep -q 'START'; then
    echo "✅ START is in allowed transitions"
else
    echo "❌ START not in allowed transitions"
fi
echo ""

# Test 5: Invalid transition (should fail)
echo "TEST 5: Try invalid transition DAMP → RUN (should fail)"
INVALID_RESULT=$(curl -s "http://localhost:8080/api/set_state?state_name=RUN" -X POST)
echo "$INVALID_RESULT" | python3 -m json.tool
if echo "$INVALID_RESULT" | grep -q '"success": false'; then
    echo "✅ Invalid transition correctly rejected"
else
    echo "❌ Invalid transition was allowed (BUG!)"
fi
echo ""

# Test 6: Valid state chain DAMP → START → LOCK_STAND
echo "TEST 6: State chain DAMP → START → LOCK_STAND"
curl -s "http://localhost:8080/api/set_state?state_name=START" -X POST > /dev/null
sleep 0.5
WALK_RESULT=$(curl -s "http://localhost:8080/api/set_state?state_name=LOCK_STAND" -X POST)
echo "$WALK_RESULT" | python3 -m json.tool
if echo "$WALK_RESULT" | grep -q '"success": true'; then
    echo "✅ Reached WALK mode (LOCK_STAND)"
else
    echo "❌ Failed to reach WALK mode"
fi
echo ""

# Test 7: Movement in WALK mode
echo "TEST 7: Send movement command in WALK mode"
MOVE_RESULT=$(curl -s "http://localhost:8080/api/move" -X POST \
    -H "Content-Type: application/json" \
    -d '{"vx": 0.5, "vy": 0, "omega": 0}')
echo "$MOVE_RESULT" | python3 -m json.tool
if echo "$MOVE_RESULT" | grep -q '"success": true'; then
    echo "✅ Movement command accepted"
else
    echo "❌ Movement command failed"
fi
echo ""

# Test 8: Gesture in WALK mode  
echo "TEST 8: Send gesture command in WALK mode"
GESTURE_RESULT=$(curl -s "http://localhost:8080/api/gesture?gesture_name=wave" -X POST)
echo "$GESTURE_RESULT" | python3 -m json.tool
if echo "$GESTURE_RESULT" | grep -q '"success": true'; then
    echo "✅ Gesture command accepted"
else
    echo "❌ Gesture command failed"
fi
echo ""

# Test 9: Emergency stop from any state
echo "TEST 9: Emergency DAMP from LOCK_STAND"
DAMP_RESULT=$(curl -s "http://localhost:8080/api/set_state?state_name=DAMP" -X POST)
echo "$DAMP_RESULT" | python3 -m json.tool
if echo "$DAMP_RESULT" | grep -q '"success": true'; then
    echo "✅ Emergency DAMP successful"
else
    echo "❌ Emergency DAMP failed"
fi
echo ""

# Test 10: Discovery
echo "TEST 10: Robot discovery"
DISCOVER_RESULT=$(curl -s "http://localhost:8080/api/discover")
echo "$DISCOVER_RESULT" | python3 -m json.tool
if echo "$DISCOVER_RESULT" | grep -q 'MOCK_G1_TEST'; then
    echo "✅ Discovery successful"
else
    echo "❌ Discovery failed"
fi
echo ""

echo "=================================="
echo "📊 TEST SUMMARY"
echo "=================================="
echo "All API tests completed!"
echo ""
echo "🌐 UI Test:"
echo "1. Copy /root/G1/unitree_sdk2/g1_app/ui/index.html to /root/G1/unitree_sdk2/g1_app/ui/test_index.html"
echo "2. Edit line with localhost:8000 to localhost:8080"
echo "3. Open http://localhost:8080 in browser"
echo "4. Test state transitions with buttons"
echo ""
echo "📋 Server logs:"
echo "tail -f /tmp/mock_server.log"
echo ""
echo "🛑 Stop server:"
echo "kill $MOCK_PID"
echo ""
