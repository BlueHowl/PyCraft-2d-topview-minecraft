"""
Client Connection Management for PyCraft 2D Server

Handles individual client connections, message processing,
and player state synchronization.
"""

import threading
import time
import json
from typing import Optional, Any, Dict

from ..protocol import NetworkProtocol
from ..message_types import MessageType
from ..packets import BasePacket
from ..connection import Connection
from ...utils.logger import log_info, log_error, log_debug, log_warning


class ClientConnection:
    """
    Represents a connection to a single client.
    
    Handles message sending/receiving and maintains client state.
    """
    
    def __init__(self, client_id: str, connection: Connection, address, server):
        """
        Initialize client connection.
        
        Args:
            client_id: Unique identifier for this client
            connection: Network connection object
            address: Client address tuple (ip, port)
            server: Reference to the main game server
        """
        self.client_id = client_id
        self.connection = connection
        self.address = address
        self.server = server
        
        # Client state
        self.player_id: Optional[str] = None
        self.authenticated = False
        self.last_activity = time.time()
        self.last_ping = time.time()
        
        # Threading
        self.running = False
        self.receive_thread: Optional[threading.Thread] = None
        
        # Statistics
        self.messages_sent = 0
        self.messages_received = 0
        self.bytes_sent = 0
        self.bytes_received = 0
        self.connect_time = time.time()
        
        # Protocol
        self.protocol = NetworkProtocol()
        
        log_debug(f"ClientConnection created: {client_id} from {address}")
    
    def start(self):
        """Start the client connection handler."""
        self.running = True
        self.receive_thread = threading.Thread(target=self._receive_loop, daemon=True)
        self.receive_thread.start()
        
        # Note: We don't send anything here - we wait for the client to send CONNECT first
    
    def stop(self):
        """Stop the client connection."""
        self.running = False
        
        if self.connection:
            self.connection.close()
        
        # Only join the thread if we're not calling from within the thread itself
        if (self.receive_thread and 
            self.receive_thread.is_alive() and 
            threading.current_thread() != self.receive_thread):
            self.receive_thread.join(timeout=1.0)
        
        log_debug(f"ClientConnection stopped: {self.client_id}")
    
    def _receive_loop(self):
        """Main receive loop for processing incoming messages."""
        log_info(f"Starting receive loop for client {self.client_id} from {self.connection.address}")
        log_info(f"Socket details: {self.connection.socket}")
        log_info(f"Socket timeout: {self.connection.socket.gettimeout()}")
        log_info(f"Running flag: {self.running}")
        
        while self.running:
            try:
                log_debug(f"About to call receive_message() for {self.client_id}")
                log_debug(f"Socket state before receive: {self.connection.socket}")
                
                # Receive message with longer timeout for established connections
                # Use 5.0 second timeout since client pings every 2 seconds
                envelope = self.connection.receive_message(timeout=10.0)
                
                log_debug(f"receive_message() returned: {type(envelope)} for {self.client_id}")
                
                if not envelope:
                    log_info(f"No message received from {self.client_id} (timeout or connection closed)")
                    log_info(f"Socket state after None: {self.connection.socket}")
                    log_info(f"Running flag when breaking: {self.running}")
                    break
                
                log_info(f"Received {envelope.get('message_type')} from {self.client_id}")
                log_debug(f"Message data: {envelope.get('data', {})}")
                
                # Update activity
                self.last_activity = time.time()
                self.messages_received += 1
                log_debug(f"Updated last_activity to {self.last_activity}, total messages: {self.messages_received}")
                
                # Extract message data
                try:
                    message_type = envelope.get('message_type')
                    data = envelope.get('data', {})
                    
                    if message_type is None:
                        log_error(f"Invalid message from {self.client_id}: missing message_type")
                        continue
                    
                    log_debug(f"Received {message_type.name} from {self.client_id}")
                    
                    # Process message
                    self._handle_message(message_type, data)
                    
                except Exception as e:
                    log_error(f"Error processing message from {self.client_id}: {e}")
                    import traceback
                    log_error(f"Message processing traceback: {traceback.format_exc()}")
                    continue
                
            except Exception as e:
                log_error(f"CRITICAL: Exception in receive loop for {self.client_id}: {e}")
                log_error(f"Exception type: {type(e)}")
                log_error(f"Socket state when exception occurred: {self.connection.socket}")
                log_error(f"Running flag when exception occurred: {self.running}")
                import traceback
                log_error(f"Full traceback: {traceback.format_exc()}")
                if self.running:
                    log_error(f"Breaking from receive loop due to exception")
                break
        
        # Connection lost
        log_info(f"Exited receive loop for {self.client_id}")
        log_info(f"Final running state: {self.running}")
        log_info(f"Final socket state: {self.connection.socket}")
        
        if self.running:
            log_info(f"Connection lost with client {self.client_id} - calling disconnect")
            self.server.disconnect_client(self.client_id, "Connection lost")
        else:
            log_info(f"Receive loop ended normally for {self.client_id} (running=False)")
    
    def _handle_message(self, message_type: MessageType, data: dict):
        """Handle a received message."""
        try:
            # Handle client-specific messages
            if message_type == MessageType.PING:
                self._handle_ping(data)
            elif message_type == MessageType.CONNECT:
                self._handle_connect(data)
            elif message_type == MessageType.DISCONNECT:
                self._handle_disconnect(data)
            else:
                # Forward to server for processing
                self.server.process_client_message(self.client_id, message_type, data)
                
        except Exception as e:
            log_error(f"Error handling {message_type.name} from {self.client_id}: {e}")
    
    def _handle_ping(self, data: dict):
        """Handle ping message."""
        self.last_ping = time.time()
        
        # Send pong response
        self.send_message(MessageType.PONG, {
            'timestamp': data.get('timestamp', time.time()),
            'server_time': time.time()
        })
    
    def _handle_connect(self, data: dict):
        """Handle initial connection request."""
        log_info(f"Processing CONNECT request from {self.client_id}")
        log_info(f"Connect data: {data}")
        log_info(f"Connection state before processing: {self.connection.connected}")
        
        try:
            # Accept both field names for compatibility
            protocol_version = data.get('protocol_version', data.get('client_version', 0))
            player_name = data.get('player_name', 'Unknown')
            world_name = data.get('world_name', 'default')
            
            log_info(f"Client info: {player_name}, protocol: {protocol_version}, world: {world_name}")
            
            if protocol_version != 1:
                log_error(f"Unsupported protocol version {protocol_version} from {self.client_id}")
                self.send_message(MessageType.ERROR, {
                    'error': 'unsupported_protocol',
                    'message': f'Unsupported protocol version: {protocol_version}'
                })
                self.server.disconnect_client(self.client_id, "Unsupported protocol")
                return
            
            # Check for duplicate player names
            if self.server.is_player_name_taken(player_name):
                log_error(f"Player name '{player_name}' is already taken")
                self.send_message(MessageType.CONNECT_RESPONSE, {
                    'success': False,
                    'error_message': f'Player name "{player_name}" is already taken. Please choose a different name.'
                })
                return
            
            # Create player data
            player_data = {
                'player_id': f"player_{self.client_id}",
                'player_name': player_name,
                'x': 0,  # Default spawn position
                'y': 0,
                'health': 100,
                'max_health': 100
            }
            
            log_info(f"Attempting to add player to game: {player_data}")
            
            # Add player to game
            if self.server.handle_player_join(self.client_id, player_data):
                self.authenticated = True
                self.player_id = player_data['player_id']
                log_info(f"Player join successful, sending CONNECT_RESPONSE...")
                
                # Send connection success response (simplified for now)
                response_data = {
                    'success': True,
                    'player_id': player_data['player_id'],
                    'spawn_x': player_data['x'],
                    'spawn_y': player_data['y']
                    # Removed world_data for now to test
                }
                
                log_info(f"Sending CONNECT_RESPONSE: {response_data}")
                send_result = self.send_message(MessageType.CONNECT_RESPONSE, response_data)
                log_info(f"CONNECT_RESPONSE send result: {send_result}")
                
                # Send world state to the new client
                log_info(f"Sending world state to new client {self.client_id}")
                world_state = self.server.world.get_world_state()
                self.send_message(MessageType.WORLD_STATE, world_state)
                
                # Send all existing player states to the new client
                for other_client_id, other_client in self.server.clients.items():
                    if other_client_id != self.client_id and other_client.player_id:
                        player_state = self.server.player_manager.get_player_state(other_client.player_id)
                        if player_state:
                            self.send_message(MessageType.PLAYER_SPAWN_DATA, {
                                'player_id': other_client.player_id,
                                'player_name': player_state.player_name,
                                'x': player_state.x,
                                'y': player_state.y,
                                'health': player_state.health,
                                'max_health': player_state.max_health,
                                'facing_direction': player_state.facing_direction
                            })
                
                # Notify other clients about the new player
                player_state = self.server.player_manager.get_player_state(self.player_id)
                if player_state:
                    for other_client_id, other_client in self.server.clients.items():
                        if other_client_id != self.client_id and other_client.authenticated:
                            other_client.send_message(MessageType.PLAYER_SPAWN_DATA, {
                                'player_id': self.player_id,
                                'player_name': player_state.player_name,
                                'x': player_state.x,
                                'y': player_state.y,
                                'health': player_state.health,
                                'max_health': player_state.max_health,
                                'facing_direction': player_state.facing_direction
                            })
                
                log_info(f"Client {self.client_id} authenticated as {player_name}")
                log_info(f"Connection state after authentication: {self.connection.connected}")
                log_info(f"Authenticated flag: {self.authenticated}")
                
            else:
                log_error(f"Failed to add player {player_name} to game")
                self.send_message(MessageType.CONNECT_RESPONSE, {
                    'success': False,
                    'error_message': 'Failed to join game'
                })
                
        except Exception as e:
            log_error(f"Error handling connect from {self.client_id}: {e}")
            self.send_message(MessageType.ERROR, {
                'error': 'internal_error',
                'message': 'Server error during connection'
            })
    
    def _handle_disconnect(self, data: dict):
        """Handle disconnect request."""
        reason = data.get('reason', 'Client requested disconnect')
        self.server.disconnect_client(self.client_id, reason)
    
    def send_message(self, message_type: MessageType, data: dict) -> bool:
        """
        Send a message to the client.
        
        Args:
            message_type: Type of message to send
            data: Message data
            
        Returns:
            True if sent successfully, False otherwise
        """
        if not self.running or not self.connection:
            log_warning(f"Cannot send {message_type.name} to {self.client_id} - connection not available")
            return False
        
        try:
            log_debug(f"Sending {message_type.name} to {self.client_id} with data: {data}")
            
            # Send message directly (Connection will handle packing)
            success = self.connection.send_message(message_type, data)
            
            if success:
                self.messages_sent += 1
                log_debug(f"Successfully sent {message_type.name} to {self.client_id}")
            else:
                log_warning(f"Failed to send {message_type.name} to {self.client_id}")
            
            return success
            
        except Exception as e:
            log_error(f"Error sending message to {self.client_id}: {e}")
            return False
    
    def send_ping(self):
        """Send a ping to the client."""
        self.send_message(MessageType.PING, {
            'timestamp': time.time()
        })
    
    def get_connection_info(self) -> dict:
        """Get connection information."""
        uptime = time.time() - self.connect_time
        
        return {
            'client_id': self.client_id,
            'player_id': self.player_id,
            'address': self.address,
            'uptime': uptime,
            'authenticated': self.authenticated,
            'last_activity': self.last_activity,
            'last_ping': self.last_ping,
            'messages_sent': self.messages_sent,
            'messages_received': self.messages_received,
            'bytes_sent': self.bytes_sent,
            'bytes_received': self.bytes_received
        }
    
    def is_alive(self) -> bool:
        """Check if the connection is still alive."""
        return self.running and self.connection and not self.connection.is_closed()
    
    def get_ping(self) -> float:
        """Get the last ping time in seconds."""
        return time.time() - self.last_ping
    
    def __str__(self) -> str:
        """String representation of the client connection."""
        return f"ClientConnection({self.client_id}, {self.address}, player={self.player_id})"
    
    def __repr__(self) -> str:
        """Detailed string representation."""
        return (f"ClientConnection(client_id='{self.client_id}', "
                f"player_id='{self.player_id}', address={self.address}, "
                f"authenticated={self.authenticated})")
