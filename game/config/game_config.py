"""
Game Configuration - Centralized configuration management
"""
import os
from typing import Dict, Any
# from dotenv import load_dotenv


class GameConfig:
    """Centralized game configuration."""
    
    # Debug and Development
    # Load environment variables from .env file
    # load_dotenv()

    DEBUG_MODE = False #os.getenv('PYCRAFT_DEBUG', 'False').lower() == 'true'
    SHOW_FPS = DEBUG_MODE
    SHOW_HITBOXES = DEBUG_MODE  # Show hitboxes in debug mode
    ENABLE_CONSOLE = DEBUG_MODE
    
    # Performance Settings
    MAX_CHUNK_CACHE_SIZE = 200 if os.getenv('PYCRAFT_DEBUG', 'False').lower() == 'true' else 50
    AUTO_SAVE_INTERVAL = 20 * 1000  # milliseconds
    CHUNK_UNLOAD_DISTANCE = 8  # Chunks beyond this distance get unloaded
    CHUNK_CLEANUP_INTERVAL = 60 * 1000  # Chunk cleanup every 60 seconds (1 minute)
    
    # Audio Settings
    MASTER_VOLUME = 0.7
    SFX_VOLUME = 0.8
    MUSIC_VOLUME = 0.6
    AUDIO_FALLBACK_ENABLED = True  # Create silent sounds for missing audio
    
    # Memory Management
    MAX_FLOATING_ITEMS = 200  # Prevent memory leaks from too many items
    ITEM_CLEANUP_INTERVAL = 5000  # Clean up old items every 5 seconds
    
    # Logging
    LOG_LEVEL = 'INFO' if not DEBUG_MODE else 'DEBUG'
    LOG_TO_FILE = True
    LOG_FILE_PATH = 'game.log'
    MAX_LOG_SIZE = 10 * 1024 * 1024  # 10MB
    
    # Error Handling
    CRASH_RECOVERY_ENABLED = True
    AUTO_BACKUP_ON_ERROR = True
    
    @classmethod
    def get_config_dict(cls) -> Dict[str, Any]:
        """Get all configuration as a dictionary."""
        config = {}
        for attr in dir(cls):
            if not attr.startswith('_') and not callable(getattr(cls, attr)):
                config[attr] = getattr(cls, attr)
        return config
    
    @classmethod
    def load_from_file(cls, config_path: str):
        """Load configuration from a file (future enhancement)."""
        # TODO: Implement loading from JSON/INI file
        pass
    
    @classmethod
    def save_to_file(cls, config_path: str):
        """Save current configuration to a file (future enhancement)."""
        # TODO: Implement saving to JSON/INI file
        pass
