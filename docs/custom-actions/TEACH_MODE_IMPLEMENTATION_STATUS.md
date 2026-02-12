# Teach Mode Implementation Status (Confirmed Sources Only)

## Sources

This status file is based only on:
- Phone logs (WebRTC JSON on `rt/api/arm/request`)
- Unitree Arm Action Service (SDK, EDU models)

## Phone-Log Confirmed APIs (G1 Air)

- **7107**: GetActionList
- **7108**: ExecuteCustomAction (by `action_name`)
- **7109**: RenameAction (`pre_name`, `new_name`)
- **7110**: RecordCustomAction (start/keepalive/stop)
- **7113**: StopCustomAction

## Current Web App Endpoints

```
GET  /api/custom_action/robot_list
POST /api/custom_action/execute?action_name=NAME
POST /api/custom_action/stop
POST /api/teach/record/start
POST /api/teach/record/stop
POST /api/teach/rename
```

## UI Status

- Custom Actions panel includes record controls, action list, play, rename, and stop.
- Recording enforces a 20-second max duration.

## Notes

- This document intentionally omits any packet-level or unverified commands.
