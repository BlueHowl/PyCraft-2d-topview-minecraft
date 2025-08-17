"""
Client Message Handler for PyCraft 2D Multiplayer

Handles processing of messages received from the game server.
"""

import time
from typing import Dict, Any, TYPE_CHECKING

from ..message_types import MessageType

if TYPE_CHECKING:
    from .game_client import GameClient

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


class ClientMessageHandler:
    """
    Handles processing of messages received from the game server.
    
    Routes messages to appropriate handlers and manages client state updates.
    """
    
    def __init__(self, client: 'GameClient'):
        """
        Initialize message handler.
        
        Args:
            client: Reference to game client
        """
        self.client = client
        
        # Message handlers map
        self.handlers = {
            MessageType.CONNECT_RESPONSE: self._handle_connect_response,
            MessageType.DISCONNECT: self._handle_disconnect,
            MessageType.PONG: self._handle_pong,
            MessageType.PLAYER_UPDATE: self._handle_player_update,
            MessageType.PLAYER_JOIN: self._handle_player_join,
            MessageType.PLAYER_LEAVE: self._handle_player_leave,
            MessageType.CHAT_MESSAGE: self._handle_chat_message,
            MessageType.CHAT_BROADCAST: self._handle_chat_broadcast,
            MessageType.BLOCK_UPDATE: self._handle_block_update,
            MessageType.CHUNK_DATA: self._handle_chunk_data,
            MessageType.ENTITY_SPAWN: self._handle_entity_spawn,
            MessageType.ENTITY_DESPAWN: self._handle_entity_despawn,
            MessageType.ENTITY_UPDATE: self._handle_entity_update,
            MessageType.INVENTORY_UPDATE: self._handle_inventory_update,
            MessageType.FLOATING_ITEM_SPAWN: self._handle_floating_item_spawn,
            MessageType.FLOATING_ITEM_PICKUP: self._handle_floating_item_pickup,
            MessageType.WORLD_TIME: self._handle_world_time,
            MessageType.SERVER_INFO: self._handle_server_info,
            MessageType.ERROR: self._handle_error,
        }
        
        # Statistics
        self.messages_handled = 0
        self.messages_by_type = {}
        
        log_debug("ClientMessageHandler initialized")
    
    def handle_message(self, message_type: MessageType, data: Dict[str, Any]):
        """
        Handle an incoming message from the server.
        
        Args:
            message_type: Type of message received
            data: Message data
        """
        # Update statistics
        self.messages_handled += 1
        type_name = message_type.name
        self.messages_by_type[type_name] = self.messages_by_type.get(type_name, 0) + 1
        
        # Route to handler
        handler = self.handlers.get(message_type)
        if handler:
            try:
                handler(data)
            except Exception as e:
                log_error(f"Handler error for {message_type.name}: {e}")
        else:
            log_warning(f"No handler for message type: {message_type.name}")
    
    def _handle_connect_response(self, data: Dict[str, Any]):
        """Handle connection response from server."""
        success = data.get('success', False)
        
        if success:
            self.client.player_id = data.get('player_id')
            self.client.server_info = data.get('server_info', {})
            
            # Initialize client world if needed
            if not self.client.world:
                from .client_game_world import ClientGameWorld
                self.client.world = ClientGameWorld(self.client)
            
            self.client.connection_manager.handle_authentication_success()
            log_info(f"Connected successfully as player {self.client.player_id}")
            
        else:
            error_message = data.get('error_message', 'Unknown error')
            log_error(f"Connection failed: {error_message}")
            from ..connection_manager import DisconnectReason
            self.client.connection_manager.handle_connection_lost(DisconnectReason.AUTHENTICATION_FAILED)
    
    def _handle_disconnect(self, data: Dict[str, Any]):
        """Handle disconnect message from server."""
        reason = data.get('reason', 'Unknown reason')
        log_info(f"Disconnected from server: {reason}")
        
        # Determine disconnect reason for connection manager
        from ..connection_manager import DisconnectReason
        disconnect_reason = DisconnectReason.SERVER_SHUTDOWN
        
        if 'kicked' in reason.lower():
            disconnect_reason = DisconnectReason.KICKED
        elif 'timeout' in reason.lower():
            disconnect_reason = DisconnectReason.TIMEOUT
        elif 'error' in reason.lower():
            disconnect_reason = DisconnectReason.PROTOCOL_ERROR
        elif 'maintenance' in reason.lower() or 'shutdown' in reason.lower():
            disconnect_reason = DisconnectReason.SERVER_SHUTDOWN
            
        self.client.connection_manager.handle_connection_lost(disconnect_reason)
    
    def _handle_pong(self, data: Dict[str, Any]):
        """Handle pong response."""
        ping_time = data.get('timestamp', 0)
        current_time = time.time()
        
        # Calculate round-trip time
        rtt = (current_time - ping_time) * 1000  # Convert to milliseconds
        self.client.record_ping(rtt)
        
        log_debug(f"Ping: {rtt:.1f}ms")
    
    def _handle_player_update(self, data: Dict[str, Any]):
        """Handle player state update."""
        player_id = data.get('player_id')
        
        if self.client.world:
            self.client.world.update_player(player_id, data)
        
        # If it's our player, update local state
        if player_id == self.client.player_id:
            # Update local player state if needed
            pass
    
    def _handle_player_join(self, data: Dict[str, Any]):
        """Handle player join notification."""
        player_id = data.get('player_id')
        player_name = data.get('player_name', 'Unknown')
        
        log_info(f"Player joined: {player_name}")
        
        if self.client.world:
            self.client.world.add_player(player_id, data)
        
        self.client._trigger_event('player_joined', data)
    
    def _handle_player_leave(self, data: Dict[str, Any]):
        """Handle player leave notification."""
        player_id = data.get('player_id')
        player_name = data.get('player_name', 'Unknown')
        reason = data.get('reason', '')
        
        log_info(f"Player left: {player_name} ({reason})")
        
        if self.client.world:
            self.client.world.remove_player(player_id)
        
        self.client._trigger_event('player_left', data)
    
    def _handle_chat_message(self, data: Dict[str, Any]):
        """Handle chat message."""
        player_name = data.get('player_name', 'Unknown')
        message = data.get('message', '')
        is_system = data.get('is_system', False)
        
        if is_system:
            log_info(f"[SYSTEM] {message}")
        else:
            log_info(f"<{player_name}> {message}")
        
        self.client._trigger_event('chat_message', data)
    
    def _handle_chat_broadcast(self, data: Dict[str, Any]):
        """Handle chat broadcast message."""
        self._handle_chat_message(data)  # Same handling as regular chat
    
    def _handle_block_update(self, data: Dict[str, Any]):
        """Handle block update from server."""
        x = data.get('x')
        y = data.get('y')
        block_id = data.get('block_id')
        
        if self.client.world and x is not None and y is not None:
            self.client.world.set_block(x, y, block_id)
            log_debug(f"Block updated at ({x}, {y}): {block_id}")
    
    def _handle_chunk_data(self, data: Dict[str, Any]):
        """Handle chunk data from server."""
        chunk_x = data.get('chunk_x')
        chunk_y = data.get('chunk_y')
        blocks = data.get('blocks', {})
        entities = data.get('entities', [])
        
        if self.client.world and chunk_x is not None and chunk_y is not None:
            self.client.world.load_chunk_data(chunk_x, chunk_y, blocks, entities)
            log_debug(f"Loaded chunk ({chunk_x}, {chunk_y})")
    
    def _handle_entity_spawn(self, data: Dict[str, Any]):
        """Handle entity spawn notification."""
        entity_id = data.get('entity_id')
        entity_type = data.get('entity_type')
        
        if self.client.world and entity_id:
            self.client.world.spawn_entity(entity_id, data)
            log_debug(f"Entity spawned: {entity_type} ({entity_id})")
    
    def _handle_entity_despawn(self, data: Dict[str, Any]):
        """Handle entity despawn notification."""
        entity_id = data.get('entity_id')
        
        if self.client.world and entity_id:
            self.client.world.despawn_entity(entity_id)
            log_debug(f"Entity despawned: {entity_id}")
    
    def _handle_entity_update(self, data: Dict[str, Any]):
        """Handle entity update."""
        entity_id = data.get('entity_id')
        
        if self.client.world and entity_id:
            self.client.world.update_entity(entity_id, data)
    
    def _handle_inventory_update(self, data: Dict[str, Any]):
        """Handle inventory update."""
        inventory = data.get('inventory', {})
        
        if self.client.world:
            self.client.world.update_local_inventory(inventory)
        
        log_debug("Inventory updated")
    
    def _handle_floating_item_spawn(self, data: Dict[str, Any]):
        """Handle floating item spawn."""
        item_id = data.get('item_id')
        item_type = data.get('item_type')
        x = data.get('x', 0)
        y = data.get('y', 0)
        quantity = data.get('quantity', 1)
        
        if self.client.world and item_id:
            self.client.world.spawn_floating_item(item_id, item_type, quantity, x, y)
            log_debug(f"Floating item spawned: {item_type} x{quantity} at ({x}, {y})")
    
    def _handle_floating_item_pickup(self, data: Dict[str, Any]):
        """Handle floating item pickup."""
        item_id = data.get('item_id')
        player_id = data.get('player_id')
        
        if self.client.world and item_id:
            self.client.world.remove_floating_item(item_id)
            log_debug(f"Floating item picked up: {item_id} by {player_id}")
    
    def _handle_world_time(self, data: Dict[str, Any]):
        """Handle world time update."""
        world_time = data.get('time', 0)
        
        if self.client.world:
            self.client.world.set_world_time(world_time)
    
    def _handle_server_info(self, data: Dict[str, Any]):
        """Handle server information update."""
        self.client.server_info.update(data)
        log_debug("Server info updated")
    
    def _handle_error(self, data: Dict[str, Any]):
        """Handle error message from server."""
        error_type = data.get('error', 'unknown')
        error_message = data.get('message', 'No details provided')
        
        log_error(f"Server error ({error_type}): {error_message}")
        self.client._trigger_event('error', data)
    
    def get_handler_stats(self) -> Dict[str, Any]:
        """
        Get message handler statistics.
        
        Returns:
            Dictionary of handler statistics
        """
        return {
            'total_messages_handled': self.messages_handled,
            'messages_by_type': self.messages_by_type.copy(),
            'handler_count': len(self.handlers)
        }
