"""
Broadcast Patterns for PyCraft 2D Multiplayer

Defines different broadcasting strategies for efficient message distribution.
"""

import time
from typing import Dict, List, Set, Optional, Any, Callable
from abc import ABC, abstractmethod
from enum import Enum
from dataclasses import dataclass

from ..message_types import MessageType


class DeliveryGuarantee(Enum):
    """Message delivery guarantee levels."""
    BEST_EFFORT = "best_effort"      # Fire and forget
    RELIABLE = "reliable"            # Guaranteed delivery with retries
    ORDERED = "ordered"              # Guaranteed order (implies reliable)


@dataclass
class BroadcastRequest:
    """Request for broadcasting a message."""
    message_type: MessageType
    data: Dict[str, Any]
    sender_id: Optional[str] = None
    delivery: DeliveryGuarantee = DeliveryGuarantee.BEST_EFFORT
    priority: int = 5  # 1 (highest) to 10 (lowest)
    max_retries: int = 3
    timeout: float = 5.0
    metadata: Dict[str, Any] = None


class BroadcastPattern(ABC):
    """Base class for broadcast patterns."""
    
    def __init__(self, name: str):
        """
        Initialize broadcast pattern.
        
        Args:
            name: Pattern name for identification
        """
        self.name = name
        self.stats = {
            'messages_sent': 0,
            'clients_reached': 0,
            'failures': 0,
            'average_latency': 0.0
        }
    
    @abstractmethod
    def broadcast(self, request: BroadcastRequest, client_manager) -> Set[str]:
        """
        Execute the broadcast pattern.
        
        Args:
            request: Broadcast request details
            client_manager: Manager for client connections
            
        Returns:
            Set of client IDs that received the message
        """
        pass
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get pattern statistics."""
        return {
            'pattern': self.name,
            **self.stats
        }


class UnicastPattern(BroadcastPattern):
    """Send message to a single specific client."""
    
    def __init__(self):
        """Initialize unicast pattern."""
        super().__init__("Unicast")
    
    def broadcast(self, request: BroadcastRequest, client_manager) -> Set[str]:
        """Send to specific client."""
        target_id = request.data.get('target_id')
        if not target_id:
            return set()
        
        if target_id in client_manager.clients:
            try:
                self._send_to_client(target_id, request, client_manager)
                self.stats['messages_sent'] += 1
                self.stats['clients_reached'] += 1
                return {target_id}
            except Exception as e:
                self.stats['failures'] += 1
                print(f"ERROR: Failed to send unicast to {target_id}: {e}")
        
        return set()
    
    def _send_to_client(self, client_id: str, request: BroadcastRequest, client_manager):
        """Send message to specific client."""
        connection = client_manager.get_client_connection(client_id)
        if connection and hasattr(connection, 'send_message'):
            connection.send_message(request.message_type, request.data)


class MulticastPattern(BroadcastPattern):
    """Send message to a specific group of clients."""
    
    def __init__(self):
        """Initialize multicast pattern."""
        super().__init__("Multicast")
    
    def broadcast(self, request: BroadcastRequest, client_manager) -> Set[str]:
        """Send to group of clients."""
        target_ids = request.data.get('target_ids', set())
        if isinstance(target_ids, list):
            target_ids = set(target_ids)
        
        successful_sends = set()
        
        for client_id in target_ids:
            if client_id in client_manager.clients:
                try:
                    self._send_to_client(client_id, request, client_manager)
                    successful_sends.add(client_id)
                except Exception as e:
                    self.stats['failures'] += 1
                    print(f"ERROR: Failed to send multicast to {client_id}: {e}")
        
        self.stats['messages_sent'] += 1
        self.stats['clients_reached'] += len(successful_sends)
        return successful_sends
    
    def _send_to_client(self, client_id: str, request: BroadcastRequest, client_manager):
        """Send message to specific client."""
        connection = client_manager.get_client_connection(client_id)
        if connection and hasattr(connection, 'send_message'):
            connection.send_message(request.message_type, request.data)


class BroadcastAllPattern(BroadcastPattern):
    """Send message to all connected clients."""
    
    def __init__(self, exclude_sender: bool = True):
        """
        Initialize broadcast all pattern.
        
        Args:
            exclude_sender: Whether to exclude message sender
        """
        super().__init__("BroadcastAll")
        self.exclude_sender = exclude_sender
    
    def broadcast(self, request: BroadcastRequest, client_manager) -> Set[str]:
        """Send to all clients."""
        all_clients = set(client_manager.clients.keys())
        
        # Exclude sender if configured
        if self.exclude_sender and request.sender_id:
            all_clients.discard(request.sender_id)
        
        successful_sends = set()
        
        for client_id in all_clients:
            try:
                self._send_to_client(client_id, request, client_manager)
                successful_sends.add(client_id)
            except Exception as e:
                self.stats['failures'] += 1
                print(f"ERROR: Failed to broadcast to {client_id}: {e}")
        
        self.stats['messages_sent'] += 1
        self.stats['clients_reached'] += len(successful_sends)
        return successful_sends
    
    def _send_to_client(self, client_id: str, request: BroadcastRequest, client_manager):
        """Send message to specific client."""
        connection = client_manager.get_client_connection(client_id)
        if connection and hasattr(connection, 'send_message'):
            connection.send_message(request.message_type, request.data)


class ProximityPattern(BroadcastPattern):
    """Send message to clients within a specific range."""
    
    def __init__(self, default_range: float = 500.0):
        """
        Initialize proximity pattern.
        
        Args:
            default_range: Default broadcast range in world units
        """
        super().__init__("Proximity")
        self.default_range = default_range
    
    def broadcast(self, request: BroadcastRequest, client_manager) -> Set[str]:
        """Send to clients within range."""
        # Get broadcast origin and range
        origin = self._get_origin_position(request, client_manager)
        if not origin:
            return set()
        
        broadcast_range = request.data.get('range', self.default_range)
        range_squared = broadcast_range ** 2
        
        # Find clients within range
        nearby_clients = set()
        origin_x, origin_y = origin
        
        for client_id, client_info in client_manager.clients.items():
            # Skip sender if configured
            if request.sender_id and client_id == request.sender_id:
                continue
            
            client_x, client_y = client_info.position
            distance_sq = (client_x - origin_x) ** 2 + (client_y - origin_y) ** 2
            
            if distance_sq <= range_squared:
                nearby_clients.add(client_id)
        
        # Send to nearby clients
        successful_sends = set()
        
        for client_id in nearby_clients:
            try:
                self._send_to_client(client_id, request, client_manager)
                successful_sends.add(client_id)
            except Exception as e:
                self.stats['failures'] += 1
                print(f"ERROR: Failed to send proximity message to {client_id}: {e}")
        
        self.stats['messages_sent'] += 1
        self.stats['clients_reached'] += len(successful_sends)
        return successful_sends
    
    def _get_origin_position(self, request: BroadcastRequest, client_manager) -> Optional[tuple]:
        """Get the origin position for proximity broadcast."""
        # Check if position is specified in request
        if 'origin_position' in request.data:
            pos = request.data['origin_position']
            if isinstance(pos, (list, tuple)) and len(pos) >= 2:
                return (float(pos[0]), float(pos[1]))
        
        # Check for x, y coordinates
        if 'x' in request.data and 'y' in request.data:
            return (float(request.data['x']), float(request.data['y']))
        
        # Use sender position if available
        if request.sender_id and request.sender_id in client_manager.clients:
            return client_manager.clients[request.sender_id].position
        
        return None
    
    def _send_to_client(self, client_id: str, request: BroadcastRequest, client_manager):
        """Send message to specific client."""
        connection = client_manager.get_client_connection(client_id)
        if connection and hasattr(connection, 'send_message'):
            connection.send_message(request.message_type, request.data)


class ChunkPattern(BroadcastPattern):
    """Send message to all clients in specific chunks."""
    
    def __init__(self, chunk_size: int = 64):
        """
        Initialize chunk pattern.
        
        Args:
            chunk_size: Size of each chunk in world units
        """
        super().__init__("Chunk")
        self.chunk_size = chunk_size
    
    def broadcast(self, request: BroadcastRequest, client_manager) -> Set[str]:
        """Send to clients in specified chunks."""
        target_chunks = self._get_target_chunks(request)
        if not target_chunks:
            return set()
        
        # Find clients in target chunks
        target_clients = set()
        
        for client_id, client_info in client_manager.clients.items():
            # Skip sender if configured
            if request.sender_id and client_id == request.sender_id:
                continue
            
            client_chunk = self._position_to_chunk(client_info.position)
            if client_chunk in target_chunks:
                target_clients.add(client_id)
        
        # Send to target clients
        successful_sends = set()
        
        for client_id in target_clients:
            try:
                self._send_to_client(client_id, request, client_manager)
                successful_sends.add(client_id)
            except Exception as e:
                self.stats['failures'] += 1
                print(f"ERROR: Failed to send chunk message to {client_id}: {e}")
        
        self.stats['messages_sent'] += 1
        self.stats['clients_reached'] += len(successful_sends)
        return successful_sends
    
    def _get_target_chunks(self, request: BroadcastRequest) -> Set[tuple]:
        """Get target chunk coordinates from request."""
        chunks = set()
        
        # Direct chunk specification
        if 'chunks' in request.data:
            chunk_list = request.data['chunks']
            for chunk in chunk_list:
                if isinstance(chunk, (list, tuple)) and len(chunk) >= 2:
                    chunks.add((int(chunk[0]), int(chunk[1])))
        
        # Single chunk specification
        if 'chunk_x' in request.data and 'chunk_y' in request.data:
            chunks.add((int(request.data['chunk_x']), int(request.data['chunk_y'])))
        
        # Position-based chunk
        if 'x' in request.data and 'y' in request.data:
            position = (float(request.data['x']), float(request.data['y']))
            chunks.add(self._position_to_chunk(position))
        
        return chunks
    
    def _position_to_chunk(self, position: tuple) -> tuple:
        """Convert world position to chunk coordinates."""
        x, y = position
        return (int(x // self.chunk_size), int(y // self.chunk_size))
    
    def _send_to_client(self, client_id: str, request: BroadcastRequest, client_manager):
        """Send message to specific client."""
        connection = client_manager.get_client_connection(client_id)
        if connection and hasattr(connection, 'send_message'):
            connection.send_message(request.message_type, request.data)


class ReliableBroadcastPattern(BroadcastPattern):
    """Send message with guaranteed delivery and acknowledgment."""
    
    def __init__(self, base_pattern: BroadcastPattern):
        """
        Initialize reliable broadcast pattern.
        
        Args:
            base_pattern: Underlying broadcast pattern to make reliable
        """
        super().__init__(f"Reliable{base_pattern.name}")
        self.base_pattern = base_pattern
        self.pending_messages: Dict[str, Dict] = {}  # message_id -> retry info
        self.next_message_id = 1
    
    def broadcast(self, request: BroadcastRequest, client_manager) -> Set[str]:
        """Send with reliable delivery."""
        # Generate unique message ID
        message_id = f"reliable_{self.next_message_id}_{time.time()}"
        self.next_message_id += 1
        
        # Add message ID to data for acknowledgment tracking
        reliable_data = request.data.copy()
        reliable_data['_message_id'] = message_id
        reliable_data['_requires_ack'] = True
        
        # Create reliable request
        reliable_request = BroadcastRequest(
            message_type=request.message_type,
            data=reliable_data,
            sender_id=request.sender_id,
            delivery=DeliveryGuarantee.RELIABLE,
            priority=request.priority,
            max_retries=request.max_retries,
            timeout=request.timeout,
            metadata=request.metadata
        )
        
        # Send using base pattern
        recipients = self.base_pattern.broadcast(reliable_request, client_manager)
        
        # Track for retries if needed
        if recipients and request.delivery == DeliveryGuarantee.RELIABLE:
            self.pending_messages[message_id] = {
                'request': reliable_request,
                'recipients': recipients.copy(),
                'timestamp': time.time(),
                'attempts': 1
            }
        
        self.stats['messages_sent'] += 1
        self.stats['clients_reached'] += len(recipients)
        
        return recipients
    
    def acknowledge_message(self, message_id: str, client_id: str):
        """Acknowledge message receipt."""
        if message_id in self.pending_messages:
            pending = self.pending_messages[message_id]
            pending['recipients'].discard(client_id)
            
            # Remove if all recipients acknowledged
            if not pending['recipients']:
                del self.pending_messages[message_id]
    
    def process_retries(self, client_manager):
        """Process retry logic for unreliable deliveries."""
        current_time = time.time()
        retry_messages = []
        
        for message_id, pending in list(self.pending_messages.items()):
            # Check if timeout exceeded
            if current_time - pending['timestamp'] > pending['request'].timeout:
                if pending['attempts'] < pending['request'].max_retries:
                    # Retry
                    pending['attempts'] += 1
                    pending['timestamp'] = current_time
                    retry_messages.append((message_id, pending))
                else:
                    # Give up
                    del self.pending_messages[message_id]
                    self.stats['failures'] += len(pending['recipients'])
                    print(f"WARNING: Reliable message {message_id} failed after {pending['attempts']} attempts")
        
        # Process retries
        for message_id, pending in retry_messages:
            # Only retry to clients that haven't acknowledged
            if pending['recipients']:
                # Create retry request targeting only unacknowledged clients
                retry_data = pending['request'].data.copy()
                retry_data['target_ids'] = list(pending['recipients'])
                
                retry_request = BroadcastRequest(
                    message_type=pending['request'].message_type,
                    data=retry_data,
                    sender_id=pending['request'].sender_id,
                    delivery=pending['request'].delivery,
                    priority=max(1, pending['request'].priority - 1),  # Higher priority for retries
                    max_retries=pending['request'].max_retries,
                    timeout=pending['request'].timeout
                )
                
                # Use multicast pattern for targeted retry
                multicast = MulticastPattern()
                multicast.broadcast(retry_request, client_manager)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get reliable broadcast statistics."""
        base_stats = super().get_statistics()
        base_stats.update({
            'pending_messages': len(self.pending_messages),
            'base_pattern': self.base_pattern.get_statistics()
        })
        return base_stats


class ConditionalPattern(BroadcastPattern):
    """Send message based on conditional logic."""
    
    def __init__(self, condition_func: Callable[[str, Dict], bool], 
                 base_pattern: BroadcastPattern):
        """
        Initialize conditional pattern.
        
        Args:
            condition_func: Function to determine if client should receive message
            base_pattern: Base pattern to use for actual sending
        """
        super().__init__(f"Conditional{base_pattern.name}")
        self.condition_func = condition_func
        self.base_pattern = base_pattern
    
    def broadcast(self, request: BroadcastRequest, client_manager) -> Set[str]:
        """Send based on conditions."""
        # Filter clients based on condition
        eligible_clients = set()
        
        for client_id, client_info in client_manager.clients.items():
            if self.condition_func(client_id, client_info.__dict__):
                eligible_clients.add(client_id)
        
        if not eligible_clients:
            return set()
        
        # Create filtered request
        filtered_data = request.data.copy()
        filtered_data['target_ids'] = list(eligible_clients)
        
        filtered_request = BroadcastRequest(
            message_type=request.message_type,
            data=filtered_data,
            sender_id=request.sender_id,
            delivery=request.delivery,
            priority=request.priority,
            max_retries=request.max_retries,
            timeout=request.timeout,
            metadata=request.metadata
        )
        
        # Use multicast pattern for filtered sending
        multicast = MulticastPattern()
        recipients = multicast.broadcast(filtered_request, client_manager)
        
        self.stats['messages_sent'] += 1
        self.stats['clients_reached'] += len(recipients)
        
        return recipients
