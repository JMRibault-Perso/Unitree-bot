"""
Audio Client - Text-to-speech and volume control
Based on VuiClient Service from SDK documentation
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)


class AudioClient:
    """
    Client for G1 audio control (TTS, volume, LED)
    
    Based on unitree::robot::g1::AudioClient from SDK
    Service name: vui_service
    """
    
    # Audio API IDs (from VuiClient Service documentation)
    TTS_MAKER = 9001          # Text-to-speech
    GET_VOLUME = 9002         # Get system volume
    SET_VOLUME = 9003         # Set system volume
    LED_CONTROL = 9004        # RGB light strip control
    PLAY_STREAM = 9005        # Audio stream playback
    PLAY_STOP = 9006          # Stop playback
    
    def __init__(self, datachannel):
        """
        Args:
            datachannel: WebRTC datachannel for sending commands
        """
        self.datachannel = datachannel
    
    async def speak(self, text: str, speaker_id: int = 0) -> dict:
        """
        Text-to-speech
        
        Args:
            text: Text to speak (Chinese or English)
            speaker_id: 0 for Chinese voice, 1 for English voice
            
        Returns:
            Command result
        """
        import json
        
        payload = {
            "api_id": self.TTS_MAKER,
            "parameter": json.dumps({
                "text": text,
                "speaker_id": speaker_id
            })
        }
        
        logger.info(f"🔊 TTS: '{text}' (speaker {speaker_id})")
        
        try:
            # Send via DDS service API
            response = await self.datachannel.pub_sub.publish_request(
                "rt/api/audio/command",
                payload
            )
            return response
        except Exception as e:
            logger.error(f"TTS failed: {e}")
            return {"error": str(e)}
    
    async def get_volume(self) -> Optional[int]:
        """
        Get system volume
        
        Returns:
            Volume level (0-100) or None if failed
        """
        import json
        
        payload = {
            "api_id": self.GET_VOLUME,
            "parameter": "{}"
        }
        
        try:
            response = await self.datachannel.pub_sub.publish_request(
                "rt/api/audio/command",
                payload
            )
            
            if isinstance(response, dict) and 'volume' in response:
                volume = response['volume']
                logger.info(f"📢 Current volume: {volume}%")
                return volume
            
            return None
        except Exception as e:
            logger.error(f"Get volume failed: {e}")
            return None
    
    async def set_volume(self, volume: int) -> bool:
        """
        Set system volume
        
        Args:
            volume: Volume level (0-100)
            
        Returns:
            True if successful
        """
        import json
        
        # Clamp volume to valid range
        volume = max(0, min(100, volume))
        
        payload = {
            "api_id": self.SET_VOLUME,
            "parameter": json.dumps({"volume": volume})
        }
        
        logger.info(f"🔊 Setting volume to {volume}%")
        
        try:
            await self.datachannel.pub_sub.publish_request(
                "rt/api/audio/command",
                payload
            )
            return True
        except Exception as e:
            logger.error(f"Set volume failed: {e}")
            return False
    
    async def set_led_color(self, r: int, g: int, b: int) -> bool:
        """
        Control RGB light strip
        
        Args:
            r: Red (0-255)
            g: Green (0-255)
            b: Blue (0-255)
            
        Returns:
            True if successful
        
        Note:
            Call interval must be > 200ms according to SDK docs
        """
        import json
        
        # Clamp RGB values
        r = max(0, min(255, r))
        g = max(0, min(255, g))
        b = max(0, min(255, b))
        
        payload = {
            "api_id": self.LED_CONTROL,
            "parameter": json.dumps({"R": r, "G": g, "B": b})
        }
        
        logger.info(f"💡 Setting LED color to RGB({r}, {g}, {b})")
        
        try:
            await self.datachannel.pub_sub.publish_request(
                "rt/api/audio/command",
                payload
            )
            return True
        except Exception as e:
            logger.error(f"LED control failed: {e}")
            return False
