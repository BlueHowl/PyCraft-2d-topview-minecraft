"""
Data models for game entities and state.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple


@dataclass
class PlayerState:
    """Player state data model."""
    position: Tuple[int, int]
    health: int
    max_health: int = 255
    inventory: List[List[int]] = field(default_factory=list)
    
    @classmethod
    def from_legacy_data(cls, legacy_data: List[str]) -> 'PlayerState':
        """Create PlayerState from legacy save format."""
        import json
        
        # Parse position and health from first line: "x:y:0:current_health:max_health" or "x:y:health"
        pos_health = legacy_data[0].split(':')
        
        if len(pos_health) >= 5:
            # New format: x:y:0:current_health:max_health
            x, y = int(pos_health[0]), int(pos_health[1])
            health = int(pos_health[3])  # Current health at index 3
            max_health = int(pos_health[4])  # Max health at index 4
        elif len(pos_health) >= 3:
            # Fallback format: x:y:health
            x, y, health = int(pos_health[0]), int(pos_health[1]), int(pos_health[2])
            max_health = 20  # Default max health for new worlds
        else:
            # Default values
            x, y, health, max_health = 0, 0, 20, 20
        
        # Parse inventory from second line (JSON format)
        inventory = json.loads(legacy_data[1])
        
        return cls(
            position=(x, y),
            health=health,
            max_health=max_health,
            inventory=inventory
        )
    
    def to_legacy_format(self) -> str:
        """Convert to legacy format for backward compatibility."""
        import json
        # Use the full legacy format: x:y:0:current_health:max_health
        pos_health = f"{self.position[0]}:{self.position[1]}:0:{self.health}:{self.max_health}"
        inventory_json = json.dumps(self.inventory)
        return f"{pos_health}\n{inventory_json}"


@dataclass
class WorldState:
    """World state data model."""
    seed: str
    spawn_point: Tuple[int, int]
    global_time: int = 0
    night_shade: int = 255
    
    @classmethod
    def from_legacy_data(cls, legacy_data: List[str]) -> 'WorldState':
        """Create WorldState from legacy save format."""
        seed = legacy_data[2]
        spawn_coords = legacy_data[3].split(':')
        spawn_x, spawn_y = int(spawn_coords[0]), int(spawn_coords[1])
        global_time = int(legacy_data[4]) if len(legacy_data) > 4 else 0
        night_shade = int(legacy_data[5]) if len(legacy_data) > 5 else 255
        
        return cls(
            seed=seed,
            spawn_point=(spawn_x, spawn_y),
            global_time=global_time,
            night_shade=night_shade
        )


@dataclass
class GameSave:
    """Complete game save data model."""
    world_name: str
    player_state: PlayerState
    world_state: WorldState
    floating_items: List[Dict[str, Any]] = field(default_factory=list)
    chests: Dict[str, Any] = field(default_factory=dict)
    furnaces: Dict[str, Any] = field(default_factory=dict)
    mobs: Dict[str, Any] = field(default_factory=dict)
    signs: Dict[str, Any] = field(default_factory=dict)
    chunks: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ItemDefinition:
    """Item definition data model."""
    id: int
    texture_x: int
    texture_y: int
    max_stack: int
    item_type: int  # 0=tool, 1=material, 2=placeable, 3=weapon
    name: str
    durability: int = -1  # -1 for no durability
    
    @classmethod
    def from_legacy_line(cls, line: str) -> 'ItemDefinition':
        """Create ItemDefinition from legacy format line."""
        parts = line.strip().split(':')
        return cls(
            id=int(parts[0]),
            texture_x=int(parts[1]),
            texture_y=int(parts[2]),
            max_stack=int(parts[3]),
            item_type=int(parts[4]),
            name=parts[5],
            durability=-1  # Default, can be enhanced later
        )


@dataclass
class CraftingRecipe:
    """Crafting recipe data model."""
    result_item_id: int
    result_quantity: int
    ingredients: List[Tuple[int, int]]  # (item_id, quantity) pairs
    requires_workbench: bool = False
    
    @classmethod
    def from_legacy_line(cls, line: str) -> 'CraftingRecipe':
        """Create CraftingRecipe from legacy format line."""
        parts = line.strip().split('|')
        if len(parts) < 2:
            # Handle malformed lines
            return cls(result_item_id=0, result_quantity=1, ingredients=[])
        
        # Parse result: "01" -> item_id, default quantity is 1
        result_id = int(parts[0])
        
        # Parse ingredients: "4,4;3,1" or "11,2:4,4;12,1"
        ingredients = []
        if len(parts) > 1:
            ingredient_parts = parts[1].split(';')
            for ingredient in ingredient_parts:
                if ':' in ingredient:
                    # Handle complex recipes like "11,2:4,4" 
                    sub_parts = ingredient.split(':')
                    for sub_part in sub_parts:
                        if ',' in sub_part:
                            try:
                                item_id, quantity = sub_part.split(',')
                                ingredients.append((int(item_id), int(quantity)))
                            except ValueError:
                                continue  # Skip malformed parts
                elif ',' in ingredient:
                    try:
                        item_id, quantity = ingredient.split(',')
                        ingredients.append((int(item_id), int(quantity)))
                    except ValueError:
                        continue  # Skip malformed parts
        
        # Determine if workbench is required (recipes starting with "10|" seem to require workbench)
        requires_workbench = parts[0] == '10'
        
        return cls(
            result_item_id=result_id,
            result_quantity=1,  # Default, can be enhanced
            ingredients=ingredients,
            requires_workbench=requires_workbench
        )


@dataclass
class AudioMapping:
    """Audio file mapping data model."""
    name: str
    file_path: str
    
    @classmethod
    def from_legacy_line(cls, line: str) -> 'AudioMapping':
        """Create AudioMapping from legacy format line."""
        parts = line.strip().split(':')
        return cls(
            name=parts[0],
            file_path=parts[1]
        )


@dataclass
class MobDefinition:
    """Mob definition data model."""
    name: str
    sprite_path: str
    spawn_item: Tuple[int, int]  # (item_id, quantity)
    health: int
    damage: int
    speed: int
    ai_type: int
    
    @classmethod
    def from_legacy_data(cls, mob_data: Tuple) -> 'MobDefinition':
        """Create MobDefinition from legacy tuple format."""
        return cls(
            name=mob_data[6],
            sprite_path="",  # sprite is loaded differently in legacy
            spawn_item=mob_data[1],
            health=mob_data[2],
            damage=mob_data[3],
            speed=mob_data[4],
            ai_type=mob_data[5]
        )
