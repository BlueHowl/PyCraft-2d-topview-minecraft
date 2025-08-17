"""
Movement Actions for PyCraft 2D

Handles all player movement-related actions including walking, running, and stopping.
"""

import math
from typing import Dict, Any

from .base_action import BaseAction, ActionResult, ActionExecutionResult
from game.config.settings import WALK_SPEED, TILESIZE
from game.utils.logger import log_debug


class MoveAction(BaseAction):
    """
    Action for player movement.
    
    This action handles player position updates with velocity and collision detection.
    """
    
    def __init__(self, player_id: str, direction: str, velocity_x: float, velocity_y: float,
                 timestamp: float = None, action_id: str = None):
        """
        Initialize movement action.
        
        Args:
            player_id: ID of the player moving
            direction: Direction string ('up', 'down', 'left', 'right', etc.)
            velocity_x: X velocity component
            velocity_y: Y velocity component
            timestamp: When the action was created
            action_id: Unique action identifier
        """
        super().__init__(player_id, timestamp, action_id)
        
        self.direction = direction
        self.velocity_x = velocity_x
        self.velocity_y = velocity_y
        
        # Movement actions can be executed multiple times
        self.requires_validation = False  # Movement is validated differently
        self.cooldown_seconds = 0.0  # No cooldown for movement
        
    def get_action_type(self) -> str:
        """Get the action type identifier."""
        return "move"
    
    def validate(self, world, player_state) -> ActionExecutionResult:
        """
        Validate the movement action.
        
        Args:
            world: The game world
            player_state: Current player state
            
        Returns:
            ActionExecutionResult with validation outcome
        """
        # Check if player exists
        if not player_state:
            return ActionExecutionResult(
                ActionResult.INVALID,
                "Player not found"
            )
        
        # Check velocity bounds (prevent cheating)
        max_speed = WALK_SPEED * 2  # Allow some buffer for running/sprinting
        speed = math.sqrt(self.velocity_x**2 + self.velocity_y**2)
        
        if speed > max_speed:
            return ActionExecutionResult(
                ActionResult.INVALID,
                f"Speed too high: {speed:.2f} > {max_speed:.2f}"
            )
        
        # Basic bounds checking (prevent teleporting)
        new_x = player_state.x + self.velocity_x * 0.1  # Approximate next position
        new_y = player_state.y + self.velocity_y * 0.1
        
        # World bounds (if any)
        world_size = getattr(world, 'world_size', 1000) * TILESIZE
        if not (-world_size <= new_x <= world_size and -world_size <= new_y <= world_size):
            return ActionExecutionResult(
                ActionResult.INVALID,
                "Movement would exceed world bounds"
            )
        
        return ActionExecutionResult(ActionResult.SUCCESS, "Movement validated")
    
    def execute(self, world, player_state) -> ActionExecutionResult:
        """
        Execute the movement action.
        
        Args:
            world: The game world
            player_state: Current player state
            
        Returns:
            ActionExecutionResult with execution outcome
        """
        try:
            # Update player position and velocity
            old_x, old_y = player_state.x, player_state.y
            
            player_state.vel_x = self.velocity_x
            player_state.vel_y = self.velocity_y
            player_state.direction = self.direction
            
            # Note: Actual position update happens in the world update loop
            # This action just sets the velocity and direction
            
            log_debug(f"Player {self.player_id} velocity set to ({self.velocity_x:.2f}, {self.velocity_y:.2f})")
            
            return ActionExecutionResult(
                ActionResult.SUCCESS,
                "Movement executed",
                {
                    'old_position': (old_x, old_y),
                    'velocity': (self.velocity_x, self.velocity_y),
                    'direction': self.direction
                }
            )
            
        except Exception as e:
            return ActionExecutionResult(
                ActionResult.FAILED,
                f"Movement execution failed: {e}"
            )
    
    def allows_multiple_execution(self) -> bool:
        """Movement actions can be executed multiple times."""
        return True
    
    def get_serializable_data(self) -> Dict[str, Any]:
        """Get serializable representation."""
        data = super().get_serializable_data()
        data.update({
            'direction': self.direction,
            'velocity_x': self.velocity_x,
            'velocity_y': self.velocity_y
        })
        return data
    
    @classmethod
    def from_serializable_data(cls, data: Dict[str, Any]):
        """Create action from serialized data."""
        return cls(
            player_id=data['player_id'],
            direction=data['direction'],
            velocity_x=data['velocity_x'],
            velocity_y=data['velocity_y'],
            timestamp=data['timestamp'],
            action_id=data['action_id']
        )


class StopAction(BaseAction):
    """
    Action for stopping player movement.
    """
    
    def __init__(self, player_id: str, timestamp: float = None, action_id: str = None):
        """Initialize stop action."""
        super().__init__(player_id, timestamp, action_id)
        self.requires_validation = False
        self.cooldown_seconds = 0.0
    
    def get_action_type(self) -> str:
        """Get the action type identifier."""
        return "stop"
    
    def validate(self, world, player_state) -> ActionExecutionResult:
        """Validate the stop action."""
        if not player_state:
            return ActionExecutionResult(ActionResult.INVALID, "Player not found")
        return ActionExecutionResult(ActionResult.SUCCESS, "Stop validated")
    
    def execute(self, world, player_state) -> ActionExecutionResult:
        """Execute the stop action."""
        try:
            player_state.vel_x = 0.0
            player_state.vel_y = 0.0
            
            log_debug(f"Player {self.player_id} stopped")
            
            return ActionExecutionResult(
                ActionResult.SUCCESS,
                "Stop executed",
                {'velocity': (0.0, 0.0)}
            )
            
        except Exception as e:
            return ActionExecutionResult(
                ActionResult.FAILED,
                f"Stop execution failed: {e}"
            )
    
    def allows_multiple_execution(self) -> bool:
        """Stop actions can be executed multiple times."""
        return True


class JumpAction(BaseAction):
    """
    Action for player jumping (if jump mechanics are implemented).
    """
    
    def __init__(self, player_id: str, jump_strength: float = 1.0,
                 timestamp: float = None, action_id: str = None):
        """Initialize jump action."""
        super().__init__(player_id, timestamp, action_id)
        
        self.jump_strength = jump_strength
        self.requires_validation = True
        self.cooldown_seconds = 0.5  # Half second cooldown between jumps
        self.cost_resources = {'energy': 5}  # Jumping costs energy
    
    def get_action_type(self) -> str:
        """Get the action type identifier."""
        return "jump"
    
    def validate(self, world, player_state) -> ActionExecutionResult:
        """Validate the jump action."""
        if not player_state:
            return ActionExecutionResult(ActionResult.INVALID, "Player not found")
        
        # Check if player is on ground (simplified check)
        # In a real implementation, this would check collision with ground
        if hasattr(player_state, 'is_on_ground') and not player_state.is_on_ground:
            return ActionExecutionResult(
                ActionResult.INVALID,
                "Cannot jump while in air"
            )
        
        # Check jump strength bounds
        if not (0.1 <= self.jump_strength <= 2.0):
            return ActionExecutionResult(
                ActionResult.INVALID,
                f"Invalid jump strength: {self.jump_strength}"
            )
        
        return ActionExecutionResult(ActionResult.SUCCESS, "Jump validated")
    
    def execute(self, world, player_state) -> ActionExecutionResult:
        """Execute the jump action."""
        try:
            # Add vertical velocity for jump
            # In a real implementation, this would affect Y velocity
            jump_velocity = self.jump_strength * 100  # Scale factor
            
            # For now, just log the jump (no actual physics implemented)
            log_debug(f"Player {self.player_id} jumped with strength {self.jump_strength}")
            
            return ActionExecutionResult(
                ActionResult.SUCCESS,
                "Jump executed",
                {
                    'jump_strength': self.jump_strength,
                    'jump_velocity': jump_velocity
                }
            )
            
        except Exception as e:
            return ActionExecutionResult(
                ActionResult.FAILED,
                f"Jump execution failed: {e}"
            )
    
    def get_serializable_data(self) -> Dict[str, Any]:
        """Get serializable representation."""
        data = super().get_serializable_data()
        data['jump_strength'] = self.jump_strength
        return data
    
    @classmethod
    def from_serializable_data(cls, data: Dict[str, Any]):
        """Create action from serialized data."""
        return cls(
            player_id=data['player_id'],
            jump_strength=data['jump_strength'],
            timestamp=data['timestamp'],
            action_id=data['action_id']
        )


class TeleportAction(BaseAction):
    """
    Action for teleporting (admin/debug action).
    """
    
    def __init__(self, player_id: str, target_x: float, target_y: float,
                 timestamp: float = None, action_id: str = None):
        """Initialize teleport action."""
        super().__init__(player_id, timestamp, action_id)
        
        self.target_x = target_x
        self.target_y = target_y
        self.requires_validation = True
        self.cooldown_seconds = 5.0  # Long cooldown for teleport
    
    def get_action_type(self) -> str:
        """Get the action type identifier."""
        return "teleport"
    
    def validate(self, world, player_state) -> ActionExecutionResult:
        """Validate the teleport action."""
        if not player_state:
            return ActionExecutionResult(ActionResult.INVALID, "Player not found")
        
        # Check if player has teleport permission (admin only)
        if not getattr(player_state, 'is_admin', False):
            return ActionExecutionResult(
                ActionResult.UNAUTHORIZED,
                "Teleport requires admin permissions"
            )
        
        # Check target location bounds
        world_size = getattr(world, 'world_size', 1000) * TILESIZE
        if not (-world_size <= self.target_x <= world_size and -world_size <= self.target_y <= world_size):
            return ActionExecutionResult(
                ActionResult.INVALID,
                "Teleport target out of world bounds"
            )
        
        return ActionExecutionResult(ActionResult.SUCCESS, "Teleport validated")
    
    def execute(self, world, player_state) -> ActionExecutionResult:
        """Execute the teleport action."""
        try:
            old_x, old_y = player_state.x, player_state.y
            
            # Set new position
            player_state.set_position(self.target_x, self.target_y)
            
            # Stop movement
            player_state.vel_x = 0.0
            player_state.vel_y = 0.0
            
            log_debug(f"Player {self.player_id} teleported from ({old_x:.2f}, {old_y:.2f}) to ({self.target_x:.2f}, {self.target_y:.2f})")
            
            return ActionExecutionResult(
                ActionResult.SUCCESS,
                "Teleport executed",
                {
                    'old_position': (old_x, old_y),
                    'new_position': (self.target_x, self.target_y)
                }
            )
            
        except Exception as e:
            return ActionExecutionResult(
                ActionResult.FAILED,
                f"Teleport execution failed: {e}"
            )
    
    def get_serializable_data(self) -> Dict[str, Any]:
        """Get serializable representation."""
        data = super().get_serializable_data()
        data.update({
            'target_x': self.target_x,
            'target_y': self.target_y
        })
        return data
    
    @classmethod
    def from_serializable_data(cls, data: Dict[str, Any]):
        """Create action from serialized data."""
        return cls(
            player_id=data['player_id'],
            target_x=data['target_x'],
            target_y=data['target_y'],
            timestamp=data['timestamp'],
            action_id=data['action_id']
        )
