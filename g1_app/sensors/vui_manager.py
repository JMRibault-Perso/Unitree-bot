"""VUI Manager - Voice User Interface (ASR, TTS, LED control)"""

import logging
from dataclasses import dataclass
from typing import Optional, Callable

from g1_app.core import EventBus, Events
from g1_app.api import Topic, LocoAPI, LEDColor, TTSSpeaker, Service

logger = logging.getLogger(__name__)


@dataclass
class ASRResult:
    """Automatic Speech Recognition result"""
    text: str
    confidence: float
    timestamp: float


class VUIManager:
    """Manages Voice User Interface (ASR, TTS, LED)"""
    
    def __init__(self, datachannel):
        self.datachannel = datachannel
        self.last_asr: Optional[ASRResult] = None
        self.asr_callback: Optional[Callable] = None
        
    def start(self, asr_callback: Optional[Callable] = None):
        """
        Start VUI manager
        
        Args:
            asr_callback: Optional callback for ASR results
        """
        self.asr_callback = asr_callback
        
        # Subscribe to ASR messages
        self.datachannel.subscribe(Topic.AUDIO_MSG, self._on_asr_message)
        
        logger.info("VUIManager started")
    
    def _on_asr_message(self, msg: dict):
        """Process ASR (speech recognition) message"""
        try:
            text = msg.get('text', '')
            confidence = msg.get('confidence', 0.0)
            timestamp = msg.get('timestamp', 0.0)
            
            result = ASRResult(
                text=text,
                confidence=confidence,
                timestamp=timestamp
            )
            
            self.last_asr = result
            EventBus.emit(Events.ASR_TEXT, result)
            
            # Call custom callback if provided
            if self.asr_callback:
                self.asr_callback(result)
            
            logger.info(f"ASR: '{text}' (confidence: {confidence:.2f})")
            
        except Exception as e:
            logger.error(f"Error processing ASR message: {e}")
    
    def speak(self, text: str, speaker: TTSSpeaker = TTSSpeaker.ENGLISH):
        """
        Text-to-Speech
        
        Args:
            text: Text to speak
            speaker: Voice type (CHINESE/ENGLISH)
        """
        payload = {
            "api_id": LocoAPI.SET_TTS,
            "parameter": {
                "text": text,
                "speaker": speaker.value
            }
        }
        
        self.datachannel.publish(f"{Topic.API_REQUEST}/{Service.SPORT}/request", payload)
        logger.info(f"TTS: '{text}' (speaker: {speaker.value})")
    
    def play_audio(self, audio_id: int):
        """
        Play pre-programmed audio
        
        Args:
            audio_id: Audio file ID
        """
        payload = {
            "api_id": LocoAPI.SET_AUDIO,
            "parameter": {
                "audio_id": audio_id
            }
        }
        
        self.datachannel.publish(f"{Topic.API_REQUEST}/{Service.SPORT}/request", payload)
        logger.info(f"Playing audio ID: {audio_id}")
    
    def set_led_color(self, color: LEDColor):
        """
        Set RGB LED strip color
        
        Args:
            color: LED color (ORANGE, BLUE, PURPLE, GREEN, YELLOW, RED)
        """
        payload = {
            "api_id": LocoAPI.SET_LED,
            "parameter": {
                "color": color.value
            }
        }
        
        self.datachannel.publish(f"{Topic.API_REQUEST}/{Service.SPORT}/request", payload)
        logger.info(f"LED color set to: {color.value}")
    
    def set_led_brightness(self, brightness: int):
        """
        Set LED brightness
        
        Args:
            brightness: 0-255
        """
        if not 0 <= brightness <= 255:
            logger.warning(f"Brightness {brightness} out of range [0,255]")
            brightness = max(0, min(255, brightness))
        
        payload = {
            "api_id": LocoAPI.SET_LED,
            "parameter": {
                "brightness": brightness
            }
        }
        
        self.datachannel.publish(f"{Topic.API_REQUEST}/{Service.SPORT}/request", payload)
        logger.info(f"LED brightness set to: {brightness}")
    
    def get_last_asr(self) -> Optional[ASRResult]:
        """Get last ASR result"""
        return self.last_asr
