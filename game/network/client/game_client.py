"""
Game Client for PyCraft 2D Multiplayer

Handles connection to game server, message processing, and client-side state management.
"""

import socket
import threading
import time
import logging
from typing import Dict, Any, Optional, Callable
from dataclasses import dataclass, field

from ..message_types import MessageType
from ..protocol import NetworkProtocol
from ..connection_manager import ConnectionManager, ConnectionState, DisconnectReason, ReconnectPolicy
from .client_connection import ClientConnection
from .client_message_handler import ClientMessageHandler
from .client_game_world import ClientGameWorld

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def log_info(message: str):
    """Log info message."""
    logger.info(message)

def log_warning(message: str):
    """Log warning message."""
    logger.warning(message)

def log_error(message: str):
    """Log error message."""
    logger.error(message)

def log_debug(message: str):
    """Log debug message."""
    logger.debug(message)


@dataclass
class ClientConfig:
    """Configuration for game client."""
    
    # Connection settings
    server_host: str = "localhost"
    server_port: int = 25565
    connection_timeout: float = 10.0
    reconnect_attempts: int = 3
    reconnect_delay: float = 2.0
    
    # Client settings
    player_name: str = "Player"
    world_name: Optional[str] = None
    auto_reconnect: bool = True
    
    # Network settings
    ping_interval: float = 5.0
    message_queue_size: int = 1000
    
    # Performance settings
    update_rate: int = 60  # Client update rate (FPS)
    network_update_rate: int = 20  # Network updates per second
    
    # Debug settings
    debug_mode: bool = False
    log_network_traffic: bool = False


class ConnectionState:
    """Enumeration of connection states."""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    AUTHENTICATING = "authenticating"
    AUTHENTICATED = "authenticated"
    RECONNECTING = "reconnecting"
    ERROR = "error"


class GameClient:
    """
    Main client class for multiplayer game functionality.
    
    Handles connection to server, message processing, and state synchronization.
    """
    
    def __init__(self, config: ClientConfig):
        """
        Initialize game client.
        
        Args:
            config: Client configuration
        """
        self.config = config
        self.connected = False
        self.running = False
        
        # Connection management
        reconnect_policy = ReconnectPolicy(
            enabled=config.auto_reconnect,
            max_attempts=config.reconnect_attempts,
            initial_delay=config.reconnect_delay
        )
        self.connection_manager = ConnectionManager(reconnect_policy)
        self.connection_manager.start_monitoring()
        
        # Network components
        self.protocol = NetworkProtocol()
        self.connection: Optional[ClientConnection] = None
        self.message_handler = ClientMessageHandler(self)
        
        # Setup connection manager callbacks
        self.connection_manager.add_event_callback('connection_lost', self._on_connection_lost)
        self.connection_manager.add_event_callback('reconnect_success', self._on_reconnect_success)
        self.connection_manager.add_event_callback('reconnect_failed', self._on_reconnect_failed)
        
        # Game state
        self.player_id: Optional[str] = None
        self.server_info: Dict[str, Any] = {}
        self.world: Optional[ClientGameWorld] = None
        
        # Threading
        self.update_thread: Optional[threading.Thread] = None
        self.network_thread: Optional[threading.Thread] = None
        self.ping_thread: Optional[threading.Thread] = None
        
        # Statistics
        self.start_time = time.time()
        self.messages_sent = 0
        self.messages_received = 0
        self.bytes_sent = 0
        self.bytes_received = 0
        self.ping_history = []
        
        # Event callbacks
        self.event_callbacks: Dict[str, list] = {
            'connected': [],
            'disconnected': [],
            'player_joined': [],
            'player_left': [],
            'chat_message': [],
            'world_update': [],
            'error': []
        }
        
        log_info(f"GameClient initialized - Player: {config.player_name}")
    
    def connect(self) -> bool:
        """
        Connect to the game server.
        
        Returns:
            True if connection successful, False otherwise
        """
        if self.connected:
            log_warning("Already connected to server")
            return True
        
        self.connection_manager.set_state(ConnectionState.CONNECTING, "Client connect request")
        log_info(f"Connecting to {self.config.server_host}:{self.config.server_port}")
        
        try:
            # Create connection
            self.connection = ClientConnection(
                self.config.server_host,
                self.config.server_port,
                self.config.connection_timeout
            )
            
            # Set message callback
            self.connection.set_message_callback(self._handle_server_message)
            
            # Connect to server
            if not self.connection.connect():
                self.connection_manager.handle_connection_lost(DisconnectReason.CONNECTION_LOST)
                return False
            
            # Update connection manager
            self.connection_manager.handle_connection_success()
            
            # Send connection request
            self.connection_manager.set_state(ConnectionState.AUTHENTICATING, "Sending auth request")
            connect_data = {
                'player_name': self.config.player_name,
                'world_name': self.config.world_name,
                'client_version': self.protocol.PROTOCOL_VERSION
            }
            
            self.send_message(MessageType.CONNECT, connect_data)
            
            # Wait for connection response
            start_time = time.time()
            while (self.connection_manager.state == ConnectionState.AUTHENTICATING and 
                   time.time() - start_time < self.config.connection_timeout):
                time.sleep(0.1)
            
            if self.connection_manager.state == ConnectionState.AUTHENTICATED:
                self.connected = True
                self.running = True
                self._start_threads()
                self._trigger_event('connected', {})
                log_info("Successfully connected to server")
                return True
            else:
                self.connection_manager.handle_connection_lost(DisconnectReason.AUTHENTICATION_FAILED)
                log_error("Failed to authenticate with server")
                return False
                
        except Exception as e:
            self.connection_manager.handle_connection_lost(DisconnectReason.CONNECTION_LOST)
            log_error(f"Connection failed: {e}")
            return False
    
    def disconnect(self, reason: str = "Client disconnect"):
        """
        Disconnect from the server.
        
        Args:
            reason: Reason for disconnection
        """
        if not self.connected:
            return
        
        log_info(f"Disconnecting from server: {reason}")
        
        # Send disconnect message
        try:
            self.send_message(MessageType.DISCONNECT, {'reason': reason})
        except Exception:
            pass  # Ignore errors when disconnecting
        
        self.running = False
        self.connected = False
        self.connection_manager.set_state(ConnectionState.DISCONNECTED, reason)
        
        # Stop threads
        self._stop_threads()
        
        # Stop connection monitoring
        self.connection_manager.stop_monitoring()
        
        # Close connection
        if self.connection:
            self.connection.disconnect()
            self.connection = None
        
        # Reset state
        self.player_id = None
        self.server_info = {}
        self.world = None
        
        self._trigger_event('disconnected', {'reason': reason})
        log_info("Disconnected from server")
    
    def send_message(self, message_type: MessageType, data: Dict[str, Any]) -> bool:
        """
        Send a message to the server.
        
        Args:
            message_type: Type of message to send
            data: Message data
            
        Returns:
            True if message sent successfully
        """
        if not self.connection or not self.connected:
            log_warning(f"Cannot send {message_type.name}: not connected")
            return False
        
        try:
            if self.config.log_network_traffic:
                log_debug(f"Sending {message_type.name}: {data}")
            
            success = self.connection.send_message(message_type, data)
            if success:
                self.messages_sent += 1
            
            return success
            
        except Exception as e:
            log_error(f"Failed to send message {message_type.name}: {e}")
            return False
    
    def add_event_callback(self, event_type: str, callback: Callable):
        """
        Add an event callback.
        
        Args:
            event_type: Type of event ('connected', 'disconnected', etc.)
            callback: Function to call when event occurs
        """
        if event_type in self.event_callbacks:
            self.event_callbacks[event_type].append(callback)
        else:
            log_warning(f"Unknown event type: {event_type}")
    
    def remove_event_callback(self, event_type: str, callback: Callable):
        """
        Remove an event callback.
        
        Args:
            event_type: Type of event
            callback: Function to remove
        """
        if event_type in self.event_callbacks:
            try:
                self.event_callbacks[event_type].remove(callback)
            except ValueError:
                pass  # Callback not found
    
    def update(self, delta_time: float):
        """
        Update client state.
        
        Args:
            delta_time: Time since last update in seconds
        """
        # Update world if available
        if self.world:
            self.world.update(delta_time)
        
        # Update connection health
        if self.connection:
            connection_stats = self.connection.get_stats()
            self.connection_manager.update_health(
                last_message_time=connection_stats.get('last_message_time', 0),
                messages_sent=connection_stats.get('messages_sent', 0),
                messages_received=connection_stats.get('messages_received', 0),
                bytes_sent=connection_stats.get('bytes_sent', 0),
                bytes_received=connection_stats.get('bytes_received', 0)
            )
        
        # Check connection health
        if self.connected and self.connection:
            if not self.connection.is_connected():
                log_warning("Lost connection to server")
                self.connection_manager.handle_connection_lost(DisconnectReason.CONNECTION_LOST)
    
    def get_client_stats(self) -> Dict[str, Any]:
        """
        Get client statistics.
        
        Returns:
            Dictionary of client statistics
        """
        uptime = time.time() - self.start_time
        
        stats = {
            'connected': self.connected,
            'uptime': uptime,
            'player_id': self.player_id,
            'player_name': self.config.player_name,
            'server_host': self.config.server_host,
            'server_port': self.config.server_port,
            'messages_sent': self.messages_sent,
            'messages_received': self.messages_received,
            'bytes_sent': self.bytes_sent,
            'bytes_received': self.bytes_received,
            'average_ping': self._calculate_average_ping(),
            'world_loaded': self.world is not None
        }
        
        # Add connection manager statistics
        connection_stats = self.connection_manager.get_connection_stats()
        stats['connection_manager'] = connection_stats
        
        # Add connection statistics if available
        if self.connection:
            connection_stats = self.connection.get_stats()
            stats.update({
                'connection_errors': connection_stats.get('errors', 0),
                'last_message_time': connection_stats.get('last_message_time', 0)
            })
        
        return stats
    
    def _handle_server_message(self, message_type: MessageType, data: Dict[str, Any]):
        """
        Handle incoming message from server.
        
        Args:
            message_type: Type of message received
            data: Message data
        """
        self.messages_received += 1
        
        if self.config.log_network_traffic:
            log_debug(f"Received {message_type.name}: {data}")
        
        # Process message through handler
        self.message_handler.handle_message(message_type, data)
    
    def _start_threads(self):
        """Start client threads."""
        # Network update thread
        self.network_thread = threading.Thread(
            target=self._network_update_loop,
            name="ClientNetwork",
            daemon=True
        )
        self.network_thread.start()
        
        # Ping thread
        self.ping_thread = threading.Thread(
            target=self._ping_loop,
            name="ClientPing", 
            daemon=True
        )
        self.ping_thread.start()
        
        log_debug("Client threads started")
    
    def _stop_threads(self):
        """Stop client threads."""
        # Threads will stop when running becomes False
        if self.network_thread and self.network_thread.is_alive():
            self.network_thread.join(timeout=1.0)
        
        if self.ping_thread and self.ping_thread.is_alive():
            self.ping_thread.join(timeout=1.0)
        
        log_debug("Client threads stopped")
    
    def _network_update_loop(self):
        """Network update loop."""
        update_interval = 1.0 / self.config.network_update_rate
        
        while self.running and self.connected:
            try:
                start_time = time.time()
                
                # Process any pending network updates
                if self.world:
                    self.world.process_network_updates()
                
                # Calculate sleep time
                elapsed = time.time() - start_time
                sleep_time = max(0, update_interval - elapsed)
                
                if sleep_time > 0:
                    time.sleep(sleep_time)
                    
            except Exception as e:
                log_error(f"Network update error: {e}")
                time.sleep(0.1)
        
        log_debug("Network update loop stopped")
    
    def _ping_loop(self):
        """Ping loop for connection keepalive."""
        while self.running and self.connected:
            try:
                # Send ping
                ping_data = {'timestamp': time.time()}
                self.send_message(MessageType.PING, ping_data)
                
                time.sleep(self.config.ping_interval)
                
            except Exception as e:
                log_error(f"Ping error: {e}")
                time.sleep(1.0)
        
        log_debug("Ping loop stopped")
    
    def _trigger_event(self, event_type: str, data: Dict[str, Any]):
        """
        Trigger event callbacks.
        
        Args:
            event_type: Type of event
            data: Event data
        """
        if event_type in self.event_callbacks:
            for callback in self.event_callbacks[event_type]:
                try:
                    callback(data)
                except Exception as e:
                    log_error(f"Event callback error for {event_type}: {e}")
    
    def _calculate_average_ping(self) -> float:
        """Calculate average ping from recent history."""
        if not self.ping_history:
            return 0.0
        
        # Keep only recent pings (last 10)
        recent_pings = self.ping_history[-10:]
        return sum(recent_pings) / len(recent_pings)
    
    def record_ping(self, ping_time: float):
        """
        Record a ping time.
        
        Args:
            ping_time: Ping time in milliseconds
        """
        self.ping_history.append(ping_time)
        
        # Record in connection manager
        self.connection_manager.record_ping(ping_time)
        
        # Keep history limited
        if len(self.ping_history) > 50:
            self.ping_history = self.ping_history[-25:]
    
    def _on_connection_lost(self, event_type: str, data: Dict[str, Any]):
        """
        Handle connection lost event from connection manager.
        
        Args:
            event_type: Type of event
            data: Event data
        """
        reason = data.get('reason', DisconnectReason.CONNECTION_LOST)
        log_warning(f"Connection manager detected connection loss: {reason}")
        
        if self.connected:
            self.disconnect(f"Connection lost: {reason}")
    
    def _on_reconnect_success(self, event_type: str, data: Dict[str, Any]):
        """
        Handle successful reconnection.
        
        Args:
            event_type: Type of event
            data: Event data
        """
        attempts = data.get('attempts', 0)
        log_info(f"Reconnection successful after {attempts} attempts")
        
        # Trigger reconnection success event
        self._trigger_event('reconnected', data)
    
    def _on_reconnect_failed(self, event_type: str, data: Dict[str, Any]):
        """
        Handle failed reconnection.
        
        Args:
            event_type: Type of event
            data: Event data
        """
        reason = data.get('reason', 'unknown')
        log_error(f"Reconnection failed: {reason}")
        
        # Trigger reconnection failed event
        self._trigger_event('reconnect_failed', data)
        
        # Ensure we're properly disconnected
        if self.connected:
            self.disconnect(f"Reconnection failed: {reason}")
