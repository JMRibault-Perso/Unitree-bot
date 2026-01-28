# Multimedia Features Implementation

## Overview

Added comprehensive multimedia support to the G1 web controller:
- **Audio Control**: Text-to-speech, volume control, RGB LED control
- **Speech Recognition**: Real-time ASR (Automatic Speech Recognition)
- **LiDAR Support**: Point cloud data subscription
- **Video Streaming**: WebRTC video track (framework ready)

## New Files Created

### 1. `g1_app/core/audio_client.py`
Audio control client based on VuiClient Service from SDK.

**Features:**
- Text-to-speech (TTS) with Chinese/English voices
- System volume control (get/set)
- RGB light strip control (256 colors)
- Audio stream playback support

**API IDs Used:**
- 9001: TTS_MAKER (text-to-speech)
- 9002: GET_VOLUME
- 9003: SET_VOLUME
- 9004: LED_CONTROL (RGB light strip)
- 9005: PLAY_STREAM
- 9006: PLAY_STOP

## Modified Files

### 1. `g1_app/api/constants.py`
**Added Topics:**
- `Topic.AUDIO_MSG` = "rt/audio_msg" (speech recognition)
- `Topic.LIDAR_CLOUD` = "rt/utlidar/cloud_livox_mid360" (10Hz point cloud)
- `Topic.LIDAR_IMU` = "rt/utlidar/imu_livox_mid360" (200Hz IMU)
- `Topic.BMS_STATE` = "rt/lf/bms" (battery state)

### 2. `g1_app/core/state_machine.py`
**Added to RobotState:**
- `audio_volume`: Optional[int] - System volume (0-100)
- `last_speech_text`: Optional[str] - Last recognized speech
- `lidar_active`: bool - LiDAR receiving status

**Updated update_state() method** to accept audio/lidar parameters.

### 3. `g1_app/core/event_bus.py`
**New Events:**
- `AUDIO_VOLUME_CHANGED`
- `SPEECH_RECOGNIZED`
- `LIDAR_DATA_RECEIVED`
- `VIDEO_FRAME_RECEIVED`

### 4. `g1_app/core/robot_controller.py`
**New Subscriptions:**
- Audio messages (rt/audio_msg) for speech recognition
- LiDAR point cloud (rt/utlidar/cloud_livox_mid360)

**New Methods:**
- `speak(text, speaker_id)` - Text-to-speech
- `set_volume(volume)` - Set system volume
- `get_volume()` - Get current volume
- `set_led_color(r, g, b)` - Control RGB light strip

**Event Handlers:**
- `on_audio_message()` - Processes ASR results, emits SPEECH_RECOGNIZED event
- `on_lidar_cloud()` - Tracks LiDAR status, emits LIDAR_DATA_RECEIVED event

### 5. `g1_app/ui/web_server.py`
**New Endpoints:**

**Audio:**
- `POST /api/audio/speak` - Text-to-speech
  ```json
  {"text": "Hello world", "speaker_id": 0}
  ```
- `POST /api/audio/volume` - Set volume
  ```json
  {"volume": 50}
  ```
- `GET /api/audio/volume` - Get current volume
- `POST /api/audio/led` - Set RGB LED color
  ```json
  {"r": 255, "g": 0, "b": 0}
  ```

**Video:**
- `GET /api/video/status` - Check WebRTC video availability

**LiDAR:**
- `GET /api/lidar/status` - Get LiDAR status and topic info

**New WebSocket Events:**
- `speech_recognized` - Broadcast recognized speech text
  ```json
  {
    "type": "speech_recognized",
    "data": {
      "text": "hello",
      "confidence": 0.95,
      "angle": 90,
      "timestamp": 123456789
    }
  }
  ```
- `lidar_active` - Broadcast LiDAR metadata
  ```json
  {
    "type": "lidar_active",
    "data": {
      "active": true,
      "height": 1,
      "width": 48000,
      "point_step": 18
    }
  }
  ```

## SDK Documentation References

Based on scraped Unitree G1 SDK documentation:

1. **VuiClient-Service.md**: Audio/TTS/LED control APIs
2. **lidar-services-interface.md**: LiDAR topics and coordinate transforms
3. **depth-camera-instruction.md**: Realsense D435i camera info
4. **architecture-description.md**: WebRTC module for video/audio streams

## Usage Examples

### Text-to-Speech
```python
# Chinese voice
await robot.speak("你好，我是机器人", speaker_id=0)

# English voice
await robot.speak("Hello, I am a robot", speaker_id=1)
```

### Volume Control
```python
# Set volume to 50%
await robot.set_volume(50)

# Get current volume
result = await robot.get_volume()
print(f"Volume: {result['volume']}%")
```

### LED Control
```python
# Red LED
await robot.set_led_color(255, 0, 0)

# Green LED
await robot.set_led_color(0, 255, 0)

# Blue LED
await robot.set_led_color(0, 0, 255)
```

### Speech Recognition (WebSocket)
```javascript
// In browser JavaScript
ws.onmessage = (event) => {
  const msg = JSON.parse(event.data);
  if (msg.type === 'speech_recognized') {
    console.log('Heard:', msg.data.text);
    console.log('Confidence:', msg.data.confidence);
  }
};
```

## Technical Notes

### Audio System
- **Service**: vui_service (must be running)
- **Hardware**: 4-microphone array, 8Ω 3W speaker, RGB light strip
- **ASR**: Local offline, non-streaming model
- **TTS**: Local offline, Chinese/English support
- **LED**: 256 colors, call interval > 200ms

### LiDAR System
- **Hardware**: Livox Mid-360 (inverted mounting, -2.3° pitch)
- **Coordinate**: (-0.0, 0.0, -0.47618) relative to robot base
- **Point Cloud**: 10Hz, frame_id="livox_frame"
- **IMU**: 200Hz (optional)

### Video System
- **Camera**: Realsense D435i depth camera
- **Features**: Stereo IR, RGB, 6-axis IMU
- **Streaming**: Via WebRTC module (not DDS topics)
- **Integration**: Handled by WebRTC connection layer

## Architecture Compliance

✅ **Follows SDK Architecture:**
- Audio via VuiClient Service (documented APIs)
- Speech recognition via DDS topic rt/audio_msg
- LiDAR via DDS topics rt/utlidar/*
- Video via WebRTC module (not DDS)
- All wrapped through WebRTC for G1 Air compatibility

✅ **Event-Driven Design:**
- EventBus for decoupled communication
- WebSocket broadcast for real-time UI updates
- State machine tracking for all system state

✅ **Error Handling:**
- Graceful fallback if services unavailable
- Validation of parameters (volume 0-100, RGB 0-255)
- Subscription failures logged as warnings

## Next Steps (Optional Enhancements)

1. **UI Integration**: Add HTML controls for audio/video/lidar
   - Volume slider
   - TTS input field
   - LED color picker
   - Video display element
   - Speech text display
   - LiDAR point cloud visualization

2. **Advanced Features**:
   - Custom audio stream playback
   - LiDAR point cloud processing
   - Video recording/snapshots
   - Speaker role selection
   - ASR language selection

3. **Service Monitoring**:
   - Track vui_service status via RobotStateClient
   - Auto-enable services if disabled
   - Service health indicators in UI
