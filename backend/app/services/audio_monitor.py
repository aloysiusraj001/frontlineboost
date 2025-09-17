# app/services/audio_monitor.py

import asyncio
import logging
from typing import Optional, Callable
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class AudioMonitor:
    """Monitor audio input and detect silence periods"""
    
    def __init__(self, silence_threshold: float = 30.0):
        self.silence_threshold = silence_threshold
        self.last_audio_time: Optional[datetime] = None
        self.is_monitoring = False
        self.silence_callback: Optional[Callable] = None
    
    def start_monitoring(self, silence_callback: Optional[Callable] = None):
        """Start monitoring for audio input"""
        self.is_monitoring = True
        self.last_audio_time = datetime.utcnow()
        self.silence_callback = silence_callback
        
        # Start background monitoring task
        asyncio.create_task(self._monitor_silence())
        logger.info("Audio monitoring started")
    
    def stop_monitoring(self):
        """Stop audio monitoring"""
        self.is_monitoring = False
        logger.info("Audio monitoring stopped")
    
    def update_audio_activity(self):
        """Call this when audio input is detected"""
        self.last_audio_time = datetime.utcnow()
    
    async def _monitor_silence(self):
        """Background task to monitor for silence periods"""
        while self.is_monitoring:
            if self.last_audio_time:
                silence_duration = (datetime.utcnow() - self.last_audio_time).total_seconds()
                
                if silence_duration > self.silence_threshold:
                    logger.warning(f"Silence detected for {silence_duration:.1f} seconds")
                    
                    if self.silence_callback:
                        await self.silence_callback(silence_duration)
                    
                    # Reset to avoid repeated triggers
                    self.last_audio_time = datetime.utcnow()
            
            # Check every 5 seconds
            await asyncio.sleep(5)
    
    def get_silence_duration(self) -> float:
        """Get current silence duration in seconds"""
        if not self.last_audio_time:
            return 0.0
        
        return (datetime.utcnow() - self.last_audio_time).total_seconds()

# Singleton instance
audio_monitor = AudioMonitor()