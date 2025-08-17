"""
Connection handling for PyCraft 2D networking.

Provides low-level TCP connection management with message framing.
"""

import socket
import threading
import time
import struct
from typing import Optional, Callable, Dict, Any
from queue import Queue, Empty

from .protocol import NetworkProtocol
from .message_types import MessageType
from ..utils.logger import log_debug, log_error, log_warning, log_info


class Connection:
    """
    Represents a single TCP connection with message framing.
    
    Handles the low-level socket communication, message framing,
    and provides a clean interface for sending/receiving messages.
    """
    
    def __init__(self, sock: socket.socket, address: tuple, protocol: NetworkProtocol):
        """
        Initialize a connection.
        
        Args:
            sock: The socket object
            address: Remote address tuple (host, port)
            protocol: Network protocol instance
        """
        self.socket = sock
        self.address = address
        self.protocol = protocol
        
        # Connection state
        self.connected = True
        self.last_activity = time.time()
        
        # Threading
        self.receive_thread = None
        self.send_thread = None
        self.running = False
        
        # Message queues
        self.outbound_queue = Queue()
        self.inbound_queue = Queue()
        
        # Callbacks
        self.on_message: Optional[Callable[[Dict[str, Any]], None]] = None
        self.on_disconnect: Optional[Callable[[str], None]] = None
        self.on_error: Optional[Callable[[Exception], None]] = None
        
        # Statistics
        self.bytes_sent = 0
        self.bytes_received = 0
        self.messages_sent = 0
        self.messages_received = 0
        
        # Buffer for partial messages
        self._receive_buffer = b''
        
    def start(self):
        """Start the connection threads."""
        if self.running:
            return
            
        self.running = True
        self.receive_thread = threading.Thread(target=self._receive_loop, daemon=True)
        self.send_thread = threading.Thread(target=self._send_loop, daemon=True)
        
        self.receive_thread.start()
        self.send_thread.start()
    
    def stop(self):
        """Stop the connection and close the socket."""
        self.running = False
        self.connected = False
        
        try:
            self.socket.close()
        except:
            pass
            
        # Wait for threads to finish
        if self.receive_thread and self.receive_thread.is_alive():
            self.receive_thread.join(timeout=1.0)
        if self.send_thread and self.send_thread.is_alive():
            self.send_thread.join(timeout=1.0)

    def close(self):
        """Alias for stop() method for compatibility."""
        self.stop()

    def receive_message(self, timeout: float = 0.1) -> Optional[Dict[str, Any]]:
        """
        Alias for get_message() method for compatibility.
        
        Args:
            timeout: Timeout in seconds
            
        Returns:
            Message dictionary or None if no message available
        """
        return self.get_message(timeout)

    def is_closed(self) -> bool:
        """Check if the connection is closed."""
        return not self.connected
    
    def send_message(self, message_type_or_data, data: Dict[str, Any] = None, 
                    player_id: Optional[str] = None):
        """
        Queue a message for sending.
        
        Args:
            message_type_or_data: MessageType and data dict, or pre-packed bytes
            data: Message data (if first param is MessageType)
            player_id: Optional player ID
        """
        if not self.connected:
            log_warning(f"Cannot send message - connection closed to {self.address}")
            return False
            
        try:
            # Handle both pre-packed bytes and MessageType + data
            if isinstance(message_type_or_data, bytes):
                # Pre-packed message
                packed_message = message_type_or_data
            else:
                # MessageType + data
                log_debug(f"Packing message {message_type_or_data.name} for {self.address}")
                packed_message = self.protocol.pack_message(message_type_or_data, data, player_id)
                log_debug(f"Message packed successfully, size: {len(packed_message)} bytes")
            
            self.outbound_queue.put(packed_message)
            return True
        except Exception as e:
            log_error(f"Error packing/queueing message to {self.address}: {e}")
            if self.on_error:
                self.on_error(e)
            return False
    
    def get_message(self, timeout: float = 0.1) -> Optional[Dict[str, Any]]:
        """
        Get a received message from the queue.
        
        Args:
            timeout: Timeout in seconds
            
        Returns:
            Message dictionary or None if no message available
        """
        log_debug(f"get_message() called with timeout={timeout} for {self.address}")
        log_debug(f"Connected status: {self.connected}")
        log_debug(f"Running status: {self.running}")
        log_debug(f"Queue size: {self.inbound_queue.qsize()}")
        
        try:
            message = self.inbound_queue.get(timeout=timeout)
            log_debug(f"Retrieved message from queue: {type(message)} for {self.address}")
            return message
        except Empty:
            log_debug(f"No message available within timeout {timeout}s for {self.address}")
            log_debug(f"Connection state during timeout: connected={self.connected}, running={self.running}")
            return None
    
    def _send_loop(self):
        """Main sending loop running in separate thread."""
        while self.running and self.connected:
            try:
                # Get message from queue with timeout
                try:
                    message_data = self.outbound_queue.get(timeout=0.1)
                except Empty:
                    continue
                
                log_debug(f"Sending message of {len(message_data)} bytes to {self.address}")
                
                # Send the message
                self._send_raw(message_data)
                self.messages_sent += 1
                self.last_activity = time.time()
                
                log_debug(f"Message sent successfully to {self.address}")
                
            except Exception as e:
                log_error(f"Send loop error to {self.address}: {e}")
                if self.on_error:
                    self.on_error(e)
                self._disconnect("Send error")
                break
    
    def _receive_loop(self):
        """Main receiving loop running in separate thread."""
        log_info(f"Starting receive loop for {self.address}")
        log_info(f"Initial state: connected={self.connected}, running={self.running}")
        
        while self.running and self.connected:
            try:
                log_debug(f"About to call _receive_message() for {self.address}")
                log_debug(f"Socket state: {self.socket}")
                
                # Try to receive a complete message
                message = self._receive_message()
                
                log_debug(f"_receive_message() returned: {type(message)} for {self.address}")
                
                if message:
                    log_debug(f"Received message, putting in queue for {self.address}")
                    self.inbound_queue.put(message)
                    self.messages_received += 1
                    self.last_activity = time.time()
                    log_debug(f"Message queued, total received: {self.messages_received}")
                    
                    # Call message callback if set
                    if self.on_message:
                        try:
                            log_debug(f"Calling message callback for {self.address}")
                            self.on_message(message)
                        except Exception as e:
                            log_error(f"Error in message callback for {self.address}: {e}")
                            if self.on_error:
                                self.on_error(e)
                else:
                    log_debug(f"No message received for {self.address}")
                
            except Exception as e:
                log_error(f"CRITICAL: Exception in receive loop for {self.address}: {e}")
                log_error(f"Exception type: {type(e)}")
                log_error(f"Socket state during exception: {self.socket}")
                log_error(f"Connected state during exception: {self.connected}")
                import traceback
                log_error(f"Full receive loop traceback: {traceback.format_exc()}")
                
                if self.on_error:
                    self.on_error(e)
                log_error(f"Calling _disconnect due to receive error: {e}")
                self._disconnect("Receive error")
                break
        
        log_info(f"Exited receive loop for {self.address}")
        log_info(f"Final state: connected={self.connected}, running={self.running}")
    
    def _send_raw(self, data: bytes):
        """Send raw bytes over the socket."""
        total_sent = 0
        while total_sent < len(data):
            try:
                sent = self.socket.send(data[total_sent:])
                if sent == 0:
                    raise ConnectionError("Socket connection broken")
                total_sent += sent
                self.bytes_sent += sent
            except socket.error as e:
                raise ConnectionError(f"Send failed: {e}")
    
    def _receive_message(self) -> Optional[Dict[str, Any]]:
        """
        Receive and parse a complete message.
        
        Returns:
            Parsed message dictionary or None
        """
        # First, ensure we have at least the header
        while len(self._receive_buffer) < NetworkProtocol.HEADER_SIZE:
            try:
                chunk = self.socket.recv(4096)
                if not chunk:
                    raise ConnectionError("Connection closed by remote")
                self._receive_buffer += chunk
                self.bytes_received += len(chunk)
            except socket.timeout:
                return None
            except socket.error as e:
                raise ConnectionError(f"Receive failed: {e}")
        
        # Parse the header to get message length
        try:
            packet_length = struct.unpack('!I', self._receive_buffer[:4])[0]
        except struct.error:
            raise ConnectionError("Invalid message header")
        
        # Validate packet length
        if packet_length > NetworkProtocol.MAX_PACKET_SIZE - NetworkProtocol.HEADER_SIZE:
            raise ConnectionError(f"Message too large: {packet_length}")
        
        # Calculate total message size
        total_message_size = NetworkProtocol.HEADER_SIZE + packet_length
        
        # Receive the rest of the message
        while len(self._receive_buffer) < total_message_size:
            try:
                needed = total_message_size - len(self._receive_buffer)
                chunk = self.socket.recv(min(needed, 4096))
                if not chunk:
                    raise ConnectionError("Connection closed by remote")
                self._receive_buffer += chunk
                self.bytes_received += len(chunk)
            except socket.timeout:
                return None
            except socket.error as e:
                raise ConnectionError(f"Receive failed: {e}")
        
        # Extract the complete message
        message_data = self._receive_buffer[:total_message_size]
        self._receive_buffer = self._receive_buffer[total_message_size:]
        
        # Parse the message
        return self.protocol.unpack_message(message_data)
    
    def _disconnect(self, reason: str):
        """Handle disconnection."""
        if not self.connected:
            return
            
        self.connected = False
        if self.on_disconnect:
            self.on_disconnect(reason)
    
    def is_alive(self) -> bool:
        """Check if the connection is still alive."""
        return self.connected and self.running
    
    def get_stats(self) -> Dict[str, Any]:
        """Get connection statistics."""
        return {
            'connected': self.connected,
            'address': self.address,
            'bytes_sent': self.bytes_sent,
            'bytes_received': self.bytes_received,
            'messages_sent': self.messages_sent,
            'messages_received': self.messages_received,
            'last_activity': self.last_activity,
            'uptime': time.time() - self.last_activity if self.connected else 0
        }


class ConnectionManager:
    """
    Manages multiple connections and provides utilities for connection handling.
    """
    
    def __init__(self, protocol: NetworkProtocol):
        """Initialize the connection manager."""
        self.protocol = protocol
        self.connections: Dict[str, Connection] = {}
        self.connection_timeout = 30.0  # seconds
        
    def add_connection(self, connection_id: str, connection: Connection):
        """Add a connection to be managed."""
        self.connections[connection_id] = connection
        
    def remove_connection(self, connection_id: str):
        """Remove and cleanup a connection."""
        if connection_id in self.connections:
            connection = self.connections[connection_id]
            connection.stop()
            del self.connections[connection_id]
    
    def get_connection(self, connection_id: str) -> Optional[Connection]:
        """Get a connection by ID."""
        return self.connections.get(connection_id)
    
    def broadcast_message(self, message_type: MessageType, data: Dict[str, Any],
                         exclude: Optional[str] = None):
        """
        Broadcast a message to all connections.
        
        Args:
            message_type: Type of message to broadcast
            data: Message data
            exclude: Connection ID to exclude from broadcast
        """
        for connection_id, connection in self.connections.items():
            if connection_id != exclude and connection.is_alive():
                connection.send_message(message_type, data)
    
    def cleanup_dead_connections(self):
        """Remove dead or timed-out connections."""
        current_time = time.time()
        dead_connections = []
        
        for connection_id, connection in self.connections.items():
            if not connection.is_alive():
                dead_connections.append(connection_id)
            elif (current_time - connection.last_activity) > self.connection_timeout:
                dead_connections.append(connection_id)
        
        for connection_id in dead_connections:
            self.remove_connection(connection_id)
    
    def get_connection_count(self) -> int:
        """Get the number of active connections."""
        return len([conn for conn in self.connections.values() if conn.is_alive()])
    
    def get_all_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get statistics for all connections."""
        return {
            connection_id: connection.get_stats()
            for connection_id, connection in self.connections.items()
        }
    
    def shutdown_all(self):
        """Shutdown all connections."""
        for connection in self.connections.values():
            connection.stop()
        self.connections.clear()


def create_client_connection(host: str, port: int, protocol: NetworkProtocol, 
                           timeout: float = 5.0) -> Connection:
    """
    Create a client connection to a server.
    
    Args:
        host: Server hostname or IP
        port: Server port
        protocol: Network protocol instance
        timeout: Connection timeout
        
    Returns:
        Connected Connection object
        
    Raises:
        ConnectionError: If connection fails
    """
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        sock.connect((host, port))
        sock.settimeout(5.0)  # Set longer timeout for ongoing operations
        
        connection = Connection(sock, (host, port), protocol)
        return connection
        
    except Exception as e:
        raise ConnectionError(f"Failed to connect to {host}:{port}: {e}")


def create_server_socket(host: str, port: int, backlog: int = 5) -> socket.socket:
    """
    Create a server socket for accepting connections.
    
    Args:
        host: Host to bind to
        port: Port to bind to
        backlog: Maximum number of pending connections
        
    Returns:
        Server socket
        
    Raises:
        ConnectionError: If socket creation fails
    """
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((host, port))
        sock.listen(backlog)
        return sock
        
    except Exception as e:
        raise ConnectionError(f"Failed to create server socket on {host}:{port}: {e}")
