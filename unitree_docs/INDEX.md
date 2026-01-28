# Unitree G1 SDK Documentation Index

**Scraped:** 2025-01-25  
**Total Documents:** 43  
**Total Images:** 98  

---

## Quick Start
- [About G1](about-G1.md) - Overview of the G1 robot
- [Quick Start](quick-start.md) - Getting started guide
- [Operational Guidance](Operational-guidance.md) - Basic operations
- [Remote Control](remote-control.md) - Remote control usage
- [Application Development](application-development.md) - Development overview

## SDK Basics
- [SDK Overview](sdk-overview.md) - SDK introduction
- [Architecture Description](architecture-description.md) - System architecture
- [Get SDK](get-sdk.md) - Installation instructions
- [Quick Development](quick-development.md) - Fast setup guide

## Basic Motion Control
- [Basic Motion Development](basic-motion-development.md) - Motion control basics
- [Basic Motion Routine](basic-motion-routine.md) - Motion examples
- [Joint Motor Sequence](joint-motor-sequence.md) - Motor configuration
- [Remote Control Data](remote-control-data.md) - Control data structures

## Services & Interfaces
- [Services Interface](services-interface.md) - Overview of services
- [DDS Services Interface](dds-services-interface.md) - **DDS communication (KEY)**
- [Robot State Client Interface](robot-state-client-interface.md) - State monitoring
- [Basic Services Interface](basic-services-interface.md) - Core services
- [Sport Services Interface](sport-services-interface.md) - Movement APIs
- [Motion Switcher Service Interface](motion-witcher-service-interface.md) - Mode switching
- [Odometer Service Interface](odometer-service-interface.md) - Position tracking
- [VuiClient Service](VuiClient-Service.md) - Voice control
- [LiDAR Services Interface](lidar-services-interface.md) - LiDAR integration
- [SLAM Navigation Services Interface](slam-navigation-services-interface.md) - Navigation

## High-Level Motion Development
- [High Motion Development](high-motion-development.md) - Advanced control
- [RPC Routine](rpc-routine.md) - Remote procedure calls
- [Arm Control Routine](arm-control-routine.md) - **Arm control (KEY)**
- [Arm Action Interface](arm-action-interface.md) - **Arm gestures (KEY)**
- [RL Control Routine](rl-control-routine.md) - Reinforcement learning

## Dexterous Hands
- [Dexterous Hand](dexterous-hand.md) - Hand overview
- [Inspire FTP Dexterity Hand](inspire-ftp-dexterity-hand.md) - FTP hand SDK
- [Inspire DFX Dexterous Hand](inspire-dfx-dexterous-hand.md) - DFX hand SDK
- [Brainco Hand](brainco-hand.md) - Brainco integration

## Communication & Integration
- [ROS2 Communication Routine](ros2-communication-routine.md) - ROS2 bridge
- [DDS Communication Routine](dds-communication-routine.md) - DDS examples

## Hardware & Sensors
- [Waist Fastener](waist-fastener.md) - Mechanical configuration
- [LiDAR Instructions](lidar-Instructions.md) - LiDAR setup
- [Depth Camera Instruction](depth-camera-instruction.md) - Camera usage

## Voice & Audio
- [Voice Assistant Instructions](voice-assistant-instructions.md) - Voice control
- [Audio Playback](audio-playback.md) - Audio features

## Debugging & Troubleshooting
- [Debugging Specification](debugging-specification.md) - Debug guide
- [FAQ](FAQ.md) - **Frequently asked questions (KEY)**
- [Common Mistakes and Definitions](common-istakes-and-definitions.md) - Error reference

## More Resources
- [More Cases](more-cases.md) - Example projects

---

## Key Documents for G1 Air Web Controller Development

Based on your current project (web-based G1 Air controller), prioritize these documents:

1. **[DDS Services Interface](dds-services-interface.md)** - Core communication protocol
2. **[Arm Action Interface](arm-action-interface.md)** - Gesture/action control
3. **[Sport Services Interface](sport-services-interface.md)** - Movement control
4. **[Robot State Client Interface](robot-state-client-interface.md)** - State monitoring
5. **[FAQ](FAQ.md)** - Troubleshooting SDK/DDS issues
6. **[Basic Motion Routine](basic-motion-routine.md)** - Motion control examples

## Usage Tips

- All images are stored in `images/` directory
- Documents are in Markdown format for easy viewing
- Use `grep -r "search term" *.md` to search across all docs
- FSM mode details: Check sport-services-interface.md for mode switching
- Battery monitoring: Check robot-state-client-interface.md for BMS data
- Custom actions: Check arm-action-interface.md for ExecuteCustomAction API
