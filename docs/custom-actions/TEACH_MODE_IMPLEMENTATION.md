# Teach Mode Recording (Confirmed Sources Only)

This document only includes information verified by:
- Phone logs (WebRTC JSON on `rt/api/arm/request`)
- Unitree Arm Action Service (SDK, EDU models)

## Phone-Log Confirmed APIs (G1 Air)

All commands are sent to `rt/api/arm/request`:
- **7107**: GetActionList
- **7108**: ExecuteCustomAction (by `action_name`)
- **7109**: RenameAction (`pre_name`, `new_name`)
- **7110**: RecordCustomAction (start/keepalive/stop)
- **7113**: StopCustomAction

## Web App Endpoints (Current Implementation)

These are the app endpoints that map to the confirmed APIs above:

```
GET  /api/custom_action/robot_list
POST /api/custom_action/execute?action_name=NAME
POST /api/custom_action/stop
POST /api/teach/record/start
POST /api/teach/record/stop
POST /api/teach/rename
```

## Recording Flow (Phone Logs)

1. **Start recording**: API 7110 with a non-empty `action_name`.
2. **Keepalive**: API 7110 with empty `action_name` about once per second.
3. **Stop recording**: API 7110 with empty `action_name`.
4. **List actions**: API 7107 to confirm the new action.
5. **Play action**: API 7108 with `action_name`.
