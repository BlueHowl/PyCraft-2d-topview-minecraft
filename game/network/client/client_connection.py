"""
Client Connection for PyCraft 2D Multiplayer

Handles low-level network communication with the game server.
"""

import socket
import threading
import time
import queue
from typing import Dict, Any, Optional, Callable

from ..message_types import MessageType
from ..protocol import NetworkProtocol

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


class ClientConnection:
    """
    Manages network connection to game server.
    
    Handles socket communication, message sending/receiving, and connection state.
    """
    
    def __init__(self, host: str, port: int, timeout: float = 10.0):
        """
        Initialize client connection.
        
        Args:
            host: Server hostname/IP
            port: Server port
            timeout: Connection timeout in seconds
        """
        self.host = host
        self.port = port
        self.timeout = timeout
        
        # Network components
        self.socket: Optional[socket.socket] = None
        self.protocol = NetworkProtocol()
        
        # Connection state
        self.connected = False
        self.running = False
        
        # Message handling
        self.message_callback: Optional[Callable] = None
        self.receive_thread: Optional[threading.Thread] = None
        self.send_queue = queue.Queue()
        self.send_thread: Optional[threading.Thread] = None
        
        # Statistics
        self.bytes_sent = 0
        self.bytes_received = 0
        self.messages_sent = 0
        self.messages_received = 0
        self.errors = 0
        self.last_message_time = 0
        self.connect_time = 0
        
        log_debug(f"ClientConnection initialized for {host}:{port}")
    
    def connect(self) -> bool:
        """
        Connect to the server.
        
        Returns:
            True if connection successful
        """
        try:
            # Create socket
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(self.timeout)
            
            # Connect to server
            log_info(f"Connecting to {self.host}:{self.port}")
            self.socket.connect((self.host, self.port))
            
            # Set socket to non-blocking for receive thread
            self.socket.settimeout(None)
            
            self.connected = True
            self.running = True
            self.connect_time = time.time()
            
            # Start communication threads
            self._start_threads()
            
            log_info("Connection established")
            return True
            
        except Exception as e:
            log_error(f"Connection failed: {e}")
            self.errors += 1
            self._cleanup()
            return False
    
    def disconnect(self):
        """Disconnect from server."""
        if not self.connected:
            return
        
        log_info("Disconnecting from server")
        
        self.running = False
        self.connected = False
        
        # Stop threads
        self._stop_threads()
        
        # Close socket
        self._cleanup()
        
        log_info("Disconnected")
    
    def send_message(self, message_type: MessageType, data: Dict[str, Any]) -> bool:
        """
        Send a message to the server.
        
        Args:
            message_type: Type of message
            data: Message data
            
        Returns:
            True if message queued successfully
        """
        if not self.connected:
            return False
        
        try:
            # Add to send queue
            self.send_queue.put((message_type, data), timeout=1.0)
            return True
            
        except queue.Full:
            log_warning("Send queue full, dropping message")
            return False
        except Exception as e:
            log_error(f"Failed to queue message: {e}")
            self.errors += 1
            return False
    
    def set_message_callback(self, callback: Callable[[MessageType, Dict[str, Any]], None]):
        """
        Set callback for received messages.
        
        Args:
            callback: Function to call when message received
        """
        self.message_callback = callback
    
    def is_connected(self) -> bool:
        """
        Check if connection is active.
        
        Returns:
            True if connected
        """
        return self.connected and self.socket is not None
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get connection statistics.
        
        Returns:
            Dictionary of connection statistics
        """
        uptime = time.time() - self.connect_time if self.connect_time > 0 else 0
        
        return {
            'connected': self.connected,
            'uptime': uptime,
            'bytes_sent': self.bytes_sent,
            'bytes_received': self.bytes_received,
            'messages_sent': self.messages_sent,
            'messages_received': self.messages_received,
            'errors': self.errors,
            'last_message_time': self.last_message_time,
            'send_queue_size': self.send_queue.qsize()
        }
    
    def _start_threads(self):
        """Start communication threads."""
        # Receive thread
        self.receive_thread = threading.Thread(
            target=self._receive_loop,
            name="ClientReceive",
            daemon=True
        )
        self.receive_thread.start()
        
        # Send thread
        self.send_thread = threading.Thread(
            target=self._send_loop,
            name="ClientSend",
            daemon=True
        )
        self.send_thread.start()
        
        log_debug("Connection threads started")
    
    def _stop_threads(self):
        """Stop communication threads."""
        # Threads will stop when running becomes False
        if self.receive_thread and self.receive_thread.is_alive():
            self.receive_thread.join(timeout=1.0)
        
        if self.send_thread and self.send_thread.is_alive():
            self.send_thread.join(timeout=1.0)
        
        log_debug("Connection threads stopped")
    
    def _receive_loop(self):
        """Message receive loop."""
        buffer = b''
        
        while self.running and self.connected:
            try:
                if not self.socket:
                    break
                
                # Receive data
                data = self.socket.recv(4096)
                if not data:
                    log_info("Server closed connection")
                    break
                
                self.bytes_received += len(data)
                buffer += data
                
                # Process complete messages
                while len(buffer) >= self.protocol.HEADER_SIZE:
                    # Try to get message length from header
                    try:
                        import struct
                        packet_length = struct.unpack('!I', buffer[:4])[0]
                        total_length = self.protocol.HEADER_SIZE + packet_length
                        
                        # Check if we have complete message
                        if len(buffer) >= total_length:
                            # Extract message
                            message_data = buffer[:total_length]
                            buffer = buffer[total_length:]
                            
                            # Process message
                            self._process_received_message(message_data)
                        else:
                            # Wait for more data
                            break
                            
                    except Exception as e:
                        log_error(f"Message parsing error: {e}")
                        # Clear buffer to recover
                        buffer = b''
                        self.errors += 1
                        break
                
            except socket.timeout:
                continue
            except ConnectionResetError:
                log_info("Connection reset by server")
                break
            except Exception as e:
                log_error(f"Receive error: {e}")
                self.errors += 1
                break
        
        # Connection lost
        if self.connected:
            self.connected = False
            log_warning("Receive loop ended, connection lost")
        
        log_debug("Receive loop stopped")
    
    def _send_loop(self):
        """Message send loop."""
        while self.running:
            try:
                # Get message from queue (with timeout)
                message_type, data = self.send_queue.get(timeout=1.0)
                
                if not self.connected or not self.socket:
                    continue
                
                # Pack message
                packed_message = self.protocol.pack_message(message_type, data)
                if not packed_message:
                    log_error(f"Failed to pack message: {message_type.name}")
                    self.errors += 1
                    continue
                
                # Send message
                self.socket.sendall(packed_message)
                self.bytes_sent += len(packed_message)
                self.messages_sent += 1
                
                log_debug(f"Sent {message_type.name} ({len(packed_message)} bytes)")
                
            except queue.Empty:
                continue  # No messages to send
            except Exception as e:
                log_error(f"Send error: {e}")
                self.errors += 1
                # Don't break - try to continue sending
        
        log_debug("Send loop stopped")
    
    def _process_received_message(self, data: bytes):
        """
        Process a received message.
        
        Args:
            data: Raw message data
        """
        try:
            # Unpack message
            envelope = self.protocol.unpack_message(data)
            if not envelope:
                log_error("Failed to unpack message")
                self.errors += 1
                return
            
            message_type = envelope['message_type']
            message_data = envelope['data']
            
            self.messages_received += 1
            self.last_message_time = time.time()
            
            log_debug(f"Received {message_type.name} ({len(data)} bytes)")
            
            # Call message callback
            if self.message_callback:
                try:
                    self.message_callback(message_type, message_data)
                except Exception as e:
                    log_error(f"Message callback error: {e}")
            
        except Exception as e:
            log_error(f"Message processing error: {e}")
            self.errors += 1
    
    def _cleanup(self):
        """Clean up connection resources."""
        if self.socket:
            try:
                self.socket.close()
            except Exception:
                pass
            self.socket = None
        
        log_debug("Connection cleanup completed")
