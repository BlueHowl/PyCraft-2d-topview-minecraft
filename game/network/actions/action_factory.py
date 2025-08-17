"""
Action Factory for PyCraft 2D

Central factory for creating and managing all action types.
Provides unified interface for action creation, validation, and execution.
"""

from typing import Dict, Any, Type, Optional, List
from enum import Enum

from .base_action import BaseAction, ActionResult, ActionExecutionResult
from .movement_actions import MoveAction, StopAction, JumpAction, TeleportAction
from .world_actions import PlaceBlockAction, BreakBlockAction, InteractAction, PlantSeedAction
from .inventory_actions import (
    MoveItemAction, CraftItemAction, DropItemAction, 
    PickupItemAction, EquipItemAction
)


class ActionType(Enum):
    """Enumeration of all available action types."""
    
    # Movement actions
    MOVE = "move"
    STOP = "stop"
    JUMP = "jump"
    TELEPORT = "teleport"
    
    # World actions
    PLACE_BLOCK = "place_block"
    BREAK_BLOCK = "break_block"
    INTERACT = "interact"
    PLANT_SEED = "plant_seed"
    
    # Inventory actions
    MOVE_ITEM = "move_item"
    CRAFT_ITEM = "craft_item"
    DROP_ITEM = "drop_item"
    PICKUP_ITEM = "pickup_item"
    EQUIP_ITEM = "equip_item"


class ActionFactory:
    """
    Factory class for creating and managing actions.
    """
    
    def __init__(self):
        """Initialize the action factory."""
        self._action_classes: Dict[str, Type[BaseAction]] = {
            # Movement actions
            ActionType.MOVE.value: MoveAction,
            ActionType.STOP.value: StopAction,
            ActionType.JUMP.value: JumpAction,
            ActionType.TELEPORT.value: TeleportAction,
            
            # World actions
            ActionType.PLACE_BLOCK.value: PlaceBlockAction,
            ActionType.BREAK_BLOCK.value: BreakBlockAction,
            ActionType.INTERACT.value: InteractAction,
            ActionType.PLANT_SEED.value: PlantSeedAction,
            
            # Inventory actions
            ActionType.MOVE_ITEM.value: MoveItemAction,
            ActionType.CRAFT_ITEM.value: CraftItemAction,
            ActionType.DROP_ITEM.value: DropItemAction,
            ActionType.PICKUP_ITEM.value: PickupItemAction,
            ActionType.EQUIP_ITEM.value: EquipItemAction,
        }
        
        self._action_priorities: Dict[str, int] = {
            # High priority (immediate response needed)
            ActionType.MOVE.value: 1,
            ActionType.STOP.value: 1,
            ActionType.JUMP.value: 1,
            
            # Medium priority (game actions)
            ActionType.PLACE_BLOCK.value: 2,
            ActionType.BREAK_BLOCK.value: 2,
            ActionType.INTERACT.value: 2,
            ActionType.PICKUP_ITEM.value: 2,
            
            # Lower priority (inventory/crafting)
            ActionType.MOVE_ITEM.value: 3,
            ActionType.CRAFT_ITEM.value: 3,
            ActionType.DROP_ITEM.value: 3,
            ActionType.EQUIP_ITEM.value: 3,
            
            # Lowest priority (special actions)
            ActionType.TELEPORT.value: 4,
            ActionType.PLANT_SEED.value: 4,
        }
    
    def create_action(self, action_type: str, **kwargs) -> Optional[BaseAction]:
        """
        Create an action instance.
        
        Args:
            action_type: Type of action to create
            **kwargs: Action-specific parameters
            
        Returns:
            Action instance or None if invalid type
        """
        action_class = self._action_classes.get(action_type)
        if not action_class:
            return None
        
        try:
            return action_class(**kwargs)
        except Exception:
            return None
    
    def create_action_from_data(self, data: Dict[str, Any]) -> Optional[BaseAction]:
        """
        Create an action from serialized data.
        
        Args:
            data: Serialized action data
            
        Returns:
            Action instance or None if invalid
        """
        action_type = data.get('action_type')
        if not action_type:
            return None
        
        action_class = self._action_classes.get(action_type)
        if not action_class:
            return None
        
        try:
            return action_class.from_serializable_data(data)
        except Exception:
            return None
    
    def get_action_priority(self, action_type: str) -> int:
        """
        Get priority level for an action type.
        
        Args:
            action_type: Type of action
            
        Returns:
            Priority level (1 = highest, higher numbers = lower priority)
        """
        return self._action_priorities.get(action_type, 999)
    
    def get_all_action_types(self) -> List[str]:
        """Get list of all supported action types."""
        return list(self._action_classes.keys())
    
    def is_valid_action_type(self, action_type: str) -> bool:
        """Check if an action type is valid."""
        return action_type in self._action_classes
    
    def get_action_class(self, action_type: str) -> Optional[Type[BaseAction]]:
        """Get the class for an action type."""
        return self._action_classes.get(action_type)


class ActionRegistry:
    """
    Registry for tracking active actions and their states.
    """
    
    def __init__(self):
        """Initialize the action registry."""
        self._active_actions: Dict[str, BaseAction] = {}
        self._completed_actions: Dict[str, ActionExecutionResult] = {}
        self._failed_actions: Dict[str, ActionExecutionResult] = {}
        self._action_history: List[str] = []
        
        # Limits
        self.max_history_size = 1000
        self.max_completed_size = 100
        self.max_failed_size = 100
    
    def register_action(self, action: BaseAction):
        """Register a new action."""
        self._active_actions[action.action_id] = action
        self._action_history.append(action.action_id)
        
        # Cleanup old history
        if len(self._action_history) > self.max_history_size:
            self._action_history = self._action_history[-self.max_history_size:]
    
    def complete_action(self, action_id: str, result: ActionExecutionResult):
        """Mark an action as completed."""
        if action_id in self._active_actions:
            del self._active_actions[action_id]
        
        if result.result == ActionResult.SUCCESS:
            self._completed_actions[action_id] = result
            
            # Cleanup old completed actions
            if len(self._completed_actions) > self.max_completed_size:
                oldest_key = next(iter(self._completed_actions))
                del self._completed_actions[oldest_key]
        else:
            self._failed_actions[action_id] = result
            
            # Cleanup old failed actions
            if len(self._failed_actions) > self.max_failed_size:
                oldest_key = next(iter(self._failed_actions))
                del self._failed_actions[oldest_key]
    
    def get_action(self, action_id: str) -> Optional[BaseAction]:
        """Get an active action by ID."""
        return self._active_actions.get(action_id)
    
    def get_active_actions_for_player(self, player_id: str) -> List[BaseAction]:
        """Get all active actions for a player."""
        return [action for action in self._active_actions.values() 
                if action.player_id == player_id]
    
    def get_action_result(self, action_id: str) -> Optional[ActionExecutionResult]:
        """Get the result of a completed action."""
        return (self._completed_actions.get(action_id) or 
                self._failed_actions.get(action_id))
    
    def cancel_action(self, action_id: str) -> bool:
        """Cancel an active action."""
        if action_id in self._active_actions:
            del self._active_actions[action_id]
            return True
        return False
    
    def cancel_player_actions(self, player_id: str) -> int:
        """Cancel all actions for a player."""
        cancelled = 0
        to_remove = []
        
        for action_id, action in self._active_actions.items():
            if action.player_id == player_id:
                to_remove.append(action_id)
                cancelled += 1
        
        for action_id in to_remove:
            del self._active_actions[action_id]
        
        return cancelled
    
    def get_stats(self) -> Dict[str, Any]:
        """Get registry statistics."""
        return {
            'active_actions': len(self._active_actions),
            'completed_actions': len(self._completed_actions),
            'failed_actions': len(self._failed_actions),
            'total_history': len(self._action_history)
        }
    
    def cleanup_old_results(self, max_age_seconds: float = 300):
        """Remove old completed/failed action results."""
        import time
        current_time = time.time()
        
        # This would need timestamps on results in a real implementation
        # For now, just limit by count (already implemented above)
        pass


# Global instances
action_factory = ActionFactory()
action_registry = ActionRegistry()


def create_action(action_type: str, **kwargs) -> Optional[BaseAction]:
    """Convenience function to create an action."""
    return action_factory.create_action(action_type, **kwargs)


def create_action_from_data(data: Dict[str, Any]) -> Optional[BaseAction]:
    """Convenience function to create action from data."""
    return action_factory.create_action_from_data(data)


def register_action(action: BaseAction):
    """Convenience function to register an action."""
    action_registry.register_action(action)


def complete_action(action_id: str, result: ActionExecutionResult):
    """Convenience function to complete an action."""
    action_registry.complete_action(action_id, result)
