"""
Resource Manager - Handles loading and managing game assets.
"""
import pygame as pg
import json
from os import path
from game.config.settings import PLAYER_SPRITE, TILESIZE


class ResourceManager:
    """Manages all game resources including textures, audio, fonts, and data files."""
    
    def __init__(self, game_folder):
        self.game_folder = game_folder
        self.fonts = {}
        self.images = {}
        self.audio = {}
        self.data = {}
        
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
        """Load all audio assets."""
        audio_list = {}
        with open(path.join(self.game_folder, 'data/audio.list'), 'rt') as f:
            for line in f:
                l = line.strip().split(':')
                audio_list[l[0]] = pg.mixer.Sound(
                    path.join(self.game_folder, l[1]))
        self.audio = audio_list
        
    def load_data_files(self):
        """Load all data files."""
        data_path = path.join(self.game_folder, 'data')
        
        # Load mob data
        mob_list = []
        with open(path.join(data_path, 'mobs.list'), 'rt') as f:
            for line in f:
                l = line.strip().split('|')
                item = l[2].split(',')
                mob_list.append((
                    pg.image.load(path.join(self.game_folder, l[1])).convert_alpha(),
                    (int(item[0]), int(item[1])),
                    int(l[3]), int(l[4]), int(l[5]), int(l[6]), l[0]
                ))
        self.data['mob_list'] = mob_list
        
        # Load item texture coordinates
        item_texture_coordinate = {}
        with open(path.join(data_path, 'item.list'), 'rt') as f:
            for line in f:
                l = line.strip().split(':')
                item_texture_coordinate[int(l[0])] = (
                    int(l[1]), int(l[2]), int(l[3]), int(l[4]), l[5]
                )
        self.data['item_texture_coordinate'] = item_texture_coordinate
        
        # Load UI maps
        ui_maps_path = path.join(data_path, 'ui_maps')
        for map_name in ['menu', 'inventory', 'furnaceUi', 'chestUi']:
            map_data = []
            with open(path.join(ui_maps_path, f'{map_name}.map'), 'rt') as f:
                for line in f:
                    map_data.append(line.strip())
            self.data[f'{map_name}_map'] = map_data
            
        # Load craft list
        craft_list = []
        with open(path.join(data_path, 'craft.list'), 'rt') as f:
            for line in f:
                l = line.strip().split('|')
                craft_list.append(l)
        self.data['craft_list'] = craft_list
        
        # Load item assignment list
        item_assignment_list = {}
        with open(path.join(data_path, 'item_assignement.list'), 'rt') as f:
            for line in f:
                l = line.strip().split(':')
                item_assignment_list[int(l[0])] = l[1:]
        self.data['item_assignment_list'] = item_assignment_list
        
        # Load furnace fuel list
        furnace_fuel_list = {}
        with open(path.join(data_path, 'furnace_fuels.list'), 'rt') as f:
            for line in f:
                l = line.strip().split(':')
                furnace_fuel_list[int(l[0])] = l[1:]
        self.data['furnace_fuel_list'] = furnace_fuel_list
        
        # Load texture coordinates
        with open(path.join(data_path, 'texCoords.txt'), 'rt') as f:
            self.data['texture_coordinate'] = json.loads(f.read())
    
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
