/*
 * Quick command-line tool to test G1 arm action APIs
 * Tests documented and undocumented APIs without changing robot state
 */

#include <iostream>
#include <unistd.h>
#include <unitree/robot/channel/channel_publisher.hpp>
#include <unitree/robot/channel/channel_subscriber.hpp>
#include <unitree/robot/g1/arm/g1_arm_action_client.hpp>

using namespace unitree::robot;
using namespace unitree::robot::g1;

// Extended client to expose Call() for testing
class TestableArmActionClient : public G1ArmActionClient {
public:
    int32_t TestAPI(int32_t api_id, const std::string& parameter, std::string& data) {
        return Call(api_id, parameter, data);
    }
};

void TestGetActionList(G1ArmActionClient& client) {
    std::cout << "\n========================================" << std::endl;
    std::cout << "Testing API 7107: GET_ACTION_LIST" << std::endl;
    std::cout << "========================================" << std::endl;
    
    std::string action_list;
    int32_t ret = client.GetActionList(action_list);
    
    std::cout << "Return code: " << ret << std::endl;
    if (ret == 0) {
        std::cout << "Success! Action list data:" << std::endl;
        std::cout << action_list << std::endl;
    } else {
        std::cout << "Failed with error code: " << ret << std::endl;
    }
}

void TestUndocumentedAPI(TestableArmActionClient& client, int32_t api_id, const std::string& name, const std::string& parameter = "{}") {
    std::cout << "\n========================================" << std::endl;
    std::cout << "Testing API " << api_id << ": " << name << std::endl;
    std::cout << "========================================" << std::endl;
    std::cout << "Parameter: " << parameter << std::endl;
    
    std::string data;
    int32_t ret = client.TestAPI(api_id, parameter, data);
    
    std::cout << "Return code: " << ret << std::endl;
    if (ret == 0) {
        std::cout << "Success! Response data:" << std::endl;
        std::cout << (data.empty() ? "(empty)" : data) << std::endl;
    } else {
        std::cout << "Failed with error code: " << ret << std::endl;
        if (ret == 3104) {
            std::cout << "  (Error 3104 = API timeout or not available)" << std::endl;
        } else if (ret == 7404) {
            std::cout << "  (Error 7404 = Invalid FSM state)" << std::endl;
        }
    }
}

int main(int argc, char** argv) {
    std::cout << "G1 Arm Action API Test Tool" << std::endl;
    std::cout << "===========================" << std::endl;
    
    if (argc > 1 && std::string(argv[1]) == "--help") {
        std::cout << "\nUsage: " << argv[0] << " [network_interface]" << std::endl;
        std::cout << "\nTests various arm action APIs without changing robot state." << std::endl;
        std::cout << "Safe to run while robot is in any mode." << std::endl;
        return 0;
    }

    std::string network_interface = (argc > 1) ? argv[1] : "eth0";
    std::cout << "Network interface: " << network_interface << std::endl;

    // Initialize DDS
    ChannelFactory::Instance()->Init(0, network_interface);
    
    // Create and initialize arm action client
    TestableArmActionClient arm_client;
    arm_client.SetTimeout(5.0f);
    arm_client.Init();
    
    std::cout << "\nWaiting for connection to robot..." << std::endl;
    sleep(2);
    
    // Test documented APIs first
    std::cout << "\n╔════════════════════════════════════════╗" << std::endl;
    std::cout << "║   TESTING DOCUMENTED APIs (7106-7108) ║" << std::endl;
    std::cout << "╚════════════════════════════════════════╝" << std::endl;
    
    TestGetActionList(arm_client);
    
    // Test the mysterious APIs 7109-7112
    std::cout << "\n\n╔════════════════════════════════════════╗" << std::endl;
    std::cout << "║  TESTING UNDOCUMENTED APIs (7109-7112) ║" << std::endl;
    std::cout << "╚════════════════════════════════════════╝" << std::endl;
    
    TestUndocumentedAPI(arm_client, 7109, "START_RECORD_ACTION (hypothesis)", "{}");
    sleep(1);
    
    TestUndocumentedAPI(arm_client, 7110, "STOP_RECORD_ACTION (hypothesis)", "{}");
    sleep(1);
    
    TestUndocumentedAPI(arm_client, 7111, "SAVE_RECORDED_ACTION (hypothesis)", R"({"action_name":"test_action"})");
    sleep(1);
    
    TestUndocumentedAPI(arm_client, 7112, "DELETE_ACTION (hypothesis)", R"({"action_name":"test_action"})");
    
    std::cout << "\n\n========================================" << std::endl;
    std::cout << "Testing complete!" << std::endl;
    std::cout << "========================================" << std::endl;
    
    std::cout << "\nSummary:" << std::endl;
    std::cout << "- If API returns 0: API exists and succeeded" << std::endl;
    std::cout << "- If API returns 3104: API timeout (likely doesn't exist)" << std::endl;
    std::cout << "- If API returns 7404: API exists but wrong FSM state" << std::endl;
    std::cout << "- Other error codes: Check SDK documentation" << std::endl;
    
    return 0;
}
