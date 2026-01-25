# G1 FSM State Investigation - FINDINGS

## Problem
Robot was reporting fsm_id=801 which was not in our FSM_STATES enum. Both APIs 7001 and 7002 return 801 or 0, never the expected states like LOCK_STAND (500).

## Root Cause FOUND
**801 is a valid G1 FSM state!** It's called "Expert Mode" or "Expert Interface"

## Evidence
From `/root/G1/unitree_sdk2/include/unitree/robot/g1/arm/g1_arm_action_error.hpp`:
```cpp
// The actions are only supported in fsm id {500, 501, 801};
// You can subscribe the topic rt/sportmodestate to check the fsm id.
// And in the state 801, the actions are only supported in the fsm mode {0, 3}.
// See https://support.unitree.com/home/en/G1_developer/sport_services_interface#Expert%20interface
```

From `example/g1/high_level/g1_arm_action_example.cpp`:
```cpp
case UT_ROBOT_ARM_ACTION_ERR_INVALID_FSM_ID:
    std::cout << "The actions are only supported in fsm id {500, 501, 801}" << std::endl;
    std::cout << "You can subscribe the topic rt/sportmodestate to check the fsm id." << std::endl;
    std::cout << "And in the state 801, the actions are only supported in the fsm mode {0, 3}." << std::endl;
```

## G1 FSM States (Updated)

### Basic States (from original SDK)
- 0: ZERO_TORQUE
- 1: DAMP
- 2: SQUAT
- 3: SIT
- 4: STAND_UP
- 200: START (Ready/Standing)

### Locomotion States
- **500: LOCK_STAND** (Walk/Run Mode - basic)
- **501: LOCK_STAND_ADVANCED** (Walk/Run Mode - advanced, NEW!)
- 706: SQUAT_TO_STAND
- 707: STAND_TO_SQUAT
- 708: LYING_STAND

### Expert States (NEW!)
- **801: EXPERT_MODE** (Expert interface, supports arm actions)
  - Within fsm_id=801, there are sub-modes via fsm_mode:
    - fsm_mode=0: Expert mode, arm actions allowed
    - fsm_mode=3: Expert mode, arm actions allowed
    - Other fsm_modes: Not documented

## Test Results

### rt/sportmodestate Subscription - ✅ WORKING!
```python
{
  "type": "msg",
  "topic": "rt/lf/sportmodestate",
  "data": {
    "fsm_id": 801,      # EXPERT_MODE
    "fsm_mode": 0,      # Arm actions allowed
    "task_id": 4,
    "task_time": 0
  }
}
```

**Received 150 updates in 10 seconds** - subscription is reliable!

### API Testing Results
- API 7001 (GET_FSM_ID): Returns 801 ✓ (was thought to be wrong, but it's correct!)
- API 7002 (GET_FSM_MODE): Returns 0 ✓ (this is the fsm_mode within state 801!)

## Correct State Detection Method
Subscribe to `rt/lf/sportmodestate` and read `fsm_id` field:
```python
conn.datachannel.pub_sub.subscribe("rt/lf/sportmodestate", callback)

def callback(data):
    fsm_id = data['data']['fsm_id']      # 801 = EXPERT_MODE
    fsm_mode = data['data']['fsm_mode']  # 0 or 3 = arm actions allowed
```

## Action Required
1. Add FSM state 801 (EXPERT_MODE) to UI
2. Add FSM state 501 (LOCK_STAND_ADVANCED) to UI
3. Update state machine transitions to include 801 and 501
4. Fix robot_controller.py to use rt/lf/sportmodestate subscription (already works!)
5. Update UI to show both fsm_id and fsm_mode for state 801
