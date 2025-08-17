"""
Network Manager - Coordinates networking components and provides unified interface.

This module provides a high-level interface for network operations and
manages the different networking components.
"""

import time
import threading
from typing import Optional, Dict, Any, Callable, List
from enum import Enum

from game.network.protocol import NetworkProtocol
from game.network.connection import Connection, ConnectionManager
from game.network.message_types import MessageType
from game.utils.logger import log_info, log_error, log_warning, log_debug


class NetworkMode(Enum):
    """Network operation modes."""
    OFFLINE = "offline"
    SINGLEPLAYER = "singleplayer"
    CLIENT = "client"
    SERVER = "server"
    LOCAL_SERVER = "local_server"


class NetworkManager:
    """
    Unified network manager for PyCraft 2D.
    
    Provides a clean interface for all networking operations and manages
    the different networking components based on the current mode.
    """
    
    def __init__(self, mode: NetworkMode = NetworkMode.OFFLINE):
        """Initialize the network manager."""
        log_info(f"Initializing NetworkManager in {mode.value} mode")
        
        self.mode = mode
        self.protocol = NetworkProtocol()
        self.connection_manager = ConnectionManager(self.protocol)
        
        # State
        self.running = False
        self.initialized = False
        
        # Client state
        self.client_connection: Optional[Connection] = None
        self.player_id: Optional[str] = None
        self.connected = False
        
        # Server state (for local server mode)
        self.server_socket = None
        self.server_thread = None
        self.max_players = 10
        
        # Callbacks
        self.on_connect: Optional[Callable[[str], None]] = None
        self.on_disconnect: Optional[Callable[[str], None]] = None
        self.on_message: Optional[Callable[[MessageType, Dict[str, Any], str], None]] = None
        self.on_error: Optional[Callable[[Exception], None]] = None
        
        # Statistics
        self.start_time = time.time()
        self.messages_sent = 0
        self.messages_received = 0
        self.bytes_sent = 0
        self.bytes_received = 0
        
    def initialize(self) -> bool:
        """Initialize the network manager."""
        if self.initialized:
            return True
        
        try:
            if self.mode == NetworkMode.OFFLINE:
                log_info("Network manager in offline mode - no networking")
                
            elif self.mode == NetworkMode.SINGLEPLAYER:
                log_info("Network manager in singleplayer mode - local only")
                
            elif self.mode == NetworkMode.LOCAL_SERVER:
                log_info("Network manager in local server mode")
                # Local server initialization would go here
                
            self.initialized = True
            self.running = True
            log_info("Network manager initialized successfully")
            return True
            
        except Exception as e:
            log_error(f"Failed to initialize network manager: {e}")
            return False
    
    def shutdown(self):
        """Shutdown the network manager."""
        if not self.initialized:
            return
        
        log_info("Shutting down network manager...")
        self.running = False
        
        # Disconnect client
        if self.client_connection:
            self.disconnect_from_server("Shutdown")
        
        # Stop server
        if self.server_socket:
            self._stop_server()
        
        # Cleanup connection manager
        self.connection_manager.shutdown_all()
        
        self.initialized = False
        log_info("Network manager shutdown complete")
    
    def set_mode(self, mode: NetworkMode) -> bool:
        """Change the network mode."""
        if self.mode == mode:
            return True
        
        log_info(f"Changing network mode from {self.mode.value} to {mode.value}")
        
        # Shutdown current mode
        if self.initialized:
            self.shutdown()
        
        # Set new mode
        self.mode = mode
        
        # Re-initialize
        return self.initialize()
    
    # Client Methods
    def connect_to_server(self, host: str, port: int, player_name: str, 
                         world_name: Optional[str] = None, timeout: float = 5.0) -> bool:
        """
        Connect to a remote server.
        
        Args:
            host: Server host
            port: Server port
            player_name: Player name
            world_name: Optional world name
            timeout: Connection timeout
            
        Returns:
            True if connection and authentication successful
        """
        if self.mode not in [NetworkMode.CLIENT, NetworkMode.LOCAL_SERVER]:
            log_error(f"Cannot connect in {self.mode.value} mode")
            return False
        
        if self.client_connection:
            log_warning("Already connected to a server")
            return False
        
        try:
            from game.network.connection import create_client_connection
            
            log_info(f"Connecting to server {host}:{port} as {player_name}")
            
            # Create connection
            self.client_connection = create_client_connection(host, port, self.protocol, timeout)
            
            # Set up callbacks
            log_info("Setting up connection callbacks...")
            self.client_connection.on_message = self._handle_client_message
            self.client_connection.on_disconnect = self._handle_client_disconnect
            self.client_connection.on_error = self._handle_client_error
            
            # Start connection
            log_info("Starting client connection...")
            self.client_connection.start()
            log_info(f"Client connection started, connected: {self.client_connection.connected}")
            
            # Send connect message
            log_info("Sending CONNECT message...")
            success = self.client_connection.send_message(
                MessageType.CONNECT,
                {
                    'player_name': player_name,
                    'world_name': world_name,
                    'client_version': self.protocol.PROTOCOL_VERSION
                }
            )
            log_info(f"CONNECT message send result: {success}")
            
            log_info("Connection request sent, waiting for response...")
            
            # Wait for authentication response (with timeout)
            import time
            start_time = time.time()
            while time.time() - start_time < timeout:
                log_debug(f"Waiting for auth... connected={self.connected}, time elapsed={time.time() - start_time:.1f}s")
                
                if self.connected:
                    log_info("Authentication successful")
                    log_info(f"Final connection state: client_connected={self.client_connection.connected}")
                    return True
                    
                if not self.client_connection or not self.client_connection.connected:
                    log_error("Connection lost while waiting for authentication")
                    log_error(f"Client connection state: {self.client_connection.connected if self.client_connection else 'None'}")
                    return False
                    
                time.sleep(0.1)  # Small sleep to prevent busy waiting
            
            log_error(f"Authentication timeout after {timeout}s")
            log_error(f"Final states: self.connected={self.connected}, client_connected={self.client_connection.connected if self.client_connection else 'None'}")
            if self.client_connection:
                self.client_connection.stop()
                self.client_connection = None
            return False
            
        except Exception as e:
            log_error(f"Failed to connect to server: {e}")
            if self.on_error:
                self.on_error(e)
            return False
    
    def disconnect_from_server(self, reason: str = "Disconnected"):
        """Disconnect from the current server."""
        if not self.client_connection:
            return
        
        log_info(f"Disconnecting from server: {reason}")
        
        # Send disconnect message
        if self.connected:
            self.client_connection.send_message(
                MessageType.DISCONNECT,
                {'reason': reason}
            )
        
        # Close connection
        self.client_connection.stop()
        self.client_connection = None
        self.connected = False
        self.player_id = None
        
        if self.on_disconnect:
            self.on_disconnect(reason)
    
    def send_message(self, message_type: MessageType, data: Dict[str, Any], 
                    player_id: Optional[str] = None) -> bool:
        """
        Send a message to the server.
        
        Args:
            message_type: Type of message
            data: Message data
            player_id: Optional player ID
            
        Returns:
            True if message sent successfully
        """
        if not self.client_connection or not self.connected:
            return False
        
        try:
            self.client_connection.send_message(message_type, data, player_id or self.player_id)
            self.messages_sent += 1
            return True
        except Exception as e:
            log_error(f"Failed to send message: {e}")
            return False
    
    # Server Methods (for local server mode)
    def start_local_server(self, port: int = 25565, max_players: int = 10) -> bool:
        """
        Start a local server.
        
        Args:
            port: Server port
            max_players: Maximum number of players
            
        Returns:
            True if server started successfully
        """
        if self.mode != NetworkMode.LOCAL_SERVER:
            log_error("Can only start server in LOCAL_SERVER mode")
            return False
        
        if self.server_socket:
            log_warning("Server already running")
            return False
        
        try:
            from game.network.connection import create_server_socket
            
            log_info(f"Starting local server on port {port}")
            
            self.server_socket = create_server_socket("localhost", port)
            self.max_players = max_players
            
            # Start server thread
            self.server_thread = threading.Thread(target=self._server_loop, daemon=True)
            self.server_thread.start()
            
            log_info(f"Local server started on port {port}")
            return True
            
        except Exception as e:
            log_error(f"Failed to start local server: {e}")
            return False
    
    def _stop_server(self):
        """Stop the local server."""
        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass
            self.server_socket = None
        
        if self.server_thread:
            self.server_thread.join(timeout=1.0)
            self.server_thread = None
    
    def _server_loop(self):
        """Main server loop."""
        log_info("Server loop started")
        
        while self.running and self.server_socket:
            try:
                # Accept new connections
                client_socket, address = self.server_socket.accept()
                log_info(f"New client connection from {address}")
                
                # Create connection
                connection = Connection(client_socket, address, self.protocol)
                connection.on_message = self._handle_server_message
                connection.on_disconnect = self._handle_server_disconnect
                connection.on_error = self._handle_server_error
                
                # Add to connection manager
                connection_id = f"{address[0]}:{address[1]}"
                self.connection_manager.add_connection(connection_id, connection)
                
                # Start connection
                connection.start()
                
            except Exception as e:
                if self.running:  # Only log if we're supposed to be running
                    log_error(f"Server loop error: {e}")
                break
        
        log_info("Server loop ended")
    
    # Message Handlers
    def _handle_client_message(self, message: Dict[str, Any]):
        """Handle message received as client."""
        log_info(f"Client received message: {message}")
        
        message_type = message.get('message_type')
        data = message.get('data', {})
        player_id = message.get('player_id')
        
        log_info(f"Processing message type: {message_type}")
        
        self.messages_received += 1
        
        # Handle connection response
        if message_type == MessageType.CONNECT_RESPONSE:
            log_info("Processing CONNECT_RESPONSE...")
            
            if data.get('success'):
                self.player_id = data.get('player_id')
                self.connected = True
                log_info(f"Connected successfully! Player ID: {self.player_id}")
                log_info(f"Connection state after success: client_connected={self.client_connection.connected}")
                
                # Send immediate ping to keep connection alive
                import time
                current_time = time.time()
                log_info("Sending immediate ping after authentication...")
                ping_result = self.client_connection.send_message(MessageType.PING, {'timestamp': current_time})
                log_info(f"Ping send result: {ping_result}")
                self.last_ping_time = current_time
                
                if self.on_connect:
                    log_info("Calling on_connect callback...")
                    self.on_connect(self.player_id)
                    log_info("on_connect callback completed")
            else:
                error_msg = data.get('error_message', 'Connection failed')
                log_error(f"Connection failed: {error_msg}")
                self.client_connection.stop()
                self.client_connection = None
        
        # Forward to application callback
        log_debug("Forwarding message to application callback if set...")
        if self.on_message:
            self.on_message(message_type, data, player_id)
        log_debug("Message handling complete")
    
    def _handle_client_disconnect(self, reason: str):
        """Handle client disconnect."""
        log_warning(f"DISCONNECT EVENT: Disconnected from server: {reason}")
        log_warning(f"Connection state before disconnect: connected={self.connected}")
        log_warning(f"Client connection state: {self.client_connection.connected if self.client_connection else 'None'}")
        
        self.connected = False
        self.client_connection = None
        self.player_id = None
        
        if self.on_disconnect:
            log_warning("Calling application disconnect callback...")
            self.on_disconnect(reason)
    
    def _handle_client_error(self, error: Exception):
        """Handle client error."""
        log_error(f"CLIENT ERROR EVENT: {error}")
        log_error(f"Error type: {type(error)}")
        log_error(f"Connection state during error: connected={self.connected}")
        log_error(f"Client connection state: {self.client_connection.connected if self.client_connection else 'None'}")
        
        import traceback
        log_error(f"Error traceback: {traceback.format_exc()}")
        
        if self.on_error:
            log_error("Calling application error callback...")
            self.on_error(error)
    
    def _handle_server_message(self, message: Dict[str, Any]):
        """Handle message received as server."""
        # Server message handling would go here
        # For now, just log it
        message_type = message.get('message_type')
        log_debug(f"Server received message: {message_type}")
    
    def _handle_server_disconnect(self, reason: str):
        """Handle server client disconnect."""
        log_info(f"Client disconnected: {reason}")
    
    def _handle_server_error(self, error: Exception):
        """Handle server error."""
        log_error(f"Server error: {error}")
    
    # Utility Methods
    def update(self, dt: float):
        """Update the network manager."""
        if not self.running:
            log_info("NetworkManager.update() called but not running")
            return
        
        # Log state every few updates for debugging
        if not hasattr(self, '_debug_counter'):
            self._debug_counter = 0
        self._debug_counter += 1
        
        if self._debug_counter % 120 == 1:  # Log every ~2 seconds at 60 FPS
            log_info(f"NetworkManager state: running={self.running}, client_connection={self.client_connection is not None}, connected={self.connected}")
        
        # Send periodic pings to keep connection alive
        if self.client_connection and self.connected:
            current_time = time.time()
            # Send ping every 2 seconds to keep connection alive
            if not hasattr(self, 'last_ping_time'):
                self.last_ping_time = current_time
                log_info("NetworkManager: Initializing ping timer")
            elif current_time - self.last_ping_time >= 2.0:
                log_info(f"NetworkManager: Sending periodic ping (last ping was {current_time - self.last_ping_time:.1f}s ago)")
                send_result = self.client_connection.send_message(MessageType.PING, {'timestamp': current_time})
                log_info(f"NetworkManager: Ping send result: {send_result}")
                self.last_ping_time = current_time
        elif self.client_connection:
            if self._debug_counter % 120 == 1:
                log_info(f"NetworkManager: Skipping ping - client_connection exists but connected={self.connected}")
        else:
            if self._debug_counter % 120 == 1:
                log_info("NetworkManager: Skipping ping - no client_connection")
        
        # Cleanup dead connections
        self.connection_manager.cleanup_dead_connections()
        
        # Update statistics
        if self.client_connection:
            stats = self.client_connection.get_stats()
            self.bytes_sent = stats.get('bytes_sent', 0)
            self.bytes_received = stats.get('bytes_received', 0)
    
    def get_status(self) -> Dict[str, Any]:
        """Get network manager status."""
        status = {
            'mode': self.mode.value,
            'initialized': self.initialized,
            'running': self.running,
            'uptime': time.time() - self.start_time,
            'messages_sent': self.messages_sent,
            'messages_received': self.messages_received,
            'bytes_sent': self.bytes_sent,
            'bytes_received': self.bytes_received
        }
        
        # Client status
        if self.client_connection:
            status['client'] = {
                'connected': self.connected,
                'player_id': self.player_id,
                'connection_stats': self.client_connection.get_stats()
            }
        
        # Server status
        if self.server_socket:
            status['server'] = {
                'running': True,
                'connections': self.connection_manager.get_connection_count(),
                'max_players': self.max_players
            }
        
        return status
    
    def is_connected(self) -> bool:
        """Check if connected to a server."""
        return self.connected and self.client_connection is not None
    
    def is_server_running(self) -> bool:
        """Check if local server is running."""
        return self.server_socket is not None
    
    def get_player_id(self) -> Optional[str]:
        """Get the current player ID."""
        return self.player_id
