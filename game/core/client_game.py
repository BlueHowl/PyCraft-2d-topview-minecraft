"""
Client Game - Rendering and networking wrapper around the core Game class.

This class handles the client-side aspects of the game including rendering,
input handling, and network communication with the server.
"""

import time
from typing import Optional, Dict, Any, Callable
import pygame as pg

from game.core.game import Game
from game.core.game_world import GameWorld, PlayerState
from game.network.protocol import NetworkProtocol, generate_player_id
from game.network.connection import Connection, create_client_connection
from game.network.message_types import MessageType
from game.network.packets import *
from game.utils.logger import log_info, log_error, log_warning, log_debug


class ClientGame(Game):
    """
    Client-side game wrapper that adds networking capabilities to the base Game class.
    
    This class maintains compatibility with the existing Game interface while
    adding multiplayer networking functionality.
    """
    
    def __init__(self, connection_mode: str = "singleplayer"):
        """
        Initialize the client game.
        
        Args:
            connection_mode: "singleplayer", "multiplayer_client", or "local_server"
        """
        log_info(f"Initializing ClientGame in {connection_mode} mode")
        
        # Initialize base game
        super().__init__()
        
        # Network state
        self.connection_mode = connection_mode
        self.network_protocol = NetworkProtocol()
        self.connection: Optional[Connection] = None
        self.player_id: Optional[str] = None
        self.player_name: str = "Player"
        
        # Local game world for singleplayer or local prediction
        self.local_world: Optional[GameWorld] = None
        
        # Network settings
        self.server_host = "localhost"
        self.server_port = 25565
        self.connection_timeout = 5.0
        self.ping_interval = 5.0
        self.last_ping = 0.0
        
        # Client state
        self.connected = False
        self.connecting = False
        self.connection_error: Optional[str] = None
        
        # Message handlers
        self.message_handlers = {
            MessageType.CONNECT_RESPONSE: self._handle_connect_response,
            MessageType.DISCONNECT: self._handle_disconnect,
            MessageType.PING: self._handle_ping,
            MessageType.PONG: self._handle_pong,
            MessageType.PLAYER_UPDATE: self._handle_player_update,
            MessageType.PLAYER_JOIN: self._handle_player_join,
            MessageType.PLAYER_LEAVE: self._handle_player_leave,
            MessageType.BLOCK_UPDATE: self._handle_block_update,
            MessageType.CHUNK_DATA: self._handle_chunk_data,
            MessageType.FLOATING_ITEM_SPAWN: self._handle_floating_item_spawn,
            MessageType.CHAT_BROADCAST: self._handle_chat_broadcast,
            MessageType.ERROR: self._handle_error,
            MessageType.WORLD_STATE: self._handle_world_state,
            MessageType.PLAYER_SPAWN_DATA: self._handle_player_spawn_data
        }
        
        # Initialize based on connection mode
        if connection_mode == "singleplayer":
            self._init_singleplayer()
        elif connection_mode == "local_server":
            self._init_local_server()
        
        log_info(f"ClientGame initialized in {connection_mode} mode")
    
    def _init_singleplayer(self):
        """Initialize singleplayer mode with local world."""
        self.local_world = GameWorld("singleplayer_world")
        self.player_id = generate_player_id()
        self.player_name = "Player"
        
        # Add local player to the world
        spawn_x, spawn_y = 0.0, 0.0  # Default spawn point
        self.local_world.add_player(self.player_id, self.player_name, spawn_x, spawn_y)
        
        log_info("Singleplayer mode initialized with local world")
    
    def _init_local_server(self):
        """Initialize local server mode."""
        # This would start an embedded server and connect to it
        # For now, just use singleplayer mode
        self._init_singleplayer()
        log_info("Local server mode initialized (using singleplayer for now)")
    
    def connect_to_server(self, host: str, port: int, player_name: str, 
                         world_name: Optional[str] = None) -> bool:
        """
        Connect to a multiplayer server.
        
        Args:
            host: Server hostname or IP
            port: Server port
            player_name: Player name
            world_name: Optional world name
            
        Returns:
            True if connection initiated successfully
        """
        if self.connected or self.connecting:
            log_warning("Already connected or connecting")
            return False
        
        self.server_host = host
        self.server_port = port
        self.player_name = player_name
        self.connecting = True
        self.connection_error = None
        
        try:
            log_info(f"Connecting to server {host}:{port} as {player_name}")
            
            # Create connection
            self.connection = create_client_connection(
                host, port, self.network_protocol, self.connection_timeout
            )
            
            # Set up connection callbacks
            self.connection.on_message = self._handle_network_message
            self.connection.on_disconnect = self._handle_network_disconnect
            self.connection.on_error = self._handle_network_error
            
            # Start connection
            self.connection.start()
            
            # Send connection request
            self.connection.send_message(
                MessageType.CONNECT,
                {
                    'player_name': player_name,
                    'world_name': world_name,
                    'client_version': self.network_protocol.PROTOCOL_VERSION
                }
            )
            
            log_info("Connection request sent, waiting for response...")
            return True
            
        except Exception as e:
            self.connection_error = str(e)
            self.connecting = False
            log_error(f"Failed to connect to server: {e}")
            return False
    
    def disconnect_from_server(self, reason: str = "Disconnected"):
        """Disconnect from the server."""
        if self.connection and self.connected:
            log_info(f"Disconnecting from server: {reason}")
            
            # Send disconnect message
            self.connection.send_message(
                MessageType.DISCONNECT,
                {'reason': reason}
            )
            
            # Close connection
            self.connection.stop()
            self.connection = None
        
        self.connected = False
        self.connecting = False
        self.player_id = None
    
    def update(self):
        """Update the client game."""
        # Call base game update
        super().update()
        
        # Handle networking
        if self.connection_mode == "singleplayer":
            self._update_singleplayer()
        elif self.connection and self.connected:
            self._update_multiplayer()
        
        # Handle ping/pong for connection keepalive
        if self.connection and self.connected:
            current_time = time.time()
            if current_time - self.last_ping > self.ping_interval:
                self._send_ping()
                self.last_ping = current_time
    
    def _update_singleplayer(self):
        """Update singleplayer game logic."""
        if self.local_world:
            self.local_world.update(self.dt)
            
            # Sync local player state with pygame player
            if hasattr(self, 'player') and self.player_id:
                local_player = self.local_world.get_player(self.player_id)
                if local_player:
                    # Update local world with pygame player state
                    local_player.set_position(self.player.pos.x, self.player.pos.y)
                    local_player.health = self.player.health
    
    def _update_multiplayer(self):
        """Update multiplayer networking."""
        if not self.connection:
            return
        
        # Process incoming messages
        while True:
            message = self.connection.get_message(timeout=0.001)
            if not message:
                break
            
            # Message is already handled by the connection callback
            # This is just for additional processing if needed
        
        # Send player updates if needed
        if hasattr(self, 'player') and self.player_id:
            self._send_player_update()
    
    def _send_player_update(self):
        """Send player state update to server."""
        if not self.connection or not hasattr(self, 'player'):
            return
        
        # Only send updates if player state has changed significantly
        player = self.player
        current_time = time.time()
        
        # Simple update throttling (send at most 20 updates per second)
        if not hasattr(self, '_last_player_update'):
            self._last_player_update = 0
        
        if current_time - self._last_player_update < 0.05:  # 50ms
            return
        
        self.connection.send_message(
            MessageType.PLAYER_MOVE,
            {
                'x': player.pos.x,
                'y': player.pos.y,
                'vel_x': player.vel.x,
                'vel_y': player.vel.y,
                'direction': getattr(player, 'direction', 'down')
            },
            self.player_id
        )
        
        self._last_player_update = current_time
    
    def _send_ping(self):
        """Send a ping to the server."""
        if self.connection and self.connected:
            self.connection.send_message(MessageType.PING, {'ping_time': time.time()})
    
    def _handle_network_message(self, message: Dict[str, Any]):
        """Handle incoming network message."""
        message_type = message.get('message_type')
        if message_type in self.message_handlers:
            try:
                self.message_handlers[message_type](message)
            except Exception as e:
                log_error(f"Error handling message {message_type}: {e}")
        else:
            log_warning(f"Unhandled message type: {message_type}")
    
    def _handle_network_disconnect(self, reason: str):
        """Handle network disconnection."""
        log_warning(f"Disconnected from server: {reason}")
        self.connected = False
        self.connecting = False
        self.connection = None
    
    def _handle_network_error(self, error: Exception):
        """Handle network error."""
        log_error(f"Network error: {error}")
        self.connection_error = str(error)
    
    # Message Handlers
    def _handle_connect_response(self, message: Dict[str, Any]):
        """Handle connection response from server."""
        data = message.get('data', {})
        
        if data.get('success'):
            self.player_id = data.get('player_id')
            self.connected = True
            self.connecting = False
            self.connection_error = None
            
            server_info = data.get('server_info', {})
            log_info(f"Connected to server successfully! Player ID: {self.player_id}")
            log_info(f"Server info: {server_info}")
            
        else:
            error_msg = data.get('error_message', 'Connection failed')
            self.connection_error = error_msg
            self.connecting = False
            log_error(f"Connection failed: {error_msg}")
            
            if self.connection:
                self.connection.stop()
                self.connection = None
    
    def _handle_disconnect(self, message: Dict[str, Any]):
        """Handle disconnect message from server."""
        data = message.get('data', {})
        reason = data.get('reason', 'Server disconnected')
        log_info(f"Server requested disconnect: {reason}")
        self.disconnect_from_server(reason)
    
    def _handle_ping(self, message: Dict[str, Any]):
        """Handle ping from server."""
        data = message.get('data', {})
        ping_time = data.get('ping_time', time.time())
        
        # Send pong response
        if self.connection:
            self.connection.send_message(
                MessageType.PONG,
                {
                    'ping_time': ping_time,
                    'pong_time': time.time()
                }
            )
    
    def _handle_pong(self, message: Dict[str, Any]):
        """Handle pong response from server."""
        data = message.get('data', {})
        ping_time = data.get('ping_time', 0)
        pong_time = data.get('pong_time', 0)
        
        # Calculate latency
        if ping_time > 0:
            latency = time.time() - ping_time
            log_debug(f"Server latency: {latency*1000:.1f}ms")
    
    def _handle_player_update(self, message: Dict[str, Any]):
        """Handle player update from server."""
        data = message.get('data', {})
        player_id = message.get('player_id')
        
        # Update other players (not implemented yet)
        log_debug(f"Player update for {player_id}: {data}")
    
    def _handle_player_join(self, message: Dict[str, Any]):
        """Handle player join notification."""
        data = message.get('data', {})
        player_name = data.get('player_name', 'Unknown')
        log_info(f"Player {player_name} joined the game")
    
    def _handle_player_leave(self, message: Dict[str, Any]):
        """Handle player leave notification."""
        data = message.get('data', {})
        player_id = data.get('player_id')
        reason = data.get('reason', 'Disconnected')
        log_info(f"Player {player_id} left the game: {reason}")
    
    def _handle_block_update(self, message: Dict[str, Any]):
        """Handle block update from server."""
        data = message.get('data', {})
        x = data.get('x')
        y = data.get('y')
        block_id = data.get('block_id')
        
        # Update local world if in singleplayer
        if self.local_world:
            self.local_world.set_block(x, y, block_id)
        
        log_debug(f"Block update: ({x}, {y}) = {block_id}")
    
    def _handle_chunk_data(self, message: Dict[str, Any]):
        """Handle chunk data from server."""
        data = message.get('data', {})
        chunk_x = data.get('chunk_x')
        chunk_y = data.get('chunk_y')
        chunk_blocks = data.get('blocks', {})
        
        log_debug(f"Received chunk data for ({chunk_x}, {chunk_y}) with {len(chunk_blocks)} blocks")
        
        # Apply chunk data to client chunk manager if available
        if hasattr(self, 'chunkmanager') and self.chunkmanager and chunk_x is not None and chunk_y is not None:
            from game.config.settings import CHUNKSIZE
            
            # Create chunk if it doesn't exist
            chunk_name = f"{chunk_x},{chunk_y}"
            if chunk_name not in self.chunkmanager.chunks:
                # Initialize empty chunk
                self.chunkmanager.chunks[chunk_name] = [[[str(0).zfill(2)] for _ in range(CHUNKSIZE)] for _ in range(CHUNKSIZE)]
            
            chunk_2d = self.chunkmanager.chunks[chunk_name]
            
            # Apply the block updates
            blocks_updated = 0
            for block_key, block_id in chunk_blocks.items():
                x, y = map(int, block_key.split(','))
                
                # Calculate chunk-local coordinates properly handling negative values
                local_x = x - (chunk_x * CHUNKSIZE)
                local_y = y - (chunk_y * CHUNKSIZE)
                
                # Ensure coordinates are within chunk bounds
                if 0 <= local_x < CHUNKSIZE and 0 <= local_y < CHUNKSIZE:
                    # Convert block ID to tile string format
                    tile_str = f"{block_id:02d}"
                    chunk_2d[local_y][local_x] = [tile_str]
                    blocks_updated += 1
            
            log_debug(f"Updated {blocks_updated} blocks in chunk ({chunk_x}, {chunk_y})")
            
            # Force chunk reload if this chunk is currently visible
            if hasattr(self, 'world_manager'):
                self.world_manager.reload_chunks()
    
    def _handle_floating_item_spawn(self, message: Dict[str, Any]):
        """Handle floating item spawn."""
        data = message.get('data', {})
        item_type = data.get('item_type')
        x = data.get('x')
        y = data.get('y')
        
        log_debug(f"Floating item spawned: {item_type} at ({x}, {y})")
    
    def _handle_chat_broadcast(self, message: Dict[str, Any]):
        """Handle chat broadcast from server."""
        data = message.get('data', {})
        player_name = data.get('player_name', 'Unknown')
        chat_message = data.get('message', '')
        
        log_info(f"[CHAT] {player_name}: {chat_message}")
    
    def _handle_error(self, message: Dict[str, Any]):
        """Handle error message from server."""
        data = message.get('data', {})
        error_code = data.get('error_code', 'UNKNOWN')
        error_message = data.get('error_message', 'Unknown error')
        
        log_error(f"Server error [{error_code}]: {error_message}")
        self.connection_error = error_message
    
    def _handle_world_state(self, message: Dict[str, Any]):
        """Handle world state synchronization from server."""
        data = message.get('data', {})
        log_info("Received world state from server")
        
        # Apply world state to the client game
        chunks = data.get('chunks', {})
        floating_items = data.get('floating_items', {})
        world_name = data.get('world_name', 'Unknown')
        
        log_info(f"Applying world state: {len(chunks)} chunks, {len(floating_items)} items")
        
        # Update the client's chunk manager with the server's world data
        if hasattr(self, 'chunkmanager'):
            # Clear any existing client-side chunks
            self.chunkmanager.clearChunks()
            
            # Apply server chunks
            for chunk_key, chunk_blocks in chunks.items():
                chunk_x, chunk_y = map(int, chunk_key.split(','))
                for block_key, block_id in chunk_blocks.items():
                    x, y = map(int, block_key.split(','))
                    self.chunkmanager.set_block(x, y, block_id)
        
        # Clear and spawn floating items
        if hasattr(self, 'floatingItems'):
            for item in self.floatingItems:
                item.kill()
            self.floatingItems.empty()
        
        # Spawn server floating items
        from game.entities.FloatingItem import FloatingItem
        for item_id, item_data in floating_items.items():
            FloatingItem(self, 
                        item_data['x'], 
                        item_data['y'], 
                        item_data['item_type'],
                        item_data['quantity'])
        
        log_info("World state applied successfully")
    
    def _handle_player_spawn_data(self, message: Dict[str, Any]):
        """Handle player spawn data from server."""
        data = message.get('data', {})
        player_id = data.get('player_id')
        player_name = data.get('player_name', 'Unknown')
        x = data.get('x', 0)
        y = data.get('y', 0)
        health = data.get('health', 100)
        max_health = data.get('max_health', 100)
        facing_direction = data.get('facing_direction', 'right')
        
        log_info(f"Spawning player: {player_name} at ({x}, {y})")
        
        # If this is our own player, update our position
        if player_id == self.player_id:
            if hasattr(self, 'player'):
                self.player.pos.x = x
                self.player.pos.y = y
                self.player.health = health
        else:
            # Spawn other player entity
            from game.entities.Player import Player
            # Create multiplayer player representation
            # Note: This is a simplified implementation - you may need to create
            # a separate MultiplayerPlayer class for remote players
            remote_player = Player(self, x, y, 0)
            remote_player.player_id = player_id
            remote_player.player_name = player_name
            remote_player.health = health
            # Add to a multiplayer players group
            if not hasattr(self, 'multiplayer_players'):
                self.multiplayer_players = pg.sprite.Group()
            self.multiplayer_players.add(remote_player)
    
    # Public interface methods
    def send_chat_message(self, message: str) -> bool:
        """Send a chat message to the server."""
        if not self.connection or not self.connected:
            return False
        
        self.connection.send_message(
            MessageType.CHAT_MESSAGE,
            {'message': message},
            self.player_id
        )
        return True
    
    def place_block(self, x: int, y: int, block_id: int) -> bool:
        """Place a block in the world."""
        if self.connection_mode == "singleplayer":
            # Direct local placement
            if self.local_world:
                return self.local_world.set_block(x, y, block_id, self.player_id)
            return False
        
        elif self.connection and self.connected:
            # Send to server
            chunk_x = x // 32  # CHUNKSIZE
            chunk_y = y // 32
            
            self.connection.send_message(
                MessageType.BLOCK_PLACE,
                {
                    'x': x,
                    'y': y,
                    'block_id': block_id,
                    'chunk_x': chunk_x,
                    'chunk_y': chunk_y
                },
                self.player_id
            )
            return True
        
        return False
    
    def break_block(self, x: int, y: int) -> bool:
        """Break a block in the world."""
        return self.place_block(x, y, 0)  # 0 = air/empty block
    
    def get_connection_status(self) -> Dict[str, Any]:
        """Get current connection status."""
        status = {
            'mode': self.connection_mode,
            'connected': self.connected,
            'connecting': self.connecting,
            'error': self.connection_error,
            'player_id': self.player_id,
            'player_name': self.player_name
        }
        
        if self.connection:
            status['connection_stats'] = self.connection.get_stats()
        
        return status
    
    def quit(self):
        """Quit the game with proper cleanup."""
        # Disconnect from server if connected
        if self.connection_mode != "singleplayer":
            self.disconnect_from_server("Client quit")
        
        # Call base game quit
        super().quit()
