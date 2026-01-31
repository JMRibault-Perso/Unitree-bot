# Teach Mode: Quick Reference

## 🎯 What is Teach Mode?

**Special zero-gravity compensation mode** (not FSM 1):
- Gravity-compensates upper body arms → **feel light and easy**
- Auto-balances lower body legs → **prevents tipping**
- Entered via command **0x0D** (not FSM API)

## 🚀 How to Use Teach Mode

```
1. Click "Enter Damping Mode" button
   └─ Robot enters zero-gravity mode
   
2. Arms should feel light/responsive
   └─ Verify working properly
   
3. Click "Start Record" button
   └─ Begin capturing motion
   
4. Move robot arms for 3-5 seconds
   └─ Smooth, natural motions recorded
   
5. Click "Stop Record" button
   └─ Recording complete
   
6. Enter action name
   └─ Give meaningful name (e.g., "wave")
   
7. Click "Save Recording"
   └─ Saved to robot memory
   
8. Click "Exit Damping Mode"
   └─ Return to normal control
```

## ✅ Is My Teach Mode Working?

### Green Lights (Working Correctly)
- ✅ Arms feel light when moved
- ✅ Can position arms precisely
- ✅ Legs stay planted (no wobble)
- ✅ Recording captures smooth motion
- ✅ Saved actions play back correctly

### Red Lights (Not Working)
- ❌ Arms won't move / very stiff → Exit and re-enter
- ❌ Robot tips over → Not in teach mode (re-enter)
- ❌ Recording doesn't save → Verify action name is set
- ❌ "Not connected" → Check WebRTC connection

## 🔧 Technical Summary

| Feature | Detail |
|---------|--------|
| **Entry Command** | 0x0D (special protocol) |
| **Exit Command** | 0x0E |
| **Record Command** | 0x0F |
| **Play Command** | 0x41 |
| **Protocol** | Not FSM API - separate system |
| **Port** | 49504 (via WebRTC datachannel) |
| **Feedback** | Arms gravity-compensated, legs auto-balanced |

## ❓ Common Questions

**Q: Why do the arms feel light?**
A: Zero-gravity compensation cancels gravity in real-time, making them weightless.

**Q: Why don't the legs move?**
A: Auto-balance system maintains standing posture while you move arms.

**Q: Is this FSM 1 (DAMP)?**
A: No! FSM 1 is general damping. Teach mode is special gravity-compensated mode (0x0D).

**Q: What if the robot feels stiff?**
A: You're probably in wrong mode. Exit teach mode and re-enter.

**Q: Can I use teach mode to control the robot's body?**
A: No - it's designed for arm/hand teaching only. Legs auto-balance.

## 🚨 Safety Notes

⚠️ **Safety Critical:**
- Teach mode disables normal motor damping
- Robot relies on auto-balance system
- Keep clear of obstacles during teaching
- Don't let robot fall during entry/exit
- Always exit teach mode before power-off

## 📚 For More Details

See: [TEACH_MODE_ZERO_GRAVITY_CLARIFICATION.md](TEACH_MODE_ZERO_GRAVITY_CLARIFICATION.md)

---

**Quick Start**: Click "Enter Damping Mode" → Move arms → "Start Record" → Position → "Stop Record" → Save
