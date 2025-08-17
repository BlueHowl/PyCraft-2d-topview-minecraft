"""
Network Protocol for PyCraft 2D

Handles message serialization, deserialization, and protocol management.
"""

import json
import struct
import time
import uuid
from typing import Dict, Any, Optional, Union, List
from enum import Enum

from .message_types import MessageType, MessagePriority, get_message_priority


class NetworkProtocol:
    """
    Main protocol class for handling network communication.
    
    Protocol Format:
    [4 bytes: packet_length][4 bytes: message_type][8 bytes: timestamp][variable: json_data]
    """
    
    HEADER_SIZE = 16  # 4 + 4 + 8 bytes
    PROTOCOL_VERSION = 1
    MAX_PACKET_SIZE = 1024 * 64  # 64KB
    
    def __init__(self):
        """Initialize the network protocol."""
        self.message_handlers = {}
        self.sequence_number = 0
        
    def pack_message(self, message_type: MessageType, data: Dict[str, Any], 
                    player_id: Optional[str] = None) -> bytes:
        """
        Pack a message into bytes for network transmission.
        
        Args:
            message_type: Type of message to send
            data: Message data dictionary
            player_id: Optional player ID for the message
            
        Returns:
            Packed message as bytes
            
        Raises:
            ValueError: If message is too large or invalid
        """
        try:
            # Create message envelope
            envelope = {
                'type': message_type.value,
                'timestamp': time.time(),
                'sequence': self._get_next_sequence(),
                'player_id': player_id,
                'data': data,
                'protocol_version': self.PROTOCOL_VERSION
            }
            
            # Serialize to JSON
            json_data = json.dumps(envelope, separators=(',', ':')).encode('utf-8')
            
            # Check size limit
            total_size = self.HEADER_SIZE + len(json_data)
            if total_size > self.MAX_PACKET_SIZE:
                raise ValueError(f"Message too large: {total_size} bytes (max: {self.MAX_PACKET_SIZE})")
            
            # Pack header: [packet_length][message_type][timestamp]
            header = struct.pack('!IIQ', 
                               len(json_data),                    # packet length (4 bytes)
                               message_type.value,                # message type (4 bytes)
                               int(envelope['timestamp'] * 1000)) # timestamp in ms (8 bytes)
            
            return header + json_data
            
        except Exception as e:
            raise ValueError(f"Failed to pack message: {e}")
    
    def unpack_message(self, data: bytes) -> Optional[Dict[str, Any]]:
        """
        Unpack a message from bytes.
        
        Args:
            data: Raw bytes received from network
            
        Returns:
            Unpacked message dictionary or None if invalid
        """
        try:
            if len(data) < self.HEADER_SIZE:
                return None
                
            # Unpack header
            packet_length, message_type_value, timestamp_ms = struct.unpack('!IIQ', data[:self.HEADER_SIZE])
            
            # Validate packet length
            if packet_length != len(data) - self.HEADER_SIZE:
                return None
                
            # Extract JSON data
            json_data = data[self.HEADER_SIZE:].decode('utf-8')
            envelope = json.loads(json_data)
            
            # Validate message type
            try:
                message_type = MessageType(message_type_value)
            except ValueError:
                return None
                
            # Validate protocol version
            if envelope.get('protocol_version', 0) != self.PROTOCOL_VERSION:
                return None
                
            envelope['message_type'] = message_type
            envelope['timestamp'] = timestamp_ms / 1000.0
            
            return envelope
            
        except Exception:
            return None
    
    def create_connect_message(self, player_name: str, world_name: Optional[str] = None) -> bytes:
        """Create a connection request message."""
        data = {
            'player_name': player_name,
            'world_name': world_name,
            'client_version': self.PROTOCOL_VERSION
        }
        return self.pack_message(MessageType.CONNECT, data)
    
    def create_connect_response_message(self, success: bool, player_id: str = None, 
                                      error_message: str = None, server_info: Dict = None) -> bytes:
        """Create a connection response message."""
        data = {
            'success': success,
            'player_id': player_id,
            'error_message': error_message,
            'server_info': server_info or {}
        }
        return self.pack_message(MessageType.CONNECT_RESPONSE, data)
    
    def create_disconnect_message(self, reason: str = "Disconnected") -> bytes:
        """Create a disconnect message."""
        data = {'reason': reason}
        return self.pack_message(MessageType.DISCONNECT, data)
    
    def create_ping_message(self) -> bytes:
        """Create a ping message for connection keepalive."""
        data = {'ping_time': time.time()}
        return self.pack_message(MessageType.PING, data)
    
    def create_pong_message(self, ping_time: float) -> bytes:
        """Create a pong response message."""
        data = {
            'ping_time': ping_time,
            'pong_time': time.time()
        }
        return self.pack_message(MessageType.PONG, data)
    
    def create_player_move_message(self, player_id: str, x: float, y: float, 
                                 vel_x: float, vel_y: float, direction: str) -> bytes:
        """Create a player movement message."""
        data = {
            'x': x,
            'y': y,
            'vel_x': vel_x,
            'vel_y': vel_y,
            'direction': direction
        }
        return self.pack_message(MessageType.PLAYER_MOVE, data, player_id)
    
    def create_player_update_message(self, player_id: str, health: int, max_health: int,
                                   inventory: List[Dict], position: Dict[str, float]) -> bytes:
        """Create a comprehensive player update message."""
        data = {
            'health': health,
            'max_health': max_health,
            'inventory': inventory,
            'position': position
        }
        return self.pack_message(MessageType.PLAYER_UPDATE, data, player_id)
    
    def create_block_place_message(self, player_id: str, x: int, y: int, 
                                 block_id: int, chunk_x: int, chunk_y: int) -> bytes:
        """Create a block placement message."""
        data = {
            'x': x,
            'y': y,
            'block_id': block_id,
            'chunk_x': chunk_x,
            'chunk_y': chunk_y
        }
        return self.pack_message(MessageType.BLOCK_PLACE, data, player_id)
    
    def create_block_break_message(self, player_id: str, x: int, y: int,
                                 chunk_x: int, chunk_y: int) -> bytes:
        """Create a block break message."""
        data = {
            'x': x,
            'y': y,
            'chunk_x': chunk_x,
            'chunk_y': chunk_y
        }
        return self.pack_message(MessageType.BLOCK_BREAK, data, player_id)
    
    def create_chunk_request_message(self, chunk_x: int, chunk_y: int) -> bytes:
        """Create a chunk data request message."""
        data = {
            'chunk_x': chunk_x,
            'chunk_y': chunk_y
        }
        return self.pack_message(MessageType.CHUNK_REQUEST, data)
    
    def create_chunk_data_message(self, chunk_x: int, chunk_y: int, 
                                chunk_data: Dict[str, Any]) -> bytes:
        """Create a chunk data message."""
        data = {
            'chunk_x': chunk_x,
            'chunk_y': chunk_y,
            'chunk_data': chunk_data
        }
        return self.pack_message(MessageType.CHUNK_DATA, data)
    
    def create_inventory_update_message(self, player_id: str, inventory: List[Dict],
                                      hotbar_selection: int) -> bytes:
        """Create an inventory update message."""
        data = {
            'inventory': inventory,
            'hotbar_selection': hotbar_selection
        }
        return self.pack_message(MessageType.INVENTORY_UPDATE, data, player_id)
    
    def create_item_pickup_message(self, player_id: str, item_id: str, 
                                 item_type: str, quantity: int) -> bytes:
        """Create an item pickup message."""
        data = {
            'item_id': item_id,
            'item_type': item_type,
            'quantity': quantity
        }
        return self.pack_message(MessageType.ITEM_PICKUP, data, player_id)
    
    def create_item_drop_message(self, player_id: str, item_type: str, 
                               quantity: int, x: float, y: float) -> bytes:
        """Create an item drop message."""
        data = {
            'item_type': item_type,
            'quantity': quantity,
            'x': x,
            'y': y
        }
        return self.pack_message(MessageType.ITEM_DROP, data, player_id)
    
    def create_floating_item_spawn_message(self, item_id: str, item_type: str,
                                         quantity: int, x: float, y: float) -> bytes:
        """Create a floating item spawn message."""
        data = {
            'item_id': item_id,
            'item_type': item_type,
            'quantity': quantity,
            'x': x,
            'y': y
        }
        return self.pack_message(MessageType.FLOATING_ITEM_SPAWN, data)
    
    def create_chat_message(self, player_id: str, message: str, 
                          message_type: str = "chat") -> bytes:
        """Create a chat message."""
        data = {
            'message': message,
            'message_type': message_type
        }
        return self.pack_message(MessageType.CHAT_MESSAGE, data, player_id)
    
    def create_server_info_message(self, server_name: str, max_players: int,
                                 current_players: int, world_name: str) -> bytes:
        """Create a server info message."""
        data = {
            'server_name': server_name,
            'max_players': max_players,
            'current_players': current_players,
            'world_name': world_name,
            'protocol_version': self.PROTOCOL_VERSION
        }
        return self.pack_message(MessageType.SERVER_INFO, data)
    
    def create_player_list_message(self, players: List[Dict[str, Any]]) -> bytes:
        """Create a player list message."""
        data = {'players': players}
        return self.pack_message(MessageType.PLAYER_LIST, data)
    
    def create_error_message(self, error_code: str, error_message: str) -> bytes:
        """Create an error message."""
        data = {
            'error_code': error_code,
            'error_message': error_message
        }
        return self.pack_message(MessageType.ERROR, data)
    
    def create_mob_spawn_message(self, mob_id: str, mob_type: str, 
                               x: float, y: float, health: int) -> bytes:
        """Create a mob spawn message."""
        data = {
            'mob_id': mob_id,
            'mob_type': mob_type,
            'x': x,
            'y': y,
            'health': health
        }
        return self.pack_message(MessageType.MOB_SPAWN, data)
    
    def create_mob_update_message(self, mob_id: str, x: float, y: float,
                                health: int, state: str) -> bytes:
        """Create a mob update message."""
        data = {
            'mob_id': mob_id,
            'x': x,
            'y': y,
            'health': health,
            'state': state
        }
        return self.pack_message(MessageType.MOB_UPDATE, data)
    
    def create_world_time_message(self, game_time: float, day_night_cycle: float) -> bytes:
        """Create a world time update message."""
        data = {
            'game_time': game_time,
            'day_night_cycle': day_night_cycle
        }
        return self.pack_message(MessageType.WORLD_TIME, data)
    
    def _get_next_sequence(self) -> int:
        """Get the next sequence number for message ordering."""
        self.sequence_number = (self.sequence_number + 1) % 65536
        return self.sequence_number
    
    def get_message_size(self, message_type: MessageType, data: Dict[str, Any]) -> int:
        """
        Calculate the approximate size of a message without packing it.
        Useful for bandwidth management.
        """
        try:
            # Quick estimate based on JSON serialization
            test_envelope = {
                'type': message_type.value,
                'timestamp': time.time(),
                'sequence': 0,
                'player_id': None,
                'data': data,
                'protocol_version': self.PROTOCOL_VERSION
            }
            json_size = len(json.dumps(test_envelope, separators=(',', ':')))
            return self.HEADER_SIZE + json_size
        except Exception:
            return self.MAX_PACKET_SIZE  # Conservative estimate
    
    def validate_message_data(self, message_type: MessageType, data: Dict[str, Any]) -> bool:
        """
        Validate message data for a given message type.
        Returns True if valid, False otherwise.
        """
        try:
            # Basic validation - can be extended with specific rules per message type
            if not isinstance(data, dict):
                return False
                
            # Message type specific validation
            if message_type == MessageType.CONNECT:
                return 'player_name' in data and isinstance(data['player_name'], str)
            elif message_type == MessageType.PLAYER_MOVE:
                required_fields = ['x', 'y', 'vel_x', 'vel_y', 'direction']
                return all(field in data for field in required_fields)
            elif message_type == MessageType.BLOCK_PLACE:
                required_fields = ['x', 'y', 'block_id', 'chunk_x', 'chunk_y']
                return all(field in data for field in required_fields)
            elif message_type == MessageType.CHAT_MESSAGE:
                return 'message' in data and isinstance(data['message'], str)
                
            # Default: allow any dict
            return True
            
        except Exception:
            return False


# Utility functions for common protocol operations
def generate_player_id() -> str:
    """Generate a unique player ID."""
    return str(uuid.uuid4())


def generate_entity_id() -> str:
    """Generate a unique entity ID."""
    return str(uuid.uuid4())


def calculate_latency(ping_time: float, pong_time: float) -> float:
    """Calculate network latency from ping/pong times."""
    return pong_time - ping_time
