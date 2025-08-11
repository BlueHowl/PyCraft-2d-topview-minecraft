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
        """Load item definitions from JSON or legacy format."""
        if 'items' in self.config_cache:
            return self.config_cache['items']
        
        # Try loading from new JSON format first
        json_path = os.path.join(self.data_path, 'items.json')
        items_data = JSONSerializer.load_from_file(json_path)
        
        if items_data:
            items = {}
            for item_data in items_data.get('items', []):
                item = ItemDefinition(**item_data)
                items[item.id] = item
            self.config_cache['items'] = items
            return items
        
        # Fallback to legacy format
        return self._load_legacy_items()
    
    def _load_legacy_items(self) -> Dict[int, ItemDefinition]:
        """Load items from legacy .list format."""
        items = {}
        legacy_path = os.path.join(self.data_path, 'item.list')
        
        if os.path.exists(legacy_path):
            try:
                with open(legacy_path, 'r') as f:
                    for line in f:
                        if line.strip():
                            item = ItemDefinition.from_legacy_line(line)
                            items[item.id] = item
                
                # Save in new JSON format
                self._save_items_to_json(items)
                
            except Exception as e:
                print(f"Error loading legacy items: {e}")
        
        self.config_cache['items'] = items
        return items
    
    def _save_items_to_json(self, items: Dict[int, ItemDefinition]) -> bool:
        """Save items to JSON format."""
        items_data = {
            'items': [
                {
                    'id': item.id,
                    'texture_x': item.texture_x,
                    'texture_y': item.texture_y,
                    'max_stack': item.max_stack,
                    'item_type': item.item_type,
                    'name': item.name,
                    'durability': item.durability
                }
                for item in items.values()
            ]
        }
        
        json_path = os.path.join(self.data_path, 'items.json')
        return JSONSerializer.save_to_file(items_data, json_path)
    
    def load_crafting_recipes(self) -> List[CraftingRecipe]:
        """Load crafting recipes from JSON or legacy format."""
        if 'crafting' in self.config_cache:
            return self.config_cache['crafting']
        
        # Try loading from new JSON format first
        json_path = os.path.join(self.data_path, 'crafting.json')
        crafting_data = JSONSerializer.load_from_file(json_path)
        
        if crafting_data:
            recipes = []
            for recipe_data in crafting_data.get('recipes', []):
                recipes.append(CraftingRecipe(**recipe_data))
            self.config_cache['crafting'] = recipes
            return recipes
        
        # Fallback to legacy format
        return self._load_legacy_crafting()
    
    def _load_legacy_crafting(self) -> List[CraftingRecipe]:
        """Load crafting recipes from legacy .list format."""
        recipes = []
        legacy_path = os.path.join(self.data_path, 'craft.list')
        
        if os.path.exists(legacy_path):
            try:
                with open(legacy_path, 'r') as f:
                    for line in f:
                        if line.strip():
                            recipe = CraftingRecipe.from_legacy_line(line)
                            recipes.append(recipe)
                
                # Save in new JSON format
                self._save_crafting_to_json(recipes)
                
            except Exception as e:
                print(f"Error loading legacy crafting: {e}")
        
        self.config_cache['crafting'] = recipes
        return recipes
    
    def _save_crafting_to_json(self, recipes: List[CraftingRecipe]) -> bool:
        """Save crafting recipes to JSON format."""
        crafting_data = {
            'recipes': [
                {
                    'result_item_id': recipe.result_item_id,
                    'result_quantity': recipe.result_quantity,
                    'ingredients': recipe.ingredients,
                    'requires_workbench': recipe.requires_workbench
                }
                for recipe in recipes
            ]
        }
        
        json_path = os.path.join(self.data_path, 'crafting.json')
        return JSONSerializer.save_to_file(crafting_data, json_path)
    
    def load_audio_mappings(self) -> Dict[str, AudioMapping]:
        """Load audio mappings from JSON or legacy format."""
        if 'audio' in self.config_cache:
            return self.config_cache['audio']
        
        # Try loading from new JSON format first
        json_path = os.path.join(self.data_path, 'audio.json')
        audio_data = JSONSerializer.load_from_file(json_path)
        
        if audio_data:
            mappings = {}
            for mapping_data in audio_data.get('mappings', []):
                mapping = AudioMapping(**mapping_data)
                mappings[mapping.name] = mapping
            self.config_cache['audio'] = mappings
            return mappings
        
        # Fallback to legacy format
        return self._load_legacy_audio()
    
    def _load_legacy_audio(self) -> Dict[str, AudioMapping]:
        """Load audio mappings from legacy .list format."""
        mappings = {}
        legacy_path = os.path.join(self.data_path, 'audio.list')
        
        if os.path.exists(legacy_path):
            try:
                with open(legacy_path, 'r') as f:
                    for line in f:
                        if line.strip():
                            mapping = AudioMapping.from_legacy_line(line)
                            mappings[mapping.name] = mapping
                
                # Save in new JSON format
                self._save_audio_to_json(mappings)
                
            except Exception as e:
                print(f"Error loading legacy audio: {e}")
        
        self.config_cache['audio'] = mappings
        return mappings
    
    def _save_audio_to_json(self, mappings: Dict[str, AudioMapping]) -> bool:
        """Save audio mappings to JSON format."""
        audio_data = {
            'mappings': [
                {
                    'name': mapping.name,
                    'file_path': mapping.file_path
                }
                for mapping in mappings.values()
            ]
        }
        
        json_path = os.path.join(self.data_path, 'audio.json')
        return JSONSerializer.save_to_file(audio_data, json_path)
    
    def load_texture_coordinates(self) -> Dict[str, any]:
        """Load texture coordinates (already in JSON format)."""
        if 'texture_coords' in self.config_cache:
            return self.config_cache['texture_coords']
        
        coords_path = os.path.join(self.data_path, 'texCoords.txt')
        if os.path.exists(coords_path):
            try:
                with open(coords_path, 'r') as f:
                    import json
                    coords = json.loads(f.read())
                    self.config_cache['texture_coords'] = coords
                    return coords
            except Exception as e:
                print(f"Error loading texture coordinates: {e}")
        
        return {}
    
    def load_mob_definitions(self) -> List[MobDefinition]:
        """Load mob definitions from JSON or legacy format."""
        if 'mobs' in self.config_cache:
            return self.config_cache['mobs']
        
        # Try loading from new JSON format first
        json_path = os.path.join(self.data_path, 'mobs.json')
        mobs_data = JSONSerializer.load_from_file(json_path)
        
        if mobs_data:
            mobs = []
            for mob_data in mobs_data.get('mobs', []):
                mobs.append(MobDefinition(**mob_data))
            self.config_cache['mobs'] = mobs
            return mobs
        
        # Fallback to legacy format
        return self._load_legacy_mobs()
    
    def _load_legacy_mobs(self) -> List[MobDefinition]:
        """Load mob definitions from legacy .list format."""
        mobs = []
        legacy_path = os.path.join(self.data_path, 'mobs.list')
        
        if os.path.exists(legacy_path):
            try:
                with open(legacy_path, 'r') as f:
                    for line in f:
                        if line.strip():
                            parts = line.strip().split('|')
                            if len(parts) >= 7:
                                name = parts[0]
                                sprite_path = parts[1]
                                spawn_item_parts = parts[2].split(',')
                                spawn_item = (int(spawn_item_parts[0]), int(spawn_item_parts[1]))
                                is_enemy = int(parts[3])  # Index 3: isEnemy
                                damage = int(parts[4])    # Index 4: damage
                                speed = int(parts[5])     # Index 5: speed
                                health = int(parts[6])    # Index 6: health
                                
                                mob = MobDefinition(
                                    name=name,
                                    sprite_path=sprite_path,
                                    spawn_item=spawn_item,
                                    is_enemy=is_enemy,
                                    health=health,
                                    damage=damage,
                                    speed=speed
                                )
                                mobs.append(mob)
                
                # Save in new JSON format
                self._save_mobs_to_json(mobs)
                
            except Exception as e:
                print(f"Error loading legacy mobs: {e}")
        
        self.config_cache['mobs'] = mobs
        return mobs
    
    def _save_mobs_to_json(self, mobs: List[MobDefinition]) -> bool:
        """Save mob definitions to JSON format."""
        mobs_data = {
            'mobs': [
                {
                    'name': mob.name,
                    'sprite_path': mob.sprite_path,
                    'spawn_item': mob.spawn_item,
                    'is_enemy': mob.is_enemy,
                    'health': mob.health,
                    'damage': mob.damage,
                    'speed': mob.speed
                }
                for mob in mobs
            ]
        }
        
        json_path = os.path.join(self.data_path, 'mobs.json')
        return JSONSerializer.save_to_file(mobs_data, json_path)
    
    def clear_cache(self):
        """Clear the configuration cache."""
        self.config_cache.clear()
    
    def reload_all(self):
        """Reload all configuration data."""
        self.clear_cache()
        self.load_items()
        self.load_crafting_recipes()
        self.load_audio_mappings()
        self.load_texture_coordinates()
        self.load_mob_definitions()
