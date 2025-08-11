"""
Game utilities package - Various utility modules for the game.
"""

from .logger import (
    game_logger, 
    log_info, 
    log_debug, 
    log_warning, 
    log_error, 
    log_exception,
    log_game_event,
    log_performance
)
from .audio_utils import SafeAudioPlayer, create_safe_audio_player
from .performance import PerformanceMonitor, get_performance_monitor, time_operation

__all__ = [
    'game_logger', 
    'log_info', 
    'log_debug', 
    'log_warning', 
    'log_error', 
    'log_exception',
    'log_game_event',
    'log_performance',
    'SafeAudioPlayer', 
    'create_safe_audio_player',
    'PerformanceMonitor', 
    'get_performance_monitor', 
    'time_operation'
]
