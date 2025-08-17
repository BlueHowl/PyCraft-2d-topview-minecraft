"""
Server Message Handler for PyCraft 2D

Handles all incoming messages from clients and processes them accordingly.
Coordinates between different server systems.
"""

import time
from typing import Dict, Any, Optional

from ..message_types import MessageType
from ..actions import create_action, create_action_from_data
from ...utils.logger import log_info, log_error, log_debug, log_warning


class ServerMessageHandler:
    """
    Handles incoming messages from clients.
    
    Routes messages to appropriate handlers and manages server responses.
    """
    
    def __init__(self, server):
        """
        Initialize the message handler.
        
        Args:
            server: Reference to the main GameServer instance
        """
        self.server = server
        
        # Message handlers map
        self.handlers = {
            MessageType.PLAYER_MOVE: self._handle_player_move,
            MessageType.PLAYER_ATTACK: self._handle_player_attack,
            MessageType.PLAYER_INTERACT: self._handle_player_interact,
            MessageType.CHAT_MESSAGE: self._handle_chat_message,
            MessageType.BLOCK_PLACE: self._handle_block_place,
            MessageType.BLOCK_BREAK: self._handle_block_break,
            MessageType.ITEM_PICKUP: self._handle_item_pickup,
            MessageType.ITEM_DROP: self._handle_item_drop,
            MessageType.INVENTORY_UPDATE: self._handle_inventory_update,
            MessageType.CRAFT_ITEM: self._handle_craft_item,
            MessageType.PLAYER_RESPAWN: self._handle_player_respawn,
            MessageType.CHUNK_REQUEST: self._handle_chunk_request,
            MessageType.WORLD_STATE: self._handle_world_state_request,
            MessageType.PLAYER_STATE_SYNC: self._handle_player_state_sync,
        }
        
        # Statistics
        self.messages_handled = 0
        self.messages_by_type = {}
        
        log_debug("ServerMessageHandler initialized")
    
    def handle_message(self, client_id: str, message_type: MessageType, data: dict):
        """
        Handle an incoming message from a client.
        
        Args:
            client_id: ID of the client that sent the message
            message_type: Type of the message
            data: Message data
        """
        try:
            # Update statistics
            self.messages_handled += 1
            type_name = message_type.name
            self.messages_by_type[type_name] = self.messages_by_type.get(type_name, 0) + 1
            
            # Get the handler
            handler = self.handlers.get(message_type)
            if handler:
                handler(client_id, data)
            else:
                log_warning(f"No handler for message type: {message_type.name} from {client_id}")
            
        except Exception as e:
            log_error(f"Error handling {message_type.name} from {client_id}: {e}")
            
            # Send error response to client
            self._send_error_response(client_id, f"Server error processing {message_type.name}")
    
    def _handle_player_move(self, client_id: str, data: dict):
        """Handle player movement messages."""
        client = self.server.clients.get(client_id)
        if not client or not client.player_id:
            return
        
        # Create move action
        action_data = {
            'action_type': 'move',
            'player_id': client.player_id,
            'direction': data.get('direction', 'right'),
            'velocity_x': data.get('velocity_x', 0),
            'velocity_y': data.get('velocity_y', 0),
            'timestamp': data.get('timestamp', time.time()),
            'action_id': data.get('action_id', f"move_{int(time.time() * 1000)}")
        }
        
        action = create_action_from_data(action_data)
        if action:
            self.server.queue_action(action)
        else:
            log_warning(f"Failed to create move action for {client_id}")
    
    def _handle_player_attack(self, client_id: str, data: dict):
        """Handle player attack actions."""
        client = self.server.clients.get(client_id)
        if not client or not client.player_id:
            return
        
        # Create attack action
        action = create_action(
            'attack',
            player_id=client.player_id,
            **data
        )
        if action:
            self.server.queue_action(action)
        else:
            log_warning(f"Failed to create attack action for {client_id}")
    
    def _handle_player_interact(self, client_id: str, data: dict):
        """Handle player interaction actions."""
        client = self.server.clients.get(client_id)
        if not client or not client.player_id:
            return
        
        # Create interact action
        action = create_action(
            'interact',
            player_id=client.player_id,
            **data
        )
        if action:
            self.server.queue_action(action)
        else:
            log_warning(f"Failed to create interact action for {client_id}")
    
    def _handle_chat_message(self, client_id: str, data: dict):
        """Handle chat messages."""
        client = self.server.clients.get(client_id)
        if not client or not client.player_id:
            return
        
        player_state = self.server.player_manager.get_player(client.player_id)
        if not player_state:
            return
        
        message = data.get('message', '').strip()
        if not message:
            return
        
        # Check for commands (starting with /)
        if message.startswith('/'):
            self._handle_chat_command(client_id, message[1:])
            return
        
        # Broadcast chat message to all clients
        chat_data = {
            'player_id': client.player_id,
            'player_name': player_state.player_name,
            'message': message,
            'timestamp': time.time()
        }
        
        self.server.broadcast_message(MessageType.CHAT_MESSAGE, chat_data)
        log_info(f"<{player_state.player_name}> {message}")
    
    def _handle_chat_command(self, client_id: str, command: str):
        """Handle chat commands."""
        client = self.server.clients.get(client_id)
        if not client or not client.player_id:
            return
        
        player_state = self.server.player_manager.get_player(client.player_id)
        if not player_state:
            return
        
        parts = command.split()
        if not parts:
            return
        
        cmd = parts[0].lower()
        args = parts[1:]
        
        # Process command
        if cmd == 'help':
            self._send_help_message(client_id)
        elif cmd == 'time':
            self._send_time_message(client_id)
        elif cmd == 'players':
            self._send_players_list(client_id)
        elif cmd == 'stats':
            self._send_player_stats(client_id)
        elif cmd == 'tp' and player_state.is_admin:
            self._handle_teleport_command(client_id, args)
        elif cmd == 'give' and player_state.is_admin:
            self._handle_give_command(client_id, args)
        elif cmd == 'kick' and player_state.is_admin:
            self._handle_kick_command(client_id, args)
        else:
            self._send_command_response(client_id, f"Unknown command: /{cmd}")
    
    def _handle_block_place(self, client_id: str, data: dict):
        """Handle block placement requests."""
        client = self.server.clients.get(client_id)
        if not client or not client.player_id:
            return
        
        # Create place block action
        action_data = {
            'action_type': 'place_block',
            'player_id': client.player_id,
            'x': data.get('x'),
            'y': data.get('y'),
            'block_id': data.get('block_id'),
            'timestamp': data.get('timestamp', time.time()),
            'action_id': data.get('action_id', f"place_{int(time.time() * 1000)}")
        }
        
        action = create_action_from_data(action_data)
        if action:
            self.server.queue_action(action)
    
    def _handle_block_break(self, client_id: str, data: dict):
        """Handle block breaking requests."""
        client = self.server.clients.get(client_id)
        if not client or not client.player_id:
            return
        
        # Create break block action
        action_data = {
            'action_type': 'break_block',
            'player_id': client.player_id,
            'x': data.get('x'),
            'y': data.get('y'),
            'timestamp': data.get('timestamp', time.time()),
            'action_id': data.get('action_id', f"break_{int(time.time() * 1000)}")
        }
        
        action = create_action_from_data(action_data)
        if action:
            self.server.queue_action(action)
    
    def _handle_item_pickup(self, client_id: str, data: dict):
        """Handle item pickup requests."""
        client = self.server.clients.get(client_id)
        if not client or not client.player_id:
            return
        
        # Create pickup action
        action_data = {
            'action_type': 'pickup_item',
            'player_id': client.player_id,
            'item_id': data.get('item_id'),
            'timestamp': data.get('timestamp', time.time()),
            'action_id': data.get('action_id', f"pickup_{int(time.time() * 1000)}")
        }
        
        action = create_action_from_data(action_data)
        if action:
            self.server.queue_action(action)
    
    def _handle_item_drop(self, client_id: str, data: dict):
        """Handle item drop requests."""
        client = self.server.clients.get(client_id)
        if not client or not client.player_id:
            return
        
        # Create drop action
        action_data = {
            'action_type': 'drop_item',
            'player_id': client.player_id,
            'slot': data.get('slot'),
            'quantity': data.get('quantity'),
            'timestamp': data.get('timestamp', time.time()),
            'action_id': data.get('action_id', f"drop_{int(time.time() * 1000)}")
        }
        
        action = create_action_from_data(action_data)
        if action:
            self.server.queue_action(action)
    
    def _handle_inventory_update(self, client_id: str, data: dict):
        """Handle inventory update requests."""
        client = self.server.clients.get(client_id)
        if not client or not client.player_id:
            return
        
        # Create move item action
        action_data = {
            'action_type': 'move_item',
            'player_id': client.player_id,
            'source_type': data.get('source_type', 'player'),
            'source_slot': data.get('source_slot'),
            'dest_type': data.get('dest_type', 'player'),
            'dest_slot': data.get('dest_slot'),
            'quantity': data.get('quantity'),
            'timestamp': data.get('timestamp', time.time()),
            'action_id': data.get('action_id', f"move_{int(time.time() * 1000)}")
        }
        
        action = create_action_from_data(action_data)
        if action:
            self.server.queue_action(action)
    
    def _handle_craft_item(self, client_id: str, data: dict):
        """Handle crafting requests."""
        client = self.server.clients.get(client_id)
        if not client or not client.player_id:
            return
        
        # Create craft action
        action_data = {
            'action_type': 'craft_item',
            'player_id': client.player_id,
            'recipe_id': data.get('recipe_id'),
            'quantity': data.get('quantity', 1),
            'timestamp': data.get('timestamp', time.time()),
            'action_id': data.get('action_id', f"craft_{int(time.time() * 1000)}")
        }
        
        action = create_action_from_data(action_data)
        if action:
            self.server.queue_action(action)
    
    def _handle_interact_request(self, client_id: str, data: dict):
        """Handle interaction requests."""
        client = self.server.clients.get(client_id)
        if not client or not client.player_id:
            return
        
        # Create interact action
        action_data = {
            'action_type': 'interact',
            'player_id': client.player_id,
            'x': data.get('x'),
            'y': data.get('y'),
            'interaction_type': data.get('interaction_type', 'use'),
            'timestamp': data.get('timestamp', time.time()),
            'action_id': data.get('action_id', f"interact_{int(time.time() * 1000)}")
        }
        
        action = create_action_from_data(action_data)
        if action:
            self.server.queue_action(action)
    
    def _handle_player_respawn(self, client_id: str, data: dict):
        """Handle player respawn requests."""
        client = self.server.clients.get(client_id)
        if not client or not client.player_id:
            return
        
        player_state = self.server.player_manager.get_player(client.player_id)
        if not player_state:
            return
        
        # Reset player state
        player_state.health = player_state.max_health
        player_state.x = player_state.spawn_x
        player_state.y = player_state.spawn_y
        player_state.velocity_x = 0
        player_state.velocity_y = 0
        
        # Send respawn response
        client.send_message(MessageType.PLAYER_RESPAWN, {
            'player_id': client.player_id,
            'x': player_state.x,
            'y': player_state.y,
            'health': player_state.health
        })
        
        log_info(f"Player {client.player_id} respawned")
    
    def _handle_chunk_request(self, client_id: str, data: dict):
        """Handle chunk data requests."""
        client = self.server.clients.get(client_id)
        if not client or not client.player_id:
            return
        
        chunk_x = data.get('chunk_x')
        chunk_y = data.get('chunk_y')
        
        if chunk_x is None or chunk_y is None:
            return
        
        # Subscribe player to chunk updates
        self.server.world.subscribe_to_chunk(chunk_x, chunk_y, client.player_id)
        
        # Send chunk data (would be actual chunk data in full implementation)
        chunk_data = {
            'chunk_x': chunk_x,
            'chunk_y': chunk_y,
            'blocks': {},  # Would contain actual block data
            'entities': []  # Would contain entities in chunk
        }
        
        client.send_message(MessageType.CHUNK_DATA, chunk_data)
    
    def _handle_world_state_request(self, client_id: str, data: dict):
        """Handle world state synchronization request."""
        client = self.server.clients.get(client_id)
        if not client or not client.player_id:
            return
        
        # Get player position and ensure chunks are loaded around them
        player_state = self.server.player_manager.get_player_state(client.player_id)
        if player_state:
            # Ensure chunks are loaded around player position
            self._handle_player_chunk_movement(player_state.x, player_state.y)
        
        # Send complete world state to the new client (this is initial connection)
        world_state = self.server.world.get_world_state()
        client.send_message(MessageType.WORLD_STATE, world_state)
        
        # Mark all current chunks as sent to this client
        if client_id not in self.server.world.client_chunks:
            self.server.world.client_chunks[client_id] = set()
        self.server.world.client_chunks[client_id].update(self.server.world.loaded_chunks)
        
        log_info(f"Sent complete world state to new client {client_id} ({len(self.server.world.loaded_chunks)} chunks)")
        
        # Send all player states to the new client
        for other_client_id, other_client in self.server.clients.items():
            if other_client_id != client_id and other_client.player_id:
                player_state = self.server.player_manager.get_player_state(other_client.player_id)
                if player_state:
                    client.send_message(MessageType.PLAYER_SPAWN_DATA, {
                        'player_id': other_client.player_id,
                        'player_name': player_state.player_name,
                        'x': player_state.x,
                        'y': player_state.y,
                        'health': player_state.health,
                        'max_health': player_state.max_health
                    })
        
        log_debug(f"Sent world state to client {client_id}")
    
    def _handle_player_state_sync(self, client_id: str, data: dict):
        """Handle player state synchronization."""
        try:
            client = self.server.clients.get(client_id)
            if not client or not client.player_id:
                log_warning(f"Player state sync from invalid client: {client_id}")
                return
            
            # Update player state in server
            player_state = self.server.player_manager.get_player_state(client.player_id)
            if not player_state:
                log_warning(f"No player state found for player: {client.player_id}")
                return
                
            # Update position
            if 'x' in data:
                player_state.x = float(data['x'])
            if 'y' in data:
                player_state.y = float(data['y'])
            if 'health' in data:
                player_state.health = int(data['health'])
            if 'facing_direction' in data:
                player_state.facing_direction = str(data['facing_direction'])
            
            # Check if player has moved to new chunks and generate them if needed
            if 'x' in data and 'y' in data:
                try:
                    self._handle_player_chunk_movement(player_state.x, player_state.y)
                except Exception as e:
                    log_error(f"Error handling chunk movement: {e}")
            
            # Broadcast position update to other players
            try:
                self._broadcast_player_update(client.player_id, player_state)
            except Exception as e:
                log_error(f"Error broadcasting player update: {e}")
                
        except Exception as e:
            log_error(f"Error handling player state sync: {e}")
            import traceback
            log_error(f"Traceback: {traceback.format_exc()}")
    
    def _handle_player_chunk_movement(self, player_x: float, player_y: float):
        """Generate chunks around player if they've moved to new areas."""
        from ...config.settings import CHUNKSIZE, TILESIZE
        import math
        
        # Calculate which chunk the player is in using proper floor for negative coordinates
        # Use math.floor to ensure negative coordinates are handled correctly
        chunk_x = int(math.floor(player_x / (CHUNKSIZE * TILESIZE)))
        chunk_y = int(math.floor(player_y / (CHUNKSIZE * TILESIZE)))
        
        # Generate chunks around the player (larger area to cover screen)
        # Screen is 24x16 tiles, with CHUNKSIZE=4, we need good chunk coverage
        # Let's load 7x7 chunks around player for excellent coverage and smooth exploration
        chunks_generated = []
        for dx in range(-3, 4):  # -3, -2, -1, 0, 1, 2, 3 (7 chunks wide)
            for dy in range(-3, 4):  # -3, -2, -1, 0, 1, 2, 3 (7 chunks tall)
                target_chunk_x = chunk_x + dx
                target_chunk_y = chunk_y + dy
                
                # Check if chunk exists, if not generate it
                if not self.server.world.has_chunk(target_chunk_x, target_chunk_y):
                    log_info(f"Generating new chunk ({target_chunk_x}, {target_chunk_y}) for player exploration")
                    self.server.world._generate_chunk(target_chunk_x, target_chunk_y)
                    chunks_generated.append((target_chunk_x, target_chunk_y))
        
        # If we generated new chunks, send world state updates to all clients
        if chunks_generated:
            log_info(f"Generated {len(chunks_generated)} new chunks, updating all clients")
            
            # Mark chunks as newly generated for incremental updates
            self.server.world.mark_chunks_generated(chunks_generated)
            
            for client_id, client in self.server.clients.items():
                if client.authenticated:
                    # Send only new chunks to this client (incremental update)
                    new_chunks_data = self.server.world.get_new_chunks_for_client(client_id)
                    
                    # Only send if there's actually new data
                    if new_chunks_data['chunks']:
                        client.send_message(MessageType.WORLD_STATE, new_chunks_data)
            
            # Clear the newly generated chunks after all clients have been updated
            self.server.world.clear_new_chunks_for_all_clients()
    
    def _broadcast_player_update(self, player_id: str, player_state):
        """Broadcast player state update to all other connected clients."""
        update_data = {
            'player_id': player_id,
            'x': player_state.x,
            'y': player_state.y,
            'health': player_state.health,
            'facing_direction': player_state.facing_direction,
            'timestamp': time.time()
        }
        
        # Send to all clients except the player who moved
        for client_id, client in self.server.clients.items():
            if client.player_id != player_id:
                client.send_message(MessageType.PLAYER_UPDATE, update_data)
    
    def get_handler_stats(self) -> Dict[str, Any]:
        """Get message handler statistics."""
        return {
            'total_messages_handled': self.messages_handled,
            'messages_by_type': self.messages_by_type.copy(),
            'handler_count': len(self.handlers)
        }
    
    def _send_error_response(self, client_id: str, error_message: str):
        """Send an error response to a client."""
        client = self.server.clients.get(client_id)
        if client:
            client.send_message(MessageType.ERROR, {
                'error': 'server_error',
                'message': error_message
            })
