"""
Base Action System for PyCraft 2D

Defines the base action classes and interfaces for the command pattern
implementation that enables server-side action validation and execution.
"""

import time
import uuid
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from enum import Enum
from dataclasses import dataclass

from game.utils.logger import log_debug, log_warning, log_error


class ActionResult(Enum):
    """Results of action execution."""
    SUCCESS = "success"
    FAILED = "failed"
    INVALID = "invalid"
    UNAUTHORIZED = "unauthorized"
    COOLDOWN = "cooldown"
    INSUFFICIENT_RESOURCES = "insufficient_resources"


@dataclass
class ActionExecutionResult:
    """Result of an action execution."""
    result: ActionResult
    message: str = ""
    data: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.data is None:
            self.data = {}
    
    def is_success(self) -> bool:
        """Check if the action was successful."""
        return self.result == ActionResult.SUCCESS
    
    def is_failed(self) -> bool:
        """Check if the action failed."""
        return self.result != ActionResult.SUCCESS


class BaseAction(ABC):
    """
    Base class for all game actions.
    
    Actions represent player intentions (move, attack, place block, etc.)
    and can be executed on both client and server sides.
    """
    
    def __init__(self, player_id: str, timestamp: float = None, action_id: str = None):
        """
        Initialize the base action.
        
        Args:
            player_id: ID of the player performing the action
            timestamp: When the action was created (defaults to current time)
            action_id: Unique identifier for this action (auto-generated if None)
        """
        self.player_id = player_id
        self.timestamp = timestamp or time.time()
        self.action_id = action_id or str(uuid.uuid4())
        self.executed = False
        self.execution_result: Optional[ActionExecutionResult] = None
        
        # Validation metadata
        self.requires_validation = True
        self.cooldown_seconds = 0.0
        self.cost_resources: Dict[str, int] = {}
        
    @abstractmethod
    def get_action_type(self) -> str:
        """Get the string identifier for this action type."""
        pass
    
    @abstractmethod
    def validate(self, world, player_state) -> ActionExecutionResult:
        """
        Validate if this action can be executed.
        
        Args:
            world: The game world instance
            player_state: The player's current state
            
        Returns:
            ActionExecutionResult indicating if validation passed
        """
        pass
    
    @abstractmethod
    def execute(self, world, player_state) -> ActionExecutionResult:
        """
        Execute this action on the game world.
        
        Args:
            world: The game world instance
            player_state: The player's current state
            
        Returns:
            ActionExecutionResult indicating execution outcome
        """
        pass
    
    def can_execute(self, world, player_state) -> bool:
        """
        Quick check if action can be executed (without side effects).
        
        Args:
            world: The game world instance
            player_state: The player's current state
            
        Returns:
            True if action can be executed
        """
        if self.executed and not self.allows_multiple_execution():
            return False
        
        if not self.requires_validation:
            return True
        
        validation_result = self.validate(world, player_state)
        return validation_result.is_success()
    
    def allows_multiple_execution(self) -> bool:
        """Check if this action can be executed multiple times."""
        return False
    
    def get_serializable_data(self) -> Dict[str, Any]:
        """
        Get serializable representation of this action.
        
        Returns:
            Dictionary containing action data for network transmission
        """
        return {
            'action_type': self.get_action_type(),
            'action_id': self.action_id,
            'player_id': self.player_id,
            'timestamp': self.timestamp,
            'executed': self.executed
        }
    
    @classmethod
    def from_serializable_data(cls, data: Dict[str, Any]):
        """
        Create action instance from serialized data.
        
        Args:
            data: Serialized action data
            
        Returns:
            Action instance
        """
        return cls(
            player_id=data['player_id'],
            timestamp=data['timestamp'],
            action_id=data['action_id']
        )
    
    def __str__(self) -> str:
        """String representation of the action."""
        return f"{self.get_action_type()}({self.action_id[:8]}...)"
    
    def __repr__(self) -> str:
        """Detailed string representation."""
        return (f"{self.__class__.__name__}(action_id='{self.action_id}', "
                f"player_id='{self.player_id}', timestamp={self.timestamp})")


class ActionValidator:
    """
    Validates actions against game rules and player permissions.
    """
    
    def __init__(self):
        """Initialize the action validator."""
        self.validation_rules = {}
        self.player_cooldowns: Dict[str, Dict[str, float]] = {}
        
    def add_validation_rule(self, action_type: str, rule_func):
        """
        Add a custom validation rule for an action type.
        
        Args:
            action_type: The action type to validate
            rule_func: Function that takes (action, world, player_state) and returns bool
        """
        if action_type not in self.validation_rules:
            self.validation_rules[action_type] = []
        self.validation_rules[action_type].append(rule_func)
    
    def validate_action(self, action: BaseAction, world, player_state) -> ActionExecutionResult:
        """
        Validate an action using built-in and custom rules.
        
        Args:
            action: The action to validate
            world: The game world
            player_state: The player's state
            
        Returns:
            ActionExecutionResult with validation outcome
        """
        action_type = action.get_action_type()
        
        # Check cooldown
        if self._is_on_cooldown(action.player_id, action_type):
            remaining = self._get_cooldown_remaining(action.player_id, action_type)
            return ActionExecutionResult(
                ActionResult.COOLDOWN,
                f"Action on cooldown for {remaining:.1f} more seconds"
            )
        
        # Check resource costs
        if not self._check_resource_costs(action, player_state):
            return ActionExecutionResult(
                ActionResult.INSUFFICIENT_RESOURCES,
                "Insufficient resources for this action"
            )
        
        # Run action's own validation
        validation_result = action.validate(world, player_state)
        if not validation_result.is_success():
            return validation_result
        
        # Run custom validation rules
        for rule_func in self.validation_rules.get(action_type, []):
            try:
                if not rule_func(action, world, player_state):
                    return ActionExecutionResult(
                        ActionResult.INVALID,
                        f"Action failed custom validation rule"
                    )
            except Exception as e:
                log_error(f"Validation rule error for {action_type}: {e}")
                return ActionExecutionResult(
                    ActionResult.FAILED,
                    f"Validation error: {e}"
                )
        
        return ActionExecutionResult(ActionResult.SUCCESS, "Validation passed")
    
    def _is_on_cooldown(self, player_id: str, action_type: str) -> bool:
        """Check if player is on cooldown for an action type."""
        if player_id not in self.player_cooldowns:
            return False
        
        if action_type not in self.player_cooldowns[player_id]:
            return False
        
        last_execution = self.player_cooldowns[player_id][action_type]
        # Note: cooldown duration would be determined by action type
        cooldown_duration = 1.0  # Default 1 second cooldown
        
        return time.time() - last_execution < cooldown_duration
    
    def _get_cooldown_remaining(self, player_id: str, action_type: str) -> float:
        """Get remaining cooldown time."""
        if not self._is_on_cooldown(player_id, action_type):
            return 0.0
        
        last_execution = self.player_cooldowns[player_id][action_type]
        cooldown_duration = 1.0  # Default 1 second cooldown
        
        return cooldown_duration - (time.time() - last_execution)
    
    def _check_resource_costs(self, action: BaseAction, player_state) -> bool:
        """Check if player has sufficient resources for the action."""
        if not action.cost_resources:
            return True
        
        # Check if player has required resources
        for resource_type, required_amount in action.cost_resources.items():
            player_amount = self._get_player_resource(player_state, resource_type)
            if player_amount < required_amount:
                return False
        
        return True
    
    def _get_player_resource(self, player_state, resource_type: str) -> int:
        """Get the amount of a resource the player has."""
        # This would check player inventory, health, etc.
        if resource_type == "health":
            return player_state.health
        elif resource_type == "energy":
            # Energy system not implemented yet
            return 100
        else:
            # Check inventory for item
            total = 0
            for slot in player_state.inventory:
                if slot and slot.get('item_type') == resource_type:
                    total += slot.get('quantity', 0)
            return total
    
    def set_cooldown(self, player_id: str, action_type: str):
        """Set cooldown for a player's action type."""
        if player_id not in self.player_cooldowns:
            self.player_cooldowns[player_id] = {}
        
        self.player_cooldowns[player_id][action_type] = time.time()


class ActionHandler:
    """
    Handles the execution of actions in the game world.
    
    This class coordinates action validation and execution,
    and can be used on both client and server sides.
    """
    
    def __init__(self, is_server: bool = True):
        """
        Initialize the action handler.
        
        Args:
            is_server: Whether this handler is running on the server
        """
        self.is_server = is_server
        self.validator = ActionValidator()
        self.action_history: List[BaseAction] = []
        self.max_history_size = 1000
        
        # Statistics
        self.actions_processed = 0
        self.actions_successful = 0
        self.actions_failed = 0
        
    def process_action(self, action: BaseAction, world, player_state) -> ActionExecutionResult:
        """
        Process an action (validate and execute if valid).
        
        Args:
            action: The action to process
            world: The game world
            player_state: The player's state
            
        Returns:
            ActionExecutionResult with the outcome
        """
        self.actions_processed += 1
        
        try:
            # Server-side validation
            if self.is_server and action.requires_validation:
                validation_result = self.validator.validate_action(action, world, player_state)
                if not validation_result.is_success():
                    self.actions_failed += 1
                    log_debug(f"Action validation failed: {action} - {validation_result.message}")
                    return validation_result
            
            # Execute the action
            execution_result = action.execute(world, player_state)
            action.executed = True
            action.execution_result = execution_result
            
            if execution_result.is_success():
                self.actions_successful += 1
                
                # Set cooldown if on server
                if self.is_server and action.cooldown_seconds > 0:
                    self.validator.set_cooldown(action.player_id, action.get_action_type())
                
                log_debug(f"Action executed successfully: {action}")
            else:
                self.actions_failed += 1
                log_debug(f"Action execution failed: {action} - {execution_result.message}")
            
            # Add to history
            self._add_to_history(action)
            
            return execution_result
            
        except Exception as e:
            self.actions_failed += 1
            log_error(f"Error processing action {action}: {e}")
            return ActionExecutionResult(
                ActionResult.FAILED,
                f"Execution error: {e}"
            )
    
    def _add_to_history(self, action: BaseAction):
        """Add action to history for debugging/replay."""
        self.action_history.append(action)
        
        # Limit history size
        if len(self.action_history) > self.max_history_size:
            self.action_history = self.action_history[-self.max_history_size//2:]
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get action processing statistics."""
        total = self.actions_processed
        success_rate = (self.actions_successful / total * 100) if total > 0 else 0
        
        return {
            'actions_processed': self.actions_processed,
            'actions_successful': self.actions_successful,
            'actions_failed': self.actions_failed,
            'success_rate': success_rate,
            'history_size': len(self.action_history)
        }
    
    def get_recent_actions(self, limit: int = 10) -> List[BaseAction]:
        """Get the most recent actions from history."""
        return self.action_history[-limit:]
    
    def clear_history(self):
        """Clear the action history."""
        self.action_history.clear()


class ActionQueue:
    """
    Queue for managing actions that need to be processed.
    
    Useful for client-side action buffering and server-side processing.
    """
    
    def __init__(self, max_size: int = 100):
        """Initialize the action queue."""
        self.actions: List[BaseAction] = []
        self.max_size = max_size
        
    def enqueue(self, action: BaseAction) -> bool:
        """
        Add an action to the queue.
        
        Args:
            action: Action to add
            
        Returns:
            True if action was added, False if queue is full
        """
        if len(self.actions) >= self.max_size:
            log_warning(f"Action queue full, dropping oldest action")
            self.actions.pop(0)  # Remove oldest
        
        self.actions.append(action)
        return True
    
    def dequeue(self) -> Optional[BaseAction]:
        """
        Remove and return the next action from the queue.
        
        Returns:
            Next action or None if queue is empty
        """
        if self.actions:
            return self.actions.pop(0)
        return None
    
    def peek(self) -> Optional[BaseAction]:
        """
        Look at the next action without removing it.
        
        Returns:
            Next action or None if queue is empty
        """
        if self.actions:
            return self.actions[0]
        return None
    
    def size(self) -> int:
        """Get the current queue size."""
        return len(self.actions)
    
    def is_empty(self) -> bool:
        """Check if the queue is empty."""
        return len(self.actions) == 0
    
    def clear(self):
        """Clear all actions from the queue."""
        self.actions.clear()
    
    def get_actions_by_player(self, player_id: str) -> List[BaseAction]:
        """Get all actions in queue for a specific player."""
        return [action for action in self.actions if action.player_id == player_id]
