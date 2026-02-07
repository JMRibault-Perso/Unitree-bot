# Arm Control Tests

Arm control, teach mode, and action playback tests.

## 🗂️ Available Tests

### Teach Mode
- `enable_teach_mode.py` - Enter/exit zero-gravity teach mode
- `record_action.py` - Record arm movements as custom actions
- `test_playback.py` - Play recorded actions

### Action Management
- `list_actions.py` - Show all available actions (preset + custom)
- `delete_action.py` - Delete custom actions
- `rename_action.py` - Rename custom actions

### Manual Control
- `manual_arm_control.py` - Direct arm position control (advanced)

## 🎯 Teach Mode Workflow

1. **Enable Teach Mode** (API 7110)
   ```bash
   python3 enable_teach_mode.py
   ```

2. **Physically move arms** to desired positions

3. **Record Action** (API 7109)
   ```bash
   python3 record_action.py --name "wave_gesture"
   ```

4. **Play Action** (API 7108)
   ```bash
   python3 test_playback.py --action "wave_gesture"
   ```

5. **Disable Teach Mode** (API 7111)
   ```bash
   python3 enable_teach_mode.py --disable
   ```

## 📝 API Reference

| API ID | Command | Description |
|--------|---------|-------------|
| 7107 | GET_ACTION_LIST | List all available actions |
| 7108 | EXECUTE_CUSTOM_ACTION | Play recorded action |
| 7109 | START_RECORDING | Begin recording arm positions |
| 7110 | ENABLE_TEACH_MODE | Enter zero-gravity mode |
| 7111 | DISABLE_TEACH_MODE | Exit teach mode |
| 7112 | DELETE_ACTION | Remove custom action |
| 7113 | STOP_CUSTOM_ACTION | Emergency stop during playback |
| 7114 | RENAME_ACTION | Rename custom action |

## 🚨 Important Notes

- **FSM requirement**: Gestures work in states 500/501 or 801 with mode 0/3
- **Recording duration**: 1-60 seconds typical
- **Action names**: Max 32 characters, alphanumeric + underscore
- **Teach mode safety**: Robot arms will go limp - support them!
- **Emergency stop**: API 7113 or disable teach mode

## 🔍 Troubleshooting

**"Action execution failed (7404)"**
- Wrong FSM state - check robot is in 500/501 or 801
- Use motion tests to set correct FSM state first

**"Teach mode not responding"**
- Verify API 7110 returned success
- Check arms can move freely (no mechanical blocks)
- Disable and re-enable teach mode

**"Recording failed"**
- Robot must be in teach mode (API 7110)
- Ensure valid action name (no spaces/special chars)
- Check storage space on robot

## 📚 Examples

### Record "pickup" gesture
```bash
python3 enable_teach_mode.py
# Move arms to pickup position
python3 record_action.py --name "pickup" --duration 3
python3 enable_teach_mode.py --disable
```

### Play all custom actions
```bash
python3 list_actions.py  # Get list
python3 test_playback.py --action "wave_gesture"
python3 test_playback.py --action "pickup"
```
