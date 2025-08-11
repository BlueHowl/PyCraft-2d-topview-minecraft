"""
Performance monitoring utilities for tracking game performance.
"""
import time
import pygame as pg
from typing import Dict, List, Optional
from collections import deque
from game.config.game_config import GameConfig
from game.utils.logger import log_performance, log_warning


class PerformanceMonitor:
    """Monitor and track game performance metrics."""
    
    def __init__(self, max_samples: int = 60):
        self.max_samples = max_samples
        
        # FPS tracking
        self.fps_samples = deque(maxlen=max_samples)
        self.last_fps_update = time.time()
        
        # Frame time tracking
        self.frame_times = deque(maxlen=max_samples)
        self.last_frame_time = time.time()
        
        # Operation timing
        self.operation_times: Dict[str, List[float]] = {}
        self.current_operations: Dict[str, float] = {}
        
        # Memory tracking (if available)
        self.memory_usage = deque(maxlen=max_samples)
        
        # Performance warnings
        self.low_fps_threshold = 30
        self.high_frame_time_threshold = 33.33  # 30 FPS in ms
        
    def update_fps(self, clock: pg.time.Clock):
        """Update FPS tracking."""
        current_fps = clock.get_fps()
        self.fps_samples.append(current_fps)
        
        # Check for performance issues
        if current_fps < self.low_fps_threshold and current_fps > 0:
            if time.time() - self.last_fps_update > 5.0:  # Don't spam warnings
                log_warning(f"Low FPS detected: {current_fps:.1f}")
                self.last_fps_update = time.time()
    
    def start_frame(self):
        """Mark the start of a new frame."""
        current_time = time.time()
        if hasattr(self, 'last_frame_time'):
            frame_time = (current_time - self.last_frame_time) * 1000  # Convert to ms
            self.frame_times.append(frame_time)
        self.last_frame_time = current_time
    
    def start_operation(self, operation_name: str):
        """Start timing an operation."""
        self.current_operations[operation_name] = time.time()
    
    def end_operation(self, operation_name: str) -> Optional[float]:
        """End timing an operation and return the duration in milliseconds."""
        if operation_name not in self.current_operations:
            log_warning(f"Operation '{operation_name}' was not started")
            return None
        
        start_time = self.current_operations.pop(operation_name)
        duration = (time.time() - start_time) * 1000  # Convert to ms
        
        # Store the timing
        if operation_name not in self.operation_times:
            self.operation_times[operation_name] = deque(maxlen=self.max_samples)
        
        self.operation_times[operation_name].append(duration)
        
        # Log if it's taking too long
        if duration > 16.67:  # Longer than one 60fps frame
            log_performance(operation_name, duration)
        
        return duration
    
    def get_average_fps(self) -> float:
        """Get average FPS over recent samples."""
        if not self.fps_samples:
            return 0.0
        return sum(self.fps_samples) / len(self.fps_samples)
    
    def get_average_frame_time(self) -> float:
        """Get average frame time in milliseconds."""
        if not self.frame_times:
            return 0.0
        return sum(self.frame_times) / len(self.frame_times)
    
    def get_operation_average(self, operation_name: str) -> Optional[float]:
        """Get average time for a specific operation."""
        if operation_name not in self.operation_times:
            return None
        
        times = self.operation_times[operation_name]
        if not times:
            return None
        
        return sum(times) / len(times)
    
    def get_operation_max(self, operation_name: str) -> Optional[float]:
        """Get maximum time for a specific operation."""
        if operation_name not in self.operation_times:
            return None
        
        times = self.operation_times[operation_name]
        if not times:
            return None
        
        return max(times)
    
    def get_performance_report(self) -> Dict[str, any]:
        """Get a comprehensive performance report."""
        report = {
            'fps': {
                'current': self.fps_samples[-1] if self.fps_samples else 0,
                'average': self.get_average_fps(),
                'min': min(self.fps_samples) if self.fps_samples else 0,
                'max': max(self.fps_samples) if self.fps_samples else 0
            },
            'frame_time': {
                'current': self.frame_times[-1] if self.frame_times else 0,
                'average': self.get_average_frame_time(),
                'min': min(self.frame_times) if self.frame_times else 0,
                'max': max(self.frame_times) if self.frame_times else 0
            },
            'operations': {}
        }
        
        for operation_name in self.operation_times:
            report['operations'][operation_name] = {
                'average': self.get_operation_average(operation_name),
                'max': self.get_operation_max(operation_name),
                'samples': len(self.operation_times[operation_name])
            }
        
        return report
    
    def reset_stats(self):
        """Reset all performance statistics."""
        self.fps_samples.clear()
        self.frame_times.clear()
        self.operation_times.clear()
        self.current_operations.clear()
        self.memory_usage.clear()


class PerformanceContext:
    """Context manager for timing operations."""
    
    def __init__(self, monitor: PerformanceMonitor, operation_name: str):
        self.monitor = monitor
        self.operation_name = operation_name
    
    def __enter__(self):
        self.monitor.start_operation(self.operation_name)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.monitor.end_operation(self.operation_name)


# Global performance monitor instance
performance_monitor = PerformanceMonitor() if GameConfig.DEBUG_MODE else None


def get_performance_monitor() -> Optional[PerformanceMonitor]:
    """Get the global performance monitor (only available in debug mode)."""
    return performance_monitor


def time_operation(operation_name: str):
    """Decorator or context manager for timing operations."""
    if performance_monitor is None:
        # Return a no-op context manager if monitoring is disabled
        class NoOpContext:
            def __enter__(self): return self
            def __exit__(self, *args): pass
        return NoOpContext()
    
    return PerformanceContext(performance_monitor, operation_name)
