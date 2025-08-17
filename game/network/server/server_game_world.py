"""
Server Game World for PyCraft 2D

Server-side game world implementation that extends the base GameWorld
with networking capabilities, persistence, and multiplayer features.
"""

import time
import json
import os
from typing import Dict, List, Any, Optional, Set, Tuple

from ...core.game_world import GameWorld
from ...utils.logger import log_info, log_error, log_debug, log_warning
from ...config.settings import CHUNKSIZE


class ServerGameWorld(GameWorld):
    """
    Server-side game world with networking and persistence features.
    
    Extends the base GameWorld with:
    - Chunk-based loading/unloading
    - Change tracking for network synchronization
    - Persistent storage
    - Multiplayer collision detection
    """
    
    def __init__(self, world_name: str = "default"):
        """Initialize the server game world."""
        super().__init__()
        
        self.world_name = world_name
        self.save_directory = f"saves/{world_name}"
        
        # Chunk management
        self.loaded_chunks: Set[Tuple[int, int]] = set()
        self.chunk_subscribers: Dict[Tuple[int, int], Set[str]] = {}  # chunk -> player_ids
        
        # Track which chunks each client has received
        self.client_chunks: Dict[str, Set[Tuple[int, int]]] = {}  # client_id -> chunks_sent
        
        # Change tracking for network sync
        self.changed_blocks: Dict[Tuple[int, int], Dict[str, Any]] = {}  # position -> change_data
        self.changed_chunks: Set[Tuple[int, int]] = set()
        self.newly_generated_chunks: Set[Tuple[int, int]] = set()  # Track new chunks for incremental updates
        
        # Floating items (server manages these)
        self.floating_items: Dict[str, 'ServerFloatingItem'] = {}
        self.item_id_counter = 0
        
        # World settings
        self.auto_save_interval = 60  # seconds
        self.last_save_time = time.time()
        self.chunk_unload_delay = 300  # seconds before unloading empty chunks
        
        # Statistics
        self.total_blocks_placed = 0
        self.total_blocks_broken = 0
        self.total_items_spawned = 0
        
        # Ensure save directory exists
        os.makedirs(self.save_directory, exist_ok=True)
        
        # Load existing world data if available
        self._load_world_data()
        
        log_info(f"ServerGameWorld initialized: {world_name}")
    
    def update(self, delta_time: float):
        """Update the server game world."""
        super().update(delta_time)
        
        # Update floating items
        self._update_floating_items(delta_time)
        
        # Check for auto-save
        current_time = time.time()
        if current_time - self.last_save_time > self.auto_save_interval:
            self.auto_save()
            self.last_save_time = current_time
        
        # Unload empty chunks
        self._check_chunk_unloading()
    
    def set_block(self, x: int, y: int, block_id: int, player_id: str = None) -> bool:
        """
        Set a block in the world with change tracking.
        
        Args:
            x: Block X coordinate
            y: Block Y coordinate  
            block_id: Block type ID
            player_id: ID of player making the change
            
        Returns:
            True if block was set successfully
        """
        # Get previous block
        old_block_id = self.get_block(x, y)
        
        # Set the block
        success = super().set_block(x, y, block_id)
        
        if success and old_block_id != block_id:
            # Track the change
            self.changed_blocks[(x, y)] = {
                'old_block_id': old_block_id,
                'new_block_id': block_id,
                'player_id': player_id,
                'timestamp': time.time()
            }
            
            # Mark chunk as changed (use proper floor division for negative coordinates)
            import math
            chunk_x, chunk_y = int(math.floor(x / CHUNKSIZE)), int(math.floor(y / CHUNKSIZE))
            self.changed_chunks.add((chunk_x, chunk_y))
            
            # Update statistics
            if block_id == 0:
                self.total_blocks_broken += 1
            else:
                self.total_blocks_placed += 1
            
            log_debug(f"Block changed at ({x}, {y}): {old_block_id} -> {block_id} by {player_id}")
        
        return success
    
    def spawn_floating_item(self, item_type: str, quantity: int, x: float, y: float, 
                           player_id: str = None) -> str:
        """
        Spawn a floating item in the world.
        
        Args:
            item_type: Type of item to spawn
            quantity: Number of items
            x: X position
            y: Y position
            player_id: ID of player who caused the spawn
            
        Returns:
            Unique item ID
        """
        item_id = f"item_{self.item_id_counter}"
        self.item_id_counter += 1
        
        floating_item = ServerFloatingItem(
            item_id=item_id,
            item_type=item_type,
            quantity=quantity,
            x=x,
            y=y,
            spawn_time=time.time(),
            spawned_by=player_id
        )
        
        self.floating_items[item_id] = floating_item
        self.total_items_spawned += 1
        
        log_debug(f"Spawned floating item {item_id}: {quantity}x {item_type} at ({x:.1f}, {y:.1f})")
        
        return item_id
    
    def get_floating_item(self, item_id: str) -> Optional['ServerFloatingItem']:
        """Get a floating item by ID."""
        return self.floating_items.get(item_id)
    
    def remove_floating_item(self, item_id: str) -> bool:
        """Remove a floating item."""
        if item_id in self.floating_items:
            del self.floating_items[item_id]
            log_debug(f"Removed floating item {item_id}")
            return True
        return False
    
    def get_floating_items_in_range(self, x: float, y: float, range_pixels: float) -> List['ServerFloatingItem']:
        """Get all floating items within range of a position."""
        items = []
        for item in self.floating_items.values():
            distance = ((x - item.x)**2 + (y - item.y)**2)**0.5
            if distance <= range_pixels:
                items.append(item)
        return items
    
    def _update_floating_items(self, delta_time: float):
        """Update floating items (despawn old ones, etc.)."""
        current_time = time.time()
        despawn_time = 300  # 5 minutes
        
        expired_items = []
        for item_id, item in self.floating_items.items():
            if current_time - item.spawn_time > despawn_time:
                expired_items.append(item_id)
        
        for item_id in expired_items:
            self.remove_floating_item(item_id)
            log_debug(f"Despawned expired floating item {item_id}")
    
    def subscribe_to_chunk(self, chunk_x: int, chunk_y: int, player_id: str):
        """Subscribe a player to chunk updates."""
        chunk_key = (chunk_x, chunk_y)
        
        if chunk_key not in self.chunk_subscribers:
            self.chunk_subscribers[chunk_key] = set()
        
        self.chunk_subscribers[chunk_key].add(player_id)
        self.loaded_chunks.add(chunk_key)
        
        log_debug(f"Player {player_id} subscribed to chunk ({chunk_x}, {chunk_y})")
    
    def unsubscribe_from_chunk(self, chunk_x: int, chunk_y: int, player_id: str):
        """Unsubscribe a player from chunk updates."""
        chunk_key = (chunk_x, chunk_y)
        
        if chunk_key in self.chunk_subscribers:
            self.chunk_subscribers[chunk_key].discard(player_id)
            
            # If no subscribers left, mark for unloading
            if not self.chunk_subscribers[chunk_key]:
                del self.chunk_subscribers[chunk_key]
        
        log_debug(f"Player {player_id} unsubscribed from chunk ({chunk_x}, {chunk_y})")
    
    def get_chunk_subscribers(self, chunk_x: int, chunk_y: int) -> Set[str]:
        """Get list of players subscribed to a chunk."""
        return self.chunk_subscribers.get((chunk_x, chunk_y), set())
    
    def _check_chunk_unloading(self):
        """Check if any chunks should be unloaded."""
        # For now, keep all loaded chunks
        # In a full implementation, would unload chunks with no subscribers
        pass
    
    def get_changes_since(self, last_update: float) -> Dict[str, Any]:
        """
        Get all world changes since a timestamp.
        
        Args:
            last_update: Timestamp to get changes since
            
        Returns:
            Dictionary of changes
        """
        changes = {
            'blocks': {},
            'items': {},
            'timestamp': time.time()
        }
        
        # Block changes
        for position, change_data in self.changed_blocks.items():
            if change_data['timestamp'] > last_update:
                changes['blocks'][f"{position[0]},{position[1]}"] = {
                    'x': position[0],
                    'y': position[1],
                    'block_id': change_data['new_block_id'],
                    'player_id': change_data.get('player_id')
                }
        
        # Floating item changes (additions/removals)
        for item in self.floating_items.values():
            if item.spawn_time > last_update:
                changes['items'][item.item_id] = {
                    'action': 'add',
                    'item_type': item.item_type,
                    'quantity': item.quantity,
                    'x': item.x,
                    'y': item.y
                }
        
        return changes
    
    def clear_change_tracking(self):
        """Clear change tracking data."""
        self.changed_blocks.clear()
        self.changed_chunks.clear()
    
    def get_initial_data(self) -> Dict[str, Any]:
        """Get initial world data for new clients."""
        return {
            'world_name': self.world_name,
            'spawn_x': 0,
            'spawn_y': 0,
            'time_of_day': 0.5,  # Noon
            'floating_items': {
                item_id: {
                    'item_type': item.item_type,
                    'quantity': item.quantity,
                    'x': item.x,
                    'y': item.y
                }
                for item_id, item in self.floating_items.items()
            }
        }
    
    def save_to_disk(self):
        """Save world data to disk."""
        try:
            # Save world metadata
            metadata = {
                'world_name': self.world_name,
                'created_time': time.time(),
                'total_blocks_placed': self.total_blocks_placed,
                'total_blocks_broken': self.total_blocks_broken,
                'total_items_spawned': self.total_items_spawned
            }
            
            metadata_path = os.path.join(self.save_directory, 'metadata.json')
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            # Save chunks
            self._save_chunks()
            
            # Save floating items
            self._save_floating_items()
            
            log_debug(f"World '{self.world_name}' saved to disk")
            
        except Exception as e:
            log_error(f"Error saving world to disk: {e}")
    
    def _save_chunks(self):
        """Save chunk data to disk."""
        # This would save chunk data in a format suitable for loading
        # For now, just save basic chunk info
        chunks_data = {
            'loaded_chunks': list(self.loaded_chunks),
            'changed_chunks': list(self.changed_chunks)
        }
        
        chunks_path = os.path.join(self.save_directory, 'chunks.json')
        with open(chunks_path, 'w') as f:
            json.dump(chunks_data, f)
    
    def _save_floating_items(self):
        """Save floating items to disk."""
        items_data = {}
        for item_id, item in self.floating_items.items():
            items_data[item_id] = {
                'item_type': item.item_type,
                'quantity': item.quantity,
                'x': item.x,
                'y': item.y,
                'spawn_time': item.spawn_time,
                'spawned_by': item.spawned_by
            }
        
        items_path = os.path.join(self.save_directory, 'floating_items.json')
        with open(items_path, 'w') as f:
            json.dump(items_data, f)
    
    def load_from_disk(self):
        """Load world data from disk."""
        try:
            # Load metadata
            metadata_path = os.path.join(self.save_directory, 'metadata.json')
            if os.path.exists(metadata_path):
                with open(metadata_path, 'r') as f:
                    metadata = json.load(f)
                
                self.total_blocks_placed = metadata.get('total_blocks_placed', 0)
                self.total_blocks_broken = metadata.get('total_blocks_broken', 0)
                self.total_items_spawned = metadata.get('total_items_spawned', 0)
            
            # Load floating items
            self._load_floating_items()
            
            log_info(f"World '{self.world_name}' loaded from disk")
            
        except Exception as e:
            log_error(f"Error loading world from disk: {e}")
    
    def _load_floating_items(self):
        """Load floating items from disk."""
        items_path = os.path.join(self.save_directory, 'floating_items.json')
        if os.path.exists(items_path):
            with open(items_path, 'r') as f:
                items_data = json.load(f)
            
            for item_id, item_data in items_data.items():
                item = ServerFloatingItem(
                    item_id=item_id,
                    item_type=item_data['item_type'],
                    quantity=item_data['quantity'],
                    x=item_data['x'],
                    y=item_data['y'],
                    spawn_time=item_data['spawn_time'],
                    spawned_by=item_data.get('spawned_by')
                )
                self.floating_items[item_id] = item
    
    def auto_save(self):
        """Perform auto-save if needed."""
        if self.changed_blocks or self.changed_chunks:
            self.save_to_disk()
            self.clear_change_tracking()
    
    def get_world_stats(self) -> Dict[str, Any]:
        """Get world statistics."""
        return {
            'world_name': self.world_name,
            'loaded_chunks': len(self.loaded_chunks),
            'total_blocks_placed': self.total_blocks_placed,
            'total_blocks_broken': self.total_blocks_broken,
            'total_items_spawned': self.total_items_spawned,
            'floating_items': len(self.floating_items),
            'changed_blocks': len(self.changed_blocks),
            'chunk_subscribers': sum(len(subs) for subs in self.chunk_subscribers.values())
        }
    
    def get_world_state(self) -> Dict[str, Any]:
        """Get the complete world state for synchronization."""
        log_debug(f"Generating world state with {len(self.loaded_chunks)} loaded chunks")
        
        # Get all loaded chunks and their blocks
        chunks_data = {}
        total_blocks = 0
        
        for chunk_pos in self.loaded_chunks:
            chunk_x, chunk_y = chunk_pos
            chunk_key = (chunk_x, chunk_y)
            
            # Get chunk from parent class chunks dictionary
            if chunk_key not in self.chunks:
                log_warning(f"Chunk ({chunk_x}, {chunk_y}) marked as loaded but not in chunks dict")
                continue
                
            chunk = self.chunks[chunk_key]
            chunk_blocks = {}
            
            # Extract blocks from the chunk
            for (local_x, local_y), block_id in chunk.blocks.items():
                if block_id != 0:  # Only include non-air blocks
                    world_x = chunk_x * CHUNKSIZE + local_x
                    world_y = chunk_y * CHUNKSIZE + local_y
                    chunk_blocks[f"{world_x},{world_y}"] = block_id
                    total_blocks += 1
            
            if chunk_blocks:
                chunks_data[f"{chunk_x},{chunk_y}"] = chunk_blocks
                log_debug(f"Chunk ({chunk_x}, {chunk_y}) has {len(chunk_blocks)} blocks")
        
        log_info(f"World state contains {len(chunks_data)} chunks with {total_blocks} total blocks")
        
        # Get floating items data
        floating_items_data = {}
        for item_id, item in self.floating_items.items():
            floating_items_data[item_id] = {
                'item_type': item.item_type,
                'quantity': item.quantity,
                'x': item.x,
                'y': item.y,
                'spawn_time': item.spawn_time
            }
        
        return {
            'chunks': chunks_data,
            'floating_items': floating_items_data,
            'world_time': getattr(self, 'world_time', 0),
            'spawn_point': [0, 0],
            'world_name': self.world_name
        }
    
    def get_new_chunks_for_client(self, client_id: str) -> Dict[str, Any]:
        """Get only the chunks that are new for a specific client."""
        if client_id not in self.client_chunks:
            self.client_chunks[client_id] = set()
        
        client_has_chunks = self.client_chunks[client_id]
        new_chunks = self.newly_generated_chunks - client_has_chunks
        
        if not new_chunks:
            return {'chunks': {}, 'floating_items': {}}
        
        log_debug(f"Sending {len(new_chunks)} new chunks to client {client_id}")
        
        # Get only the new chunks data
        chunks_data = {}
        total_blocks = 0
        
        for chunk_pos in new_chunks:
            chunk_x, chunk_y = chunk_pos
            chunk_key = (chunk_x, chunk_y)
            
            if chunk_key not in self.chunks:
                continue
                
            chunk = self.chunks[chunk_key]
            chunk_blocks = {}
            
            # Extract blocks from the chunk
            for (local_x, local_y), block_id in chunk.blocks.items():
                if block_id != 0:  # Only include non-air blocks
                    world_x = chunk_x * CHUNKSIZE + local_x
                    world_y = chunk_y * CHUNKSIZE + local_y
                    chunk_blocks[f"{world_x},{world_y}"] = block_id
                    total_blocks += 1
            
            if chunk_blocks:
                chunks_data[f"{chunk_x},{chunk_y}"] = chunk_blocks
        
        # Mark these chunks as sent to this client
        self.client_chunks[client_id].update(new_chunks)
        
        log_info(f"Sending {len(chunks_data)} new chunks with {total_blocks} blocks to client {client_id}")
        
        return {
            'chunks': chunks_data,
            'floating_items': {},  # Only send floating items in full world state
            'world_time': getattr(self, 'world_time', 0),
            'spawn_point': [0, 0],
            'world_name': self.world_name
        }
    
    def mark_chunks_generated(self, chunk_positions: List[Tuple[int, int]]):
        """Mark chunks as newly generated for incremental updates."""
        for pos in chunk_positions:
            self.newly_generated_chunks.add(pos)
        log_debug(f"Marked {len(chunk_positions)} chunks as newly generated")
    
    def clear_new_chunks_for_all_clients(self):
        """Clear the newly generated chunks list after all clients have been updated."""
        self.newly_generated_chunks.clear()
    
    def client_disconnected(self, client_id: str):
        """Clean up client data when a client disconnects."""
        if client_id in self.client_chunks:
            del self.client_chunks[client_id]
        log_debug(f"Cleaned up chunk tracking for disconnected client {client_id}")
    
    def _load_world_data(self):
        """Load existing world data from the data manager."""
        try:
            from ...data import DataManager
            
            # Initialize data manager
            game_folder = os.path.join(os.path.dirname(self.save_directory), '..')
            data_manager = DataManager(game_folder)
            
            # Load game data
            game_data = data_manager.load_game(self.world_name)
            if game_data:
                log_info(f"Loading existing world data for '{self.world_name}'")
                
                # Load world state
                world_state = game_data.get('world_state', {})
                self.world_time = world_state.get('global_time', 0)
                self.spawn_point = world_state.get('spawn_point', {'x': 0, 'y': 0})
                
                # Load chunks
                entities = game_data.get('entities', {})
                if 'chunks' in entities:
                    # Convert chunk data to loaded chunks for the server
                    for chunk_name, chunk_data in entities['chunks'].items():
                        chunk_x, chunk_y = map(int, chunk_name.split(','))
                        self.loaded_chunks.add((chunk_x, chunk_y))
                        
                        # Load blocks from chunk data into the world
                        for y_idx, row in enumerate(chunk_data):
                            for x_idx, block_id in enumerate(row):
                                if block_id != '00':  # Skip air blocks
                                    world_x = chunk_x * CHUNKSIZE + x_idx
                                    world_y = chunk_y * CHUNKSIZE + y_idx
                                    self.set_block(world_x, world_y, int(block_id), None)
                
                # Load floating items
                floating_items_data = entities.get('floating_items', [])
                for item_data in floating_items_data:
                    if len(item_data) >= 3:
                        item_id = f"loaded_item_{self.item_id_counter}"
                        self.item_id_counter += 1
                        
                        floating_item = ServerFloatingItem(
                            item_id=item_id,
                            item_type=item_data[0],
                            quantity=item_data[1],
                            x=item_data[2][0],
                            y=item_data[2][1],
                            spawn_time=time.time()
                        )
                        self.floating_items[item_id] = floating_item
                
                log_info(f"Loaded {len(self.loaded_chunks)} chunks and {len(self.floating_items)} floating items")
                
                # Check if we have any chunks loaded, if not generate initial world
                if len(self.loaded_chunks) == 0:
                    log_info("No chunks found in existing world data, generating initial world")
                    self._generate_initial_world()
            else:
                log_info(f"No existing world data found for '{self.world_name}', creating new world")
                # Generate some initial chunks around spawn point
                self._generate_initial_world()
                
        except Exception as e:
            log_error(f"Failed to load world data: {e}")
            log_info("Starting with empty world")
            # Generate some initial chunks around spawn point
            self._generate_initial_world()
    
    def _generate_initial_world(self):
        """Generate initial world chunks around spawn point."""
        try:
            log_info("Starting initial world generation...")
            # Generate a 8x8 area around spawn to provide excellent coverage
            # Screen is 24x16 tiles, so we need good chunk coverage
            # With CHUNKSIZE=4, 8x8 chunks = 32x32 tiles = 1024x1024 pixels (more than enough)
            spawn_chunk_x, spawn_chunk_y = 0, 0  # Center at 0,0
            
            for dx in range(-4, 4):
                for dy in range(-4, 4):
                    chunk_x = spawn_chunk_x + dx
                    chunk_y = spawn_chunk_y + dy
                    log_debug(f"Generating chunk ({chunk_x}, {chunk_y})")
                    self._generate_chunk(chunk_x, chunk_y)
                    
            log_info(f"Generated initial world: {8*8} chunks around spawn, total loaded chunks: {len(self.loaded_chunks)}")
            
        except Exception as e:
            log_error(f"Failed to generate initial world: {e}")
            import traceback
            log_error(f"Traceback: {traceback.format_exc()}")
    
    def has_chunk(self, chunk_x: int, chunk_y: int) -> bool:
        """Check if a chunk is already loaded."""
        return (chunk_x, chunk_y) in self.loaded_chunks
    
    def _generate_chunk(self, chunk_x: int, chunk_y: int):
        """Generate a single chunk using the proper terrain generation system."""
        try:
            from ...config.settings import CHUNKSIZE, TERRAIN_SCALE, BIOME_SCALE, TERRAIN_OCTAVE, BIOME_OCTAVE
            from perlin_noise import PerlinNoise
            import random
            from random import randint
            
            log_debug(f"Generating chunk ({chunk_x}, {chunk_y}) with {CHUNKSIZE}x{CHUNKSIZE} blocks")
            
            # Create chunk using parent class method to ensure proper chunk state
            self._load_chunk(chunk_x, chunk_y)
            
            # Initialize noise generators with fixed seed for consistent world generation
            seed = 12345
            terrain_noise = PerlinNoise(octaves=TERRAIN_OCTAVE, seed=seed)
            biome_noise = PerlinNoise(octaves=BIOME_OCTAVE, seed=seed + 1)
            
            # Game block IDs (using the same IDs as client-side generation)
            GRASS = '01'
            DIRT = '07'
            WATER = '00'
            STONE = '1s'
            BUSH = '111'
            ICY_GRASS = '013'
            ICE = '012'
            ICY_BUSH = '114'
            ICY_DIRT = '015'
            ROCK = '1p'
            ICY_ROCK = '116'
            IRON_ORE = '118'
            DIAMOND_ORE = '119'
            COALD_ORE = '123'
            
            # Generate terrain for this chunk using the same algorithm as client
            blocks_created = 0
            for y in range(CHUNKSIZE):
                for x in range(CHUNKSIZE):
                    world_x = chunk_x * CHUNKSIZE + x
                    world_y = chunk_y * CHUNKSIZE + y
                    
                    # Use the same noise-based terrain generation as client
                    tVal = round(terrain_noise([world_x / TERRAIN_SCALE, world_y / TERRAIN_SCALE]), 5)
                    bVal = round(biome_noise([world_x / BIOME_SCALE, world_y / BIOME_SCALE]), 5)
                    
                    # Use the same terrain logic as client-side generation
                    block_layers = []
                    
                    if tVal >= -0.05 and tVal <= 0.19:
                        if bVal >= 0.2:
                            # Biome forest temperate
                            if randint(0, 10) == 0:
                                block_layers = [GRASS, BUSH]
                            else:
                                block_layers = [GRASS]
                        elif bVal >= 0 and bVal < 0.2:
                            # Biome plains temperate
                            if randint(0, 150) == 0:
                                block_layers = [GRASS, BUSH]
                            else:
                                block_layers = [GRASS]
                        elif bVal > -0.2 and bVal < 0:
                            # Biome snow plains
                            if randint(0, 150) == 0:
                                block_layers = [ICY_GRASS, ICY_BUSH]
                            else:
                                block_layers = [ICY_GRASS]
                        elif bVal <= -0.2:
                            # Biome snow forest
                            if randint(0, 10) == 0:
                                block_layers = [ICY_GRASS, ICY_BUSH]
                            else:
                                block_layers = [ICY_GRASS]

                    elif tVal > 0.19 and tVal <= 0.27:
                        if bVal > 0:
                            if randint(0, 5) == 0:
                                block_layers = [GRASS]
                            else:
                                if randint(0, 7) == 0:
                                    block_layers = [DIRT, ROCK]
                                else:
                                    block_layers = [DIRT]
                        elif bVal < 0:
                            if randint(0, 5) == 0:
                                block_layers = [ICY_GRASS]
                            else:
                                if randint(0, 7) == 0:
                                    block_layers = [ICY_DIRT, ICY_ROCK]
                                else:
                                    block_layers = [ICY_DIRT]

                    elif tVal > 0.27:
                        if bVal >= 0:
                            block_layers = [DIRT]
                        elif bVal < 0:
                            block_layers = [ICY_DIRT]

                        if randint(0, 15) == 0 and tVal > 0.285:
                            if randint(0, 20) == 0:
                                block_layers.append(DIAMOND_ORE)
                            elif randint(0, 3) == 0:
                                block_layers.append(COALD_ORE)
                            else:
                                block_layers.append(IRON_ORE)
                        else:
                            block_layers.append(STONE)

                    elif tVal > -0.3 and tVal < -0.05 and bVal < 0:
                        block_layers = [ICE]
                    else:
                        block_layers = [WATER]
                    
                    # Store the block layers using the proper format
                    if block_layers:
                        # Use the parent class set_block method to store blocks properly
                        super().set_block(world_x, world_y, block_layers)
                        blocks_created += 1
            
            # Mark chunk as loaded
            self.loaded_chunks.add((chunk_x, chunk_y))
            
            # Mark this chunk as newly generated for incremental updates
            self.newly_generated_chunks.add((chunk_x, chunk_y))
            
            log_debug(f"Generated chunk ({chunk_x}, {chunk_y}) with {blocks_created} blocks")
            
        except Exception as e:
            log_error(f"Failed to generate chunk ({chunk_x}, {chunk_y}): {e}")
            import traceback
            log_error(f"Traceback: {traceback.format_exc()}")
    
    def save_to_disk(self):
        """Save world data to disk."""
        try:
            from ...data import DataManager
            
            # Initialize data manager
            game_folder = os.path.join(os.path.dirname(self.save_directory), '..')
            data_manager = DataManager(game_folder)
            
            # Prepare world state
            world_state = {
                'global_time': getattr(self, 'world_time', 0),
                'spawn_point': getattr(self, 'spawn_point', {'x': 0, 'y': 0}),
                'seed': '0',  # Default seed
                'night_shade': 255
            }
            
            # Prepare entities data
            entities = {
                'chunks': {},
                'floating_items': [],
                'signs': {},
                'mobs': {},
                'chests': {},
                'furnaces': {}
            }
            
            # Convert floating items to save format
            for item_id, item in self.floating_items.items():
                entities['floating_items'].append([
                    item.item_type,
                    item.quantity,
                    [item.x, item.y]
                ])
            
            # Prepare game data
            game_data = {
                'world_state': world_state,
                'entities': entities,
                'player_state': {}  # Will be updated by player manager
            }
            
            # Save the data
            data_manager.save_game(self.world_name, game_data)
            log_info(f"Saved world '{self.world_name}' to disk")
            
        except Exception as e:
            log_error(f"Failed to save world data: {e}")


class ServerFloatingItem:
    """Represents a floating item on the server."""
    
    def __init__(self, item_id: str, item_type: str, quantity: int, 
                 x: float, y: float, spawn_time: float, spawned_by: str = None):
        self.item_id = item_id
        self.item_type = item_type
        self.quantity = quantity
        self.x = x
        self.y = y
        self.spawn_time = spawn_time
        self.spawned_by = spawned_by
        
        # Item physics (simplified)
        self.velocity_x = 0.0
        self.velocity_y = 0.0
    
    def update(self, delta_time: float):
        """Update item physics."""
        # Simple gravity and movement
        self.velocity_y += 100 * delta_time  # Gravity
        
        self.x += self.velocity_x * delta_time
        self.y += self.velocity_y * delta_time
        
        # Simple collision with ground (y = 0)
        if self.y > 0:
            self.y = 0
            self.velocity_y = 0
            self.velocity_x *= 0.9  # Friction
    
    def __str__(self) -> str:
        return f"ServerFloatingItem({self.item_id}: {self.quantity}x {self.item_type})"
