"""
Client Game World for PyCraft 2D Multiplayer

Manages client-side game world state with server synchronization.
"""

import time
from typing import Dict, Any, Optional, List, TYPE_CHECKING

if TYPE_CHECKING:
    from .game_client import GameClient

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


class ClientGameWorld:
    """
    Client-side game world that synchronizes with server state.
    
    Manages local world state, entity tracking, and server communication.
    """
    
    def __init__(self, client: 'GameClient'):
        """
        Initialize client game world.
        
        Args:
            client: Reference to game client
        """
        self.client = client
        
        # World state
        self.world_time = 0.0
        self.loaded_chunks = set()
        self.blocks = {}  # (x, y) -> block_id
        self.entities = {}  # entity_id -> entity_data
        self.players = {}  # player_id -> player_data
        self.floating_items = {}  # item_id -> item_data
        
        # Local player state
        self.local_inventory = {}
        self.local_player_x = 0.0
        self.local_player_y = 0.0
        self.local_player_health = 100
        
        # Pending updates
        self.pending_block_updates = []
        self.pending_entity_updates = []
        
        # Prediction and interpolation
        self.entity_positions = {}  # For smooth movement interpolation
        self.last_update_time = time.time()
        
        log_info("ClientGameWorld initialized")
    
    def update(self, delta_time: float):
        """
        Update client world state.
        
        Args:
            delta_time: Time since last update in seconds
        """
        current_time = time.time()
        self.last_update_time = current_time
        
        # Update entity interpolation
        self._update_entity_interpolation(delta_time)
        
        # Process pending updates
        self._process_pending_updates()
        
        # Request chunks if needed
        self._request_needed_chunks()
    
    def set_block(self, x: int, y: int, block_id: int):
        """
        Set a block in the world.
        
        Args:
            x: Block X coordinate
            y: Block Y coordinate
            block_id: Block type ID
        """
        if block_id == 0:
            # Remove block
            self.blocks.pop((x, y), None)
        else:
            # Set block
            self.blocks[(x, y)] = block_id
        
        log_debug(f"Block set at ({x}, {y}): {block_id}")
    
    def get_block(self, x: int, y: int) -> int:
        """
        Get block at position.
        
        Args:
            x: Block X coordinate
            y: Block Y coordinate
            
        Returns:
            Block ID (0 if empty)
        """
        return self.blocks.get((x, y), 0)
    
    def load_chunk_data(self, chunk_x: int, chunk_y: int, blocks: Dict[str, int], entities: List[Dict]):
        """
        Load chunk data from server.
        
        Args:
            chunk_x: Chunk X coordinate
            chunk_y: Chunk Y coordinate
            blocks: Block data for chunk
            entities: Entity data for chunk
        """
        # Mark chunk as loaded
        self.loaded_chunks.add((chunk_x, chunk_y))
        
        # Load block data
        for pos_str, block_id in blocks.items():
            try:
                x, y = map(int, pos_str.split(','))
                self.set_block(x, y, block_id)
            except ValueError:
                log_warning(f"Invalid block position format: {pos_str}")
        
        # Load entities
        for entity_data in entities:
            entity_id = entity_data.get('entity_id')
            if entity_id:
                self.entities[entity_id] = entity_data
        
        log_debug(f"Loaded chunk ({chunk_x}, {chunk_y}) with {len(blocks)} blocks and {len(entities)} entities")
    
    def spawn_entity(self, entity_id: str, entity_data: Dict[str, Any]):
        """
        Spawn an entity in the world.
        
        Args:
            entity_id: Unique entity ID
            entity_data: Entity data
        """
        self.entities[entity_id] = entity_data
        
        # Initialize position tracking for interpolation
        x = entity_data.get('x', 0)
        y = entity_data.get('y', 0)
        self.entity_positions[entity_id] = {
            'current_x': x,
            'current_y': y,
            'target_x': x,
            'target_y': y,
            'last_update': time.time()
        }
        
        log_debug(f"Entity spawned: {entity_id}")
    
    def despawn_entity(self, entity_id: str):
        """
        Remove an entity from the world.
        
        Args:
            entity_id: Entity ID to remove
        """
        self.entities.pop(entity_id, None)
        self.entity_positions.pop(entity_id, None)
        log_debug(f"Entity despawned: {entity_id}")
    
    def update_entity(self, entity_id: str, entity_data: Dict[str, Any]):
        """
        Update entity data.
        
        Args:
            entity_id: Entity ID
            entity_data: New entity data
        """
        if entity_id in self.entities:
            # Update entity data
            self.entities[entity_id].update(entity_data)
            
            # Update position tracking for smooth movement
            x = entity_data.get('x')
            y = entity_data.get('y')
            
            if x is not None and y is not None:
                if entity_id in self.entity_positions:
                    pos_data = self.entity_positions[entity_id]
                    pos_data['target_x'] = x
                    pos_data['target_y'] = y
                    pos_data['last_update'] = time.time()
                else:
                    self.entity_positions[entity_id] = {
                        'current_x': x,
                        'current_y': y,
                        'target_x': x,
                        'target_y': y,
                        'last_update': time.time()
                    }
    
    def add_player(self, player_id: str, player_data: Dict[str, Any]):
        """
        Add a player to the world.
        
        Args:
            player_id: Player ID
            player_data: Player data
        """
        self.players[player_id] = player_data
        
        # Also treat as entity for rendering
        self.spawn_entity(f"player_{player_id}", player_data)
        
        log_debug(f"Player added: {player_id}")
    
    def remove_player(self, player_id: str):
        """
        Remove a player from the world.
        
        Args:
            player_id: Player ID to remove
        """
        self.players.pop(player_id, None)
        self.despawn_entity(f"player_{player_id}")
        log_debug(f"Player removed: {player_id}")
    
    def update_player(self, player_id: str, player_data: Dict[str, Any]):
        """
        Update player data.
        
        Args:
            player_id: Player ID
            player_data: Updated player data
        """
        if player_id in self.players:
            self.players[player_id].update(player_data)
            self.update_entity(f"player_{player_id}", player_data)
        else:
            # Player not known, add them
            self.add_player(player_id, player_data)
    
    def spawn_floating_item(self, item_id: str, item_type: str, quantity: int, x: float, y: float):
        """
        Spawn a floating item.
        
        Args:
            item_id: Unique item ID
            item_type: Type of item
            quantity: Item quantity
            x: X position
            y: Y position
        """
        self.floating_items[item_id] = {
            'item_id': item_id,
            'item_type': item_type,
            'quantity': quantity,
            'x': x,
            'y': y,
            'spawn_time': time.time()
        }
        
        log_debug(f"Floating item spawned: {item_type} x{quantity} at ({x}, {y})")
    
    def remove_floating_item(self, item_id: str):
        """
        Remove a floating item.
        
        Args:
            item_id: Item ID to remove
        """
        self.floating_items.pop(item_id, None)
        log_debug(f"Floating item removed: {item_id}")
    
    def update_local_inventory(self, inventory: Dict[str, int]):
        """
        Update local player inventory.
        
        Args:
            inventory: New inventory state
        """
        self.local_inventory = inventory.copy()
        log_debug("Local inventory updated")
    
    def set_world_time(self, world_time: float):
        """
        Set world time.
        
        Args:
            world_time: New world time
        """
        self.world_time = world_time
    
    def request_chunk(self, chunk_x: int, chunk_y: int):
        """
        Request chunk data from server.
        
        Args:
            chunk_x: Chunk X coordinate
            chunk_y: Chunk Y coordinate
        """
        if (chunk_x, chunk_y) not in self.loaded_chunks:
            chunk_data = {
                'chunk_x': chunk_x,
                'chunk_y': chunk_y
            }
            
            from ..message_types import MessageType
            self.client.send_message(MessageType.CHUNK_REQUEST, chunk_data)
            log_debug(f"Requested chunk ({chunk_x}, {chunk_y})")
    
    def get_entity_position(self, entity_id: str) -> tuple[float, float]:
        """
        Get interpolated entity position.
        
        Args:
            entity_id: Entity ID
            
        Returns:
            Tuple of (x, y) position
        """
        if entity_id in self.entity_positions:
            pos_data = self.entity_positions[entity_id]
            return pos_data['current_x'], pos_data['current_y']
        
        # Fallback to raw entity data
        if entity_id in self.entities:
            entity_data = self.entities[entity_id]
            return entity_data.get('x', 0), entity_data.get('y', 0)
        
        return 0.0, 0.0
    
    def process_network_updates(self):
        """Process any pending network updates."""
        # This would handle prediction/rollback for local player
        # For now, just a placeholder
        pass
    
    def _update_entity_interpolation(self, delta_time: float):
        """
        Update entity position interpolation for smooth movement.
        
        Args:
            delta_time: Time since last update
        """
        interpolation_speed = 10.0  # Units per second
        
        for entity_id, pos_data in self.entity_positions.items():
            current_x = pos_data['current_x']
            current_y = pos_data['current_y']
            target_x = pos_data['target_x']
            target_y = pos_data['target_y']
            
            # Calculate distance to target
            dx = target_x - current_x
            dy = target_y - current_y
            distance = (dx * dx + dy * dy) ** 0.5
            
            if distance > 0.1:  # Only interpolate if distance is significant
                # Interpolate towards target
                move_distance = interpolation_speed * delta_time
                
                if move_distance >= distance:
                    # Snap to target
                    pos_data['current_x'] = target_x
                    pos_data['current_y'] = target_y
                else:
                    # Move towards target
                    ratio = move_distance / distance
                    pos_data['current_x'] += dx * ratio
                    pos_data['current_y'] += dy * ratio
    
    def _process_pending_updates(self):
        """Process any pending world updates."""
        # Process pending block updates
        for update in self.pending_block_updates:
            x, y, block_id = update
            self.set_block(x, y, block_id)
        
        self.pending_block_updates.clear()
        
        # Process pending entity updates
        for update in self.pending_entity_updates:
            entity_id, entity_data = update
            self.update_entity(entity_id, entity_data)
        
        self.pending_entity_updates.clear()
    
    def _request_needed_chunks(self):
        """Request chunks that need to be loaded based on player position."""
        # Calculate which chunks we need based on local player position
        # For now, just request chunks around player
        
        # Get player chunk position
        chunk_x = int(self.local_player_x // 16)  # Assuming 16x16 chunks
        chunk_y = int(self.local_player_y // 16)
        
        # Load chunks in a radius around player
        load_radius = 2
        for dx in range(-load_radius, load_radius + 1):
            for dy in range(-load_radius, load_radius + 1):
                target_chunk_x = chunk_x + dx
                target_chunk_y = chunk_y + dy
                
                if (target_chunk_x, target_chunk_y) not in self.loaded_chunks:
                    self.request_chunk(target_chunk_x, target_chunk_y)
    
    def get_world_stats(self) -> Dict[str, Any]:
        """
        Get world statistics.
        
        Returns:
            Dictionary of world statistics
        """
        return {
            'loaded_chunks': len(self.loaded_chunks),
            'total_blocks': len(self.blocks),
            'total_entities': len(self.entities),
            'total_players': len(self.players),
            'floating_items': len(self.floating_items),
            'world_time': self.world_time,
            'local_player_pos': (self.local_player_x, self.local_player_y),
            'inventory_items': len(self.local_inventory)
        }
