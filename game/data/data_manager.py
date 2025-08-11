"""
Data Manager - Main interface for all data operations.
"""

from typing import Optional, List, Dict, Any, Tuple
from .models import GameSave, ItemDefinition, CraftingRecipe, AudioMapping, MobDefinition
from .repositories import SaveRepository, ConfigRepository


class DataManager:
    """
    Main data manager that provides a unified interface for all data operations.
    This class decouples game logic from data persistence implementation.
    """
    
    def __init__(self, game_folder: str):
        self.game_folder = game_folder
        self.save_repository = SaveRepository(game_folder)
        self.config_repository = ConfigRepository(game_folder)
    
    # === SAVE/LOAD OPERATIONS ===
    
    def save_game(self, world_name: str, player_state: dict, world_state: dict, 
                  entities: dict = None) -> bool:
        """
        Save complete game state.
        
        Args:
            world_name: Name of the world/save
            player_state: Player data (position, health, inventory)
            world_state: World data (seed, spawn, time, etc.)
            entities: Optional entity data (items, chests, furnaces, mobs)
        """
        from .models import PlayerState, WorldState
        
        # Convert dictionaries to data models
        player = PlayerState(
            position=tuple(player_state.get('position', (0, 0))),
            health=player_state.get('health', 255),
            max_health=player_state.get('max_health', 255),
            inventory=player_state.get('inventory', [])
        )
        
        world = WorldState(
            seed=world_state.get('seed', ''),
            spawn_point=tuple(world_state.get('spawn_point', (0, 0))),
            global_time=world_state.get('global_time', 0),
            night_shade=world_state.get('night_shade', 255)
        )
        
        entities = entities or {}
        game_save = GameSave(
            world_name=world_name,
            player_state=player,
            world_state=world,
            floating_items=entities.get('floating_items', []),
            chests=entities.get('chests', {}),
            furnaces=entities.get('furnaces', {}),
            mobs=entities.get('mobs', {}),
            signs=entities.get('signs', {}),
            chunks=entities.get('chunks', {})
        )
        
        return self.save_repository.save_game(game_save)
    
    def load_game(self, world_name: str) -> Optional[Dict[str, Any]]:
        """
        Load complete game state.
        
        Args:
            world_name: Name of the world/save to load
            
        Returns:
            Dictionary containing all game data or None if load failed
        """
        game_save = self.save_repository.load_game(world_name)
        if not game_save:
            return None
        
        return {
            'player_state': {
                'position': game_save.player_state.position,
                'health': game_save.player_state.health,
                'max_health': game_save.player_state.max_health,
                'inventory': game_save.player_state.inventory
            },
            'world_state': {
                'seed': game_save.world_state.seed,
                'spawn_point': game_save.world_state.spawn_point,
                'global_time': game_save.world_state.global_time,
                'night_shade': game_save.world_state.night_shade
            },
            'entities': {
                'floating_items': game_save.floating_items,
                'chests': game_save.chests,
                'furnaces': game_save.furnaces,
                'mobs': game_save.mobs,
                'signs': game_save.signs,
                'chunks': game_save.chunks
            }
        }
    
    def create_new_world(self, world_name: str, seed: str, spawn_point: Tuple[int, int]) -> bool:
        """Create a new world save."""
        game_save = self.save_repository.create_new_save(world_name, seed, spawn_point)
        return game_save is not None
    
    def list_worlds(self) -> List[str]:
        """Get list of all available worlds."""
        return self.save_repository.list_saves()
    
    def delete_world(self, world_name: str) -> bool:
        """Delete a world save."""
        return self.save_repository.delete_save(world_name)
    
    # === CONFIGURATION DATA ===
    
    def get_items(self) -> Dict[int, Dict[str, Any]]:
        """Get all item definitions."""
        items = self.config_repository.load_items()
        return {
            item_id: {
                'id': item.id,
                'texture_x': item.texture_x,
                'texture_y': item.texture_y,
                'max_stack': item.max_stack,
                'item_type': item.item_type,
                'name': item.name,
                'durability': item.durability
            }
            for item_id, item in items.items()
        }
    
    def get_item(self, item_id: int) -> Optional[Dict[str, Any]]:
        """Get specific item definition."""
        items = self.config_repository.load_items()
        item = items.get(item_id)
        if item:
            return {
                'id': item.id,
                'texture_x': item.texture_x,
                'texture_y': item.texture_y,
                'max_stack': item.max_stack,
                'item_type': item.item_type,
                'name': item.name,
                'durability': item.durability
            }
        return None
    
    def get_crafting_recipes(self) -> List[Dict[str, Any]]:
        """Get all crafting recipes."""
        recipes = self.config_repository.load_crafting_recipes()
        return [
            {
                'result_item_id': recipe.result_item_id,
                'result_quantity': recipe.result_quantity,
                'ingredients': recipe.ingredients,
                'requires_workbench': recipe.requires_workbench
            }
            for recipe in recipes
        ]
    
    def get_audio_mappings(self) -> Dict[str, str]:
        """Get audio file mappings."""
        mappings = self.config_repository.load_audio_mappings()
        return {name: mapping.file_path for name, mapping in mappings.items()}
    
    def get_texture_coordinates(self) -> Dict[str, Any]:
        """Get texture coordinate mappings."""
        return self.config_repository.load_texture_coordinates()
    
    def get_mob_definitions(self) -> List[Dict[str, Any]]:
        """Get mob definitions."""
        mobs = self.config_repository.load_mob_definitions()
        return [
            {
                'name': mob.name,
                'sprite_path': mob.sprite_path,
                'spawn_item': mob.spawn_item,
                'health': mob.health,
                'damage': mob.damage,
                'speed': mob.speed,
                'ai_type': mob.ai_type
            }
            for mob in mobs
        ]
    
    # === UTILITY METHODS ===
    
    def reload_configuration(self):
        """Reload all configuration data from files."""
        self.config_repository.reload_all()
    
    def clear_cache(self):
        """Clear all cached configuration data."""
        self.config_repository.clear_cache()
    
    # === LEGACY COMPATIBILITY ===
    
    def get_legacy_level_data(self, world_name: str) -> Optional[List[str]]:
        """
        Get data in legacy level.save format for backward compatibility.
        This method helps transition existing code gradually.
        """
        game_data = self.load_game(world_name)
        if not game_data:
            return None
        
        player = game_data['player_state']
        world = game_data['world_state']
        
        # Recreate legacy format: x:y:0:health:maxHealth
        pos_health = f"{player['position'][0]}:{player['position'][1]}:0:{player['health']}:{player['max_health']}"
        inventory_json = str(player['inventory']).replace("'", '"')
        seed = world['seed']
        spawn = f"{world['spawn_point'][0]}:{world['spawn_point'][1]}"
        global_time = str(world['global_time'])
        night_shade = str(world['night_shade'])
        
        return [pos_health, inventory_json, seed, spawn, global_time, night_shade]
