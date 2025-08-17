"""
World Actions for PyCraft 2D

Handles all world modification actions including block placement, breaking,
and environmental interactions.
"""

import math
from typing import Dict, Any, Optional

from .base_action import BaseAction, ActionResult, ActionExecutionResult
from game.config.settings import TILESIZE, MELEEREACH
from game.utils.logger import log_debug


class PlaceBlockAction(BaseAction):
    """
    Action for placing blocks in the world.
    """
    
    def __init__(self, player_id: str, x: int, y: int, block_id: int,
                 timestamp: float = None, action_id: str = None):
        """
        Initialize block placement action.
        
        Args:
            player_id: ID of the player placing the block
            x: X coordinate of the block
            y: Y coordinate of the block
            block_id: ID of the block type to place
            timestamp: When the action was created
            action_id: Unique action identifier
        """
        super().__init__(player_id, timestamp, action_id)
        
        self.x = x
        self.y = y
        self.block_id = block_id
        
        self.requires_validation = True
        self.cooldown_seconds = 0.1  # Prevent spam clicking
        
        # Placing blocks costs the block item
        self.cost_resources = {f'block_{block_id}': 1}
    
    def get_action_type(self) -> str:
        """Get the action type identifier."""
        return "place_block"
    
    def validate(self, world, player_state) -> ActionExecutionResult:
        """
        Validate the block placement action.
        
        Args:
            world: The game world
            player_state: Current player state
            
        Returns:
            ActionExecutionResult with validation outcome
        """
        if not player_state:
            return ActionExecutionResult(ActionResult.INVALID, "Player not found")
        
        # Check if block position is within reach
        player_x, player_y = player_state.x, player_state.y
        block_center_x = self.x * TILESIZE + TILESIZE // 2
        block_center_y = self.y * TILESIZE + TILESIZE // 2
        
        distance = math.sqrt((player_x - block_center_x)**2 + (player_y - block_center_y)**2)
        
        if distance > MELEEREACH:
            return ActionExecutionResult(
                ActionResult.INVALID,
                f"Block too far away: {distance:.1f} > {MELEEREACH}"
            )
        
        # Check if position is already occupied
        existing_block = world.get_block(self.x, self.y)
        if existing_block != 0:  # 0 = air/empty
            return ActionExecutionResult(
                ActionResult.INVALID,
                f"Position already occupied by block {existing_block}"
            )
        
        # Check if block ID is valid
        if self.block_id <= 0:
            return ActionExecutionResult(
                ActionResult.INVALID,
                f"Invalid block ID: {self.block_id}"
            )
        
        # Check if player has the block in inventory
        if not self._player_has_block(player_state):
            return ActionExecutionResult(
                ActionResult.INSUFFICIENT_RESOURCES,
                f"Player doesn't have block type {self.block_id}"
            )
        
        return ActionExecutionResult(ActionResult.SUCCESS, "Block placement validated")
    
    def execute(self, world, player_state) -> ActionExecutionResult:
        """
        Execute the block placement action.
        
        Args:
            world: The game world
            player_state: Current player state
            
        Returns:
            ActionExecutionResult with execution outcome
        """
        try:
            # Remove block from player inventory
            if not self._consume_block_from_inventory(player_state):
                return ActionExecutionResult(
                    ActionResult.FAILED,
                    "Failed to consume block from inventory"
                )
            
            # Place block in world
            success = world.set_block(self.x, self.y, self.block_id, self.player_id)
            
            if not success:
                # Refund the block if placement failed
                self._refund_block_to_inventory(player_state)
                return ActionExecutionResult(
                    ActionResult.FAILED,
                    "Failed to place block in world"
                )
            
            log_debug(f"Player {self.player_id} placed block {self.block_id} at ({self.x}, {self.y})")
            
            return ActionExecutionResult(
                ActionResult.SUCCESS,
                "Block placed successfully",
                {
                    'position': (self.x, self.y),
                    'block_id': self.block_id,
                    'chunk_x': self.x // 32,  # CHUNKSIZE
                    'chunk_y': self.y // 32
                }
            )
            
        except Exception as e:
            return ActionExecutionResult(
                ActionResult.FAILED,
                f"Block placement failed: {e}"
            )
    
    def _player_has_block(self, player_state) -> bool:
        """Check if player has the required block in inventory."""
        block_item_type = f'block_{self.block_id}'
        
        for slot in player_state.inventory:
            if slot and slot.get('item_type') == block_item_type:
                if slot.get('quantity', 0) > 0:
                    return True
        return False
    
    def _consume_block_from_inventory(self, player_state) -> bool:
        """Remove one block from player inventory."""
        block_item_type = f'block_{self.block_id}'
        return player_state.remove_item(block_item_type, 1) > 0
    
    def _refund_block_to_inventory(self, player_state) -> bool:
        """Add block back to player inventory (refund)."""
        block_item_type = f'block_{self.block_id}'
        return player_state.add_item(block_item_type, 1)
    
    def get_serializable_data(self) -> Dict[str, Any]:
        """Get serializable representation."""
        data = super().get_serializable_data()
        data.update({
            'x': self.x,
            'y': self.y,
            'block_id': self.block_id
        })
        return data
    
    @classmethod
    def from_serializable_data(cls, data: Dict[str, Any]):
        """Create action from serialized data."""
        return cls(
            player_id=data['player_id'],
            x=data['x'],
            y=data['y'],
            block_id=data['block_id'],
            timestamp=data['timestamp'],
            action_id=data['action_id']
        )


class BreakBlockAction(BaseAction):
    """
    Action for breaking blocks in the world.
    """
    
    def __init__(self, player_id: str, x: int, y: int,
                 timestamp: float = None, action_id: str = None):
        """Initialize block breaking action."""
        super().__init__(player_id, timestamp, action_id)
        
        self.x = x
        self.y = y
        
        self.requires_validation = True
        self.cooldown_seconds = 0.2  # Prevent spam clicking
    
    def get_action_type(self) -> str:
        """Get the action type identifier."""
        return "break_block"
    
    def validate(self, world, player_state) -> ActionExecutionResult:
        """Validate the block breaking action."""
        if not player_state:
            return ActionExecutionResult(ActionResult.INVALID, "Player not found")
        
        # Check if block position is within reach
        player_x, player_y = player_state.x, player_state.y
        block_center_x = self.x * TILESIZE + TILESIZE // 2
        block_center_y = self.y * TILESIZE + TILESIZE // 2
        
        distance = math.sqrt((player_x - block_center_x)**2 + (player_y - block_center_y)**2)
        
        if distance > MELEEREACH:
            return ActionExecutionResult(
                ActionResult.INVALID,
                f"Block too far away: {distance:.1f} > {MELEEREACH}"
            )
        
        # Check if there's actually a block to break
        existing_block = world.get_block(self.x, self.y)
        if existing_block == 0:  # 0 = air/empty
            return ActionExecutionResult(
                ActionResult.INVALID,
                "No block to break at this position"
            )
        
        return ActionExecutionResult(ActionResult.SUCCESS, "Block breaking validated")
    
    def execute(self, world, player_state) -> ActionExecutionResult:
        """Execute the block breaking action."""
        try:
            # Get the block type before breaking
            broken_block_id = world.get_block(self.x, self.y)
            
            if broken_block_id == 0:
                return ActionExecutionResult(
                    ActionResult.FAILED,
                    "No block to break"
                )
            
            # Remove block from world (set to air)
            success = world.set_block(self.x, self.y, 0, self.player_id)
            
            if not success:
                return ActionExecutionResult(
                    ActionResult.FAILED,
                    "Failed to break block in world"
                )
            
            # Spawn floating item for the broken block
            block_x = self.x * TILESIZE + TILESIZE // 2
            block_y = self.y * TILESIZE + TILESIZE // 2
            
            item_type = f'block_{broken_block_id}'
            world.spawn_floating_item(item_type, 1, block_x, block_y)
            
            log_debug(f"Player {self.player_id} broke block {broken_block_id} at ({self.x}, {self.y})")
            
            return ActionExecutionResult(
                ActionResult.SUCCESS,
                "Block broken successfully",
                {
                    'position': (self.x, self.y),
                    'broken_block_id': broken_block_id,
                    'item_spawned': item_type,
                    'chunk_x': self.x // 32,  # CHUNKSIZE
                    'chunk_y': self.y // 32
                }
            )
            
        except Exception as e:
            return ActionExecutionResult(
                ActionResult.FAILED,
                f"Block breaking failed: {e}"
            )
    
    def get_serializable_data(self) -> Dict[str, Any]:
        """Get serializable representation."""
        data = super().get_serializable_data()
        data.update({
            'x': self.x,
            'y': self.y
        })
        return data
    
    @classmethod
    def from_serializable_data(cls, data: Dict[str, Any]):
        """Create action from serialized data."""
        return cls(
            player_id=data['player_id'],
            x=data['x'],
            y=data['y'],
            timestamp=data['timestamp'],
            action_id=data['action_id']
        )


class InteractAction(BaseAction):
    """
    Action for interacting with world objects (chests, furnaces, doors, etc.).
    """
    
    def __init__(self, player_id: str, x: int, y: int, interaction_type: str = "use",
                 timestamp: float = None, action_id: str = None):
        """Initialize interaction action."""
        super().__init__(player_id, timestamp, action_id)
        
        self.x = x
        self.y = y
        self.interaction_type = interaction_type  # "use", "open", "close", etc.
        
        self.requires_validation = True
        self.cooldown_seconds = 0.1
    
    def get_action_type(self) -> str:
        """Get the action type identifier."""
        return "interact"
    
    def validate(self, world, player_state) -> ActionExecutionResult:
        """Validate the interaction action."""
        if not player_state:
            return ActionExecutionResult(ActionResult.INVALID, "Player not found")
        
        # Check if interaction position is within reach
        player_x, player_y = player_state.x, player_state.y
        interact_x = self.x * TILESIZE + TILESIZE // 2
        interact_y = self.y * TILESIZE + TILESIZE // 2
        
        distance = math.sqrt((player_x - interact_x)**2 + (player_y - interact_y)**2)
        
        if distance > MELEEREACH:
            return ActionExecutionResult(
                ActionResult.INVALID,
                f"Interaction target too far away: {distance:.1f} > {MELEEREACH}"
            )
        
        # Check if there's something to interact with
        block_id = world.get_block(self.x, self.y)
        if not self._is_interactive_block(block_id):
            return ActionExecutionResult(
                ActionResult.INVALID,
                f"Block {block_id} is not interactive"
            )
        
        return ActionExecutionResult(ActionResult.SUCCESS, "Interaction validated")
    
    def execute(self, world, player_state) -> ActionExecutionResult:
        """Execute the interaction action."""
        try:
            block_id = world.get_block(self.x, self.y)
            
            # Handle different interaction types
            result_data = {
                'position': (self.x, self.y),
                'block_id': block_id,
                'interaction_type': self.interaction_type
            }
            
            if self._is_chest(block_id):
                # Open chest inventory
                result_data['action'] = 'open_chest'
                message = "Chest opened"
                
            elif self._is_furnace(block_id):
                # Open furnace interface
                result_data['action'] = 'open_furnace'
                message = "Furnace opened"
                
            elif self._is_door(block_id):
                # Toggle door state
                result_data['action'] = 'toggle_door'
                message = "Door toggled"
                
            else:
                # Generic interaction
                result_data['action'] = 'generic_interact'
                message = f"Interacted with block {block_id}"
            
            log_debug(f"Player {self.player_id} interacted with block {block_id} at ({self.x}, {self.y})")
            
            return ActionExecutionResult(
                ActionResult.SUCCESS,
                message,
                result_data
            )
            
        except Exception as e:
            return ActionExecutionResult(
                ActionResult.FAILED,
                f"Interaction failed: {e}"
            )
    
    def _is_interactive_block(self, block_id: int) -> bool:
        """Check if a block can be interacted with."""
        # Define interactive block IDs
        interactive_blocks = {3, 4, 5}  # Example: chest, furnace, door
        return block_id in interactive_blocks
    
    def _is_chest(self, block_id: int) -> bool:
        """Check if block is a chest."""
        return block_id == 3  # Example chest ID
    
    def _is_furnace(self, block_id: int) -> bool:
        """Check if block is a furnace."""
        return block_id == 4  # Example furnace ID
    
    def _is_door(self, block_id: int) -> bool:
        """Check if block is a door."""
        return block_id == 5  # Example door ID
    
    def get_serializable_data(self) -> Dict[str, Any]:
        """Get serializable representation."""
        data = super().get_serializable_data()
        data.update({
            'x': self.x,
            'y': self.y,
            'interaction_type': self.interaction_type
        })
        return data
    
    @classmethod
    def from_serializable_data(cls, data: Dict[str, Any]):
        """Create action from serialized data."""
        return cls(
            player_id=data['player_id'],
            x=data['x'],
            y=data['y'],
            interaction_type=data['interaction_type'],
            timestamp=data['timestamp'],
            action_id=data['action_id']
        )


class PlantSeedAction(BaseAction):
    """
    Action for planting seeds (farming).
    """
    
    def __init__(self, player_id: str, x: int, y: int, seed_type: str,
                 timestamp: float = None, action_id: str = None):
        """Initialize seed planting action."""
        super().__init__(player_id, timestamp, action_id)
        
        self.x = x
        self.y = y
        self.seed_type = seed_type
        
        self.requires_validation = True
        self.cooldown_seconds = 0.5
        self.cost_resources = {seed_type: 1}
    
    def get_action_type(self) -> str:
        """Get the action type identifier."""
        return "plant_seed"
    
    def validate(self, world, player_state) -> ActionExecutionResult:
        """Validate the seed planting action."""
        if not player_state:
            return ActionExecutionResult(ActionResult.INVALID, "Player not found")
        
        # Check reach
        player_x, player_y = player_state.x, player_state.y
        plant_x = self.x * TILESIZE + TILESIZE // 2
        plant_y = self.y * TILESIZE + TILESIZE // 2
        
        distance = math.sqrt((player_x - plant_x)**2 + (player_y - plant_y)**2)
        
        if distance > MELEEREACH:
            return ActionExecutionResult(
                ActionResult.INVALID,
                f"Planting location too far away: {distance:.1f} > {MELEEREACH}"
            )
        
        # Check if soil is suitable (must be farmland or dirt)
        block_id = world.get_block(self.x, self.y)
        if not self._is_farmable_soil(block_id):
            return ActionExecutionResult(
                ActionResult.INVALID,
                f"Cannot plant on block type {block_id}"
            )
        
        return ActionExecutionResult(ActionResult.SUCCESS, "Seed planting validated")
    
    def execute(self, world, player_state) -> ActionExecutionResult:
        """Execute the seed planting action."""
        try:
            # Remove seed from inventory
            if player_state.remove_item(self.seed_type, 1) == 0:
                return ActionExecutionResult(
                    ActionResult.INSUFFICIENT_RESOURCES,
                    f"No {self.seed_type} in inventory"
                )
            
            # Plant the seed (convert to crop block)
            crop_block_id = self._get_crop_block_id(self.seed_type)
            world.set_block(self.x, self.y, crop_block_id, self.player_id)
            
            log_debug(f"Player {self.player_id} planted {self.seed_type} at ({self.x}, {self.y})")
            
            return ActionExecutionResult(
                ActionResult.SUCCESS,
                "Seed planted successfully",
                {
                    'position': (self.x, self.y),
                    'seed_type': self.seed_type,
                    'crop_block_id': crop_block_id
                }
            )
            
        except Exception as e:
            return ActionExecutionResult(
                ActionResult.FAILED,
                f"Seed planting failed: {e}"
            )
    
    def _is_farmable_soil(self, block_id: int) -> bool:
        """Check if block can be farmed on."""
        farmable_blocks = {1, 2}  # Example: dirt, farmland
        return block_id in farmable_blocks
    
    def _get_crop_block_id(self, seed_type: str) -> int:
        """Get the block ID for the crop."""
        crop_mapping = {
            'wheat_seed': 10,
            'carrot_seed': 11,
            'potato_seed': 12
        }
        return crop_mapping.get(seed_type, 10)  # Default to wheat
    
    def get_serializable_data(self) -> Dict[str, Any]:
        """Get serializable representation."""
        data = super().get_serializable_data()
        data.update({
            'x': self.x,
            'y': self.y,
            'seed_type': self.seed_type
        })
        return data
    
    @classmethod
    def from_serializable_data(cls, data: Dict[str, Any]):
        """Create action from serialized data."""
        return cls(
            player_id=data['player_id'],
            x=data['x'],
            y=data['y'],
            seed_type=data['seed_type'],
            timestamp=data['timestamp'],
            action_id=data['action_id']
        )
