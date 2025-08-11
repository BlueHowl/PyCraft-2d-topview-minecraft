"""
Audio utilities for safe audio playback with error handling.
"""
import pygame as pg
from typing import Optional, Dict, Any
from game.config.game_config import GameConfig
from game.utils.logger import log_warning, log_error


class SafeAudioPlayer:
    """Safe audio player that handles missing or corrupt audio files gracefully."""
    
    def __init__(self, audio_dict: Dict[str, pg.mixer.Sound]):
        self.audio_dict = audio_dict
        self._missing_sounds = set()  # Track missing sounds to avoid spam
    
    def play_sound(self, sound_name: str, volume: Optional[float] = None) -> bool:
        """
        Play a sound safely with error handling.
        
        Args:
            sound_name: Name of the sound to play
            volume: Optional volume override (0.0 to 1.0)
            
        Returns:
            True if sound was played successfully, False otherwise
        """
        if sound_name not in self.audio_dict:
            if sound_name not in self._missing_sounds:
                log_warning(f"Sound '{sound_name}' not found in audio dictionary")
                self._missing_sounds.add(sound_name)
            return False
        
        try:
            sound = self.audio_dict[sound_name]
            if volume is not None:
                # Store original volume to restore later
                original_volume = sound.get_volume()
                sound.set_volume(volume * GameConfig.MASTER_VOLUME)
                sound.play()
                # Restore original volume
                sound.set_volume(original_volume)
            else:
                sound.play()
            return True
            
        except pg.error as e:
            if sound_name not in self._missing_sounds:
                log_error(f"Error playing sound '{sound_name}': {e}")
                self._missing_sounds.add(sound_name)
            return False
        except Exception as e:
            if sound_name not in self._missing_sounds:
                log_error(f"Unexpected error playing sound '{sound_name}': {e}")
                self._missing_sounds.add(sound_name)
            return False
    
    def play_sound_positional(self, sound_name: str, player_pos: tuple, 
                            sound_pos: tuple, max_distance: float = 300.0) -> bool:
        """
        Play a sound with positional audio (distance-based volume).
        
        Args:
            sound_name: Name of the sound to play
            player_pos: Player's position (x, y)
            sound_pos: Sound source position (x, y) 
            max_distance: Maximum distance at which sound can be heard
            
        Returns:
            True if sound was played successfully, False otherwise
        """
        import math
        
        # Calculate distance
        distance = math.hypot(player_pos[0] - sound_pos[0], player_pos[1] - sound_pos[1])
        
        if distance > max_distance:
            return False  # Too far to hear
        
        # Calculate volume based on distance (linear falloff)
        volume = max(0.0, 1.0 - (distance / max_distance))
        volume *= GameConfig.SFX_VOLUME
        
        return self.play_sound(sound_name, volume)
    
    def is_sound_available(self, sound_name: str) -> bool:
        """Check if a sound is available to play."""
        return sound_name in self.audio_dict and sound_name not in self._missing_sounds
    
    def get_missing_sounds(self) -> set:
        """Get a set of sound names that failed to play."""
        return self._missing_sounds.copy()


def create_safe_audio_player(audio_dict: Dict[str, pg.mixer.Sound]) -> SafeAudioPlayer:
    """Create a SafeAudioPlayer instance."""
    return SafeAudioPlayer(audio_dict)
