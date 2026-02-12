# Teach Mode Summary (Confirmed Sources Only)

This summary is based only on:
- Phone logs (WebRTC JSON on `rt/api/arm/request`)
- Unitree Arm Action Service (SDK, EDU models)

## Confirmed APIs (G1 Air)

- **7107**: GetActionList
- **7108**: ExecuteCustomAction (by `action_name`)
- **7109**: RenameAction (`pre_name`, `new_name`)
- **7110**: RecordCustomAction (start/keepalive/stop)
- **7113**: StopCustomAction

## Web App Endpoints (Current Implementation)

```
GET  /api/custom_action/robot_list
POST /api/custom_action/execute?action_name=NAME
POST /api/custom_action/stop
POST /api/teach/record/start
POST /api/teach/record/stop
POST /api/teach/rename
```

## Recording Flow (Phone Logs)

1. Start recording with API 7110 and a non-empty `action_name`.
2. Send keepalive packets using API 7110 with empty `action_name`.
3. Stop recording with API 7110 and empty `action_name`.
4. Confirm the action appears in the list (API 7107).
5. Play action by name (API 7108).
