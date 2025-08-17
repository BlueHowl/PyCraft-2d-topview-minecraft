"""
Pure Game World Logic - Server-side game state management.

This module contains the core game logic separated from rendering,
enabling server-side game state management for multiplayer.
"""

import time
import math
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field

from game.config.settings import *
from game.config.game_config import GameConfig
from game.utils.logger import log_info, log_error, log_warning, log_debug


@dataclass
class PlayerState:
    """Represents the state of a player in the game world."""
    player_id: str
    name: str
    x: float
    y: float
    vel_x: float = 0.0
    vel_y: float = 0.0
    health: int = 20
    max_health: int = 20
    direction: str = "down"
    inventory: List[Dict[str, Any]] = field(default_factory=list)
    hotbar_selection: int = 0
    last_update: float = field(default_factory=time.time)
    is_connected: bool = True
    chunk_x: int = 0
    chunk_y: int = 0
    
    def __post_init__(self):
        """Initialize default inventory if empty."""
        if not self.inventory:
            self.inventory = [None] * 36  # Standard inventory size
    
    def get_position(self) -> Tuple[float, float]:
        """Get player position as tuple."""
        return (self.x, self.y)
    
    def set_position(self, x: float, y: float):
        """Set player position and update chunk."""
        self.x = x
        self.y = y
        self.chunk_x = int(x // (CHUNKSIZE * TILESIZE))
        self.chunk_y = int(y // (CHUNKSIZE * TILESIZE))
        self.last_update = time.time()
    
    def move(self, vel_x: float, vel_y: float, dt: float):
        """Update player position based on velocity."""
        self.vel_x = vel_x
        self.vel_y = vel_y
        self.x += vel_x * dt
        self.y += vel_y * dt
        
        # Update chunk position
        new_chunk_x = int(self.x // (CHUNKSIZE * TILESIZE))
        new_chunk_y = int(self.y // (CHUNKSIZE * TILESIZE))
        
        if new_chunk_x != self.chunk_x or new_chunk_y != self.chunk_y:
            self.chunk_x = new_chunk_x
            self.chunk_y = new_chunk_y
        
        self.last_update = time.time()
    
    def take_damage(self, damage: int) -> bool:
        """Apply damage to player. Returns True if player died."""
        self.health = max(0, self.health - damage)
        self.last_update = time.time()
        return self.health <= 0
    
    def heal(self, amount: int):
        """Heal the player."""
        self.health = min(self.max_health, self.health + amount)
        self.last_update = time.time()
    
    def add_item(self, item_type: str, quantity: int) -> bool:
        """Add item to inventory. Returns True if successful."""
        # Try to stack with existing items first
        for i, slot in enumerate(self.inventory):
            if slot and slot.get('item_type') == item_type:
                current_qty = slot.get('quantity', 0)
                if current_qty < STACK:
                    can_add = min(quantity, STACK - current_qty)
                    slot['quantity'] = current_qty + can_add
                    quantity -= can_add
                    if quantity <= 0:
                        self.last_update = time.time()
                        return True
        
        # Find empty slots
        for i, slot in enumerate(self.inventory):
            if slot is None and quantity > 0:
                add_qty = min(quantity, STACK)
                self.inventory[i] = {
                    'item_type': item_type,
                    'quantity': add_qty
                }
                quantity -= add_qty
                if quantity <= 0:
                    self.last_update = time.time()
                    return True
        
        self.last_update = time.time()
        return quantity <= 0
    
    def remove_item(self, item_type: str, quantity: int) -> int:
        """Remove items from inventory. Returns actual amount removed."""
        removed = 0
        for i, slot in enumerate(self.inventory):
            if slot and slot.get('item_type') == item_type:
                current_qty = slot.get('quantity', 0)
                can_remove = min(quantity - removed, current_qty)
                slot['quantity'] -= can_remove
                removed += can_remove
                
                if slot['quantity'] <= 0:
                    self.inventory[i] = None
                
                if removed >= quantity:
                    break
        
        if removed > 0:
            self.last_update = time.time()
        return removed


@dataclass
class EntityState:
    """Base class for entity state in the game world."""
    entity_id: str
    entity_type: str
    x: float
    y: float
    health: int
    max_health: int
    last_update: float = field(default_factory=time.time)
    
    def get_position(self) -> Tuple[float, float]:
        """Get entity position as tuple."""
        return (self.x, self.y)
    
    def set_position(self, x: float, y: float):
        """Set entity position."""
        self.x = x
        self.y = y
        self.last_update = time.time()
    
    def take_damage(self, damage: int) -> bool:
        """Apply damage to entity. Returns True if entity died."""
        self.health = max(0, self.health - damage)
        self.last_update = time.time()
        return self.health <= 0


@dataclass
class FloatingItemState:
    """Represents a floating item in the game world."""
    item_id: str
    item_type: str
    quantity: int
    x: float
    y: float
    spawn_time: float = field(default_factory=time.time)
    
    def get_position(self) -> Tuple[float, float]:
        """Get item position as tuple."""
        return (self.x, self.y)
    
    def is_expired(self, max_lifetime: float = 300.0) -> bool:
        """Check if item has expired."""
        return time.time() - self.spawn_time > max_lifetime


class ChunkState:
    """Represents the state of a world chunk."""
    
    def __init__(self, chunk_x: int, chunk_y: int):
        self.chunk_x = chunk_x
        self.chunk_y = chunk_y
        self.blocks: Dict[Tuple[int, int], int] = {}
        self.last_modified = time.time()
        self.loaded = False
    
    def set_block(self, x: int, y: int, block_id: int):
        """Set a block in this chunk."""
        local_x = x % CHUNKSIZE
        local_y = y % CHUNKSIZE
        self.blocks[(local_x, local_y)] = block_id
        self.last_modified = time.time()
    
    def get_block(self, x: int, y: int) -> int:
        """Get a block from this chunk."""
        local_x = x % CHUNKSIZE
        local_y = y % CHUNKSIZE
        return self.blocks.get((local_x, local_y), 0)
    
    def get_chunk_key(self) -> Tuple[int, int]:
        """Get the chunk coordinates as a key."""
        return (self.chunk_x, self.chunk_y)


class GameWorld:
    """
    Pure game logic without rendering dependencies.
    
    This class manages the core game state including players, entities,
    world chunks, and game mechanics without any pygame/rendering code.
    """
    
    def __init__(self, world_name: str = "default", seed: Optional[int] = None):
        """Initialize the game world."""
        log_info(f"Initializing GameWorld: {world_name}")
        
        self.world_name = world_name
        self.seed = seed or int(time.time())
        
        # Game state
        self.running = True
        self.paused = False
        self.game_time = 0.0
        self.day_time = 0.0
        self.tick_count = 0
        
        # Players and entities
        self.players: Dict[str, PlayerState] = {}
        self.entities: Dict[str, EntityState] = {}
        self.floating_items: Dict[str, FloatingItemState] = {}
        
        # World data
        self.chunks: Dict[Tuple[int, int], ChunkState] = {}
        self.loaded_chunks: set = set()
        
        # Game settings
        self.max_players = 10
        self.view_distance = 8  # chunks
        self.tick_rate = 20  # ticks per second
        self.auto_save_interval = 300.0  # seconds
        self.last_auto_save = time.time()
        
        # World generation settings
        self.world_size = 1000  # chunks in each direction
        
        log_info(f"GameWorld initialized with seed: {self.seed}")
    
    def update(self, dt: float):
        """Update the game world logic."""
        if self.paused:
            return
        
        self.game_time += dt
        self.tick_count += 1
        
        # Update day/night cycle
        self._update_day_night_cycle(dt)
        
        # Update players
        self._update_players(dt)
        
        # Update entities
        self._update_entities(dt)
        
        # Update floating items
        self._update_floating_items(dt)
        
        # Cleanup expired items
        self._cleanup_expired_items()
        
        # Auto-save if needed
        if time.time() - self.last_auto_save > self.auto_save_interval:
            self._auto_save()
    
    def add_player(self, player_id: str, player_name: str, x: float = 0, y: float = 0) -> bool:
        """Add a new player to the world."""
        if player_id in self.players:
            log_warning(f"Player {player_id} already exists")
            return False
        
        if len(self.players) >= self.max_players:
            log_warning(f"World full, cannot add player {player_name}")
            return False
        
        player = PlayerState(
            player_id=player_id,
            name=player_name,
            x=x,
            y=y
        )
        
        self.players[player_id] = player
        log_info(f"Added player {player_name} ({player_id}) at ({x}, {y})")
        return True
    
    def remove_player(self, player_id: str) -> bool:
        """Remove a player from the world."""
        if player_id in self.players:
            player = self.players[player_id]
            del self.players[player_id]
            log_info(f"Removed player {player.name} ({player_id})")
            return True
        return False
    
    def get_player(self, player_id: str) -> Optional[PlayerState]:
        """Get a player by ID."""
        return self.players.get(player_id)
    
    def move_player(self, player_id: str, x: float, y: float, vel_x: float, vel_y: float, dt: float) -> bool:
        """Move a player and update their state."""
        player = self.players.get(player_id)
        if not player:
            return False
        
        # Simple collision detection can be added here
        player.move(vel_x, vel_y, dt)
        
        # Ensure chunk is loaded
        chunk_key = (player.chunk_x, player.chunk_y)
        if chunk_key not in self.chunks:
            self._load_chunk(player.chunk_x, player.chunk_y)
        
        return True
    
    def set_block(self, x: int, y: int, block_id: int, player_id: Optional[str] = None) -> bool:
        """Set a block in the world."""
        chunk_x = x // CHUNKSIZE
        chunk_y = y // CHUNKSIZE
        chunk_key = (chunk_x, chunk_y)
        
        # Ensure chunk is loaded
        if chunk_key not in self.chunks:
            self._load_chunk(chunk_x, chunk_y)
        
        chunk = self.chunks[chunk_key]
        old_block = chunk.get_block(x, y)
        chunk.set_block(x, y, block_id)
        
        log_debug(f"Block changed at ({x}, {y}): {old_block} -> {block_id}")
        return True
    
    def get_block(self, x: int, y: int) -> int:
        """Get a block from the world."""
        chunk_x = x // CHUNKSIZE
        chunk_y = y // CHUNKSIZE
        chunk_key = (chunk_x, chunk_y)
        
        if chunk_key not in self.chunks:
            # Return air/empty block for unloaded chunks
            return 0
        
        return self.chunks[chunk_key].get_block(x, y)
    
    def spawn_floating_item(self, item_type: str, quantity: int, x: float, y: float) -> str:
        """Spawn a floating item in the world."""
        from game.network.protocol import generate_entity_id
        
        item_id = generate_entity_id()
        floating_item = FloatingItemState(
            item_id=item_id,
            item_type=item_type,
            quantity=quantity,
            x=x,
            y=y
        )
        
        self.floating_items[item_id] = floating_item
        log_debug(f"Spawned floating item {item_type} x{quantity} at ({x}, {y})")
        return item_id
    
    def pickup_floating_item(self, item_id: str, player_id: str) -> bool:
        """Pick up a floating item."""
        if item_id not in self.floating_items:
            return False
        
        player = self.players.get(player_id)
        if not player:
            return False
        
        item = self.floating_items[item_id]
        
        # Try to add to player inventory
        if player.add_item(item.item_type, item.quantity):
            del self.floating_items[item_id]
            log_debug(f"Player {player.name} picked up {item.item_type} x{item.quantity}")
            return True
        
        return False
    
    def get_players_in_chunk(self, chunk_x: int, chunk_y: int) -> List[str]:
        """Get all players in a specific chunk."""
        players_in_chunk = []
        for player_id, player in self.players.items():
            if player.chunk_x == chunk_x and player.chunk_y == chunk_y:
                players_in_chunk.append(player_id)
        return players_in_chunk
    
    def get_nearby_players(self, x: float, y: float, radius: float) -> List[str]:
        """Get all players within a radius of a position."""
        nearby_players = []
        for player_id, player in self.players.items():
            dx = player.x - x
            dy = player.y - y
            distance = math.sqrt(dx * dx + dy * dy)
            if distance <= radius:
                nearby_players.append(player_id)
        return nearby_players
    
    def get_chunk_data(self, chunk_x: int, chunk_y: int) -> Optional[Dict[str, Any]]:
        """Get chunk data for transmission."""
        chunk_key = (chunk_x, chunk_y)
        if chunk_key not in self.chunks:
            return None
        
        chunk = self.chunks[chunk_key]
        return {
            'chunk_x': chunk_x,
            'chunk_y': chunk_y,
            'blocks': dict(chunk.blocks),
            'last_modified': chunk.last_modified
        }
    
    def load_chunk_data(self, chunk_data: Dict[str, Any]) -> bool:
        """Load chunk data from external source."""
        try:
            chunk_x = chunk_data['chunk_x']
            chunk_y = chunk_data['chunk_y']
            
            chunk = ChunkState(chunk_x, chunk_y)
            
            # Load blocks
            blocks_data = chunk_data.get('blocks', {})
            for pos_str, block_id in blocks_data.items():
                if isinstance(pos_str, str):
                    # Parse string keys like "(x, y)"
                    pos = eval(pos_str)
                else:
                    pos = pos_str
                chunk.blocks[pos] = block_id
            
            chunk.last_modified = chunk_data.get('last_modified', time.time())
            chunk.loaded = True
            
            self.chunks[(chunk_x, chunk_y)] = chunk
            self.loaded_chunks.add((chunk_x, chunk_y))
            
            log_debug(f"Loaded chunk ({chunk_x}, {chunk_y}) with {len(chunk.blocks)} blocks")
            return True
            
        except Exception as e:
            log_error(f"Failed to load chunk data: {e}")
            return False
    
    def _update_day_night_cycle(self, dt: float):
        """Update the day/night cycle."""
        # Day length in real seconds (e.g., 20 minutes = 1200 seconds)
        day_length = 1200.0
        self.day_time = (self.game_time % day_length) / day_length
    
    def _update_players(self, dt: float):
        """Update all players."""
        for player in self.players.values():
            # Player-specific updates (regeneration, etc.)
            if player.health < player.max_health:
                # Slow health regeneration
                if self.game_time % 5.0 < dt:  # Every 5 seconds
                    player.heal(1)
    
    def _update_entities(self, dt: float):
        """Update all entities."""
        # Entity AI and physics updates would go here
        pass
    
    def _update_floating_items(self, dt: float):
        """Update floating items."""
        # Items could have physics, magnets to players, etc.
        pass
    
    def _cleanup_expired_items(self):
        """Remove expired floating items."""
        expired_items = []
        for item_id, item in self.floating_items.items():
            if item.is_expired():
                expired_items.append(item_id)
        
        for item_id in expired_items:
            del self.floating_items[item_id]
            log_debug(f"Removed expired floating item {item_id}")
    
    def _load_chunk(self, chunk_x: int, chunk_y: int):
        """Load a chunk (basic implementation)."""
        chunk_key = (chunk_x, chunk_y)
        if chunk_key in self.chunks:
            return
        
        chunk = ChunkState(chunk_x, chunk_y)
        
        # Basic chunk generation (would be replaced with proper world generation)
        # For now, just create an empty chunk
        chunk.loaded = True
        
        self.chunks[chunk_key] = chunk
        self.loaded_chunks.add(chunk_key)
        
        log_debug(f"Generated new chunk ({chunk_x}, {chunk_y})")
    
    def _auto_save(self):
        """Perform auto-save."""
        log_info("Performing auto-save...")
        # Save logic would go here
        self.last_auto_save = time.time()
    
    def get_world_state(self) -> Dict[str, Any]:
        """Get a complete snapshot of the world state."""
        return {
            'world_name': self.world_name,
            'game_time': self.game_time,
            'day_time': self.day_time,
            'tick_count': self.tick_count,
            'player_count': len(self.players),
            'entity_count': len(self.entities),
            'floating_item_count': len(self.floating_items),
            'loaded_chunk_count': len(self.loaded_chunks)
        }
    
    def get_player_list(self) -> List[Dict[str, Any]]:
        """Get a list of all players with basic info."""
        return [
            {
                'player_id': player.player_id,
                'name': player.name,
                'x': player.x,
                'y': player.y,
                'health': player.health,
                'is_connected': player.is_connected
            }
            for player in self.players.values()
        ]
