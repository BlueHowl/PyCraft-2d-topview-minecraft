"""
Server Proxy for PyCraft 2D Multiplayer

Provides a high-level interface for client-server communication.
Abstracts network details and provides convenient methods for game actions.
"""

import time
from typing import Dict, Any, Optional

from ..message_types import MessageType


class ServerProxy:
    """
    High-level interface for client-server communication.
    
    Provides convenient methods for common game actions and abstracts
    the underlying network protocol.
    """
    
    def __init__(self, client):
        """
        Initialize server proxy.
        
        Args:
            client: Reference to game client
        """
        self.client = client
    
    # Movement actions
    def move_player(self, direction: str, velocity_x: float, velocity_y: float) -> bool:
        """
        Send player movement to server.
        
        Args:
            direction: Movement direction ('left', 'right', 'up', 'down')
            velocity_x: X velocity
            velocity_y: Y velocity
            
        Returns:
            True if message sent successfully
        """
        data = {
            'direction': direction,
            'velocity_x': velocity_x,
            'velocity_y': velocity_y,
            'timestamp': time.time()
        }
        
        return self.client.send_message(MessageType.PLAYER_MOVE, data)
    
    def stop_player(self) -> bool:
        """
        Send player stop to server.
        
        Returns:
            True if message sent successfully
        """
        data = {
            'timestamp': time.time()
        }
        
        return self.client.send_message(MessageType.PLAYER_STOP, data)
    
    # World interaction
    def place_block(self, x: int, y: int, block_id: int) -> bool:
        """
        Place a block in the world.
        
        Args:
            x: Block X coordinate
            y: Block Y coordinate
            block_id: Block type ID
            
        Returns:
            True if message sent successfully
        """
        data = {
            'x': x,
            'y': y,
            'block_id': block_id,
            'timestamp': time.time()
        }
        
        return self.client.send_message(MessageType.BLOCK_PLACE, data)
    
    def break_block(self, x: int, y: int) -> bool:
        """
        Break a block in the world.
        
        Args:
            x: Block X coordinate
            y: Block Y coordinate
            
        Returns:
            True if message sent successfully
        """
        data = {
            'x': x,
            'y': y,
            'timestamp': time.time()
        }
        
        return self.client.send_message(MessageType.BLOCK_BREAK, data)
    
    # Combat actions
    def attack(self, target_x: float, target_y: float, attack_type: str = 'melee') -> bool:
        """
        Send attack action to server.
        
        Args:
            target_x: Target X coordinate
            target_y: Target Y coordinate
            attack_type: Type of attack ('melee', 'ranged')
            
        Returns:
            True if message sent successfully
        """
        data = {
            'target_x': target_x,
            'target_y': target_y,
            'attack_type': attack_type,
            'timestamp': time.time()
        }
        
        return self.client.send_message(MessageType.PLAYER_ATTACK, data)
    
    def interact(self, target_x: int, target_y: int, interaction_type: str = 'use') -> bool:
        """
        Send interaction action to server.
        
        Args:
            target_x: Target X coordinate
            target_y: Target Y coordinate
            interaction_type: Type of interaction ('use', 'open', 'activate')
            
        Returns:
            True if message sent successfully
        """
        data = {
            'target_x': target_x,
            'target_y': target_y,
            'interaction_type': interaction_type,
            'timestamp': time.time()
        }
        
        return self.client.send_message(MessageType.PLAYER_INTERACT, data)
    
    # Inventory actions
    def pickup_item(self, item_id: str) -> bool:
        """
        Pick up a floating item.
        
        Args:
            item_id: ID of item to pick up
            
        Returns:
            True if message sent successfully
        """
        data = {
            'item_id': item_id,
            'timestamp': time.time()
        }
        
        return self.client.send_message(MessageType.ITEM_PICKUP, data)
    
    def drop_item(self, item_type: str, quantity: int, x: Optional[float] = None, y: Optional[float] = None) -> bool:
        """
        Drop an item from inventory.
        
        Args:
            item_type: Type of item to drop
            quantity: Quantity to drop
            x: Drop X position (optional, uses player position if None)
            y: Drop Y position (optional, uses player position if None)
            
        Returns:
            True if message sent successfully
        """
        data = {
            'item_type': item_type,
            'quantity': quantity,
            'timestamp': time.time()
        }
        
        if x is not None:
            data['x'] = x
        if y is not None:
            data['y'] = y
        
        return self.client.send_message(MessageType.ITEM_DROP, data)
    
    def use_item(self, item_type: str, target_x: Optional[int] = None, target_y: Optional[int] = None) -> bool:
        """
        Use an item from inventory.
        
        Args:
            item_type: Type of item to use
            target_x: Target X coordinate (optional)
            target_y: Target Y coordinate (optional)
            
        Returns:
            True if message sent successfully
        """
        data = {
            'item_type': item_type,
            'timestamp': time.time()
        }
        
        if target_x is not None:
            data['target_x'] = target_x
        if target_y is not None:
            data['target_y'] = target_y
        
        return self.client.send_message(MessageType.ITEM_USE, data)
    
    def change_hotbar_slot(self, slot: int) -> bool:
        """
        Change active hotbar slot.
        
        Args:
            slot: Hotbar slot index (0-9)
            
        Returns:
            True if message sent successfully
        """
        data = {
            'slot': slot,
            'timestamp': time.time()
        }
        
        return self.client.send_message(MessageType.HOTBAR_CHANGE, data)
    
    # Crafting
    def craft_item(self, recipe_id: str, quantity: int = 1) -> bool:
        """
        Craft an item.
        
        Args:
            recipe_id: ID of recipe to craft
            quantity: Quantity to craft
            
        Returns:
            True if message sent successfully
        """
        data = {
            'recipe_id': recipe_id,
            'quantity': quantity,
            'timestamp': time.time()
        }
        
        return self.client.send_message(MessageType.CRAFT_ITEM, data)
    
    # Communication
    def send_chat(self, message: str) -> bool:
        """
        Send a chat message.
        
        Args:
            message: Chat message to send
            
        Returns:
            True if message sent successfully
        """
        data = {
            'message': message,
            'timestamp': time.time()
        }
        
        return self.client.send_message(MessageType.CHAT_MESSAGE, data)
    
    # World management
    def request_chunk(self, chunk_x: int, chunk_y: int) -> bool:
        """
        Request chunk data from server.
        
        Args:
            chunk_x: Chunk X coordinate
            chunk_y: Chunk Y coordinate
            
        Returns:
            True if message sent successfully
        """
        data = {
            'chunk_x': chunk_x,
            'chunk_y': chunk_y
        }
        
        return self.client.send_message(MessageType.CHUNK_REQUEST, data)
    
    # Utility methods
    def ping_server(self) -> bool:
        """
        Send ping to server.
        
        Returns:
            True if ping sent successfully
        """
        data = {
            'timestamp': time.time()
        }
        
        return self.client.send_message(MessageType.PING, data)
    
    def respawn_player(self) -> bool:
        """
        Request player respawn.
        
        Returns:
            True if message sent successfully
        """
        data = {
            'timestamp': time.time()
        }
        
        return self.client.send_message(MessageType.PLAYER_RESPAWN, data)
    
    # Batch operations
    def send_player_state_update(self, position: tuple, health: int, inventory: Dict[str, int]) -> bool:
        """
        Send comprehensive player state update.
        
        Args:
            position: Tuple of (x, y) position
            health: Player health
            inventory: Player inventory
            
        Returns:
            True if message sent successfully
        """
        x, y = position
        data = {
            'x': x,
            'y': y,
            'health': health,
            'inventory': inventory,
            'timestamp': time.time()
        }
        
        return self.client.send_message(MessageType.PLAYER_UPDATE, data)
    
    # Connection helpers
    def is_connected(self) -> bool:
        """
        Check if client is connected to server.
        
        Returns:
            True if connected
        """
        return self.client.connected
    
    def get_connection_stats(self) -> Dict[str, Any]:
        """
        Get connection statistics.
        
        Returns:
            Dictionary of connection statistics
        """
        return self.client.get_client_stats()
    
    def get_player_id(self) -> Optional[str]:
        """
        Get local player ID.
        
        Returns:
            Player ID or None if not connected
        """
        return self.client.player_id
    
    def get_server_info(self) -> Dict[str, Any]:
        """
        Get server information.
        
        Returns:
            Dictionary of server information
        """
        return self.client.server_info.copy()
    
    def get_world_state(self) -> Optional[Dict[str, Any]]:
        """
        Get current world state.
        
        Returns:
            World state dictionary or None if world not loaded
        """
        if self.client.world:
            return self.client.world.get_world_stats()
        return None
