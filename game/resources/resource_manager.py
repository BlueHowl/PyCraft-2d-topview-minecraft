"""
Resource Manager - Handles loading and managing game assets.
"""
import pygame as pg
import json
from os import path
from game.config.settings import PLAYER_SPRITE, TILESIZE
from game.data import DataManager


class ResourceManager:
    """Manages all game resources including textures, audio, fonts, and data files."""
    
    def __init__(self, game_folder):
        self.game_folder = game_folder
        self.fonts = {}
        self.images = {}
        self.audio = {}
        self.data = {}
        
        # Initialize the new data manager
        self.data_manager = DataManager(game_folder)
        
    def load_all_resources(self):
        """Load all game resources."""
        self.load_fonts()
        self.load_images()
        self.load_audio()
        self.load_data_files()
        
    def load_fonts(self):
        """Load all font assets."""
        font_path = path.join(self.game_folder, 'Pixellari.ttf')
        self.fonts = {
            'font_64': pg.font.Font(font_path, 64),
            'font_32': pg.font.Font(font_path, 32),
            'font_16': pg.font.Font(font_path, 16),
            'font_10': pg.font.Font(font_path, 10)
        }
        
    def load_images(self):
        """Load all image assets."""
        textures_path = path.join(self.game_folder, 'textures')
        
        # Load tile images
        tile_images = []
        tile_images.append(pg.image.load(
            path.join(textures_path, 'map/natureTileset.png')).convert_alpha())
        tile_images.append(pg.image.load(
            path.join(textures_path, 'map/IceTileset.png')).convert_alpha())
        self.images['tile_images'] = tile_images
        
        # Load player sprite
        player_sprite = pg.image.load(
            path.join(textures_path, PLAYER_SPRITE)).convert_alpha()
        self.images['player_sprite'] = player_sprite
        
        # Set game icon
        pg.display.set_icon(player_sprite.subsurface(
            (0*TILESIZE, 0*TILESIZE, TILESIZE, TILESIZE)))
        
        # Load GUI images
        gui_path = path.join(textures_path, 'gui')
        self.images['hearts'] = pg.image.load(
            path.join(gui_path, 'hearts.png')).convert_alpha()
        self.images['hotbar'] = pg.image.load(
            path.join(gui_path, 'hotbar.png')).convert_alpha()
        self.images['menu'] = pg.image.load(
            path.join(gui_path, 'menu.png')).convert_alpha()
        
        # Load other images
        self.images['items'] = pg.image.load(
            path.join(textures_path, 'items.png')).convert_alpha()
        self.images['crosshair'] = pg.image.load(
            path.join(textures_path, 'crosshair.png')).convert_alpha()
        self.images['light'] = pg.transform.scale(pg.image.load(
            path.join(textures_path, 'light_.png')).convert_alpha(), (550, 550))
            
    def load_audio(self):
        """Load all audio assets using the new data manager."""
        audio_mappings = self.data_manager.get_audio_mappings()
        audio_list = {}
        for name, file_path in audio_mappings.items():
            full_path = path.join(self.game_folder, file_path)
            audio_list[name] = pg.mixer.Sound(full_path)
        self.audio = audio_list
        
    def load_data_files(self):
        """Load all data files using the new data manager."""
        # Load item texture coordinates using new data manager
        items = self.data_manager.get_items()
        item_texture_coordinate = {}
        for item_id, item_data in items.items():
            item_texture_coordinate[item_id] = (
                item_data['texture_x'], 
                item_data['texture_y'], 
                item_data['max_stack'], 
                item_data['item_type'], 
                item_data['name']
            )
        self.data['item_texture_coordinate'] = item_texture_coordinate
        
        # Load crafting recipes using legacy format to maintain compatibility
        craft_list = []
        legacy_craft_file = path.join(self.game_folder, 'data', 'craft.list')
        if path.exists(legacy_craft_file):
            with open(legacy_craft_file, 'rt') as f:
                for line in f:
                    if line.strip():
                        l = line.strip().split('|')
                        craft_list.append(l)
        else:
            # Try loading from new format and convert back
            recipes = self.data_manager.get_crafting_recipes()
            for recipe in recipes:
                # Convert back to legacy format for compatibility
                result_id = str(recipe['result_item_id']).zfill(2)
                ingredients_str = ""
                if recipe['ingredients']:
                    ingredient_parts = []
                    for item_id, quantity in recipe['ingredients']:
                        ingredient_parts.append(f"{item_id},{quantity}")
                    ingredients_str = ";".join(ingredient_parts)
                
                if recipe['requires_workbench']:
                    result_id = "10"  # Legacy workbench indicator
                
                craft_list.append([result_id, ingredients_str])
        
        self.data['craft_list'] = craft_list
        
        # Load texture coordinates using new data manager
        self.data['texture_coordinate'] = self.data_manager.get_texture_coordinates()
        
        # Load mob definitions
        mob_definitions = self.data_manager.get_mob_definitions()
        mob_list = []
        for mob in mob_definitions:
            # Create mob data in legacy format for compatibility
            if mob['sprite_path']:  # Only if sprite path exists
                try:
                    sprite = pg.image.load(path.join(self.game_folder, mob['sprite_path'])).convert_alpha()
                    # Fix mob tuple structure to match expected legacy format:
                    # [0]: sprite, [1]: spawn_item, [2]: isEnemy, [3]: damage, [4]: speed, [5]: health, [6]: name
                    # Use the corrected field names from JSON
                    is_enemy = mob.get('is_enemy', 1 if mob['damage'] > 0 else 0)
                    mob_tuple = (
                        sprite,
                        mob['spawn_item'],
                        is_enemy,           # Index 2: isEnemy (0 for friendly, 1 for hostile)
                        mob['damage'],      # Index 3: Attacktype/damage
                        mob['speed'],       # Index 4: stopDistance/speed
                        mob['health'],      # Index 5: health
                        mob['name']         # Index 6: name
                    )
                    mob_list.append(mob_tuple)
                except Exception as e:
                    print(f"Error loading mob sprite {mob['sprite_path']}: {e}")
        self.data['mob_list'] = mob_list
        
        # Load UI maps (these remain file-based for now)
        data_path = path.join(self.game_folder, 'data')
        ui_maps_path = path.join(data_path, 'ui_maps')
        for map_name in ['menu', 'inventory', 'furnaceUi', 'chestUi']:
            map_data = []
            map_file = path.join(ui_maps_path, f'{map_name}.map')
            if path.exists(map_file):
                with open(map_file, 'rt') as f:
                    for line in f:
                        map_data.append(line.strip())
            self.data[f'{map_name}_map'] = map_data
        
        # Load remaining legacy files that need separate migration
        self._load_legacy_assignment_and_fuel_data(data_path)
    
    def _load_legacy_assignment_and_fuel_data(self, data_path):
        """Load legacy assignment and fuel data (temporary until migrated)."""
        # Load item assignment list
        item_assignment_list = {}
        assignment_file = path.join(data_path, 'item_assignement.list')
        if path.exists(assignment_file):
            with open(assignment_file, 'rt') as f:
                for line in f:
                    l = line.strip().split(':')
                    if len(l) > 1:
                        item_assignment_list[int(l[0])] = l[1:]
        self.data['item_assignment_list'] = item_assignment_list
        
        # Load furnace fuel list
        furnace_fuel_list = {}
        fuel_file = path.join(data_path, 'furnace_fuels.list')
        if path.exists(fuel_file):
            with open(fuel_file, 'rt') as f:
                for line in f:
                    l = line.strip().split(':')
                    if len(l) > 1:
                        furnace_fuel_list[int(l[0])] = l[1:]
        self.data['furnace_fuel_list'] = furnace_fuel_list
    
    def get_font(self, size_name):
        """Get a font by size name."""
        return self.fonts.get(size_name)
    
    def get_image(self, image_name):
        """Get an image by name."""
        return self.images.get(image_name)
    
    def get_audio(self, audio_name):
        """Get an audio clip by name."""
        return self.audio.get(audio_name)
    
    def get_data(self, data_name):
        """Get data by name."""
        return self.data.get(data_name)
