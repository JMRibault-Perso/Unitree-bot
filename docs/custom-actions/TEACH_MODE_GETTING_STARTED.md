# Teach Mode Getting Started (Confirmed Sources Only)

This guide only uses phone logs and SDK documentation.

## Confirmed APIs (Phone Logs)

Commands are sent to `rt/api/arm/request`:
- **7107**: GetActionList
- **7108**: ExecuteCustomAction (by `action_name`)
- **7109**: RenameAction (`pre_name`, `new_name`)
- **7110**: RecordCustomAction (start/keepalive/stop)
- **7113**: StopCustomAction

## Start Recording (UI)

1. Open **Custom Actions**.
2. Click **Start**.
3. Move the arms for up to **20 seconds**.
4. Click **Stop & Save**.
5. (Optional) **Rename** the new action.

## Start Recording (HTTP)

```
POST /api/teach/record/start
POST /api/teach/record/stop
POST /api/teach/rename
```

## Play an Action

```
POST /api/custom_action/execute?action_name=YOUR_ACTION
POST /api/custom_action/stop
```

## List Actions

```
GET /api/custom_action/robot_list
```
