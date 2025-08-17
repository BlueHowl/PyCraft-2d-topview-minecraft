"""
Message Compression System for PyCraft 2D Multiplayer

Provides efficient compression and delta compression for network messages
to reduce bandwidth usage and improve performance.
"""

import json
import time
import zlib
import pickle
from typing import Dict, List, Any, Optional, Union, Tuple
from dataclasses import dataclass, asdict
from copy import deepcopy
import struct

from ..message_types import MessageType


class CompressionType:
    """Available compression algorithms."""
    NONE = "none"
    ZLIB = "zlib"
    DELTA = "delta"
    HYBRID = "hybrid"


@dataclass
class CompressionStats:
    """Compression statistics."""
    original_size: int = 0
    compressed_size: int = 0
    compression_ratio: float = 0.0
    compression_time: float = 0.0
    decompression_time: float = 0.0
    algorithm_used: str = CompressionType.NONE


class DeltaCompressor:
    """
    Delta compression for state updates.
    
    Tracks state changes and only sends differences,
    significantly reducing bandwidth for frequent updates.
    """
    
    def __init__(self, max_history: int = 100):
        """
        Initialize delta compressor.
        
        Args:
            max_history: Maximum number of states to keep in history
        """
        self.max_history = max_history
        self.state_history: Dict[str, List[Dict[str, Any]]] = {}
        self.last_full_send: Dict[str, float] = {}
        self.full_send_interval = 10.0  # Send full state every 10 seconds
    
    def compress_state(self, entity_id: str, current_state: Dict[str, Any]) -> Tuple[Dict[str, Any], bool]:
        """
        Compress state using delta compression.
        
        Args:
            entity_id: Unique identifier for the entity
            current_state: Current state to compress
            
        Returns:
            Tuple of (compressed_data, is_full_state)
        """
        current_time = time.time()
        
        # Check if we need to send full state
        last_full = self.last_full_send.get(entity_id, 0)
        force_full = (current_time - last_full) > self.full_send_interval
        
        if entity_id not in self.state_history or force_full:
            # Send full state
            self.state_history[entity_id] = [deepcopy(current_state)]
            self.last_full_send[entity_id] = current_time
            return current_state, True
        
        # Generate delta
        history = self.state_history[entity_id]
        last_state = history[-1] if history else {}
        
        delta = self._generate_delta(last_state, current_state)
        
        # Add to history
        history.append(deepcopy(current_state))
        if len(history) > self.max_history:
            history.pop(0)
        
        # If delta is too large, send full state instead
        if len(str(delta)) > len(str(current_state)) * 0.8:
            self.last_full_send[entity_id] = current_time
            return current_state, True
        
        return delta, False
    
    def decompress_state(self, entity_id: str, compressed_data: Dict[str, Any], 
                        is_full_state: bool) -> Dict[str, Any]:
        """
        Decompress state data.
        
        Args:
            entity_id: Entity identifier
            compressed_data: Compressed state data
            is_full_state: Whether this is a full state or delta
            
        Returns:
            Full decompressed state
        """
        if is_full_state:
            # Store full state
            self.state_history[entity_id] = [deepcopy(compressed_data)]
            return compressed_data
        
        # Apply delta to last known state
        if entity_id not in self.state_history or not self.state_history[entity_id]:
            # No previous state, request full state
            raise ValueError(f"No previous state for entity {entity_id}, full state required")
        
        last_state = self.state_history[entity_id][-1]
        new_state = self._apply_delta(last_state, compressed_data)
        
        # Add to history
        history = self.state_history[entity_id]
        history.append(deepcopy(new_state))
        if len(history) > self.max_history:
            history.pop(0)
        
        return new_state
    
    def _generate_delta(self, old_state: Dict[str, Any], new_state: Dict[str, Any]) -> Dict[str, Any]:
        """Generate delta between two states."""
        delta = {}
        
        # Check for changes and additions
        for key, new_value in new_state.items():
            if key not in old_state or old_state[key] != new_value:
                if isinstance(new_value, dict) and isinstance(old_state.get(key), dict):
                    # Nested dictionary - recurse
                    nested_delta = self._generate_delta(old_state[key], new_value)
                    if nested_delta:
                        delta[key] = nested_delta
                elif isinstance(new_value, list) and isinstance(old_state.get(key), list):
                    # List - check if different
                    if old_state[key] != new_value:
                        delta[key] = new_value
                else:
                    # Simple value change
                    delta[key] = new_value
        
        # Check for deletions
        deleted_keys = set(old_state.keys()) - set(new_state.keys())
        for key in deleted_keys:
            delta[f"__deleted__{key}"] = True
        
        return delta
    
    def _apply_delta(self, base_state: Dict[str, Any], delta: Dict[str, Any]) -> Dict[str, Any]:
        """Apply delta to base state."""
        new_state = deepcopy(base_state)
        
        for key, value in delta.items():
            if key.startswith("__deleted__"):
                # Handle deletion
                actual_key = key[11:]  # Remove "__deleted__" prefix
                if actual_key in new_state:
                    del new_state[actual_key]
            elif isinstance(value, dict) and key in new_state and isinstance(new_state[key], dict):
                # Nested dictionary - recurse
                new_state[key] = self._apply_delta(new_state[key], value)
            else:
                # Simple value or list
                new_state[key] = value
        
        return new_state
    
    def clear_history(self, entity_id: Optional[str] = None):
        """Clear compression history."""
        if entity_id:
            self.state_history.pop(entity_id, None)
            self.last_full_send.pop(entity_id, None)
        else:
            self.state_history.clear()
            self.last_full_send.clear()


class MessageCompressor:
    """
    Main message compression system.
    
    Handles multiple compression algorithms and automatically
    selects the best compression method for each message type.
    """
    
    def __init__(self):
        """Initialize message compressor."""
        self.delta_compressor = DeltaCompressor()
        
        # Compression settings per message type
        self.compression_settings = {
            MessageType.PLAYER_POSITION: CompressionType.DELTA,
            MessageType.PLAYER_UPDATE: CompressionType.DELTA,
            MessageType.CHUNK_DATA: CompressionType.ZLIB,
            MessageType.INVENTORY_UPDATE: CompressionType.DELTA,
            MessageType.CHAT_MESSAGE: CompressionType.NONE,
            MessageType.CHAT_BROADCAST: CompressionType.NONE,
            MessageType.BLOCK_PLACE: CompressionType.NONE,
            MessageType.BLOCK_BREAK: CompressionType.NONE,
            MessageType.ENTITY_UPDATE: CompressionType.HYBRID,
        }
        
        # Compression statistics
        self.stats: Dict[str, CompressionStats] = {}
        
        # Compression thresholds
        self.min_compression_size = 100  # Don't compress messages smaller than this
        self.compression_ratio_threshold = 0.8  # Only use if compression ratio < 0.8
    
    def compress_message(self, message_type: MessageType, data: Dict[str, Any], 
                        entity_id: Optional[str] = None) -> Tuple[bytes, Dict[str, Any]]:
        """
        Compress message data.
        
        Args:
            message_type: Type of message
            data: Message data to compress
            entity_id: Entity ID for delta compression
            
        Returns:
            Tuple of (compressed_data, compression_metadata)
        """
        start_time = time.time()
        original_data = json.dumps(data, separators=(',', ':')).encode('utf-8')
        original_size = len(original_data)
        
        # Get compression method
        compression_type = self.compression_settings.get(message_type, CompressionType.NONE)
        
        # Skip compression for small messages
        if original_size < self.min_compression_size:
            compression_type = CompressionType.NONE
        
        compressed_data = original_data
        is_full_state = True
        algorithm_used = CompressionType.NONE
        
        try:
            if compression_type == CompressionType.ZLIB:
                compressed_data = self._compress_zlib(original_data)
                algorithm_used = CompressionType.ZLIB
                
            elif compression_type == CompressionType.DELTA and entity_id:
                delta_data, is_full_state = self.delta_compressor.compress_state(entity_id, data)
                compressed_data = json.dumps(delta_data, separators=(',', ':')).encode('utf-8')
                algorithm_used = CompressionType.DELTA
                
            elif compression_type == CompressionType.HYBRID:
                # Try both delta and zlib, use best
                if entity_id:
                    delta_data, is_full_state = self.delta_compressor.compress_state(entity_id, data)
                    delta_compressed = json.dumps(delta_data, separators=(',', ':')).encode('utf-8')
                    zlib_compressed = self._compress_zlib(original_data)
                    
                    if len(delta_compressed) < len(zlib_compressed):
                        compressed_data = delta_compressed
                        algorithm_used = CompressionType.DELTA
                    else:
                        compressed_data = zlib_compressed
                        algorithm_used = CompressionType.ZLIB
                        is_full_state = True
                else:
                    compressed_data = self._compress_zlib(original_data)
                    algorithm_used = CompressionType.ZLIB
        
        except Exception as e:
            # Fallback to uncompressed
            print(f"Compression failed for {message_type}: {e}")
            compressed_data = original_data
            algorithm_used = CompressionType.NONE
        
        # Check if compression was effective
        compression_ratio = len(compressed_data) / original_size
        if compression_ratio > self.compression_ratio_threshold:
            # Compression not effective, use original
            compressed_data = original_data
            algorithm_used = CompressionType.NONE
            is_full_state = True
        
        compression_time = time.time() - start_time
        compressed_size = len(compressed_data)
        
        # Update statistics
        stats_key = f"{message_type.value}_{algorithm_used}"
        if stats_key not in self.stats:
            self.stats[stats_key] = CompressionStats()
        
        stats = self.stats[stats_key]
        stats.original_size += original_size
        stats.compressed_size += compressed_size
        stats.compression_ratio = stats.compressed_size / stats.original_size if stats.original_size > 0 else 1.0
        stats.compression_time += compression_time
        stats.algorithm_used = algorithm_used
        
        # Metadata for decompression
        metadata = {
            'algorithm': algorithm_used,
            'original_size': original_size,
            'compressed_size': compressed_size,
            'is_full_state': is_full_state,
            'entity_id': entity_id,
            'message_type': message_type.value
        }
        
        return compressed_data, metadata
    
    def decompress_message(self, compressed_data: bytes, 
                          metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Decompress message data.
        
        Args:
            compressed_data: Compressed data
            metadata: Compression metadata
            
        Returns:
            Decompressed message data
        """
        start_time = time.time()
        algorithm = metadata.get('algorithm', CompressionType.NONE)
        entity_id = metadata.get('entity_id')
        is_full_state = metadata.get('is_full_state', True)
        message_type = MessageType(metadata.get('message_type'))
        
        try:
            if algorithm == CompressionType.NONE:
                # No compression
                decompressed_data = json.loads(compressed_data.decode('utf-8'))
                
            elif algorithm == CompressionType.ZLIB:
                # Zlib compression
                decompressed_bytes = self._decompress_zlib(compressed_data)
                decompressed_data = json.loads(decompressed_bytes.decode('utf-8'))
                
            elif algorithm == CompressionType.DELTA:
                # Delta compression
                delta_data = json.loads(compressed_data.decode('utf-8'))
                decompressed_data = self.delta_compressor.decompress_state(
                    entity_id, delta_data, is_full_state
                )
                
            else:
                raise ValueError(f"Unknown compression algorithm: {algorithm}")
        
        except Exception as e:
            print(f"Decompression failed: {e}")
            raise
        
        # Update decompression time statistics
        decompression_time = time.time() - start_time
        stats_key = f"{message_type.value}_{algorithm}"
        if stats_key in self.stats:
            self.stats[stats_key].decompression_time += decompression_time
        
        return decompressed_data
    
    def _compress_zlib(self, data: bytes) -> bytes:
        """Compress data using zlib."""
        return zlib.compress(data, level=6)
    
    def _decompress_zlib(self, compressed_data: bytes) -> bytes:
        """Decompress zlib data."""
        return zlib.decompress(compressed_data)
    
    def set_compression_method(self, message_type: MessageType, 
                              compression_type: str):
        """Set compression method for message type."""
        self.compression_settings[message_type] = compression_type
    
    def get_compression_stats(self) -> Dict[str, Any]:
        """Get compression statistics."""
        total_stats = {
            'total_original_size': sum(stats.original_size for stats in self.stats.values()),
            'total_compressed_size': sum(stats.compressed_size for stats in self.stats.values()),
            'total_compression_time': sum(stats.compression_time for stats in self.stats.values()),
            'total_decompression_time': sum(stats.decompression_time for stats in self.stats.values()),
            'overall_compression_ratio': 0.0,
            'by_message_type': {}
        }
        
        if total_stats['total_original_size'] > 0:
            total_stats['overall_compression_ratio'] = (
                total_stats['total_compressed_size'] / total_stats['total_original_size']
            )
        
        # Per message type stats
        for key, stats in self.stats.items():
            total_stats['by_message_type'][key] = {
                'original_size': stats.original_size,
                'compressed_size': stats.compressed_size,
                'compression_ratio': stats.compression_ratio,
                'compression_time': stats.compression_time,
                'decompression_time': stats.decompression_time,
                'algorithm': stats.algorithm_used
            }
        
        return total_stats
    
    def reset_stats(self):
        """Reset compression statistics."""
        self.stats.clear()
    
    def clear_delta_history(self, entity_id: Optional[str] = None):
        """Clear delta compression history."""
        self.delta_compressor.clear_history(entity_id)


class StreamCompressor:
    """
    Stream-based compression for continuous data.
    
    Useful for compressing streams of similar messages
    or large data transfers.
    """
    
    def __init__(self, window_size: int = 32768):
        """
        Initialize stream compressor.
        
        Args:
            window_size: Compression window size
        """
        self.window_size = window_size
        self.compressor = zlib.compressobj(level=6, wbits=-15)
        self.decompressor = zlib.decompressobj(wbits=-15)
        self.compression_buffer = b''
        
    def compress_chunk(self, data: bytes) -> bytes:
        """Compress a chunk of data."""
        return self.compressor.compress(data)
    
    def flush_compression(self) -> bytes:
        """Flush compression buffer."""
        return self.compressor.flush()
    
    def decompress_chunk(self, compressed_data: bytes) -> bytes:
        """Decompress a chunk of data."""
        return self.decompressor.decompress(compressed_data)
    
    def reset(self):
        """Reset compression state."""
        self.compressor = zlib.compressobj(level=6, wbits=-15)
        self.decompressor = zlib.decompressobj(wbits=-15)


# Global compression instance
message_compressor = MessageCompressor()
