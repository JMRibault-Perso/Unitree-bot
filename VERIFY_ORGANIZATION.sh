#!/bin/bash
set -e

echo "🔍 Verifying Unitree SDK2 Organization..."
echo ""

# Check 1: No test files in root
echo "✓ Check 1: No test files in root directory"
if find . -maxdepth 1 -name "test_*.py" -o -name "robot_test_helpers.py" 2>/dev/null | grep -q .; then
    echo "  ❌ FAILED: Test files found in root"
    exit 1
fi
echo "  ✅ PASSED: No test files in root"
echo ""

# Check 2: All test files in G1_tests
echo "✓ Check 2: All test files in G1_tests/"
TEST_COUNT=$(find G1_tests -maxdepth 1 -name "test_*.py" | wc -l)
if [ "$TEST_COUNT" -lt 10 ]; then
    echo "  ❌ FAILED: Expected 10+ test files, found $TEST_COUNT"
    exit 1
fi
echo "  ✅ PASSED: Found $TEST_COUNT test files in G1_tests/"
echo ""

# Check 3: robot_test_helpers.py in G1_tests
echo "✓ Check 3: robot_test_helpers.py location"
if [ ! -f "G1_tests/robot_test_helpers.py" ]; then
    echo "  ❌ FAILED: robot_test_helpers.py not found in G1_tests/"
    exit 1
fi
echo "  ✅ PASSED: robot_test_helpers.py in G1_tests/"
echo ""

# Check 4: Documentation structure
echo "✓ Check 4: Documentation structure"
REQUIRED_DIRS=(
    "docs"
    "docs/api"
    "docs/guides"
    "docs/reference"
    "docs/archived"
    "g1_app"
    "G1_tests"
    "slam_example"
)
for dir in "${REQUIRED_DIRS[@]}"; do
    if [ ! -d "$dir" ]; then
        echo "  ❌ FAILED: Directory '$dir' not found"
        exit 1
    fi
done
echo "  ✅ PASSED: All required directories present"
echo ""

# Check 5: Key documentation files
echo "✓ Check 5: Key documentation files"
REQUIRED_DOCS=(
    "docs/README.md"
    "docs/api/robot-discovery.md"
    "docs/guides/slam-navigation.md"
    "docs/guides/testing-guide.md"
    "docs/reference/project-structure.md"
)
for doc in "${REQUIRED_DOCS[@]}"; do
    if [ ! -f "$doc" ]; then
        echo "  ❌ FAILED: Documentation file '$doc' not found"
        exit 1
    fi
done
echo "  ✅ PASSED: All key documentation present"
echo ""

# Check 6: Centralized discovery module
echo "✓ Check 6: Centralized discovery API"
if [ ! -f "g1_app/utils/robot_discovery.py" ]; then
    echo "  ❌ FAILED: Centralized discovery not found"
    exit 1
fi
if ! grep -q "def discover_robot" g1_app/utils/robot_discovery.py; then
    echo "  ❌ FAILED: discover_robot() function not found"
    exit 1
fi
echo "  ✅ PASSED: Centralized discovery API present"
echo ""

# Check 7: SLAM examples moved
echo "✓ Check 7: SLAM examples in slam_example/"
REQUIRED_SLAM=(
    "slam_example/G1_SLAM_IMPLEMENTATION.py"
    "slam_example/build_room_map.py"
)
for file in "${REQUIRED_SLAM[@]}"; do
    if [ ! -f "$file" ]; then
        echo "  ❌ FAILED: SLAM file '$file' not found"
        exit 1
    fi
done
echo "  ✅ PASSED: SLAM examples present in slam_example/"
echo ""

# Check 8: Docs moved from root
echo "✓ Check 8: Documentation files moved from root"
MOVED_DOCS=(
    "docs/guides/3D_VIEWER_IMPLEMENTATION_GUIDE.md"
    "docs/guides/README_NAVIGATION_SYSTEM.md"
)
for file in "${MOVED_DOCS[@]}"; do
    if [ ! -f "$file" ]; then
        echo "  ❌ FAILED: Documentation file '$file' not found"
        exit 1
    fi
done
echo "  ✅ PASSED: All documentation files moved to docs/guides/"
echo ""

# Check 9: No orphaned files in root
echo "✓ Check 9: No orphaned Python files in root"
if [ -f "build_room_map.py" ] || [ -f "G1_SLAM_IMPLEMENTATION.py" ]; then
    echo "  ❌ FAILED: Python files still in root"
    exit 1
fi
echo "  ✅ PASSED: No orphaned Python files"
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ All organization checks PASSED!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📍 Key Locations:"
echo "   • Documentation:     docs/README.md"
echo "   • Tests:             G1_tests/test_*.py"
echo "   • Discovery API:     g1_app/utils/robot_discovery.py"
echo "   • Web Server:        g1_app/ui/web_server.py (port 3000)"
echo "   • SLAM Examples:     slam_example/"
echo "   • Moved Guides:      docs/guides/"
echo ""
