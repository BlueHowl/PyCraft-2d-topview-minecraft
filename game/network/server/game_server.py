"""
Game Server Implementation for PyCraft 2D

Main server class that handles client connections, game state management,
and message processing for multiplayer gameplay.
"""

import socket
import threading
import time
import json
from typing import Dict, List, Optional, Set
from dataclasses import dataclass

from ..protocol import NetworkProtocol
from ..message_types import MessageType
from ..packets import BasePacket, ConnectPacket, DisconnectPacket, PlayerJoinPacket
from ..connection import Connection
from ...core.game_world import GameWorld
from ...utils.logger import log_info, log_error, log_debug, log_warning
from ..actions import ActionHandler, ActionQueue, create_action_from_data, register_action, complete_action

from .client_connection import ClientConnection
from .player_manager import PlayerManager
from .server_game_world import ServerGameWorld
from .message_handler import ServerMessageHandler


@dataclass
class ServerConfig:
    """Configuration for the game server."""
    host: str = "localhost"
    port: int = 25565
    max_players: int = 100
    tick_rate: int = 20  # Server ticks per second
    save_interval: int = 300  # Auto-save interval in seconds
    timeout_seconds: int = 30  # Client timeout
    debug_mode: bool = False


class GameServer:
    """
    Main game server class.
    
    Handles client connections, game state updates, and message broadcasting.
    """
    
    def __init__(self, config: ServerConfig = None, world_name: str = "default"):
        """Initialize the game server."""
        self.config = config or ServerConfig()
        self.world_name = world_name
        
        # Networking
        self.protocol = NetworkProtocol()
        self.socket: Optional[socket.socket] = None
        self.running = False
        
        # Client management
        self.clients: Dict[str, ClientConnection] = {}
        self.client_lock = threading.RLock()
        
        # Game systems
        self.world = ServerGameWorld(world_name)
        self.player_manager = PlayerManager()
        self.message_handler = ServerMessageHandler(self)
        self.action_handler = ActionHandler()
        self.action_queue = ActionQueue()
        
        # Threading
        self.accept_thread: Optional[threading.Thread] = None
        self.game_thread: Optional[threading.Thread] = None
        self.save_thread: Optional[threading.Thread] = None
        
        # Statistics
        self.start_time = 0
        self.total_connections = 0
        self.messages_processed = 0
        self.last_save_time = 0
        
        log_info(f"GameServer initialized - Max players: {self.config.max_players}, Tick rate: {self.config.tick_rate}")
    
    def start(self) -> bool:
        """
        Start the game server.
        
        Returns:
            True if server started successfully, False otherwise
        """
        try:
            # Create server socket
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket.bind((self.config.host, self.config.port))
            self.socket.listen(10)
            
            self.running = True
            self.start_time = time.time()
            
            # Start server threads
            self.accept_thread = threading.Thread(target=self._accept_connections, daemon=True)
            self.game_thread = threading.Thread(target=self._game_loop, daemon=True)
            self.save_thread = threading.Thread(target=self._auto_save_loop, daemon=True)
            
            self.accept_thread.start()
            self.game_thread.start() 
            self.save_thread.start()
            
            log_info(f"GameServer started on {self.config.host}:{self.config.port}")
            return True
            
        except Exception as e:
            log_error(f"Failed to start server: {e}")
            self.stop()
            return False
    
    def stop(self):
        """Stop the game server."""
        log_info("Stopping GameServer...")
        
        self.running = False
        
        # Disconnect all clients
        with self.client_lock:
            for client in list(self.clients.values()):
                self.disconnect_client(client.client_id, "Server shutting down")
        
        # Close server socket
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
            self.socket = None
        
        # Wait for threads to finish
        for thread in [self.accept_thread, self.game_thread, self.save_thread]:
            if thread and thread.is_alive():
                thread.join(timeout=2.0)
        
        log_info("GameServer stopped")
    
    def _accept_connections(self):
        """Accept incoming client connections."""
        while self.running:
            try:
                client_socket, client_address = self.socket.accept()
                
                if len(self.clients) >= self.config.max_players:
                    log_warning(f"Connection rejected - server full: {client_address}")
                    client_socket.close()
                    continue
                
                log_debug(f"New connection from {client_address}")
                self._handle_new_connection(client_socket, client_address)
                
            except Exception as e:
                if self.running:
                    log_error(f"Error accepting connections: {e}")
                break
    
    def _handle_new_connection(self, client_socket: socket.socket, client_address):
        """Handle a new client connection."""
        try:
            # Create connection wrapper
            connection = Connection(client_socket, client_address, self.protocol)
            
            # Start the connection threads
            connection.start()
            
            # Generate client ID
            client_id = f"client_{int(time.time() * 1000)}_{client_address[1]}"
            
            # Create client connection object
            client_conn = ClientConnection(
                client_id=client_id,
                connection=connection,
                address=client_address,
                server=self
            )
            
            # Add to clients
            with self.client_lock:
                self.clients[client_id] = client_conn
            
            # Start client handler
            client_conn.start()
            
            self.total_connections += 1
            log_info(f"Client connected: {client_id} from {client_address}")
            
        except Exception as e:
            log_error(f"Error handling new connection: {e}")
            try:
                client_socket.close()
            except:
                pass
    
    def disconnect_client(self, client_id: str, reason: str = "Disconnected"):
        """Disconnect a client."""
        with self.client_lock:
            client = self.clients.get(client_id)
            if not client:
                return
            
            log_info(f"Disconnecting client {client_id}: {reason}")
            
            # Remove player from game
            if client.player_id:
                self.player_manager.remove_player(client.player_id)
                
                # Broadcast player left message
                self.broadcast_message(
                    MessageType.PLAYER_LEAVE,
                    {
                        'player_id': client.player_id,
                        'reason': reason
                    },
                    exclude_client=client_id
                )
            
            # Clean up chunk tracking for this client
            self.world.client_disconnected(client_id)
            
            # Stop client connection
            client.stop()
            
            # Remove from clients list
            del self.clients[client_id]
    
    def _game_loop(self):
        """Main game loop running at configured tick rate."""
        tick_interval = 1.0 / self.config.tick_rate
        last_tick = time.time()
        
        while self.running:
            current_time = time.time()
            delta_time = current_time - last_tick
            
            if delta_time >= tick_interval:
                self._update_game(delta_time)
                last_tick = current_time
            else:
                # Sleep for remaining time
                sleep_time = tick_interval - delta_time
                time.sleep(max(0.001, sleep_time))
    
    def _update_game(self, delta_time: float):
        """Update game state."""
        try:
            # Process queued actions
            self._process_actions()
            
            # Update world simulation
            self.world.update(delta_time)
            
            # Update players
            self.player_manager.update(delta_time)
            
            # Check for timeouts
            self._check_client_timeouts()
            
            # Broadcast state updates
            self._broadcast_state_updates()
            
        except Exception as e:
            log_error(f"Error in game loop: {e}")
    
    def _process_actions(self):
        """Process queued actions from clients."""
        while not self.action_queue.is_empty():
            action = self.action_queue.get_next_action()
            if not action:
                break
            
            try:
                # Get player state
                player_state = self.player_manager.get_player(action.player_id)
                if not player_state:
                    continue
                
                # Validate action
                validation_result = action.validate(self.world, player_state)
                if validation_result.result.name != 'SUCCESS':
                    log_debug(f"Action validation failed: {action.get_action_type()} - {validation_result.message}")
                    continue
                
                # Execute action
                execution_result = action.execute(self.world, player_state)
                complete_action(action.action_id, execution_result)
                
                if execution_result.result.name == 'SUCCESS':
                    # Broadcast action result to relevant clients
                    self._broadcast_action_result(action, execution_result)
                
                self.messages_processed += 1
                
            except Exception as e:
                log_error(f"Error processing action {action.get_action_type()}: {e}")
    
    def _check_client_timeouts(self):
        """Check for client timeouts and disconnect inactive clients."""
        current_time = time.time()
        timeout_clients = []
        
        with self.client_lock:
            for client_id, client in self.clients.items():
                if current_time - client.last_activity > self.config.timeout_seconds:
                    timeout_clients.append(client_id)
        
        for client_id in timeout_clients:
            self.disconnect_client(client_id, "Timeout")
    
    def _broadcast_state_updates(self):
        """Broadcast periodic state updates to clients."""
        # This would send position updates, world changes, etc.
        # Implementation depends on what needs to be synchronized
        pass
    
    def _broadcast_action_result(self, action, result):
        """Broadcast action result to relevant clients."""
        # Determine which clients need to know about this action
        # For now, broadcast movement to nearby players, world changes to chunk subscribers
        action_type = action.get_action_type()
        
        if action_type in ['move', 'stop', 'jump']:
            # Broadcast to nearby players
            self._broadcast_to_nearby_players(action.player_id, {
                'type': 'player_action',
                'action_type': action_type,
                'player_id': action.player_id,
                'data': result.data
            })
        elif action_type in ['place_block', 'break_block']:
            # Broadcast to chunk subscribers
            chunk_data = result.data or {}
            chunk_x = chunk_data.get('chunk_x', 0)
            chunk_y = chunk_data.get('chunk_y', 0)
            
            self._broadcast_to_chunk_subscribers(chunk_x, chunk_y, {
                'type': 'world_update',
                'action_type': action_type,
                'data': result.data
            })
    
    def _broadcast_to_nearby_players(self, player_id: str, message_data: dict):
        """Broadcast message to players near the given player."""
        player_state = self.player_manager.get_player(player_id)
        if not player_state:
            return
        
        # Simple range check - in real implementation would use spatial indexing
        VIEW_RANGE = 500  # pixels
        
        nearby_clients = []
        with self.client_lock:
            for client in self.clients.values():
                if not client.player_id or client.player_id == player_id:
                    continue
                
                other_player = self.player_manager.get_player(client.player_id)
                if not other_player:
                    continue
                
                distance = ((player_state.x - other_player.x)**2 + 
                           (player_state.y - other_player.y)**2)**0.5
                
                if distance <= VIEW_RANGE:
                    nearby_clients.append(client)
        
        for client in nearby_clients:
            client.send_message(MessageType.GAME_UPDATE, message_data)
    
    def _broadcast_to_chunk_subscribers(self, chunk_x: int, chunk_y: int, message_data: dict):
        """Broadcast message to clients subscribed to a chunk."""
        # For now, broadcast to all clients - would optimize with chunk subscriptions
        self.broadcast_message(MessageType.WORLD_UPDATE, message_data)
    
    def _auto_save_loop(self):
        """Auto-save game state periodically."""
        while self.running:
            time.sleep(self.config.save_interval)
            if self.running:
                self._save_game_state()
    
    def _save_game_state(self):
        """Save current game state to disk."""
        try:
            current_time = time.time()
            
            # Save world state
            self.world.save_to_disk()
            
            # Save player states
            self.player_manager.save_to_disk()
            
            self.last_save_time = current_time
            log_debug("Game state saved")
            
        except Exception as e:
            log_error(f"Error saving game state: {e}")
    
    def broadcast_message(self, message_type: MessageType, data: dict, exclude_client: str = None):
        """Broadcast a message to all connected clients."""
        with self.client_lock:
            for client_id, client in self.clients.items():
                if client_id != exclude_client:
                    client.send_message(message_type, data)
    
    def process_client_message(self, client_id: str, message_type: MessageType, data: dict):
        """Process a message from a client."""
        try:
            self.message_handler.handle_message(client_id, message_type, data)
        except Exception as e:
            log_error(f"Error processing message from {client_id}: {e}")
    
    def get_server_stats(self) -> dict:
        """Get server statistics."""
        uptime = time.time() - self.start_time if self.start_time else 0
        
        with self.client_lock:
            connected_clients = len(self.clients)
        
        return {
            'uptime': uptime,
            'connected_clients': connected_clients,
            'total_connections': self.total_connections,
            'messages_processed': self.messages_processed,
            'tick_rate': self.config.tick_rate,
            'max_players': self.config.max_players,
            'last_save': self.last_save_time,
            'world_chunks': len(self.world.chunks) if hasattr(self.world, 'chunks') else 0
        }
    
    def handle_player_join(self, client_id: str, player_data: dict) -> bool:
        """Handle a player joining the game."""
        try:
            player_id = player_data.get('player_id')
            if not player_id:
                return False
            
            # Ensure world has initial chunks when first player joins
            if len(self.world.loaded_chunks) == 0:
                log_info("No chunks loaded, generating initial world for first player")
                self.world._generate_initial_world()
            
            # Create player state
            player_state = self.player_manager.create_player(player_id, player_data)
            if not player_state:
                return False
            
            # Associate client with player
            client = self.clients.get(client_id)
            if client:
                client.player_id = player_id
            
            # Broadcast player joined
            self.broadcast_message(
                MessageType.PLAYER_JOIN,
                {
                    'player_id': player_id,
                    'player_data': self.player_manager.get_player_data(player_id)
                },
                exclude_client=client_id
            )
            
            log_info(f"Player {player_id} joined the game (client: {client_id})")
            return True
            
        except Exception as e:
            log_error(f"Error handling player join: {e}")
            return False
    
    def queue_action(self, action):
        """Queue an action for processing."""
        register_action(action)
        self.action_queue.add_action(action)
    
    def update(self):
        """Public update method for external server management."""
        if not self.running:
            return
        
        # This method can be called by dedicated server to perform periodic tasks
        # The main game loop runs in its own thread, so this is just for external monitoring
        pass
    
    def get_player_count(self) -> int:
        """Get the current number of connected players."""
        return len(self.clients)
    
    def is_player_name_taken(self, player_name: str) -> bool:
        """Check if a player name is already taken by a connected player."""
        for client in self.clients.values():
            if client.player_id:
                player_state = self.player_manager.get_player_state(client.player_id)
                if player_state and player_state.player_name == player_name:
                    return True
        return False
