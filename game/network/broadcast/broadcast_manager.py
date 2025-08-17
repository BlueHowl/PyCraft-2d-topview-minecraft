"""
Broadcast Manager for PyCraft 2D Multiplayer

Central hub for managing message distribution across all connected clients.
Provides efficient broadcasting patterns, message filtering, and performance optimization.
"""

import time
import threading
from typing import Dict, List, Set, Optional, Any, Callable
from enum import Enum
from dataclasses import dataclass, field
from collections import defaultdict

from ..message_types import MessageType


def log_info(message: str):
    """Simple logging function."""
    print(f"[BroadcastManager] {message}")


def log_debug(message: str):
    """Simple debug logging function."""
    print(f"[BroadcastManager DEBUG] {message}")


@dataclass
class ClientInfo:
    """Information about a connected client."""
    client_id: str
    position: tuple = (0, 0)
    chunk_coords: tuple = (0, 0)
    last_update: float = field(default_factory=time.time)
    interests: Set[str] = field(default_factory=set)
    connection_quality: float = 1.0  # 0.0 to 1.0


@dataclass
class BroadcastConfig:
    """Configuration for the broadcast manager."""
    max_queue_size: int = 10000
    batch_size: int = 10
    batch_timeout: float = 0.05
    compression_enabled: bool = True
    spatial_filtering_enabled: bool = True
    performance_monitoring_enabled: bool = True
    reliable_delivery_enabled: bool = True
    max_retry_attempts: int = 3
    chunk_broadcast_enabled: bool = True
    proximity_broadcast_range: float = 100.0


class BroadcastType(Enum):
    """Types of broadcast patterns."""
    UNICAST = "unicast"           # Send to specific client
    MULTICAST = "multicast"       # Send to specific group
    BROADCAST = "broadcast"       # Send to all clients
    PROXIMITY = "proximity"       # Send to clients within range
    CHUNK_CAST = "chunk_cast"     # Send to clients in same chunk
    RELIABLE = "reliable"         # Guaranteed delivery with ACK


class MessagePriority(Enum):
    """Message priority levels."""
    CRITICAL = 0    # Must be sent immediately (e.g., connection events)
    HIGH = 1        # Important game events (e.g., player death)
    NORMAL = 2      # Regular updates (e.g., position updates)
    LOW = 3         # Optional updates (e.g., cosmetic effects)
    BULK = 4        # Bulk data (e.g., chunk data)


@dataclass
class BroadcastMessage:
    """A message to be broadcasted."""
    message_type: MessageType
    data: Dict[str, Any]
    targets: Set[str] = field(default_factory=set)  # Client IDs
    broadcast_type: BroadcastType = BroadcastType.BROADCAST
    priority: MessagePriority = MessagePriority.NORMAL
    reliable: bool = False
    timestamp: float = field(default_factory=time.time)
    attempts: int = 0
    max_attempts: int = 3
    
    # Spatial filtering
    origin_position: Optional[tuple] = None  # (x, y) for proximity/chunk casting
    max_distance: Optional[float] = None
    chunk_coords: Optional[tuple] = None  # (chunk_x, chunk_y)
    
    # Filtering criteria
    exclude_sender: bool = True
    sender_id: Optional[str] = None
    filter_func: Optional[Callable] = None


@dataclass
class ClientInfo:
    """Information about a connected client for broadcasting."""
    client_id: str
    position: tuple = (0, 0)  # (x, y)
    chunk_coords: tuple = (0, 0)  # (chunk_x, chunk_y)
    interest_areas: Set[tuple] = field(default_factory=set)  # Chunks of interest
    connection_quality: float = 1.0  # 0.0 (poor) to 1.0 (excellent)
    last_update: float = field(default_factory=time.time)
    is_active: bool = True


def log_info(message: str):
    """Log info message."""
    print(f"INFO: {message}")

def log_warning(message: str):
    """Log warning message."""
    print(f"WARNING: {message}")

def log_error(message: str):
    """Log error message."""
    print(f"ERROR: {message}")

def log_debug(message: str):
    """Log debug message."""
    print(f"DEBUG: {message}")


class BroadcastManager:
    """
    Manages message broadcasting across all connected clients.
    
    Provides efficient message distribution with various broadcasting patterns,
    priority queuing, message filtering, and performance optimization.
    """
    
    def __init__(self, config: BroadcastConfig = None, server=None):
        """
        Initialize broadcast manager.
        
        Args:
            config: Broadcast configuration
            server: Reference to game server for client access
        """
        self.config = config or BroadcastConfig()
        self.server = server
        
        # Client management
        self.clients: Dict[str, ClientInfo] = {}
        self.client_connections: Dict[str, Any] = {}  # Client connection objects
        
        # Message queuing (use new system)
        from .message_queue import MessageQueue
        from .message_filters import InterestManager
        from .compression import MessageCompressor
        from .performance_monitor import performance_monitor
        
        self.message_queue = MessageQueue(max_queue_size=self.config.max_queue_size)
        self.interest_manager = InterestManager() if self.config.spatial_filtering_enabled else None
        self.message_compressor = MessageCompressor() if self.config.compression_enabled else None
        self.performance_monitor = performance_monitor if self.config.performance_monitoring_enabled else None
        
        # Legacy message queues (keep for backward compatibility)
        self.message_queues: Dict[MessagePriority, List[BroadcastMessage]] = {
            priority: [] for priority in MessagePriority
        }
        self.pending_reliable: Dict[str, BroadcastMessage] = {}  # message_id -> message
        
        # Client manager reference (will be set externally)
        self.client_manager = None
        
        # Threading
        self.broadcast_thread: Optional[threading.Thread] = None
        self.running = False
        self.queue_lock = threading.Lock()
        
        # Performance settings (updated from config)
        self.max_messages_per_frame = 50
        self.batch_size = self.config.batch_size
        self.flush_interval = self.config.batch_timeout
        self.compression_threshold = 512  # Compress messages > 512 bytes
        
        # Statistics
        self.stats = {
            'messages_sent': 0,
            'messages_queued': 0,
            'messages_dropped': 0,
            'bytes_sent': 0,
            'compression_ratio': 0.0,
            'average_latency': 0.0
        }
        
        # Interest management
        self.chunk_subscribers: Dict[tuple, Set[str]] = defaultdict(set)  # chunk -> client_ids
        self.spatial_index: Dict[str, tuple] = {}  # client_id -> position
        
        log_info("BroadcastManager initialized")
    
    def start(self):
        """Start the broadcast manager."""
        if self.running:
            return
        
        self.running = True
        self.broadcast_thread = threading.Thread(
            target=self._broadcast_loop,
            name="BroadcastManager",
            daemon=True
        )
        self.broadcast_thread.start()
        log_info("BroadcastManager started")
    
    def stop(self):
        """Stop the broadcast manager."""
        self.running = False
        if self.broadcast_thread and self.broadcast_thread.is_alive():
            self.broadcast_thread.join(timeout=1.0)
        log_info("BroadcastManager stopped")
    
    def register_client(self, client_id: str, connection, position: tuple = (0, 0)):
        """
        Register a new client for broadcasting.
        
        Args:
            client_id: Unique client identifier
            connection: Client connection object
            position: Initial client position (x, y)
        """
        self.clients[client_id] = ClientInfo(
            client_id=client_id,
            position=position,
            chunk_coords=self._position_to_chunk(position)
        )
        self.client_connections[client_id] = connection
        self._update_spatial_index(client_id, position)
        
        log_info(f"Client {client_id} registered for broadcasting")
    
    def unregister_client(self, client_id: str):
        """
        Unregister a client from broadcasting.
        
        Args:
            client_id: Client identifier to remove
        """
        if client_id in self.clients:
            client_info = self.clients[client_id]
            
            # Remove from chunk subscriptions
            for chunk_coords in client_info.interest_areas:
                self.chunk_subscribers[chunk_coords].discard(client_id)
            
            # Remove from spatial index
            self.spatial_index.pop(client_id, None)
            
            # Clean up
            del self.clients[client_id]
            self.client_connections.pop(client_id, None)
            
            log_info(f"Client {client_id} unregistered from broadcasting")
    
    def update_client_position(self, client_id: str, position: tuple):
        """
        Update client position for spatial broadcasting.
        
        Args:
            client_id: Client identifier
            position: New position (x, y)
        """
        if client_id not in self.clients:
            return
        
        old_chunk = self.clients[client_id].chunk_coords
        new_chunk = self._position_to_chunk(position)
        
        # Update client info
        self.clients[client_id].position = position
        self.clients[client_id].chunk_coords = new_chunk
        self.clients[client_id].last_update = time.time()
        
        # Update spatial index
        self._update_spatial_index(client_id, position)
        
        # Update chunk subscriptions if changed
        if old_chunk != new_chunk:
            self.chunk_subscribers[old_chunk].discard(client_id)
            self.chunk_subscribers[new_chunk].add(client_id)
            self.clients[client_id].interest_areas.add(new_chunk)
    
    def broadcast_message(self, message_type: MessageType, data: Dict[str, Any], 
                         broadcast_type: BroadcastType = BroadcastType.BROADCAST,
                         priority: MessagePriority = MessagePriority.NORMAL,
                         **kwargs) -> str:
        """
        Queue a message for broadcasting.
        
        Args:
            message_type: Type of message to send
            data: Message data
            broadcast_type: How to broadcast the message
            priority: Message priority
            **kwargs: Additional broadcast parameters
            
        Returns:
            Message ID for tracking
        """
        message = BroadcastMessage(
            message_type=message_type,
            data=data,
            broadcast_type=broadcast_type,
            priority=priority,
            **kwargs
        )
        
        message_id = f"{message_type.name}_{time.time()}_{id(message)}"
        
        with self.queue_lock:
            self.message_queues[priority].append(message)
            self.stats['messages_queued'] += 1
        
        # Handle reliable messages
        if message.reliable:
            self.pending_reliable[message_id] = message
        
        return message_id
    
    def broadcast_to_all(self, message_type: MessageType, data: Dict[str, Any],
                        priority: MessagePriority = MessagePriority.NORMAL,
                        exclude_sender: str = None) -> bool:
        """Broadcast message to all connected clients."""
        try:
            from .message_queue import QueuedMessage
            
            message = QueuedMessage(
                priority=priority,
                message_type=message_type,
                data=data,
                sender_id=exclude_sender
            )
            
            # Add to new queue system
            if self.message_queue:
                return self.message_queue.enqueue(message)
            else:
                # Fallback to legacy system
                return self.broadcast_message(
                    message_type, data, BroadcastType.BROADCAST, priority,
                    sender_id=exclude_sender, exclude_sender=exclude_sender is not None
                ) is not None
        except Exception as e:
            log_info(f"Error in broadcast_to_all: {e}")
            return False
    
    def broadcast_to_client(self, client_id: str, message_type: MessageType, 
                           data: Dict[str, Any],
                           priority: MessagePriority = MessagePriority.NORMAL) -> str:
        """Send message to specific client."""
        return self.broadcast_message(
            message_type, data, BroadcastType.UNICAST, priority,
            targets={client_id}
        )
    
    def broadcast_to_chunk(self, message_type: MessageType, data: Dict[str, Any],
                          chunk_coords: tuple,
                          priority: MessagePriority = MessagePriority.NORMAL,
                          exclude_sender: str = None) -> bool:
        """Broadcast message to clients in specific chunk."""
        try:
            from .message_queue import QueuedMessage
            
            message = QueuedMessage(
                priority=priority,
                message_type=message_type,
                data=data,
                sender_id=exclude_sender
            )
            
            # Add to new queue system
            if self.message_queue:
                return self.message_queue.enqueue(message)
            else:
                # Fallback to legacy system
                return self.broadcast_message(
                    message_type, data, BroadcastType.CHUNK_CAST, priority,
                    chunk_coords=chunk_coords,
                    sender_id=exclude_sender, exclude_sender=exclude_sender is not None
                ) is not None
        except Exception as e:
            log_info(f"Error in chunk broadcast: {e}")
            return False
        """Broadcast message to all clients in a specific chunk."""
        return self.broadcast_message(
            message_type, data, BroadcastType.CHUNK_CAST, priority,
            chunk_coords=chunk_coords,
            sender_id=exclude_sender, exclude_sender=exclude_sender is not None
        )
    
    def broadcast_proximity(self, message_type: MessageType, data: Dict[str, Any],
                           center_position: tuple, radius: float,
                           priority: MessagePriority = MessagePriority.NORMAL,
                           exclude_sender: str = None) -> bool:
        """Broadcast message to clients within range of position."""
        try:
            from .message_queue import QueuedMessage
            
            message = QueuedMessage(
                priority=priority,
                message_type=message_type,
                data=data,
                sender_id=exclude_sender
            )
            
            # Add to new queue system
            if self.message_queue:
                return self.message_queue.enqueue(message)
            else:
                # Fallback to legacy system
                return self.broadcast_message(
                    message_type, data, BroadcastType.PROXIMITY, priority,
                    origin_position=center_position, max_distance=radius,
                    sender_id=exclude_sender, exclude_sender=exclude_sender is not None
                ) is not None
        except Exception as e:
            log_info(f"Error in proximity broadcast: {e}")
            return False
    
    def broadcast_to_clients(self, message_type: MessageType, data: Dict[str, Any],
                            target_clients: List[str],
                            priority: MessagePriority = MessagePriority.NORMAL) -> bool:
        """Broadcast message to specific list of clients."""
        try:
            from .message_queue import QueuedMessage
            
            message = QueuedMessage(
                priority=priority,
                message_type=message_type,
                data=data,
                targets=target_clients
            )
            
            # Add to new queue system
            if self.message_queue:
                return self.message_queue.enqueue(message)
            else:
                # Fallback: send to each client individually
                for client_id in target_clients:
                    self.broadcast_to_client(client_id, message_type, data, priority)
                return True
        except Exception as e:
            log_info(f"Error in clients broadcast: {e}")
            return False
    
    def _process_message_batch(self):
        """Process a batch of messages from the queue."""
        if not self.message_queue:
            return
        
        try:
            batch = self.message_queue.dequeue_batch()
            if not batch:
                return
            
            messages = batch.get_messages()
            if not messages:
                return
            
            for message in messages:
                self._send_message_to_targets(message)
                
        except Exception as e:
            log_info(f"Error processing message batch: {e}")
    
    def _send_message_to_targets(self, message):
        """Send a message to its targets."""
        if not self.client_manager:
            log_info("No client manager configured")
            return
        
        try:
            # Determine targets
            if not message.targets:
                # Broadcast to all
                clients = self.client_manager.get_all_clients()
                targets = list(clients.keys())
            else:
                targets = message.targets
            
            # Send to each target
            for target in targets:
                if self.client_manager.send_message:
                    self.client_manager.send_message(target, message.message_type, message.data)
                    
        except Exception as e:
            log_info(f"Error sending message to targets: {e}")
    
    def shutdown(self):
        """Shutdown the broadcast manager."""
        self.stop()
        if self.message_queue:
            self.message_queue.clear()
        log_info("BroadcastManager shutdown complete")

    def acknowledge_message(self, message_id: str, client_id: str):
        """Acknowledge receipt of reliable message."""
        if message_id in self.pending_reliable:
            message = self.pending_reliable[message_id]
            message.targets.discard(client_id)
            
            if not message.targets:
                del self.pending_reliable[message_id]
                log_debug(f"Reliable message {message_id} fully acknowledged")
    
    def _broadcast_loop(self):
        """Main broadcasting loop."""
        last_flush = time.time()
        
        while self.running:
            current_time = time.time()
            
            try:
                # Process messages by priority
                messages_processed = 0
                
                for priority in MessagePriority:
                    if messages_processed >= self.max_messages_per_frame:
                        break
                    
                    with self.queue_lock:
                        queue = self.message_queues[priority]
                        if not queue:
                            continue
                        
                        # Process batch of messages
                        batch_size = min(self.batch_size, len(queue), 
                                       self.max_messages_per_frame - messages_processed)
                        batch = queue[:batch_size]
                        del queue[:batch_size]
                    
                    for message in batch:
                        self._process_message(message)
                        messages_processed += 1
                
                # Handle reliable message retries
                self._process_reliable_retries(current_time)
                
                # Flush at regular intervals
                if current_time - last_flush >= self.flush_interval:
                    self._flush_connections()
                    last_flush = current_time
                
                # Sleep briefly to prevent busy waiting
                time.sleep(0.001)
                
            except Exception as e:
                log_error(f"Broadcast loop error: {e}")
                time.sleep(0.1)
    
    def _process_message(self, message: BroadcastMessage):
        """Process a single broadcast message."""
        try:
            # Determine target clients
            targets = self._determine_targets(message)
            
            if not targets:
                return
            
            # Apply message filtering
            targets = self._apply_filters(message, targets)
            
            if not targets:
                return
            
            # Send to targets
            for client_id in targets:
                if client_id in self.client_connections:
                    self._send_to_client(client_id, message)
            
            self.stats['messages_sent'] += 1
            
        except Exception as e:
            log_error(f"Error processing message {message.message_type}: {e}")
    
    def _determine_targets(self, message: BroadcastMessage) -> Set[str]:
        """Determine which clients should receive the message."""
        if message.broadcast_type == BroadcastType.UNICAST:
            return message.targets
        
        elif message.broadcast_type == BroadcastType.BROADCAST:
            targets = set(self.clients.keys())
            
        elif message.broadcast_type == BroadcastType.CHUNK_CAST:
            if message.chunk_coords:
                targets = self.chunk_subscribers[message.chunk_coords].copy()
            else:
                targets = set()
        
        elif message.broadcast_type == BroadcastType.PROXIMITY:
            targets = self._get_proximity_targets(message)
            
        elif message.broadcast_type == BroadcastType.MULTICAST:
            targets = message.targets
            
        else:
            targets = set()
        
        # Exclude sender if requested
        if message.exclude_sender and message.sender_id:
            targets.discard(message.sender_id)
        
        return targets
    
    def _get_proximity_targets(self, message: BroadcastMessage) -> Set[str]:
        """Get clients within proximity range."""
        if not message.origin_position or message.max_distance is None:
            return set()
        
        targets = set()
        origin_x, origin_y = message.origin_position
        max_dist_sq = message.max_distance ** 2
        
        for client_id, client_info in self.clients.items():
            if not client_info.is_active:
                continue
            
            client_x, client_y = client_info.position
            dist_sq = (client_x - origin_x) ** 2 + (client_y - origin_y) ** 2
            
            if dist_sq <= max_dist_sq:
                targets.add(client_id)
        
        return targets
    
    def _apply_filters(self, message: BroadcastMessage, targets: Set[str]) -> Set[str]:
        """Apply message filters to target list."""
        if message.filter_func:
            filtered_targets = set()
            for client_id in targets:
                if client_id in self.clients:
                    client_info = self.clients[client_id]
                    if message.filter_func(client_info, message):
                        filtered_targets.add(client_id)
            return filtered_targets
        
        return targets
    
    def _send_to_client(self, client_id: str, message: BroadcastMessage):
        """Send message to specific client."""
        try:
            connection = self.client_connections.get(client_id)
            if not connection:
                return
            
            # Use the connection's send method
            if hasattr(connection, 'send_message'):
                connection.send_message(message.message_type, message.data)
                self.stats['bytes_sent'] += len(str(message.data))
            else:
                log_warning(f"Client {client_id} connection has no send_message method")
                
        except Exception as e:
            log_error(f"Failed to send message to client {client_id}: {e}")
    
    def _process_reliable_retries(self, current_time: float):
        """Process retries for reliable messages."""
        retry_messages = []
        
        for message_id, message in list(self.pending_reliable.items()):
            if current_time - message.timestamp > 5.0:  # 5 second timeout
                if message.attempts < message.max_attempts:
                    message.attempts += 1
                    message.timestamp = current_time
                    retry_messages.append(message)
                    log_debug(f"Retrying reliable message {message_id} (attempt {message.attempts})")
                else:
                    del self.pending_reliable[message_id]
                    log_warning(f"Reliable message {message_id} failed after {message.max_attempts} attempts")
        
        # Re-queue retry messages
        for message in retry_messages:
            with self.queue_lock:
                self.message_queues[MessagePriority.HIGH].append(message)
    
    def _flush_connections(self):
        """Flush all client connections."""
        for connection in self.client_connections.values():
            if hasattr(connection, 'flush'):
                try:
                    connection.flush()
                except Exception as e:
                    log_debug(f"Error flushing connection: {e}")
    
    def _position_to_chunk(self, position: tuple) -> tuple:
        """Convert world position to chunk coordinates."""
        x, y = position
        chunk_size = 64  # Match game's chunk size
        return (int(x // chunk_size), int(y // chunk_size))
    
    def _update_spatial_index(self, client_id: str, position: tuple):
        """Update spatial index for proximity queries."""
        self.spatial_index[client_id] = position
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get broadcasting statistics."""
        total_queued = sum(len(queue) for queue in self.message_queues.values())
        
        return {
            **self.stats,
            'active_clients': len(self.clients),
            'queued_messages': total_queued,
            'pending_reliable': len(self.pending_reliable),
            'chunk_subscriptions': len(self.chunk_subscribers)
        }
    
    def clear_statistics(self):
        """Clear broadcasting statistics."""
        self.stats = {
            'messages_sent': 0,
            'messages_queued': 0,
            'messages_dropped': 0,
            'bytes_sent': 0,
            'compression_ratio': 0.0,
            'average_latency': 0.0
        }
