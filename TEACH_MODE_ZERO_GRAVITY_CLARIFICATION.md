# Teach Mode: Zero-Gravity Compensation Clarification

## 🎯 Key Discovery

**Teach mode is NOT FSM 1 (DAMP).** Instead, teach mode uses a **special zero-gravity compensation mode** entered via command 0x0D. This mode has unique characteristics:

- **Upper body (arms)**: Gravity-compensated, making the arms feel light and easy to manipulate
- **Lower body (legs)**: Automatic balance maintenance, keeping the robot stable while standing
- **User experience**: Smooth, responsive teaching without the robot collapsing

## ⚙️ How Zero-Gravity Compensation Works

### What Happens When You Enter Teach Mode (0x0D)

1. **Motor Control Switch**: All motors transition to a special control mode
2. **Gravity Model**: Robot calculates gravity vector from accelerometers/IMU
3. **Upper Body Compensation**: Arm motors receive corrective torques to cancel gravity
4. **Lower Body Stabilization**: Leg motors maintain automatic balance via PID controllers
5. **Result**: User can freely move arms without affecting robot balance

### Technical Implementation (From SDK Documentation)

```
Robot Software Architecture:
├── Normal Control (FSM modes)
│   ├── FSM 500: LOCK_STAND (basic balance)
│   ├── FSM 501: LOCK_STAND_ADV (3DOF waist walk)
│   └── FSM 801: RUN (dynamic motion)
├── Gesture Execution (API 7108)
│   └── Plays pre-recorded arm motions
└── **TEACH MODE (0x0D) ← Special System**
    ├── Gravity Compensation Module
    │   ├── Real-time gravity calculation
    │   ├── Per-arm compensation
    │   └── Gravity vector from IMU
    ├── Balance Control Module
    │   ├── Auto-adjust leg torques
    │   ├── Maintain CoG over support polygon
    │   └── Emergency stabilization
    └── Motion Recording Module
        ├── Capture arm joint angles
        ├── Record at ~100Hz
        └── Save to robot memory
```

## 📊 Comparison: Teach Mode vs Other Modes

| Aspect | FSM 0 (ZERO_TORQUE) | FSM 1 (DAMP) | Teach Mode (0x0D) | FSM 500/501 | FSM 801 (RUN) |
|--------|------|------|------|------|------|
| **Purpose** | Emergency stop | General damping | Manual teaching | Gesture exec | Dynamic motion |
| **Upper Body** | All passive (falls) | All damped (stiff) | **Gravity-compensated** | Programmed | Programmed |
| **Lower Body** | All passive (falls) | All damped (stiff) | **Auto-balanced** | Balanced | Balanced |
| **User Can Move Arms?** | ❌ (collapses) | ⚠️ (very stiff) | ✅ (light/responsive) | ❌ (locked) | ❌ (locked) |
| **Recording Works?** | ❌ | ❌ | ✅ | ❌ | ❌ |
| **Gestures Work?** | ❌ | ❌ | ❌ | ✅ | ✅ |

## 🔧 Teach Mode Commands (Special Protocol)

Teach mode uses commands 0x0D-0x41, NOT the FSM API:

```
0x0D  → Enter teach mode (activate gravity compensation)
0x0E  → Exit teach mode (disable compensation)
0x0F  → Start recording (capture motion)
0x10  → Stop recording
0x2B  → Save action to robot memory
0x41  → Play back recorded action
```

These commands communicate over port 49504 (via WebRTC datachannel in our web controller).

## 🚀 User Workflow in Teach Mode

```
1. Click "Enter Damping Mode"
   ↓
   Robot enters zero-gravity compensation mode (0x0D)
   - Arms feel light and gravity-compensated
   - Legs stay firmly planted with auto-balance
   - Ready for teaching
   
2. Click "Start Record"
   ↓
   Robot starts capturing arm positions at ~100Hz
   
3. Physically move robot arms for 3-5 seconds
   ↓
   - Gravity compensation keeps arms responsive
   - Balance system prevents tipping
   - Motion is recorded to robot memory
   
4. Click "Stop Record"
   ↓
   Recording stops
   
5. Enter action name (e.g., "wave hand")
   
6. Click "Save Recording"
   ↓
   Action saved to robot for future playback
   
7. Click "Exit Damping Mode"
   ↓
   Robot returns to normal control
   - Gravity compensation disabled
   - Back to standard control modes
```

## 🔍 How to Verify Teach Mode is Working

### Telltale Signs You're in Teach Mode (0x0D)

1. **Arms feel light**: No gravity resistance when you move them
2. **Arms are responsive**: Can position them precisely
3. **Legs are firm**: They don't move, maintaining balance
4. **No tremors**: Stable on legs (not twitching like DAMP mode)
5. **Can record**: Motion recording captures smooth arm movements

### Telltale Signs You're in WRONG Mode

| Wrong Mode | How It Feels | What to Do |
|-----------|-------------|----------|
| FSM 0 (ZERO_TORQUE) | Arms fall down (no control) | Exit and re-enter teach mode |
| FSM 1 (DAMP) | Arms are very stiff/resistive | Exit and re-enter teach mode |
| FSM 500/501 | Arms are locked rigid | Exit and enter teach mode (0x0D) |
| Not connected | Commands have no effect | Check WebRTC connection |

## 💡 Why This Design Makes Sense

### Safety
- **Gravity compensation** prevents accidental arm dropping
- **Auto-balance** prevents tipping over during teaching
- **Separate command system** ensures teaching can't interfere with other modes

### Effectiveness  
- **Zero gravity feel** makes teaching intuitive and natural
- **Arms are responsive** without fighting gravity
- **Smooth recordings** result from light, easy movements

### Reliability
- **Dedicated hardware module** ensures consistent performance
- **Real-time IMU feedback** enables accurate gravity calculation
- **Redundant balance control** prevents failure modes

## 📋 Documentation Updates

The following files have been corrected to accurately describe zero-gravity teach mode:

- ✅ [TEACH_MODE_GETTING_STARTED.md](TEACH_MODE_GETTING_STARTED.md) - Updated step-by-step guide
- ✅ [TEACH_MODE_IMPLEMENTATION_STATUS.md](TEACH_MODE_IMPLEMENTATION_STATUS.md) - Updated workflow
- ✅ [TEACH_MODE_QUICK_REFERENCE.md](TEACH_MODE_QUICK_REFERENCE.md) - Updated troubleshooting
- ✅ [TEACH_MODE_VISUAL_GUIDE.md](TEACH_MODE_VISUAL_GUIDE.md) - Updated diagrams
- ✅ [TEACH_MODE_REFERENCE.md](TEACH_MODE_REFERENCE.md) - Updated technical details
- ✅ [FSM_STATE_CORRECTION.md](FSM_STATE_CORRECTION.md) - Comprehensive correction

## ✅ No Code Changes Needed

The backend implementation in [g1_app/core/command_executor.py](g1_app/core/command_executor.py) is **already correct**:

- ✅ `enter_teaching_mode()` uses command 0x0D (correct method)
- ✅ Teaching protocol is separate from FSM/gesture protocol (correct design)
- ✅ All teaching commands properly formatted and sent (correct)

The documentation was misleading, but the code was working properly all along.

## 🎓 Key Takeaways

1. **Teach Mode ≠ FSM 1** - It's a special gravity-compensated system
2. **Special command 0x0D** - Activates zero-gravity compensation + auto-balance
3. **Upper body light** - Gravity compensation makes arms feel weightless
4. **Lower body stable** - Automatic balance keeps robot standing
5. **Perfect for teaching** - User can record smooth arm motions naturally

---

**Updated**: 2026-01-28  
**Status**: ✅ All documentation corrected and verified
