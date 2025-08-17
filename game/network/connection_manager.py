"""
Connection Management for PyCraft 2D Multiplayer

Handles connection lifecycle, health monitoring, reconnection logic, and error recovery.
"""

import time
import threading
import queue
from typing import Dict, Any, Optional, Callable, List
from enum import Enum
from dataclasses import dataclass

from .message_types import MessageType


class ConnectionState(Enum):
    """Connection state enumeration."""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    AUTHENTICATING = "authenticating"
    AUTHENTICATED = "authenticated"
    RECONNECTING = "reconnecting"
    ERROR = "error"
    TIMEOUT = "timeout"


class DisconnectReason(Enum):
    """Disconnect reason enumeration."""
    CLIENT_REQUEST = "client_request"
    USER_REQUESTED = "user_requested"  # Alias for CLIENT_REQUEST
    SERVER_SHUTDOWN = "server_shutdown"
    CONNECTION_LOST = "connection_lost"
    NETWORK_ERROR = "network_error"  # Alias for CONNECTION_LOST
    TIMEOUT = "timeout"
    AUTHENTICATION_FAILED = "authentication_failed"
    PROTOCOL_ERROR = "protocol_error"
    KICKED = "kicked"
    BANNED = "banned"
    SERVER_FULL = "server_full"
    VERSION_MISMATCH = "version_mismatch"


@dataclass
class ConnectionHealth:
    """Connection health metrics."""
    ping: float = 0.0
    packet_loss: float = 0.0
    last_message_time: float = 0.0
    messages_sent: int = 0
    messages_received: int = 0
    bytes_sent: int = 0
    bytes_received: int = 0
    connection_uptime: float = 0.0
    reconnect_count: int = 0
    error_count: int = 0


@dataclass
class ReconnectPolicy:
    """Reconnection policy configuration."""
    enabled: bool = True
    max_attempts: int = 5
    initial_delay: float = 1.0
    max_delay: float = 30.0
    backoff_multiplier: float = 2.0
    jitter: bool = True


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


class ConnectionManager:
    """
    Manages connection lifecycle, health monitoring, and reconnection logic.
    
    Provides robust connection management with automatic reconnection,
    health monitoring, and error recovery.
    """
    
    def __init__(self, client=None, reconnect_policy: Optional[ReconnectPolicy] = None):
        """
        Initialize connection manager.
        
        Args:
            client: Client instance (optional for testing)
            reconnect_policy: Reconnection policy configuration
        """
        self.client = client
        self.reconnect_policy = reconnect_policy or ReconnectPolicy()
        
        # Connection state
        self.state = ConnectionState.DISCONNECTED
        self.health = ConnectionHealth()
        self.last_state_change = time.time()
        
        # Monitoring
        self.ping_history: List[float] = []
        self.packet_loss_history: List[float] = []
        self.connection_events: List[Dict[str, Any]] = []
        
        # Reconnection
        self.reconnect_attempts = 0
        self.last_reconnect_time = 0.0
        self.reconnect_thread: Optional[threading.Thread] = None
        
        # Health monitoring
        self.health_check_interval = 5.0
        self.ping_interval = 5.0  # How often to send pings
        self.timeout_threshold = 10.0  # Connection timeout threshold
        self.health_thread: Optional[threading.Thread] = None
        self.monitoring_active = False
        
        # Event callbacks
        self.event_callbacks: Dict[str, List[Callable]] = {
            'state_changed': [],
            'connection_lost': [],
            'reconnect_started': [],
            'reconnect_success': [],
            'reconnect_failed': [],
            'health_degraded': [],
            'health_recovered': []
        }
        
        log_info("ConnectionManager initialized")
    
    @property
    def max_reconnect_attempts(self) -> int:
        """Get maximum reconnection attempts."""
        return self.reconnect_policy.max_attempts
    
    @max_reconnect_attempts.setter
    def max_reconnect_attempts(self, value: int):
        """Set maximum reconnection attempts."""
        self.reconnect_policy.max_attempts = value
    
    @property
    def reconnect_delay(self) -> float:
        """Get initial reconnection delay."""
        return self.reconnect_policy.initial_delay
    
    @reconnect_delay.setter
    def reconnect_delay(self, value: float):
        """Set initial reconnection delay."""
        self.reconnect_policy.initial_delay = value
    
    @property
    def auto_reconnect(self) -> bool:
        """Get auto-reconnection enabled state."""
        return self.reconnect_policy.enabled
    
    @auto_reconnect.setter
    def auto_reconnect(self, value: bool):
        """Set auto-reconnection enabled state."""
        self.reconnect_policy.enabled = value
    
    def set_state(self, new_state: ConnectionState, reason: str = ""):
        """
        Set connection state.
        
        Args:
            new_state: New connection state
            reason: Reason for state change
        """
        if self.state != new_state:
            old_state = self.state
            self.state = new_state
            self.last_state_change = time.time()
            
            # Record event
            self._record_event('state_change', {
                'old_state': old_state.value,
                'new_state': new_state.value,
                'reason': reason
            })
            
            # Trigger callbacks
            self._trigger_event('state_changed', {
                'old_state': old_state,
                'new_state': new_state,
                'reason': reason
            })
            
            log_info(f"Connection state: {old_state.value} -> {new_state.value} ({reason})")
    
    def get_state(self) -> ConnectionState:
        """Get current connection state."""
        return self.state
    
    def start_monitoring(self):
        """Start connection health monitoring."""
        if self.monitoring_active:
            return
        
        self.monitoring_active = True
        
        # Start health monitoring thread
        self.health_thread = threading.Thread(
            target=self._health_monitoring_loop,
            name="ConnectionHealthMonitor",
            daemon=True
        )
        self.health_thread.start()
        
        log_debug("Connection monitoring started")
    
    def start_health_monitoring(self):
        """Alias for start_monitoring for compatibility."""
        self.start_monitoring()
    
    def stop_health_monitoring(self):
        """Alias for stop_monitoring for compatibility."""
        self.stop_monitoring()
    
    def stop_monitoring(self):
        """Stop connection health monitoring."""
        self.monitoring_active = False
        
        if self.health_thread and self.health_thread.is_alive():
            self.health_thread.join(timeout=1.0)
        
        log_debug("Connection monitoring stopped")
    
    def update_health(self, **metrics):
        """
        Update connection health metrics.
        
        Args:
            **metrics: Health metrics to update
        """
        for key, value in metrics.items():
            if hasattr(self.health, key):
                setattr(self.health, key, value)
        
        # Update connection uptime
        if self.state in [ConnectionState.CONNECTED, ConnectionState.AUTHENTICATED]:
            self.health.connection_uptime = time.time() - self.last_state_change
        
        # Check health thresholds
        self._check_health_thresholds()
    
    def record_ping(self, ping_time: float):
        """
        Record ping measurement.
        
        Args:
            ping_time: Ping time in milliseconds
        """
        self.health.ping = ping_time
        self.ping_history.append(ping_time)
        
        # Keep history limited
        if len(self.ping_history) > 100:
            self.ping_history = self.ping_history[-50:]
    
    def calculate_packet_loss(self, sent_count: int, received_count: int):
        """
        Calculate and record packet loss.
        
        Args:
            sent_count: Number of packets sent
            received_count: Number of packets received
        """
        if sent_count > 0:
            loss_rate = max(0, (sent_count - received_count) / sent_count)
            self.health.packet_loss = loss_rate
            self.packet_loss_history.append(loss_rate)
            
            # Keep history limited
            if len(self.packet_loss_history) > 50:
                self.packet_loss_history = self.packet_loss_history[-25:]
    
    def handle_connection_lost(self, reason: DisconnectReason):
        """
        Handle connection loss.
        
        Args:
            reason: Reason for connection loss
        """
        self.set_state(ConnectionState.DISCONNECTED, f"Connection lost: {reason.value}")
        self.health.error_count += 1
        
        # Record event
        self._record_event('connection_lost', {
            'reason': reason.value,
            'uptime': self.health.connection_uptime
        })
        
        # Trigger callback
        self._trigger_event('connection_lost', {'reason': reason})
        
        # Start reconnection if enabled
        if self.reconnect_policy.enabled and reason != DisconnectReason.CLIENT_REQUEST:
            self._start_reconnection()
    
    def handle_connection_success(self):
        """Handle successful connection."""
        self.set_state(ConnectionState.CONNECTED, "Connection established")
        self.reconnect_attempts = 0
        self.last_reconnect_time = 0
        
        # Reset health metrics
        self.health.error_count = 0
        self.health.connection_uptime = 0
        
        # Record event
        self._record_event('connection_success', {
            'attempts': self.reconnect_attempts
        })
    
    def handle_authentication_success(self):
        """Handle successful authentication."""
        self.set_state(ConnectionState.AUTHENTICATED, "Authentication successful")
        
        # Record event
        self._record_event('authentication_success', {})
    
    def cancel_reconnection(self):
        """Cancel ongoing reconnection attempts."""
        if self.reconnect_thread and self.reconnect_thread.is_alive():
            # Signal thread to stop (would need a stop flag in real implementation)
            pass
        
        self.reconnect_attempts = 0
        
        if self.state == ConnectionState.RECONNECTING:
            self.set_state(ConnectionState.DISCONNECTED, "Reconnection cancelled")
    
    def force_reconnect(self):
        """Force immediate reconnection attempt."""
        if self.state in [ConnectionState.CONNECTED, ConnectionState.AUTHENTICATED]:
            log_warning("Forcing reconnection while connected")
        
        self._start_reconnection()
    
    def get_connection_stats(self) -> Dict[str, Any]:
        """
        Get comprehensive connection statistics.
        
        Returns:
            Dictionary of connection statistics
        """
        avg_ping = sum(self.ping_history) / len(self.ping_history) if self.ping_history else 0
        avg_packet_loss = sum(self.packet_loss_history) / len(self.packet_loss_history) if self.packet_loss_history else 0
        
        return {
            'state': self.state.value,
            'health': {
                'ping': self.health.ping,
                'average_ping': avg_ping,
                'packet_loss': self.health.packet_loss,
                'average_packet_loss': avg_packet_loss,
                'last_message_time': self.health.last_message_time,
                'connection_uptime': self.health.connection_uptime,
                'error_count': self.health.error_count
            },
            'reconnection': {
                'policy_enabled': self.reconnect_policy.enabled,
                'attempts': self.reconnect_attempts,
                'max_attempts': self.reconnect_policy.max_attempts,
                'total_reconnects': self.health.reconnect_count
            },
            'traffic': {
                'messages_sent': self.health.messages_sent,
                'messages_received': self.health.messages_received,
                'bytes_sent': self.health.bytes_sent,
                'bytes_received': self.health.bytes_received
            },
            'events_recorded': len(self.connection_events)
        }
    
    def get_recent_events(self, count: int = 10) -> List[Dict[str, Any]]:
        """
        Get recent connection events.
        
        Args:
            count: Number of recent events to return
            
        Returns:
            List of recent events
        """
        return self.connection_events[-count:] if self.connection_events else []
    
    def add_event_callback(self, event_type: str, callback: Callable):
        """
        Add event callback.
        
        Args:
            event_type: Type of event
            callback: Callback function
        """
        if event_type in self.event_callbacks:
            self.event_callbacks[event_type].append(callback)
    
    def on_state_changed(self, callback: Callable):
        """Add callback for state change events."""
        self.add_event_callback('state_changed', callback)
    
    def on_connection_lost(self, callback: Callable):
        """Add callback for connection lost events."""
        self.add_event_callback('connection_lost', callback)
    
    def on_reconnect_attempt(self, callback: Callable):
        """Add callback for reconnect attempt events."""
        self.add_event_callback('reconnect_started', callback)
    
    def remove_event_callback(self, event_type: str, callback: Callable):
        """
        Remove event callback.
        
        Args:
            event_type: Type of event
            callback: Callback function to remove
        """
        if event_type in self.event_callbacks:
            try:
                self.event_callbacks[event_type].remove(callback)
            except ValueError:
                pass
    
    def _start_reconnection(self):
        """Start reconnection process."""
        if self.state == ConnectionState.RECONNECTING:
            return  # Already reconnecting
        
        if self.reconnect_attempts >= self.reconnect_policy.max_attempts:
            log_error(f"Max reconnection attempts ({self.reconnect_policy.max_attempts}) exceeded")
            self.set_state(ConnectionState.ERROR, "Max reconnection attempts exceeded")
            self._trigger_event('reconnect_failed', {'reason': 'max_attempts_exceeded'})
            return
        
        self.set_state(ConnectionState.RECONNECTING, "Starting reconnection")
        self._trigger_event('reconnect_started', {'attempt': self.reconnect_attempts + 1})
        
        # Start reconnection thread
        self.reconnect_thread = threading.Thread(
            target=self._reconnection_loop,
            name="ConnectionReconnect",
            daemon=True
        )
        self.reconnect_thread.start()
    
    def _reconnection_loop(self):
        """Reconnection loop with exponential backoff."""
        while (self.state == ConnectionState.RECONNECTING and 
               self.reconnect_attempts < self.reconnect_policy.max_attempts):
            
            self.reconnect_attempts += 1
            
            # Calculate delay with exponential backoff
            delay = min(
                self.reconnect_policy.initial_delay * (self.reconnect_policy.backoff_multiplier ** (self.reconnect_attempts - 1)),
                self.reconnect_policy.max_delay
            )
            
            # Add jitter if enabled
            if self.reconnect_policy.jitter:
                import random
                delay *= (0.5 + random.random() * 0.5)  # 50-100% of calculated delay
            
            log_info(f"Reconnection attempt {self.reconnect_attempts}/{self.reconnect_policy.max_attempts} in {delay:.1f}s")
            
            # Wait for delay
            time.sleep(delay)
            
            # Attempt reconnection (this would call the actual connection logic)
            if self._attempt_reconnection():
                self.health.reconnect_count += 1
                self._trigger_event('reconnect_success', {'attempts': self.reconnect_attempts})
                log_info("Reconnection successful")
                return
            else:
                log_warning(f"Reconnection attempt {self.reconnect_attempts} failed")
        
        # All attempts failed
        if self.reconnect_attempts >= self.reconnect_policy.max_attempts:
            self.set_state(ConnectionState.ERROR, "Reconnection failed")
            self._trigger_event('reconnect_failed', {'reason': 'all_attempts_failed'})
            log_error("All reconnection attempts failed")
    
    def _attempt_reconnection(self) -> bool:
        """
        Attempt to reconnect.
        
        Returns:
            True if reconnection successful
        """
        # This would contain the actual reconnection logic
        # For now, simulate a reconnection attempt
        self.last_reconnect_time = time.time()
        
        # Simulate success/failure (in real implementation, this would try to connect)
        import random
        success = random.random() > 0.3  # 70% success rate for simulation
        
        if success:
            self.handle_connection_success()
            return True
        else:
            return False
    
    def _health_monitoring_loop(self):
        """Health monitoring loop."""
        last_ping_time = 0.0
        
        while self.monitoring_active:
            try:
                current_time = time.time()
                
                # Send periodic pings if client is available and connected
                if (self.client and hasattr(self.client, 'send_ping') and 
                    self.state in [ConnectionState.CONNECTED, ConnectionState.AUTHENTICATED] and
                    current_time - last_ping_time >= self.ping_interval):
                    
                    try:
                        self.client.send_ping()
                        last_ping_time = current_time
                    except Exception as e:
                        log_warning(f"Failed to send ping: {e}")
                
                # Check for connection timeout
                if (self.health.last_message_time > 0 and 
                    current_time - self.health.last_message_time > self.timeout_threshold):
                    
                    if self.state in [ConnectionState.CONNECTED, ConnectionState.AUTHENTICATED]:
                        log_warning("Connection timeout detected")
                        self.handle_connection_lost(DisconnectReason.TIMEOUT)
                
                # Check ping health
                if self.ping_history:
                    recent_pings = self.ping_history[-10:]  # Last 10 pings
                    avg_recent_ping = sum(recent_pings) / len(recent_pings)
                    
                    if avg_recent_ping > 1000:  # High ping threshold
                        self._record_event('health_warning', {
                            'type': 'high_ping',
                            'value': avg_recent_ping
                        })
                
                # Check packet loss
                if self.packet_loss_history:
                    recent_loss = self.packet_loss_history[-5:]  # Last 5 measurements
                    avg_recent_loss = sum(recent_loss) / len(recent_loss)
                    
                    if avg_recent_loss > 0.1:  # 10% packet loss threshold
                        self._record_event('health_warning', {
                            'type': 'high_packet_loss',
                            'value': avg_recent_loss
                        })
                
                time.sleep(self.health_check_interval)
                
            except Exception as e:
                log_error(f"Health monitoring error: {e}")
                time.sleep(1.0)
        
        log_debug("Health monitoring loop stopped")
    
    def _check_health_thresholds(self):
        """Check if health metrics exceed thresholds."""
        # Ping threshold
        if self.health.ping > 500:  # 500ms
            self._trigger_event('health_degraded', {
                'metric': 'ping',
                'value': self.health.ping,
                'threshold': 500
            })
        
        # Packet loss threshold
        if self.health.packet_loss > 0.05:  # 5%
            self._trigger_event('health_degraded', {
                'metric': 'packet_loss',
                'value': self.health.packet_loss,
                'threshold': 0.05
            })
    
    def _record_event(self, event_type: str, data: Dict[str, Any]):
        """
        Record a connection event.
        
        Args:
            event_type: Type of event
            data: Event data
        """
        event = {
            'type': event_type,
            'timestamp': time.time(),
            'data': data
        }
        
        self.connection_events.append(event)
        
        # Keep event history limited
        if len(self.connection_events) > 1000:
            self.connection_events = self.connection_events[-500:]
    
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
                    callback(event_type, data)
                except Exception as e:
                    log_error(f"Event callback error for {event_type}: {e}")


class ConnectionPool:
    """
    Manages multiple connections for load balancing and redundancy.
    """
    
    def __init__(self, max_connections: int = 3, max_size: int = None):
        """
        Initialize connection pool.
        
        Args:
            max_connections: Maximum number of connections
            max_size: Alias for max_connections (for compatibility)
        """
        # Support both parameter names for compatibility
        if max_size is not None:
            max_connections = max_size
            
        self.max_connections = max_connections
        self.connections: Dict[str, ConnectionManager] = {}
        self.active_connection: Optional[str] = None
        
        log_info(f"ConnectionPool initialized with max {max_connections} connections")
    
    def add_connection(self, connection_id: str, manager: ConnectionManager):
        """
        Add connection to pool.
        
        Args:
            connection_id: Unique connection ID
            manager: Connection manager instance
        """
        if len(self.connections) >= self.max_connections:
            log_warning(f"Connection pool full, cannot add {connection_id}")
            return False
        
        self.connections[connection_id] = manager
        
        if self.active_connection is None:
            self.active_connection = connection_id
        
        log_info(f"Added connection {connection_id} to pool")
        return True
    
    def remove_connection(self, connection_id: str):
        """
        Remove connection from pool.
        
        Args:
            connection_id: Connection ID to remove
        """
        if connection_id in self.connections:
            del self.connections[connection_id]
            
            if self.active_connection == connection_id:
                # Switch to another connection
                self.active_connection = next(iter(self.connections), None)
            
            log_info(f"Removed connection {connection_id} from pool")
    
    def get_active_connection(self) -> Optional[ConnectionManager]:
        """
        Get active connection manager.
        
        Returns:
            Active connection manager or None
        """
        if self.active_connection and self.active_connection in self.connections:
            return self.connections[self.active_connection]
        return None
    
    def size(self) -> int:
        """Get number of connections in pool."""
        return len(self.connections)
    
    def get_connection(self, connection_id: str) -> Optional[ConnectionManager]:
        """Get specific connection by ID."""
        return self.connections.get(connection_id)
    
    def switch_connection(self, connection_id: str) -> bool:
        """
        Switch to different connection.
        
        Args:
            connection_id: Connection ID to switch to
            
        Returns:
            True if switch successful
        """
        if connection_id in self.connections:
            self.active_connection = connection_id
            log_info(f"Switched to connection {connection_id}")
            return True
        return False
    
    def get_pool_stats(self) -> Dict[str, Any]:
        """
        Get connection pool statistics.
        
        Returns:
            Pool statistics
        """
        stats = {
            'total_connections': len(self.connections),
            'active_connection': self.active_connection,
            'connections': {}
        }
        
        for conn_id, manager in self.connections.items():
            stats['connections'][conn_id] = manager.get_connection_stats()
        
        return stats
