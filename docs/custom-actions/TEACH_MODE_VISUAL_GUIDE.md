# Teach Mode Visual Guide (Confirmed Sources Only)

## UI Flow

```
[Custom Actions]
   ├─ Start Recording
   ├─ Move arms (<= 20s)
   ├─ Stop & Save
   ├─ Rename (optional)
   └─ Play
```

## HTTP Flow

```
POST /api/teach/record/start
POST /api/teach/record/stop
POST /api/teach/rename
POST /api/custom_action/execute?action_name=NAME
POST /api/custom_action/stop
GET  /api/custom_action/robot_list
```
