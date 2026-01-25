"""Video Manager - Processes WebRTC video stream"""

import logging
from dataclasses import dataclass
from typing import Optional, Callable
import asyncio

from g1_app.core import EventBus, Events

logger = logging.getLogger(__name__)


@dataclass
class VideoFrame:
    """Video frame data"""
    data: bytes
    width: int
    height: int
    format: str  # 'H264', 'H265', 'RGB', etc.
    timestamp: float


class VideoManager:
    """Manages video stream from robot cameras"""
    
    def __init__(self, webrtc_connection):
        """
        Args:
            webrtc_connection: WebRTC connection object with video track
        """
        self.webrtc_conn = webrtc_connection
        self.current_frame: Optional[VideoFrame] = None
        self.frame_callback: Optional[Callable] = None
        self._running = False
        
    async def start(self, frame_callback: Optional[Callable] = None):
        """
        Start video stream processing
        
        Args:
            frame_callback: Optional callback for each frame
        """
        self.frame_callback = frame_callback
        self._running = True
        
        # Start frame processing loop
        asyncio.create_task(self._process_frames())
        
        logger.info("VideoManager started")
    
    async def _process_frames(self):
        """Process incoming video frames"""
        try:
            while self._running:
                # Get frame from WebRTC video track
                frame_data = await self._get_next_frame()
                
                if frame_data:
                    frame = VideoFrame(
                        data=frame_data['data'],
                        width=frame_data.get('width', 1920),
                        height=frame_data.get('height', 1080),
                        format=frame_data.get('format', 'H264'),
                        timestamp=frame_data.get('timestamp', 0.0)
                    )
                    
                    self.current_frame = frame
                    EventBus.emit(Events.VIDEO_FRAME, frame)
                    
                    # Call custom callback
                    if self.frame_callback:
                        self.frame_callback(frame)
                
                # Control frame rate (avoid overwhelming)
                await asyncio.sleep(1/30)  # 30 FPS
                
        except Exception as e:
            logger.error(f"Error processing video frames: {e}")
    
    async def _get_next_frame(self) -> Optional[dict]:
        """Get next frame from WebRTC connection"""
        try:
            # This depends on go2_webrtc_connect API
            # Placeholder - actual implementation depends on library API
            if hasattr(self.webrtc_conn, 'get_video_frame'):
                return await self.webrtc_conn.get_video_frame()
            return None
        except Exception as e:
            logger.error(f"Error getting frame: {e}")
            return None
    
    def stop(self):
        """Stop video processing"""
        self._running = False
        logger.info("VideoManager stopped")
    
    def get_current_frame(self) -> Optional[VideoFrame]:
        """Get current video frame"""
        return self.current_frame
    
    def take_snapshot(self) -> Optional[VideoFrame]:
        """Capture current frame as snapshot"""
        if self.current_frame:
            logger.info("Snapshot captured")
            return self.current_frame
        else:
            logger.warning("No frame available for snapshot")
            return None
