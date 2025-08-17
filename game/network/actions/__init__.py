"""
Actions Module for PyCraft 2D Networking

This module provides a comprehensive action/command system for client-server
communication. Actions represent all player inputs and game state changes
that need to be validated and synchronized between clients and server.

Key Components:
- BaseAction: Abstract base class for all actions
- ActionResult: Enumeration of action execution outcomes
- ActionExecutionResult: Container for action execution details
- ActionValidator: Validation logic for actions
- ActionHandler: Action processing and execution
- ActionQueue: Buffering and ordering of actions
- ActionFactory: Central factory for creating actions
- ActionRegistry: Tracking active and completed actions

Action Types:
- Movement Actions: Player movement, jumping, teleportation
- World Actions: Block placement/breaking, interactions
- Inventory Actions: Item management, crafting, equipment

Usage:
    from game.network.actions import (
        create_action, register_action, complete_action,
        ActionType, ActionResult
    )
    
    # Create a movement action
    move_action = create_action(
        ActionType.MOVE.value,
        player_id="player_123",
        target_x=100,
        target_y=200,
        velocity_x=50,
        velocity_y=0
    )
    
    # Register for tracking
    register_action(move_action)
    
    # Validate and execute
    result = move_action.validate(world, player_state)
    if result.result == ActionResult.SUCCESS:
        execution_result = move_action.execute(world, player_state)
        complete_action(move_action.action_id, execution_result)
"""

from .base_action import (
    BaseAction,
    ActionResult, 
    ActionExecutionResult,
    ActionValidator,
    ActionHandler,
    ActionQueue
)

from .movement_actions import (
    MoveAction,
    StopAction, 
    JumpAction,
    TeleportAction
)

from .world_actions import (
    PlaceBlockAction,
    BreakBlockAction,
    InteractAction,
    PlantSeedAction
)

from .inventory_actions import (
    MoveItemAction,
    CraftItemAction,
    DropItemAction,
    PickupItemAction,
    EquipItemAction
)

from .action_factory import (
    ActionType,
    ActionFactory,
    ActionRegistry,
    action_factory,
    action_registry,
    create_action,
    create_action_from_data,
    register_action,
    complete_action
)


__all__ = [
    # Base classes
    'BaseAction',
    'ActionResult',
    'ActionExecutionResult', 
    'ActionValidator',
    'ActionHandler',
    'ActionQueue',
    
    # Movement actions
    'MoveAction',
    'StopAction',
    'JumpAction', 
    'TeleportAction',
    
    # World actions
    'PlaceBlockAction',
    'BreakBlockAction',
    'InteractAction',
    'PlantSeedAction',
    
    # Inventory actions
    'MoveItemAction',
    'CraftItemAction',
    'DropItemAction',
    'PickupItemAction',
    'EquipItemAction',
    
    # Factory and registry
    'ActionType',
    'ActionFactory',
    'ActionRegistry',
    'action_factory',
    'action_registry',
    
    # Convenience functions
    'create_action',
    'create_action_from_data', 
    'register_action',
    'complete_action'
]


def get_action_system_info():
    """
    Get information about the action system.
    
    Returns:
        Dict containing system information
    """
    return {
        'total_action_types': len(action_factory.get_all_action_types()),
        'supported_actions': action_factory.get_all_action_types(),
        'registry_stats': action_registry.get_stats(),
        'version': '1.0.0'
    }
