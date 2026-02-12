# Teach Mode Quick Start (Confirmed Sources Only)

## UI Workflow

1. Open **Custom Actions**.
2. Click **Start** to begin recording.
3. Move the arms for up to **20 seconds**.
4. Click **Stop & Save**.
5. (Optional) **Rename** the action.
6. Click **Play** to test.

## HTTP Workflow

```
POST /api/teach/record/start
POST /api/teach/record/stop
POST /api/teach/rename
POST /api/custom_action/execute?action_name=NAME
POST /api/custom_action/stop
GET  /api/custom_action/robot_list
```
