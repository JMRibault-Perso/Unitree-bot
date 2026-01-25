#include <iostream>
#include <unitree/robot/channel/channel_subscriber.hpp>
#include <unitree/idl/hg/LowState_.hpp>

using namespace unitree::robot;

void LowStateHandler(const void* msg)
{
    const unitree_hg::msg::dds_::LowState_* state = (const unitree_hg::msg::dds_::LowState_*)msg;
    
    std::cout << "\n=== Received Robot State ===" << std::endl;
    std::cout << "IMU Temperature: " << state->imu_state().temperature() << std::endl;
    std::cout << "Battery Voltage: " << state->battery_state().battery_voltage() << "V" << std::endl;
    std::cout << "===========================\n" << std::endl;
}

int main(int argc, char** argv)
{
    std::string networkInterface = "";
    
    if (argc > 1) {
        networkInterface = argv[1];
    }
    
    std::cout << "=== G1 Robot State Listener ===" << std::endl;
    std::cout << "Listening for robot broadcasts on topic: rt/lowstate" << std::endl;
    if (!networkInterface.empty()) {
        std::cout << "Network Interface: " << networkInterface << std::endl;
    }
    std::cout << "Waiting for messages...\n" << std::endl;
    
    // Initialize DDS with domain 0
    ChannelFactory::Instance()->Init(0, networkInterface);
    
    // Subscribe to low-level state topic
    ChannelSubscriber<unitree_hg::msg::dds_::LowState_> subscriber("rt/lowstate");
    subscriber.InitChannel(LowStateHandler);
    
    // Keep listening
    while (true) {
        sleep(1);
    }
    
    return 0;
}
