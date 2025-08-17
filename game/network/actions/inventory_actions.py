"""
Inventory Actions for PyCraft 2D

Handles all inventory-related actions including item management,
crafting, trading, and equipment management.
"""

from typing import Dict, Any, List, Optional

from .base_action import BaseAction, ActionResult, ActionExecutionResult
from game.utils.logger import log_debug


class MoveItemAction(BaseAction):
    """
    Action for moving items within or between inventories.
    """
    
    def __init__(self, player_id: str, source_type: str, source_slot: int,
                 dest_type: str, dest_slot: int, quantity: int = None,
                 timestamp: float = None, action_id: str = None):
        """
        Initialize item movement action.
        
        Args:
            player_id: ID of the player performing the action
            source_type: Source inventory type ('player', 'chest', 'furnace')
            source_slot: Source slot index
            dest_type: Destination inventory type
            dest_slot: Destination slot index
            quantity: Amount to move (None = all)
            timestamp: When the action was created
            action_id: Unique action identifier
        """
        super().__init__(player_id, timestamp, action_id)
        
        self.source_type = source_type
        self.source_slot = source_slot
        self.dest_type = dest_type
        self.dest_slot = dest_slot
        self.quantity = quantity
        
        self.requires_validation = True
        self.cooldown_seconds = 0.05  # Prevent inventory spam
    
    def get_action_type(self) -> str:
        """Get the action type identifier."""
        return "move_item"
    
    def validate(self, world, player_state) -> ActionExecutionResult:
        """Validate the item movement action."""
        if not player_state:
            return ActionExecutionResult(ActionResult.INVALID, "Player not found")
        
        # Get source and destination inventories
        source_inv = self._get_inventory(world, player_state, self.source_type)
        dest_inv = self._get_inventory(world, player_state, self.dest_type)
        
        if not source_inv or not dest_inv:
            return ActionExecutionResult(
                ActionResult.INVALID,
                "Invalid inventory type"
            )
        
        # Check slot bounds
        if (self.source_slot < 0 or self.source_slot >= len(source_inv) or
            self.dest_slot < 0 or self.dest_slot >= len(dest_inv)):
            return ActionExecutionResult(
                ActionResult.INVALID,
                "Slot index out of bounds"
            )
        
        # Check if source slot has items
        source_item = source_inv[self.source_slot]
        if not source_item or source_item.get('quantity', 0) <= 0:
            return ActionExecutionResult(
                ActionResult.INVALID,
                "Source slot is empty"
            )
        
        # Validate quantity
        available_quantity = source_item.get('quantity', 0)
        move_quantity = self.quantity if self.quantity is not None else available_quantity
        
        if move_quantity <= 0 or move_quantity > available_quantity:
            return ActionExecutionResult(
                ActionResult.INVALID,
                f"Invalid quantity: {move_quantity} (available: {available_quantity})"
            )
        
        # Check if destination can accept the items
        dest_item = dest_inv[self.dest_slot]
        if dest_item and dest_item.get('item_type') != source_item.get('item_type'):
            return ActionExecutionResult(
                ActionResult.INVALID,
                "Cannot stack different item types"
            )
        
        return ActionExecutionResult(ActionResult.SUCCESS, "Item movement validated")
    
    def execute(self, world, player_state) -> ActionExecutionResult:
        """Execute the item movement action."""
        try:
            source_inv = self._get_inventory(world, player_state, self.source_type)
            dest_inv = self._get_inventory(world, player_state, self.dest_type)
            
            source_item = source_inv[self.source_slot]
            dest_item = dest_inv[self.dest_slot]
            
            move_quantity = self.quantity if self.quantity is not None else source_item['quantity']
            
            # Perform the move
            if dest_item and dest_item.get('item_type') == source_item.get('item_type'):
                # Stack items
                dest_item['quantity'] += move_quantity
            else:
                # Move to empty slot or swap
                if dest_item:
                    # Swap items
                    source_inv[self.source_slot] = dest_item
                else:
                    # Clear source if moving all
                    source_inv[self.source_slot] = None
                
                # Set destination
                dest_inv[self.dest_slot] = {
                    'item_type': source_item['item_type'],
                    'quantity': move_quantity
                }
            
            # Update source quantity
            source_item['quantity'] -= move_quantity
            if source_item['quantity'] <= 0:
                source_inv[self.source_slot] = None
            
            log_debug(f"Player {self.player_id} moved {move_quantity} {source_item['item_type']} "
                     f"from {self.source_type}[{self.source_slot}] to {self.dest_type}[{self.dest_slot}]")
            
            return ActionExecutionResult(
                ActionResult.SUCCESS,
                "Item moved successfully",
                {
                    'source_type': self.source_type,
                    'source_slot': self.source_slot,
                    'dest_type': self.dest_type,
                    'dest_slot': self.dest_slot,
                    'quantity': move_quantity,
                    'item_type': source_item['item_type']
                }
            )
            
        except Exception as e:
            return ActionExecutionResult(
                ActionResult.FAILED,
                f"Item movement failed: {e}"
            )
    
    def _get_inventory(self, world, player_state, inv_type: str):
        """Get inventory by type."""
        if inv_type == 'player':
            return player_state.inventory
        elif inv_type == 'chest':
            # Would need chest location info in actual implementation
            return None  # Placeholder
        elif inv_type == 'furnace':
            # Would need furnace location info in actual implementation
            return None  # Placeholder
        else:
            return None
    
    def get_serializable_data(self) -> Dict[str, Any]:
        """Get serializable representation."""
        data = super().get_serializable_data()
        data.update({
            'source_type': self.source_type,
            'source_slot': self.source_slot,
            'dest_type': self.dest_type,
            'dest_slot': self.dest_slot,
            'quantity': self.quantity
        })
        return data
    
    @classmethod
    def from_serializable_data(cls, data: Dict[str, Any]):
        """Create action from serialized data."""
        return cls(
            player_id=data['player_id'],
            source_type=data['source_type'],
            source_slot=data['source_slot'],
            dest_type=data['dest_type'],
            dest_slot=data['dest_slot'],
            quantity=data.get('quantity'),
            timestamp=data['timestamp'],
            action_id=data['action_id']
        )


class CraftItemAction(BaseAction):
    """
    Action for crafting items.
    """
    
    def __init__(self, player_id: str, recipe_id: str, quantity: int = 1,
                 timestamp: float = None, action_id: str = None):
        """Initialize crafting action."""
        super().__init__(player_id, timestamp, action_id)
        
        self.recipe_id = recipe_id
        self.quantity = quantity
        
        self.requires_validation = True
        self.cooldown_seconds = 0.2  # Prevent crafting spam
    
    def get_action_type(self) -> str:
        """Get the action type identifier."""
        return "craft_item"
    
    def validate(self, world, player_state) -> ActionExecutionResult:
        """Validate the crafting action."""
        if not player_state:
            return ActionExecutionResult(ActionResult.INVALID, "Player not found")
        
        # Get recipe details
        recipe = self._get_recipe(self.recipe_id)
        if not recipe:
            return ActionExecutionResult(
                ActionResult.INVALID,
                f"Unknown recipe: {self.recipe_id}"
            )
        
        # Check if player has required materials
        for material, required_amount in recipe['materials'].items():
            total_needed = required_amount * self.quantity
            available = self._count_item_in_inventory(player_state, material)
            
            if available < total_needed:
                return ActionExecutionResult(
                    ActionResult.INSUFFICIENT_RESOURCES,
                    f"Need {total_needed} {material}, have {available}"
                )
        
        # Check if player has inventory space for output
        output_item = recipe['output']['item_type']
        output_quantity = recipe['output']['quantity'] * self.quantity
        
        if not self._has_inventory_space(player_state, output_item, output_quantity):
            return ActionExecutionResult(
                ActionResult.INSUFFICIENT_RESOURCES,
                "Not enough inventory space"
            )
        
        return ActionExecutionResult(ActionResult.SUCCESS, "Crafting validated")
    
    def execute(self, world, player_state) -> ActionExecutionResult:
        """Execute the crafting action."""
        try:
            recipe = self._get_recipe(self.recipe_id)
            
            # Consume materials
            for material, required_amount in recipe['materials'].items():
                total_needed = required_amount * self.quantity
                consumed = player_state.remove_item(material, total_needed)
                
                if consumed < total_needed:
                    # Refund what we've consumed so far
                    player_state.add_item(material, consumed)
                    return ActionExecutionResult(
                        ActionResult.FAILED,
                        f"Failed to consume {material}"
                    )
            
            # Add crafted items
            output_item = recipe['output']['item_type']
            output_quantity = recipe['output']['quantity'] * self.quantity
            
            added = player_state.add_item(output_item, output_quantity)
            if added < output_quantity:
                # This shouldn't happen if validation passed
                return ActionExecutionResult(
                    ActionResult.FAILED,
                    "Failed to add crafted items to inventory"
                )
            
            log_debug(f"Player {self.player_id} crafted {self.quantity}x {self.recipe_id}")
            
            return ActionExecutionResult(
                ActionResult.SUCCESS,
                "Item crafted successfully",
                {
                    'recipe_id': self.recipe_id,
                    'quantity': self.quantity,
                    'output_item': output_item,
                    'output_quantity': output_quantity
                }
            )
            
        except Exception as e:
            return ActionExecutionResult(
                ActionResult.FAILED,
                f"Crafting failed: {e}"
            )
    
    def _get_recipe(self, recipe_id: str) -> Optional[Dict[str, Any]]:
        """Get recipe data by ID."""
        # This would load from actual recipe data
        recipes = {
            'wooden_pickaxe': {
                'materials': {
                    'wood': 3,
                    'stick': 2
                },
                'output': {
                    'item_type': 'wooden_pickaxe',
                    'quantity': 1
                }
            },
            'stone_pickaxe': {
                'materials': {
                    'stone': 3,
                    'stick': 2
                },
                'output': {
                    'item_type': 'stone_pickaxe',
                    'quantity': 1
                }
            },
            'bread': {
                'materials': {
                    'wheat': 3
                },
                'output': {
                    'item_type': 'bread',
                    'quantity': 1
                }
            }
        }
        return recipes.get(recipe_id)
    
    def _count_item_in_inventory(self, player_state, item_type: str) -> int:
        """Count total quantity of item in inventory."""
        total = 0
        for slot in player_state.inventory:
            if slot and slot.get('item_type') == item_type:
                total += slot.get('quantity', 0)
        return total
    
    def _has_inventory_space(self, player_state, item_type: str, quantity: int) -> bool:
        """Check if inventory has space for items."""
        # Simple check - would be more complex in real implementation
        empty_slots = sum(1 for slot in player_state.inventory if not slot)
        return empty_slots > 0 or quantity <= 64  # Assuming max stack size of 64
    
    def get_serializable_data(self) -> Dict[str, Any]:
        """Get serializable representation."""
        data = super().get_serializable_data()
        data.update({
            'recipe_id': self.recipe_id,
            'quantity': self.quantity
        })
        return data
    
    @classmethod
    def from_serializable_data(cls, data: Dict[str, Any]):
        """Create action from serialized data."""
        return cls(
            player_id=data['player_id'],
            recipe_id=data['recipe_id'],
            quantity=data['quantity'],
            timestamp=data['timestamp'],
            action_id=data['action_id']
        )


class DropItemAction(BaseAction):
    """
    Action for dropping items from inventory.
    """
    
    def __init__(self, player_id: str, slot: int, quantity: int = None,
                 timestamp: float = None, action_id: str = None):
        """Initialize item dropping action."""
        super().__init__(player_id, timestamp, action_id)
        
        self.slot = slot
        self.quantity = quantity  # None = drop all
        
        self.requires_validation = True
        self.cooldown_seconds = 0.1
    
    def get_action_type(self) -> str:
        """Get the action type identifier."""
        return "drop_item"
    
    def validate(self, world, player_state) -> ActionExecutionResult:
        """Validate the item dropping action."""
        if not player_state:
            return ActionExecutionResult(ActionResult.INVALID, "Player not found")
        
        # Check slot bounds
        if self.slot < 0 or self.slot >= len(player_state.inventory):
            return ActionExecutionResult(
                ActionResult.INVALID,
                "Slot index out of bounds"
            )
        
        # Check if slot has items
        item = player_state.inventory[self.slot]
        if not item or item.get('quantity', 0) <= 0:
            return ActionExecutionResult(
                ActionResult.INVALID,
                "Slot is empty"
            )
        
        # Validate quantity
        available_quantity = item.get('quantity', 0)
        drop_quantity = self.quantity if self.quantity is not None else available_quantity
        
        if drop_quantity <= 0 or drop_quantity > available_quantity:
            return ActionExecutionResult(
                ActionResult.INVALID,
                f"Invalid quantity: {drop_quantity} (available: {available_quantity})"
            )
        
        return ActionExecutionResult(ActionResult.SUCCESS, "Item dropping validated")
    
    def execute(self, world, player_state) -> ActionExecutionResult:
        """Execute the item dropping action."""
        try:
            item = player_state.inventory[self.slot]
            item_type = item['item_type']
            
            drop_quantity = self.quantity if self.quantity is not None else item['quantity']
            
            # Remove items from inventory
            item['quantity'] -= drop_quantity
            if item['quantity'] <= 0:
                player_state.inventory[self.slot] = None
            
            # Spawn floating item at player location
            world.spawn_floating_item(item_type, drop_quantity, player_state.x, player_state.y)
            
            log_debug(f"Player {self.player_id} dropped {drop_quantity} {item_type}")
            
            return ActionExecutionResult(
                ActionResult.SUCCESS,
                "Item dropped successfully",
                {
                    'slot': self.slot,
                    'item_type': item_type,
                    'quantity': drop_quantity,
                    'position': (player_state.x, player_state.y)
                }
            )
            
        except Exception as e:
            return ActionExecutionResult(
                ActionResult.FAILED,
                f"Item dropping failed: {e}"
            )
    
    def get_serializable_data(self) -> Dict[str, Any]:
        """Get serializable representation."""
        data = super().get_serializable_data()
        data.update({
            'slot': self.slot,
            'quantity': self.quantity
        })
        return data
    
    @classmethod
    def from_serializable_data(cls, data: Dict[str, Any]):
        """Create action from serialized data."""
        return cls(
            player_id=data['player_id'],
            slot=data['slot'],
            quantity=data.get('quantity'),
            timestamp=data['timestamp'],
            action_id=data['action_id']
        )


class PickupItemAction(BaseAction):
    """
    Action for picking up floating items.
    """
    
    def __init__(self, player_id: str, item_id: str,
                 timestamp: float = None, action_id: str = None):
        """Initialize item pickup action."""
        super().__init__(player_id, timestamp, action_id)
        
        self.item_id = item_id  # ID of the floating item to pick up
        
        self.requires_validation = True
        self.cooldown_seconds = 0.1
    
    def get_action_type(self) -> str:
        """Get the action type identifier."""
        return "pickup_item"
    
    def validate(self, world, player_state) -> ActionExecutionResult:
        """Validate the item pickup action."""
        if not player_state:
            return ActionExecutionResult(ActionResult.INVALID, "Player not found")
        
        # Check if floating item exists
        floating_item = world.get_floating_item(self.item_id)
        if not floating_item:
            return ActionExecutionResult(
                ActionResult.INVALID,
                f"Floating item {self.item_id} not found"
            )
        
        # Check if item is within pickup range
        distance = ((player_state.x - floating_item.x)**2 + 
                   (player_state.y - floating_item.y)**2)**0.5
        
        if distance > 32:  # TILESIZE pickup range
            return ActionExecutionResult(
                ActionResult.INVALID,
                f"Item too far away: {distance:.1f} > 32"
            )
        
        # Check if player has inventory space
        if not self._has_inventory_space(player_state, floating_item.item_type, floating_item.quantity):
            return ActionExecutionResult(
                ActionResult.INSUFFICIENT_RESOURCES,
                "Not enough inventory space"
            )
        
        return ActionExecutionResult(ActionResult.SUCCESS, "Item pickup validated")
    
    def execute(self, world, player_state) -> ActionExecutionResult:
        """Execute the item pickup action."""
        try:
            floating_item = world.get_floating_item(self.item_id)
            if not floating_item:
                return ActionExecutionResult(
                    ActionResult.FAILED,
                    "Floating item no longer exists"
                )
            
            # Add item to inventory
            added = player_state.add_item(floating_item.item_type, floating_item.quantity)
            
            if added < floating_item.quantity:
                # Partial pickup - update floating item
                floating_item.quantity -= added
                pickup_quantity = added
            else:
                # Full pickup - remove floating item
                world.remove_floating_item(self.item_id)
                pickup_quantity = floating_item.quantity
            
            log_debug(f"Player {self.player_id} picked up {pickup_quantity} {floating_item.item_type}")
            
            return ActionExecutionResult(
                ActionResult.SUCCESS,
                "Item picked up successfully",
                {
                    'item_id': self.item_id,
                    'item_type': floating_item.item_type,
                    'quantity': pickup_quantity
                }
            )
            
        except Exception as e:
            return ActionExecutionResult(
                ActionResult.FAILED,
                f"Item pickup failed: {e}"
            )
    
    def _has_inventory_space(self, player_state, item_type: str, quantity: int) -> bool:
        """Check if inventory has space for items."""
        # Try to find existing stacks first
        for slot in player_state.inventory:
            if slot and slot.get('item_type') == item_type:
                # Assuming max stack size of 64
                if slot.get('quantity', 0) < 64:
                    return True
        
        # Check for empty slots
        empty_slots = sum(1 for slot in player_state.inventory if not slot)
        return empty_slots > 0
    
    def get_serializable_data(self) -> Dict[str, Any]:
        """Get serializable representation."""
        data = super().get_serializable_data()
        data.update({
            'item_id': self.item_id
        })
        return data
    
    @classmethod
    def from_serializable_data(cls, data: Dict[str, Any]):
        """Create action from serialized data."""
        return cls(
            player_id=data['player_id'],
            item_id=data['item_id'],
            timestamp=data['timestamp'],
            action_id=data['action_id']
        )


class EquipItemAction(BaseAction):
    """
    Action for equipping items (tools, armor, etc.).
    """
    
    def __init__(self, player_id: str, slot: int, equipment_slot: str,
                 timestamp: float = None, action_id: str = None):
        """Initialize equipment action."""
        super().__init__(player_id, timestamp, action_id)
        
        self.slot = slot  # Inventory slot
        self.equipment_slot = equipment_slot  # 'tool', 'helmet', 'chest', etc.
        
        self.requires_validation = True
        self.cooldown_seconds = 0.1
    
    def get_action_type(self) -> str:
        """Get the action type identifier."""
        return "equip_item"
    
    def validate(self, world, player_state) -> ActionExecutionResult:
        """Validate the equipment action."""
        if not player_state:
            return ActionExecutionResult(ActionResult.INVALID, "Player not found")
        
        # Check slot bounds
        if self.slot < 0 or self.slot >= len(player_state.inventory):
            return ActionExecutionResult(
                ActionResult.INVALID,
                "Slot index out of bounds"
            )
        
        # Check if slot has items
        item = player_state.inventory[self.slot]
        if not item:
            return ActionExecutionResult(
                ActionResult.INVALID,
                "Slot is empty"
            )
        
        # Check if item can be equipped in this slot
        if not self._can_equip_item(item['item_type'], self.equipment_slot):
            return ActionExecutionResult(
                ActionResult.INVALID,
                f"Cannot equip {item['item_type']} in {self.equipment_slot} slot"
            )
        
        return ActionExecutionResult(ActionResult.SUCCESS, "Equipment validated")
    
    def execute(self, world, player_state) -> ActionExecutionResult:
        """Execute the equipment action."""
        try:
            item = player_state.inventory[self.slot]
            item_type = item['item_type']
            
            # Get currently equipped item (if any)
            current_equipment = getattr(player_state, self.equipment_slot, None)
            
            # Equip new item
            setattr(player_state, self.equipment_slot, item_type)
            
            # Move old equipment to inventory (if there was one)
            if current_equipment:
                player_state.inventory[self.slot] = {
                    'item_type': current_equipment,
                    'quantity': 1
                }
            else:
                player_state.inventory[self.slot] = None
            
            log_debug(f"Player {self.player_id} equipped {item_type} in {self.equipment_slot}")
            
            return ActionExecutionResult(
                ActionResult.SUCCESS,
                "Item equipped successfully",
                {
                    'slot': self.slot,
                    'equipment_slot': self.equipment_slot,
                    'equipped_item': item_type,
                    'previous_item': current_equipment
                }
            )
            
        except Exception as e:
            return ActionExecutionResult(
                ActionResult.FAILED,
                f"Equipment failed: {e}"
            )
    
    def _can_equip_item(self, item_type: str, equipment_slot: str) -> bool:
        """Check if item can be equipped in the given slot."""
        equipment_rules = {
            'tool': ['wooden_pickaxe', 'stone_pickaxe', 'wooden_axe', 'stone_axe', 'sword'],
            'helmet': ['leather_helmet', 'iron_helmet'],
            'chest': ['leather_chestplate', 'iron_chestplate'],
            'legs': ['leather_leggings', 'iron_leggings'],
            'boots': ['leather_boots', 'iron_boots']
        }
        
        allowed_items = equipment_rules.get(equipment_slot, [])
        return item_type in allowed_items
    
    def get_serializable_data(self) -> Dict[str, Any]:
        """Get serializable representation."""
        data = super().get_serializable_data()
        data.update({
            'slot': self.slot,
            'equipment_slot': self.equipment_slot
        })
        return data
    
    @classmethod
    def from_serializable_data(cls, data: Dict[str, Any]):
        """Create action from serialized data."""
        return cls(
            player_id=data['player_id'],
            slot=data['slot'],
            equipment_slot=data['equipment_slot'],
            timestamp=data['timestamp'],
            action_id=data['action_id']
        )
