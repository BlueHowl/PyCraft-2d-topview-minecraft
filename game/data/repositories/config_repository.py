"""
Configuration repository - Handles game configuration data (items, crafting, audio, etc.).
"""

import os
from typing import Dict, List, Optional
from ..models import ItemDefinition, CraftingRecipe, AudioMapping, MobDefinition
from ..serializers import JSONSerializer


class ConfigRepository:
    """Repository for managing game configuration data."""
    
    def __init__(self, game_folder: str):
        self.game_folder = game_folder
        self.data_path = os.path.join(game_folder, 'data')
        self.config_cache = {}
    
    def load_items(self) -> Dict[int, ItemDefinition]:
        """Load item definitions from JSON format."""
        if 'items' in self.config_cache:
            return self.config_cache['items']
        
        # Load from JSON format
        json_path = os.path.join(self.data_path, 'items.json')
        items_data = JSONSerializer.load_from_file(json_path)
        
        items = {}
        if items_data:
            for item_data in items_data.get('items', []):
                item = ItemDefinition(**item_data)
                items[item.id] = item
        
        self.config_cache['items'] = items
        return items
    
    def load_crafting_recipes(self) -> List[CraftingRecipe]:
        """Load crafting recipes from JSON format."""
        if 'crafting' in self.config_cache:
            return self.config_cache['crafting']
        
        # Load from JSON format
        json_path = os.path.join(self.data_path, 'crafting.json')
        crafting_data = JSONSerializer.load_from_file(json_path)
        
        recipes = []
        if crafting_data:
            for recipe_data in crafting_data.get('recipes', []):
                recipes.append(CraftingRecipe(**recipe_data))
        
        self.config_cache['crafting'] = recipes
        return recipes
    
    def load_item_config(self) -> Dict:
        """Load item configuration (assignments and furnace fuels)."""
        if 'item_config' in self.config_cache:
            return self.config_cache['item_config']
        
        json_path = os.path.join(self.data_path, 'item_config.json')
        config_data = JSONSerializer.load_from_file(json_path)
        
        # Use default structure if no file exists
        if not config_data:
            config_data = {
                'item_assignments': {},
                'furnace_fuels': {}
            }
        
        self.config_cache['item_config'] = config_data
        return config_data
    
    def load_audio_mappings(self) -> Dict[str, AudioMapping]:
        """Load audio mappings from JSON format."""
        if 'audio' in self.config_cache:
            return self.config_cache['audio']
        
        # Load from JSON format
        json_path = os.path.join(self.data_path, 'audio.json')
        audio_data = JSONSerializer.load_from_file(json_path)
        
        mappings = {}
        if audio_data:
            for mapping_data in audio_data.get('mappings', []):
                mapping = AudioMapping(**mapping_data)
                mappings[mapping.name] = mapping
        
        self.config_cache['audio'] = mappings
        return mappings
    
    def load_mobs(self) -> List[MobDefinition]:
        """Load mob definitions from JSON format."""
        if 'mobs' in self.config_cache:
            return self.config_cache['mobs']
        
        # Load from JSON format
        json_path = os.path.join(self.data_path, 'mobs.json')
        mobs_data = JSONSerializer.load_from_file(json_path)
        
        mobs = []
        if mobs_data:
            for mob_data in mobs_data.get('mobs', []):
                mobs.append(MobDefinition(**mob_data))
        
        self.config_cache['mobs'] = mobs
        return mobs
    
    def load_mob_definitions(self) -> List[MobDefinition]:
        """Alias for load_mobs method for backward compatibility."""
        return self.load_mobs()
    
    def load_texture_coordinates(self) -> Dict:
        """Load texture coordinates from JSON format."""
        if 'texture_coordinates' in self.config_cache:
            return self.config_cache['texture_coordinates']
        
        # Load from JSON format
        json_path = os.path.join(self.data_path, 'texture_coordinates.json')
        tex_coords_data = JSONSerializer.load_from_file(json_path)
        
        texture_coordinates = {}
        if tex_coords_data:
            texture_coordinates = tex_coords_data.get('texture_coordinates', {})
        
        self.config_cache['texture_coordinates'] = texture_coordinates
        return texture_coordinates
    
    def clear_cache(self):
        """Clear all cached configuration data."""
        self.config_cache.clear()
