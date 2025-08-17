"""
Message Broadcasting System for PyCraft 2D Multiplayer

Provides efficient message distribution, compression, and performance monitoring
for multiplayer game networking.

This module implements Phase 2.4 of the multiplayer networking system,
focusing on scalable message broadcasting with:
- Priority-based message queuing
- Interest management and spatial filtering
- Multiple broadcast patterns (unicast, multicast, proximity-based)
- Delta compression for state updates
- Performance monitoring and optimization
"""

from .broadcast_manager import BroadcastManager, BroadcastConfig
from .message_filters import (
    MessageFilter, SpatialFilter, ChunkFilter, PrivacyFilter,
    RateLimitFilter, RelevanceFilter, InterestManager
)
from .broadcast_patterns import (
    BroadcastPattern, UnicastPattern, MulticastPattern, BroadcastAllPattern,
    ProximityPattern, ChunkPattern, ReliableBroadcastPattern
)
from .message_queue import (
    MessageQueue, PriorityMessageQueue, MessageScheduler,
    QueuedMessage, MessageBatch, MessagePriority
)
from .compression import (
    MessageCompressor, DeltaCompressor, StreamCompressor,
    CompressionType, CompressionStats, message_compressor
)
from .performance_monitor import (
    BroadcastPerformanceMonitor, MetricCollector, PerformanceAlert,
    TimingContext, performance_monitor
)

__all__ = [
    # Core broadcasting
    'BroadcastManager',
    'BroadcastConfig',
    
    # Message filtering
    'MessageFilter',
    'SpatialFilter',
    'ChunkFilter',
    'PrivacyFilter',
    'RateLimitFilter',
    'RelevanceFilter',
    'InterestManager',
    
    # Broadcast patterns
    'BroadcastPattern',
    'UnicastPattern',
    'MulticastPattern',
    'BroadcastAllPattern',
    'ProximityPattern',
    'ChunkPattern',
    'ReliableBroadcastPattern',
    
    # Message queuing
    'MessageQueue',
    'PriorityMessageQueue',
    'MessageScheduler',
    'QueuedMessage',
    'MessageBatch',
    'MessagePriority',
    
    # Compression
    'MessageCompressor',
    'DeltaCompressor',
    'StreamCompressor',
    'CompressionType',
    'CompressionStats',
    'message_compressor',
    
    # Performance monitoring
    'BroadcastPerformanceMonitor',
    'MetricCollector',
    'PerformanceAlert',
    'TimingContext',
    'performance_monitor'
]

# Version information
__version__ = "2.4.0"
__author__ = "PyCraft 2D Development Team"
__description__ = "Message Broadcasting System for PyCraft 2D Multiplayer"

# Default configurations
DEFAULT_BROADCAST_CONFIG = BroadcastConfig(
    max_queue_size=10000,
    batch_size=10,
    batch_timeout=0.05,
    compression_enabled=True,
    spatial_filtering_enabled=True,
    performance_monitoring_enabled=True
)

# Global instances
broadcast_manager = None

def initialize_broadcasting(config: BroadcastConfig = None) -> BroadcastManager:
    """
    Initialize the broadcasting system.
    
    Args:
        config: Broadcasting configuration
        
    Returns:
        Configured BroadcastManager instance
    """
    global broadcast_manager
    
    if config is None:
        config = DEFAULT_BROADCAST_CONFIG
    
    broadcast_manager = BroadcastManager(config)
    return broadcast_manager

def get_broadcast_manager() -> BroadcastManager:
    """
    Get the global broadcast manager instance.
    
    Returns:
        BroadcastManager instance or None if not initialized
    """
    return broadcast_manager

def shutdown_broadcasting():
    """Shutdown the broadcasting system."""
    global broadcast_manager
    
    if broadcast_manager:
        broadcast_manager.shutdown()
        broadcast_manager = None

# Performance monitoring shortcuts
def start_performance_monitoring():
    """Start performance monitoring."""
    performance_monitor.enable_monitoring()

def stop_performance_monitoring():
    """Stop performance monitoring."""
    performance_monitor.disable_monitoring()

def get_performance_stats():
    """Get current performance statistics."""
    return performance_monitor.get_performance_summary()

def get_optimization_recommendations():
    """Get performance optimization recommendations."""
    return performance_monitor.get_optimization_recommendations()

# Quick setup functions
def setup_basic_broadcasting() -> BroadcastManager:
    """
    Setup basic broadcasting configuration.
    
    Returns:
        Configured BroadcastManager for basic use
    """
    config = BroadcastConfig(
        max_queue_size=5000,
        batch_size=5,
        batch_timeout=0.1,
        compression_enabled=False,
        spatial_filtering_enabled=False,
        performance_monitoring_enabled=False
    )
    
    return initialize_broadcasting(config)

def setup_high_performance_broadcasting() -> BroadcastManager:
    """
    Setup high-performance broadcasting configuration.
    
    Returns:
        Configured BroadcastManager for high-performance use
    """
    config = BroadcastConfig(
        max_queue_size=20000,
        batch_size=20,
        batch_timeout=0.02,
        compression_enabled=True,
        spatial_filtering_enabled=True,
        performance_monitoring_enabled=True
    )
    
    return initialize_broadcasting(config)

def setup_low_latency_broadcasting() -> BroadcastManager:
    """
    Setup low-latency broadcasting configuration.
    
    Returns:
        Configured BroadcastManager for low-latency use
    """
    config = BroadcastConfig(
        max_queue_size=2000,
        batch_size=1,
        batch_timeout=0.001,
        compression_enabled=False,
        spatial_filtering_enabled=True,
        performance_monitoring_enabled=True
    )
    
    return initialize_broadcasting(config)
