"""
Event Bus - Central pub-sub system for sensor data and state changes
Allows decoupled communication between robot controller and UI
"""

from typing import Callable, Dict, List, Any
from threading import Lock
import logging

logger = logging.getLogger(__name__)


class EventBus:
    """Thread-safe pub-sub event bus"""
    
    _subscribers: Dict[str, List[Callable]] = {}
    _lock = Lock()
    
    @classmethod
    def subscribe(cls, event_type: str, callback: Callable[[Any], None]) -> None:
        """
        Subscribe to an event type
        
        Args:
            event_type: Event name (e.g., "state_changed", "odometry", "lidar")
            callback: Function to call when event is emitted
        """
        with cls._lock:
            if event_type not in cls._subscribers:
                cls._subscribers[event_type] = []
            cls._subscribers[event_type].append(callback)
            logger.debug(f"Subscribed to '{event_type}' (total subscribers: {len(cls._subscribers[event_type])})")
    
    @classmethod
    def unsubscribe(cls, event_type: str, callback: Callable[[Any], None]) -> None:
        """Remove a subscription"""
        with cls._lock:
            if event_type in cls._subscribers:
                cls._subscribers[event_type].remove(callback)
                logger.debug(f"Unsubscribed from '{event_type}'")
    
    @classmethod
    def emit(cls, event_type: str, data: Any = None) -> None:
        """
        Emit an event to all subscribers
        
        Args:
            event_type: Event name
            data: Event payload
        """
        with cls._lock:
            subscribers = cls._subscribers.get(event_type, []).copy()
        
        logger.debug(f"Emitting '{event_type}' to {len(subscribers)} subscribers")
        
        for callback in subscribers:
            try:
                callback(data)
            except Exception as e:
                logger.error(f"Error in subscriber for '{event_type}': {e}")
    
    @classmethod
    def clear(cls) -> None:
        """Clear all subscriptions (useful for testing)"""
        with cls._lock:
            cls._subscribers.clear()
            logger.debug("Cleared all event subscriptions")


# Event type constants for type safety
class Events:
    """Standard event types"""
    # State changes
    STATE_CHANGED = "state_changed"
    LED_CHANGED = "led_changed"
    CONNECTION_CHANGED = "connection_changed"
    BATTERY_UPDATED = "battery_updated"
    AUDIO_VOLUME_CHANGED = "audio_volume_changed"
    SPEECH_RECOGNIZED = "speech_recognized"
    LIDAR_DATA_RECEIVED = "lidar_data_received"
    VIDEO_FRAME_RECEIVED = "video_frame_received"
    
    # Sensor data
    ODOMETRY = "odometry"
    LIDAR_CLOUD = "lidar_cloud"
    LIDAR_IMU = "lidar_imu"
    VIDEO_FRAME = "video_frame"
    
    # VUI
    ASR_TEXT = "asr_text"
    TTS_STATUS = "tts_status"
    AUDIO_PLAYBACK = "audio_playback"
    
    # Commands
    COMMAND_SENT = "command_sent"
    COMMAND_RESULT = "command_result"
    
    # Errors
    ERROR = "error"
