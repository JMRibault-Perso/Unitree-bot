#!/bin/bash
echo "=== TEST 1: Connect ==="
curl -s -X POST "http://localhost:8080/api/connect?ip=127.0.0.1&serial_number=MOCK_TEST" | python3 -m json.tool
echo ""

echo "=== TEST 2: Get State (should be ZERO_TORQUE) ==="
curl -s "http://localhost:8080/api/state" | python3 -m json.tool
echo ""

echo "=== TEST 3: Transition to DAMP ==="
curl -s -X POST "http://localhost:8080/api/set_state?state_name=DAMP" | python3 -m json.tool
echo ""

echo "=== TEST 4: Get State (should be DAMP with allowed transitions) ==="
curl -s "http://localhost:8080/api/state" | python3 -m json.tool
echo ""

echo "=== TEST 5: Try invalid transition DAMP → RUN (should fail) ==="
curl -s -X POST "http://localhost:8080/api/set_state?state_name=RUN" | python3 -m json.tool
echo ""

echo "=== TEST 6: Valid chain DAMP → START → LOCK_STAND ==="
curl -s -X POST "http://localhost:8080/api/set_state?state_name=START" | python3 -m json.tool
sleep 0.5
curl -s -X POST "http://localhost:8080/api/set_state?state_name=LOCK_STAND" | python3 -m json.tool
echo ""

echo "=== TEST 7: Get State (should be LOCK_STAND) ==="
curl -s "http://localhost:8080/api/state" | python3 -m json.tool
echo ""

echo "=== TEST 8: Emergency DAMP from LOCK_STAND ==="
curl -s -X POST "http://localhost:8080/api/set_state?state_name=DAMP" | python3 -m json.tool
echo ""

echo "=== All tests complete! ==="
