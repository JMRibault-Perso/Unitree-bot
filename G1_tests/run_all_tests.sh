#!/bin/bash
#
# G1 Test Suite - Run All Tests
# Execute comprehensive test suite across all categories
#

set -e  # Exit on error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo ""
echo "=========================================="
echo " G1 Robot Test Suite"
echo "=========================================="
echo ""

# Function to run category tests
run_category() {
    category=$1
    echo -e "${BLUE}Testing: $category${NC}"
    echo "----------------------------------------"
    
    if [ -d "$category" ]; then
        # List available tests
        tests=$(find "$category" -name "*.py" -type f | sort)
        
        if [ -z "$tests" ]; then
            echo -e "${YELLOW}No tests found${NC}"
        else
            for test in $tests; do
                echo "  • $(basename $test)"
            done
        fi
    else
        echo -e "${RED}Directory not found: $category${NC}"
    fi
    
    echo ""
}

# Discovery check
echo -e "${BLUE}📡 Robot Discovery${NC}"
echo "----------------------------------------"
python3 utilities/discover_robot.py
if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Robot not found! Please check network connection.${NC}"
    echo ""
    exit 1
fi
echo ""

# Show available test categories
echo -e "${BLUE}📋 Available Test Categories${NC}"
echo "----------------------------------------"
echo ""

run_category "slam"
run_category "motion"
run_category "arm"
run_category "sensors"
run_category "utilities"

echo "=========================================="
echo ""
echo "To run specific tests:"
echo "  cd slam/ && python3 test_navigation_v2.py"
echo "  cd motion/ && python3 simple_control.py"
echo "  cd arm/ && python3 list_actions.py"
echo "  cd sensors/ && python3 monitor_lidar.py"
echo "  cd utilities/ && python3 monitor_telemetry.py"
echo ""
echo "For help on any test:"
echo "  python3 <test_name>.py --help"
echo ""
