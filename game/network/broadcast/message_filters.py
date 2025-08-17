"""
Message Filtering System for PyCraft 2D Multiplayer

Provides interest management and message filtering to optimize network traffic
by only sending relevant messages to each client.
"""

import time
from typing import Dict, List, Set, Optional, Any, Callable
from enum import Enum
from dataclasses import dataclass
from abc import ABC, abstractmethod

from ..message_types import MessageType


class FilterResult(Enum):
    """Result of message filtering."""
    ALLOW = "allow"      # Send the message
    DENY = "deny"        # Don't send the message
    MODIFY = "modify"    # Send modified version


@dataclass
class FilterContext:
    """Context information for message filtering."""
    client_id: str
    client_position: tuple
    client_chunk: tuple
    message_type: MessageType
    message_data: Dict[str, Any]
    sender_id: Optional[str] = None
    timestamp: float = 0.0


class MessageFilter(ABC):
    """Base class for message filters."""
    
    def __init__(self, name: str, enabled: bool = True):
        """
        Initialize message filter.
        
        Args:
            name: Filter name for debugging
            enabled: Whether filter is active
        """
        self.name = name
        self.enabled = enabled
        self.stats = {
            'messages_processed': 0,
            'messages_allowed': 0,
            'messages_denied': 0,
            'messages_modified': 0
        }
    
    @abstractmethod
    def filter_message(self, context: FilterContext) -> FilterResult:
        """
        Filter a message for a specific client.
        
        Args:
            context: Filter context with client and message info
            
        Returns:
            Filter result (allow, deny, or modify)
        """
        pass
    
    def filter_clients(self, message: Dict[str, Any], clients: Dict[str, Any], 
                      sender_context: Dict[str, Any] = None) -> List[str]:
        """
        Filter clients that should receive a message.
        
        Args:
            message: Message data
            clients: Dictionary of client_id -> client_info
            sender_context: Additional context about sender
            
        Returns:
            List of client IDs that should receive the message
        """
        filtered_clients = []
        
        for client_id, client_info in clients.items():
            context = FilterContext(
                client_id=client_id,
                message_type=MessageType.CHAT_MESSAGE,  # Default type
                message_data=message,
                sender_id=sender_context.get('sender_id') if sender_context else None,
                timestamp=time.time(),
                client_position=client_info.get('position', (0, 0)),
                client_chunk=client_info.get('chunk', (0, 0))
            )
            
            result = self.filter_message(context)
            if result == FilterResult.ALLOW:
                filtered_clients.append(client_id)
        
        return filtered_clients
    
    def process_message(self, context: FilterContext) -> FilterResult:
        """
        Process message through filter with statistics tracking.
        
        Args:
            context: Filter context
            
        Returns:
            Filter result
        """
        if not self.enabled:
            return FilterResult.ALLOW
        
        self.stats['messages_processed'] += 1
        result = self.filter_message(context)
        
        if result == FilterResult.ALLOW:
            self.stats['messages_allowed'] += 1
        elif result == FilterResult.DENY:
            self.stats['messages_denied'] += 1
        elif result == FilterResult.MODIFY:
            self.stats['messages_modified'] += 1
        
        return result
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get filter statistics."""
        return {
            'name': self.name,
            'enabled': self.enabled,
            **self.stats
        }


class SpatialFilter(MessageFilter):
    """Filter messages based on spatial relevance."""
    
    def __init__(self, max_distance: float = 500.0):
        """
        Initialize spatial filter.
        
        Args:
            max_distance: Maximum distance for spatial relevance
        """
        super().__init__("SpatialFilter")
        self.max_distance = max_distance
        self.spatial_message_types = {
            MessageType.ENTITY_UPDATE,
            MessageType.PLAYER_UPDATE,
            MessageType.FLOATING_ITEM_SPAWN,
            MessageType.ENTITY_SPAWN,
            MessageType.BLOCK_UPDATE
        }
    
    def filter_message(self, context: FilterContext) -> FilterResult:
        """Filter based on spatial distance."""
        # Only apply to spatial message types
        if context.message_type not in self.spatial_message_types:
            return FilterResult.ALLOW
        
        # Get message position
        message_pos = self._extract_position(context.message_data)
        if not message_pos:
            return FilterResult.ALLOW
        
        # Calculate distance
        client_x, client_y = context.client_position
        msg_x, msg_y = message_pos
        distance = ((client_x - msg_x) ** 2 + (client_y - msg_y) ** 2) ** 0.5
        
        return FilterResult.ALLOW if distance <= self.max_distance else FilterResult.DENY
    
    def _extract_position(self, data: Dict[str, Any]) -> Optional[tuple]:
        """Extract position from message data."""
        # Try common position field names
        for pos_field in ['position', 'pos', 'x,y', 'location']:
            if pos_field in data:
                pos = data[pos_field]
                if isinstance(pos, (list, tuple)) and len(pos) >= 2:
                    return (float(pos[0]), float(pos[1]))
        
        # Try separate x, y fields
        if 'x' in data and 'y' in data:
            return (float(data['x']), float(data['y']))
        
        return None


class ChunkFilter(MessageFilter):
    """Filter messages based on chunk relevance."""
    
    def __init__(self, chunk_size: int = 64, chunk_radius: int = 2):
        """
        Initialize chunk filter.
        
        Args:
            chunk_size: Size of each chunk in world units
            chunk_radius: Radius of chunks to include around client
        """
        super().__init__("ChunkFilter")
        self.chunk_size = chunk_size
        self.chunk_radius = chunk_radius
        self.chunk_message_types = {
            MessageType.BLOCK_UPDATE,
            MessageType.CHUNK_DATA,
            MessageType.ENTITY_SPAWN,
            MessageType.ENTITY_DESPAWN,
            MessageType.FLOATING_ITEM_SPAWN
        }
    
    def filter_message(self, context: FilterContext) -> FilterResult:
        """Filter based on chunk relevance."""
        if context.message_type not in self.chunk_message_types:
            return FilterResult.ALLOW
        
        # Get message chunk
        message_chunk = self._extract_chunk(context.message_data)
        if not message_chunk:
            return FilterResult.ALLOW
        
        # Check if message chunk is within client's interest area
        client_chunk_x, client_chunk_y = context.client_chunk
        msg_chunk_x, msg_chunk_y = message_chunk
        
        chunk_distance = max(
            abs(client_chunk_x - msg_chunk_x),
            abs(client_chunk_y - msg_chunk_y)
        )
        
        return FilterResult.ALLOW if chunk_distance <= self.chunk_radius else FilterResult.DENY
    
    def _extract_chunk(self, data: Dict[str, Any]) -> Optional[tuple]:
        """Extract chunk coordinates from message data."""
        # Direct chunk coordinates
        if 'chunk_x' in data and 'chunk_y' in data:
            return (int(data['chunk_x']), int(data['chunk_y']))
        
        if 'chunk' in data:
            chunk = data['chunk']
            if isinstance(chunk, (list, tuple)) and len(chunk) >= 2:
                return (int(chunk[0]), int(chunk[1]))
        
        # Convert from world position
        position = self._extract_position(data)
        if position:
            x, y = position
            return (int(x // self.chunk_size), int(y // self.chunk_size))
        
        return None
    
    def _extract_position(self, data: Dict[str, Any]) -> Optional[tuple]:
        """Extract position from message data."""
        for pos_field in ['position', 'pos', 'location']:
            if pos_field in data:
                pos = data[pos_field]
                if isinstance(pos, (list, tuple)) and len(pos) >= 2:
                    return (float(pos[0]), float(pos[1]))
        
        if 'x' in data and 'y' in data:
            return (float(data['x']), float(data['y']))
        
        return None


class PrivacyFilter(MessageFilter):
    """Filter messages containing private or sensitive data."""
    
    def __init__(self):
        """Initialize privacy filter."""
        super().__init__("PrivacyFilter")
        self.private_message_types = {
            MessageType.INVENTORY_UPDATE,
            MessageType.CHAT_MESSAGE,  # Direct messages only
            MessageType.PLAYER_INVENTORY  # Use available MessageType
        }
        self.private_fields = {
            'inventory', 'health', 'experience', 'private_data',
            'ip_address', 'session_token', 'password'
        }
    
    def filter_message(self, context: FilterContext) -> FilterResult:
        """Filter private messages."""
        # Allow private messages to their intended recipient
        if context.message_type in self.private_message_types:
            target_id = context.message_data.get('target_id') or context.message_data.get('player_id')
            if target_id and target_id != context.client_id:
                return FilterResult.DENY
        
        # Check for private fields in message data
        if self._contains_private_data(context.message_data, context.client_id):
            return FilterResult.MODIFY  # Will need to strip private fields
        
        return FilterResult.ALLOW
    
    def _contains_private_data(self, data: Dict[str, Any], client_id: str) -> bool:
        """Check if message contains private data not belonging to client."""
        # Check if this is another player's private data
        owner_id = data.get('player_id') or data.get('owner_id')
        if owner_id and owner_id != client_id:
            return any(field in data for field in self.private_fields)
        
        return False


class RateLimitFilter(MessageFilter):
    """Filter messages to prevent spam and rate limiting."""
    
    def __init__(self, max_messages_per_second: float = 10.0):
        """
        Initialize rate limit filter.
        
        Args:
            max_messages_per_second: Maximum messages per second per client
        """
        super().__init__("RateLimitFilter")
        self.max_messages_per_second = max_messages_per_second
        self.client_timestamps: Dict[str, List[float]] = {}
        self.window_size = 1.0  # 1 second window
    
    def filter_message(self, context: FilterContext) -> FilterResult:
        """Filter based on rate limiting."""
        current_time = time.time()
        client_id = context.client_id
        
        # Initialize client timestamp list
        if client_id not in self.client_timestamps:
            self.client_timestamps[client_id] = []
        
        timestamps = self.client_timestamps[client_id]
        
        # Remove old timestamps outside the window
        cutoff_time = current_time - self.window_size
        timestamps[:] = [t for t in timestamps if t > cutoff_time]
        
        # Check rate limit
        if len(timestamps) >= self.max_messages_per_second:
            return FilterResult.DENY
        
        # Add current timestamp
        timestamps.append(current_time)
        
        return FilterResult.ALLOW


class RelevanceFilter(MessageFilter):
    """Filter messages based on content relevance to client."""
    
    def __init__(self):
        """Initialize relevance filter."""
        super().__init__("RelevanceFilter")
        self.relevance_checkers: Dict[MessageType, Callable] = {
            MessageType.PLAYER_UPDATE: self._check_player_relevance,
            MessageType.ENTITY_UPDATE: self._check_entity_relevance,
            MessageType.CHAT_MESSAGE: self._check_chat_relevance
        }
    
    def filter_message(self, context: FilterContext) -> FilterResult:
        """Filter based on message relevance."""
        checker = self.relevance_checkers.get(context.message_type)
        if not checker:
            return FilterResult.ALLOW
        
        return FilterResult.ALLOW if checker(context) else FilterResult.DENY
    
    def _check_player_relevance(self, context: FilterContext) -> bool:
        """Check if player update is relevant."""
        # Always relevant if it's about the client themselves
        player_id = context.message_data.get('player_id')
        if player_id == context.client_id:
            return True
        
        # Check if player is in visible range
        player_pos = self._extract_position(context.message_data)
        if not player_pos:
            return True  # Assume relevant if no position
        
        client_x, client_y = context.client_position
        player_x, player_y = player_pos
        distance = ((client_x - player_x) ** 2 + (client_y - player_y) ** 2) ** 0.5
        
        return distance <= 300.0  # Visible range
    
    def _check_entity_relevance(self, context: FilterContext) -> bool:
        """Check if entity update is relevant."""
        # Similar to player relevance but with different range
        entity_pos = self._extract_position(context.message_data)
        if not entity_pos:
            return True
        
        client_x, client_y = context.client_position
        entity_x, entity_y = entity_pos
        distance = ((client_x - entity_x) ** 2 + (client_y - entity_y) ** 2) ** 0.5
        
        return distance <= 400.0  # Entity visibility range
    
    def _check_chat_relevance(self, context: FilterContext) -> bool:
        """Check if chat message is relevant."""
        # Global chat is always relevant
        is_global = context.message_data.get('is_global', True)
        if is_global:
            return True
        
        # Local chat based on proximity
        sender_pos = self._extract_position(context.message_data)
        if not sender_pos:
            return True  # Assume relevant if no position
        
        client_x, client_y = context.client_position
        sender_x, sender_y = sender_pos
        distance = ((client_x - sender_x) ** 2 + (client_y - sender_y) ** 2) ** 0.5
        
        return distance <= 100.0  # Local chat range
    
    def _extract_position(self, data: Dict[str, Any]) -> Optional[tuple]:
        """Extract position from message data."""
        for pos_field in ['position', 'pos', 'location']:
            if pos_field in data:
                pos = data[pos_field]
                if isinstance(pos, (list, tuple)) and len(pos) >= 2:
                    return (float(pos[0]), float(pos[1]))
        
        if 'x' in data and 'y' in data:
            return (float(data['x']), float(data['y']))
        
        return None


class InterestManager:
    """
    Manages client interest areas and message filtering.
    
    Coordinates multiple filters to optimize message delivery.
    """
    
    def __init__(self):
        """Initialize interest manager."""
        self.filters: List[MessageFilter] = []
        self.client_interests: Dict[str, Set[tuple]] = {}  # client_id -> chunk set
        self.stats = {
            'total_messages': 0,
            'messages_allowed': 0,
            'messages_denied': 0,
            'messages_modified': 0
        }
        
        # Add default filters
        self.add_filter(SpatialFilter())
        self.add_filter(ChunkFilter())
        self.add_filter(PrivacyFilter())
        self.add_filter(RateLimitFilter())
        self.add_filter(RelevanceFilter())
    
    def add_filter(self, filter_instance: MessageFilter):
        """Add a message filter."""
        self.filters.append(filter_instance)
    
    def remove_filter(self, filter_name: str):
        """Remove a message filter by name."""
        self.filters = [f for f in self.filters if f.name != filter_name]
    
    def should_send_message(self, client_id: str, client_position: tuple,
                           client_chunk: tuple, message_type: MessageType,
                           message_data: Dict[str, Any],
                           sender_id: Optional[str] = None) -> bool:
        """
        Determine if message should be sent to client.
        
        Args:
            client_id: Target client ID
            client_position: Client position (x, y)
            client_chunk: Client chunk coordinates
            message_type: Type of message
            message_data: Message data
            sender_id: ID of message sender
            
        Returns:
            True if message should be sent
        """
        self.stats['total_messages'] += 1
        
        context = FilterContext(
            client_id=client_id,
            client_position=client_position,
            client_chunk=client_chunk,
            message_type=message_type,
            message_data=message_data,
            sender_id=sender_id,
            timestamp=time.time()
        )
        
        # Run through all filters
        for filter_instance in self.filters:
            result = filter_instance.process_message(context)
            
            if result == FilterResult.DENY:
                self.stats['messages_denied'] += 1
                return False
            elif result == FilterResult.MODIFY:
                self.stats['messages_modified'] += 1
                # TODO: Apply modifications to message_data
                continue
        
        self.stats['messages_allowed'] += 1
        return True
    
    def update_client_interest(self, client_id: str, chunk_coords: Set[tuple]):
        """Update client's area of interest."""
        self.client_interests[client_id] = chunk_coords
    
    def get_interested_clients(self, chunk_coords: tuple) -> Set[str]:
        """Get clients interested in a specific chunk."""
        interested = set()
        for client_id, interests in self.client_interests.items():
            if chunk_coords in interests:
                interested.add(client_id)
        return interested
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get interest manager and filter statistics."""
        filter_stats = [f.get_statistics() for f in self.filters]
        
        return {
            'total_stats': self.stats,
            'filter_stats': filter_stats,
            'active_filters': len(self.filters),
            'clients_tracked': len(self.client_interests)
        }
