"""
Player Manager for PyCraft 2D Server

Manages player states, sessions, and persistence for multiplayer gameplay.
"""

import time
import json
import os
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict

from ...utils.logger import log_info, log_error, log_debug


@dataclass
class PlayerState:
    """Represents a player's complete game state."""
    player_id: str
    player_name: str
    
    # Position and movement
    x: float = 0.0
    y: float = 0.0
    velocity_x: float = 0.0
    velocity_y: float = 0.0
    facing_direction: str = 'right'
    
    # Health and stats
    health: int = 100
    max_health: int = 100
    energy: int = 100
    max_energy: int = 100
    hunger: int = 100
    max_hunger: int = 100
    
    # Experience and levels
    experience: int = 0
    level: int = 1
    
    # Inventory (36 slots)
    inventory: List[Optional[Dict[str, Any]]] = None
    
    # Equipment
    equipped_tool: Optional[str] = None
    equipped_helmet: Optional[str] = None
    equipped_chest: Optional[str] = None
    equipped_legs: Optional[str] = None
    equipped_boots: Optional[str] = None
    
    # Game state
    spawn_x: float = 0.0
    spawn_y: float = 0.0
    last_login: float = 0.0
    total_playtime: float = 0.0
    session_start: float = 0.0
    
    # Permissions and settings
    is_admin: bool = False
    can_build: bool = True
    can_interact: bool = True
    
    def __post_init__(self):
        """Initialize default values after object creation."""
        if self.inventory is None:
            self.inventory = [None] * 36
        
        if self.session_start == 0.0:
            self.session_start = time.time()
        
        if self.last_login == 0.0:
            self.last_login = time.time()
    
    def add_item(self, item_type: str, quantity: int) -> int:
        """
        Add items to inventory.
        
        Args:
            item_type: Type of item to add
            quantity: Number of items to add
            
        Returns:
            Number of items actually added
        """
        added = 0
        remaining = quantity
        
        # First, try to stack with existing items
        for slot in self.inventory:
            if slot and slot.get('item_type') == item_type:
                current_quantity = slot.get('quantity', 0)
                max_stack = 64  # Default max stack size
                
                can_add = min(remaining, max_stack - current_quantity)
                if can_add > 0:
                    slot['quantity'] += can_add
                    added += can_add
                    remaining -= can_add
                    
                    if remaining <= 0:
                        break
        
        # Then, try to fill empty slots
        if remaining > 0:
            for i, slot in enumerate(self.inventory):
                if not slot:
                    max_stack = 64
                    can_add = min(remaining, max_stack)
                    
                    self.inventory[i] = {
                        'item_type': item_type,
                        'quantity': can_add
                    }
                    
                    added += can_add
                    remaining -= can_add
                    
                    if remaining <= 0:
                        break
        
        return added
    
    def remove_item(self, item_type: str, quantity: int) -> int:
        """
        Remove items from inventory.
        
        Args:
            item_type: Type of item to remove
            quantity: Number of items to remove
            
        Returns:
            Number of items actually removed
        """
        removed = 0
        remaining = quantity
        
        for i, slot in enumerate(self.inventory):
            if slot and slot.get('item_type') == item_type:
                current_quantity = slot.get('quantity', 0)
                can_remove = min(remaining, current_quantity)
                
                slot['quantity'] -= can_remove
                removed += can_remove
                remaining -= can_remove
                
                # Remove slot if empty
                if slot['quantity'] <= 0:
                    self.inventory[i] = None
                
                if remaining <= 0:
                    break
        
        return removed
    
    def has_item(self, item_type: str, quantity: int = 1) -> bool:
        """Check if player has specified items."""
        total = 0
        for slot in self.inventory:
            if slot and slot.get('item_type') == item_type:
                total += slot.get('quantity', 0)
                if total >= quantity:
                    return True
        return False
    
    def get_inventory_summary(self) -> Dict[str, int]:
        """Get a summary of all items in inventory."""
        summary = {}
        for slot in self.inventory:
            if slot:
                item_type = slot.get('item_type')
                quantity = slot.get('quantity', 0)
                if item_type:
                    summary[item_type] = summary.get(item_type, 0) + quantity
        return summary
    
    def update_session_time(self):
        """Update session playtime."""
        current_time = time.time()
        if self.session_start > 0:
            session_duration = current_time - self.session_start
            self.total_playtime += session_duration
        self.session_start = current_time
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PlayerState':
        """Create PlayerState from dictionary."""
        # Handle inventory field specially
        inventory = data.get('inventory', [None] * 36)
        if len(inventory) < 36:
            inventory.extend([None] * (36 - len(inventory)))
        
        return cls(
            player_id=data['player_id'],
            player_name=data['player_name'],
            x=data.get('x', 0.0),
            y=data.get('y', 0.0),
            velocity_x=data.get('velocity_x', 0.0),
            velocity_y=data.get('velocity_y', 0.0),
            facing_direction=data.get('facing_direction', 'right'),
            health=data.get('health', 100),
            max_health=data.get('max_health', 100),
            energy=data.get('energy', 100),
            max_energy=data.get('max_energy', 100),
            hunger=data.get('hunger', 100),
            max_hunger=data.get('max_hunger', 100),
            experience=data.get('experience', 0),
            level=data.get('level', 1),
            inventory=inventory,
            equipped_tool=data.get('equipped_tool'),
            equipped_helmet=data.get('equipped_helmet'),
            equipped_chest=data.get('equipped_chest'),
            equipped_legs=data.get('equipped_legs'),
            equipped_boots=data.get('equipped_boots'),
            spawn_x=data.get('spawn_x', 0.0),
            spawn_y=data.get('spawn_y', 0.0),
            last_login=data.get('last_login', time.time()),
            total_playtime=data.get('total_playtime', 0.0),
            session_start=data.get('session_start', time.time()),
            is_admin=data.get('is_admin', False),
            can_build=data.get('can_build', True),
            can_interact=data.get('can_interact', True)
        )


class PlayerManager:
    """
    Manages all player states and sessions on the server.
    """
    
    def __init__(self, save_directory: str = "saves/players"):
        """Initialize the player manager."""
        self.save_directory = save_directory
        self.players: Dict[str, PlayerState] = {}
        self.player_sessions: Dict[str, float] = {}  # player_id -> login_time
        
        # Statistics
        self.total_players_ever = 0
        self.peak_concurrent_players = 0
        
        # Ensure save directory exists
        os.makedirs(save_directory, exist_ok=True)
        
        log_info("PlayerManager initialized")
    
    def create_player(self, player_id: str, player_data: Dict[str, Any]) -> Optional[PlayerState]:
        """
        Create or load a player state.
        
        Args:
            player_id: Unique player identifier
            player_data: Initial player data
            
        Returns:
            PlayerState object or None if creation failed
        """
        try:
            # Try to load existing player first
            existing_player = self.load_player(player_id)
            if existing_player:
                # Update session info
                existing_player.last_login = time.time()
                existing_player.session_start = time.time()
                self.players[player_id] = existing_player
                self.player_sessions[player_id] = time.time()
                
                log_info(f"Loaded existing player: {player_id}")
                return existing_player
            
            # Create new player
            player_state = PlayerState(
                player_id=player_id,
                player_name=player_data.get('player_name', 'Unknown'),
                x=player_data.get('x', 0.0),
                y=player_data.get('y', 0.0),
                health=player_data.get('health', 100),
                max_health=player_data.get('max_health', 100)
            )
            
            # Give starting items
            self._give_starting_items(player_state)
            
            self.players[player_id] = player_state
            self.player_sessions[player_id] = time.time()
            self.total_players_ever += 1
            
            # Update peak concurrent players
            current_count = len(self.players)
            if current_count > self.peak_concurrent_players:
                self.peak_concurrent_players = current_count
            
            log_info(f"Created new player: {player_id} ({player_state.player_name})")
            return player_state
            
        except Exception as e:
            log_error(f"Error creating player {player_id}: {e}")
            return None
    
    def _give_starting_items(self, player_state: PlayerState):
        """Give starting items to a new player."""
        starting_items = [
            ('wood', 10),
            ('stone', 5),
            ('bread', 3),
            ('wooden_pickaxe', 1)
        ]
        
        for item_type, quantity in starting_items:
            player_state.add_item(item_type, quantity)
        
        log_debug(f"Gave starting items to {player_state.player_id}")
    
    def remove_player(self, player_id: str):
        """Remove a player from the active session."""
        if player_id in self.players:
            player_state = self.players[player_id]
            
            # Update session time
            player_state.update_session_time()
            
            # Save player data
            self.save_player(player_state)
            
            # Remove from active players
            del self.players[player_id]
            self.player_sessions.pop(player_id, None)
            
            log_info(f"Removed player: {player_id}")
    
    def get_player(self, player_id: str) -> Optional[PlayerState]:
        """Get a player state by ID."""
        return self.players.get(player_id)
    
    def get_player_state(self, player_id: str) -> Optional[PlayerState]:
        """Get a player state by ID (alias for get_player for compatibility)."""
        return self.players.get(player_id)
    
    def get_all_players(self) -> List[PlayerState]:
        """Get all active player states."""
        return list(self.players.values())
    
    def get_player_data(self, player_id: str) -> Optional[Dict[str, Any]]:
        """Get player data for network transmission."""
        player = self.get_player(player_id)
        if not player:
            return None
        
        return {
            'player_id': player.player_id,
            'player_name': player.player_name,
            'x': player.x,
            'y': player.y,
            'health': player.health,
            'max_health': player.max_health,
            'level': player.level,
            'facing_direction': player.facing_direction
        }
    
    def update(self, delta_time: float):
        """Update all player states."""
        for player_state in self.players.values():
            self._update_player(player_state, delta_time)
    
    def _update_player(self, player_state: PlayerState, delta_time: float):
        """Update a single player's state."""
        # Regenerate energy over time
        if player_state.energy < player_state.max_energy:
            player_state.energy = min(
                player_state.max_energy,
                player_state.energy + int(10 * delta_time)  # 10 energy per second
            )
        
        # Hunger decreases slowly
        current_time = time.time()
        if current_time % 60 < delta_time:  # Every minute
            player_state.hunger = max(0, player_state.hunger - 1)
        
        # Health regeneration when well-fed
        if player_state.hunger > 80 and player_state.health < player_state.max_health:
            if current_time % 5 < delta_time:  # Every 5 seconds
                player_state.health = min(player_state.max_health, player_state.health + 1)
    
    def save_player(self, player_state: PlayerState):
        """Save a player's data to disk."""
        try:
            player_file = os.path.join(self.save_directory, f"{player_state.player_id}.json")
            
            with open(player_file, 'w') as f:
                json.dump(player_state.to_dict(), f, indent=2)
            
            log_debug(f"Saved player data: {player_state.player_id}")
            
        except Exception as e:
            log_error(f"Error saving player {player_state.player_id}: {e}")
    
    def load_player(self, player_id: str) -> Optional[PlayerState]:
        """Load a player's data from disk."""
        try:
            player_file = os.path.join(self.save_directory, f"{player_id}.json")
            
            if not os.path.exists(player_file):
                return None
            
            with open(player_file, 'r') as f:
                player_data = json.load(f)
            
            player_state = PlayerState.from_dict(player_data)
            log_debug(f"Loaded player data: {player_id}")
            
            return player_state
            
        except Exception as e:
            log_error(f"Error loading player {player_id}: {e}")
            return None
    
    def save_to_disk(self):
        """Save all active player data to disk."""
        saved_count = 0
        for player_state in self.players.values():
            try:
                player_state.update_session_time()
                self.save_player(player_state)
                saved_count += 1
            except Exception as e:
                log_error(f"Error saving player {player_state.player_id}: {e}")
        
        log_debug(f"Saved {saved_count} player states to disk")
    
    def get_players_in_range(self, x: float, y: float, range_pixels: float) -> List[PlayerState]:
        """Get all players within range of a position."""
        nearby_players = []
        
        for player_state in self.players.values():
            distance = ((x - player_state.x)**2 + (y - player_state.y)**2)**0.5
            if distance <= range_pixels:
                nearby_players.append(player_state)
        
        return nearby_players
    
    def get_player_count(self) -> int:
        """Get the current number of active players."""
        return len(self.players)
    
    def get_manager_stats(self) -> Dict[str, Any]:
        """Get player manager statistics."""
        total_playtime = sum(player.total_playtime for player in self.players.values())
        
        return {
            'active_players': len(self.players),
            'total_players_ever': self.total_players_ever,
            'peak_concurrent_players': self.peak_concurrent_players,
            'total_playtime_hours': total_playtime / 3600,
            'average_session_length': self._get_average_session_length()
        }
    
    def _get_average_session_length(self) -> float:
        """Calculate average session length in seconds."""
        if not self.player_sessions:
            return 0.0
        
        current_time = time.time()
        total_session_time = 0.0
        
        for login_time in self.player_sessions.values():
            total_session_time += current_time - login_time
        
        return total_session_time / len(self.player_sessions)
    
    def broadcast_to_all_players(self, message: str):
        """Send a message to all active players (for admin commands)."""
        # This would be implemented by the server to send chat messages
        log_info(f"Broadcast message: {message}")
    
    def kick_player(self, player_id: str, reason: str = "Kicked by admin"):
        """Kick a player from the server."""
        if player_id in self.players:
            log_info(f"Kicking player {player_id}: {reason}")
            self.remove_player(player_id)
            return True
        return False
    
    def set_player_admin(self, player_id: str, is_admin: bool):
        """Set a player's admin status."""
        player = self.get_player(player_id)
        if player:
            player.is_admin = is_admin
            log_info(f"Set admin status for {player_id}: {is_admin}")
            return True
        return False
