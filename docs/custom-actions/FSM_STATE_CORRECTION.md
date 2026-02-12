# Teach Mode Clarification: Recording vs FSM

## What Is Confirmed

- Teach mode recording uses `rt/api/arm/request` with API IDs 7107, 7108, 7109,
  7110, 7113 (from phone logs).
- The SDK Arm Action Service documents `ExecuteAction(action_id)`,
  `ExecuteAction(action_name)`, `StopCustomAction()`, and `GetActionList()` for
  EDU models.

## Practical Guidance

- Use API 7110 to start/stop recording.
- Use API 7107 to list actions, 7108 to execute, 7109 to rename, and 7113 to stop
  playback.
