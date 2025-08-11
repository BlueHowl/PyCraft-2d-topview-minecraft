"""
Game Logging System - Centralized logging for debugging and error tracking
"""
import logging
import logging.handlers
import os
import sys
from datetime import datetime
from typing import Optional

from game.config.game_config import GameConfig


class GameLogger:
    """Centralized logging system for the game."""
    
    _instance: Optional['GameLogger'] = None
    _logger: Optional[logging.Logger] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(GameLogger, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._logger is None:
            self._setup_logger()
    
    def _setup_logger(self):
        """Setup the main logger with file and console handlers."""
        self._logger = logging.getLogger('pycraft')
        self._logger.setLevel(getattr(logging, GameConfig.LOG_LEVEL.upper()))
        
        # Clear any existing handlers
        self._logger.handlers.clear()
        
        # Create formatters
        detailed_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s'
        )
        simple_formatter = logging.Formatter(
            '%(levelname)s: %(message)s'
        )
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(simple_formatter)
        self._logger.addHandler(console_handler)
        
        # File handler (if enabled)
        if GameConfig.LOG_TO_FILE:
            try:
                # Create logs directory if it doesn't exist
                log_dir = os.path.dirname(GameConfig.LOG_FILE_PATH)
                if log_dir and not os.path.exists(log_dir):
                    os.makedirs(log_dir)
                
                # Use rotating file handler to prevent huge log files
                file_handler = logging.handlers.RotatingFileHandler(
                    GameConfig.LOG_FILE_PATH,
                    maxBytes=GameConfig.MAX_LOG_SIZE,
                    backupCount=3
                )
                file_handler.setLevel(logging.DEBUG)
                file_handler.setFormatter(detailed_formatter)
                self._logger.addHandler(file_handler)
                
            except Exception as e:
                self._logger.warning(f"Could not setup file logging: {e}")
    
    @property
    def logger(self) -> logging.Logger:
        """Get the main logger instance."""
        return self._logger
    
    def info(self, message: str, *args, **kwargs):
        """Log info message."""
        self._logger.info(message, *args, **kwargs)
    
    def debug(self, message: str, *args, **kwargs):
        """Log debug message."""
        self._logger.debug(message, *args, **kwargs)
    
    def warning(self, message: str, *args, **kwargs):
        """Log warning message."""
        self._logger.warning(message, *args, **kwargs)
    
    def error(self, message: str, *args, **kwargs):
        """Log error message."""
        self._logger.error(message, *args, **kwargs)
    
    def critical(self, message: str, *args, **kwargs):
        """Log critical message."""
        self._logger.critical(message, *args, **kwargs)
    
    def exception(self, message: str, *args, **kwargs):
        """Log exception with traceback."""
        self._logger.exception(message, *args, **kwargs)
    
    def game_event(self, event: str, details: dict = None):
        """Log game-specific events with structured data."""
        if details:
            self._logger.info(f"GAME_EVENT: {event} - {details}")
        else:
            self._logger.info(f"GAME_EVENT: {event}")
    
    def performance(self, operation: str, duration_ms: float):
        """Log performance metrics."""
        self._logger.debug(f"PERFORMANCE: {operation} took {duration_ms:.2f}ms")


# Global logger instance
game_logger = GameLogger()

# Convenience functions for easy importing
def log_info(message: str, *args, **kwargs):
    game_logger.info(message, *args, **kwargs)

def log_debug(message: str, *args, **kwargs):
    game_logger.debug(message, *args, **kwargs)

def log_warning(message: str, *args, **kwargs):
    game_logger.warning(message, *args, **kwargs)

def log_error(message: str, *args, **kwargs):
    game_logger.error(message, *args, **kwargs)

def log_exception(message: str, *args, **kwargs):
    game_logger.exception(message, *args, **kwargs)

def log_game_event(event: str, details: dict = None):
    game_logger.game_event(event, details)

def log_performance(operation: str, duration_ms: float):
    game_logger.performance(operation, duration_ms)
