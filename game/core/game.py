"""
Core Game class - Main game engine and state management.
"""
import math
import pygame as pg
import sys
import threading
import json
from os import path
from random import *

from game.config.settings import *
from game.resources.resource_manager import ResourceManager
from game.systems.world_manager import WorldManager
from game.systems.game_state_manager import GameStateManager
from game.systems.render_manager import RenderManager
from game.systems.input_manager import InputManager
from game.entities.FloatingItem import FloatingItem
from game.entities.mobs.Mob import Mob
from game.entities.Player import Player
from game.systems.Camera import Camera
from game.systems.chunk_manager import *
from game.ui.InputBox import InputBox
from game.ui.Menu import Menu
from game.ui.TextObject import TextObject
from game.world.Ground import Ground
from game.world.Map import Map
from game.world.Layer1_Objs import Layer1_objs


class Game:
    """Main game class that handles the core game loop and state management."""
    
    def __init__(self):
        """Initialize the game."""
        self.game_folder = path.dirname(path.dirname(path.dirname(__file__)))  # Go up one level from game/core

        self._init_pygame()
        self._init_display()
        self._init_game_state()
        self._init_sprite_groups()
        
        # Load all resources
        self.resource_manager = ResourceManager(self.game_folder)
        self.resource_manager.load_all_resources()
        
        # Initialize managers
        self.world_manager = WorldManager(self)
        self.game_state_manager = GameStateManager(self)
        self.render_manager = RenderManager(self)
        self.input_manager = InputManager(self)
        
        # Create input box
        self.input_commands_txt = InputBox(
            self, 20, HEIGHT - 60, 600, 40, limit=999)
        
    def _init_pygame(self):
        """Initialize pygame modules."""
        pg.init()
        pg.font.init()
        pg.mixer.init()
        pg.event.set_allowed([pg.QUIT, pg.KEYDOWN, pg.KEYUP, pg.MOUSEBUTTONDOWN])
        
    def _init_display(self):
        """Initialize display settings."""
        self.screen = pg.display.set_mode((WIDTH, HEIGHT))
        pg.display.set_caption(TITLE)
        self.clock = pg.time.Clock()
        pg.key.set_repeat(500, 100)
        pg.mouse.set_visible(True)
        
    def _init_game_state(self):
        """Initialize game state variables."""
        self.playing = True
        self.isGamePaused = False
        self.topleftCam = (0, 0)
        self.now = 0
        self.mousePos = pg.mouse.get_pos()
        self.isTabPressed = False
        self.isEPressed = False
        self.isPowerPressed = False
        self.isInventoryOpened = False
        self.hitboxDebug = False
        self.input_commands = False
        self.hasPlayerStateChanged = False
        self.last_save = 0
        self.isSaving = False
        self.lastChestId = ""
        self.lastFurnaceId = ""
        self.selectedTileToWritePos = (0, 0)
        self.area = []
        self.worldName = ''
        self.global_time = 0
        self.day_time = 0
        self.last_day_time = 0
        self.night_shade = 255
        self.isNight = False
        self.hostile_mobs_amount = 0
        self.friendly_mobs_amount = 0
        self.respawn_rect = (0, 0, 0, 0)
        
    def _init_sprite_groups(self):
        """Initialize sprite groups."""
        self.all_sprites = pg.sprite.Group()
        self.moving_sprites = pg.sprite.Group()
        self.player_collisions = pg.sprite.Group()
        self.grounds = pg.sprite.Group()
        self.floatingItems = pg.sprite.Group()
        self.players = pg.sprite.Group()
        self.mobs = pg.sprite.Group()
        self.Layer1 = pg.sprite.Group()
        self.projectiles = pg.sprite.Group()
        self.gui = pg.sprite.Group()
        
    # Properties to access resources easily
    @property
    def fonts(self):
        return self.resource_manager.fonts
        
    @property
    def images(self):
        return self.resource_manager.images
        
    @property
    def audio(self):
        return self.resource_manager.audio
        
    @property  
    def data(self):
        return self.resource_manager.data
    
    # Legacy property access for compatibility
    @property
    def font_64(self):
        return self.fonts['font_64']
    
    @property
    def font_32(self):
        return self.fonts['font_32']
    
    @property
    def font_16(self):
        return self.fonts['font_16']
    
    @property
    def font_10(self):
        return self.fonts['font_10']
        
    @property
    def mobList(self):
        return self.data['mob_list']
    
    @property
    def itemTextureCoordinate(self):
        return self.data['item_texture_coordinate']
    
    @property
    def audioList(self):
        return self.audio
    
    @property
    def menuData(self):
        return self.data['menu_map']
    
    @property
    def inventoryMap(self):
        return self.data['inventory_map']
    
    @property
    def furnaceUiMap(self):
        return self.data['furnaceUi_map']
    
    @property
    def chestUiMap(self):
        return self.data['chestUi_map']
    
    @property
    def craftList(self):
        return self.data['craft_list']
    
    @property
    def itemAssignementList(self):
        return self.data['item_assignment_list']
    
    @property
    def furnaceFuelList(self):
        return self.data['furnace_fuel_list']
    
    @property
    def textureCoordinate(self):
        return self.data['texture_coordinate']
    
    @property
    def tileImage(self):
        return self.images['tile_images']
    
    @property
    def palyer_sprite(self):  # Keep the typo for compatibility
        return self.images['player_sprite']
    
    @property
    def hearts_img(self):
        return self.images['hearts']
    
    @property
    def hotbar_img(self):
        return self.images['hotbar']
    
    @property
    def menu_img(self):
        return self.images['menu']
    
    @property
    def items_img(self):
        return self.images['items']
    
    @property
    def crosshair_img(self):
        return self.images['crosshair']
    
    @property
    def light(self):
        return self.images['light']
    
    def new(self):
        """Initialize a new game."""
        pg.mouse.set_visible(False)
        
        # Create map with game folder for new data manager
        self.map = Map(path.join(self.game_folder, 'saves/' + self.worldName), self.game_folder)
        
        # Create pathfinding matrix
        self.pathfind = [vec(0, 0), [[1] * (CHUNKRENDERX * 2 + 2) * CHUNKSIZE] * (
            CHUNKRENDERY * 2 + 2) * CHUNKSIZE]
        
        # Create chunk manager
        self.chunkmanager = Chunk(path.join(
            self.game_folder, 'saves/' + self.worldName), int(self.map.levelSavedData[2]))
        
        # Create player
        playerState = self.map.levelSavedData[0].split(':')
        # Convert tile coordinates to pixel coordinates
        player_x = int(playerState[0]) * TILESIZE
        player_y = int(playerState[1]) * TILESIZE
        self.player = Player(self, player_x, player_y, 0)  # lws = 0 as default
        
        # Set spawn point (convert from tile coordinates to pixel coordinates)
        spawn = self.map.levelSavedData[3].split(':')
        self.spawnPoint = vec(int(spawn[0]) * TILESIZE, int(spawn[1]) * TILESIZE)
        
        # Load saved game state
        self.global_time = int(self.map.levelSavedData[4])
        self.night_shade = int(self.map.levelSavedData[5])
        
        # Create camera
        self.camera = Camera(WIDTH, HEIGHT)
        
        # Load floating items
        for item in self.map.floatingItemsData:
            FloatingItem(self, item[0], item[1], item[2])
    
    def run(self):
        """Main game loop."""
        while self.playing:
            self.dt = self.clock.tick(FPS) / 1000
            self.events()
            self.update()
            self.draw()
    
    def quit(self):
        """Quit the game."""
        pg.quit()
        sys.exit()
    
    def update(self):
        """Update game state."""
        self.now = pg.time.get_ticks()
        self.mousePos = pg.mouse.get_pos()

        # Auto-save logic
        if self.now >= self.last_save + SAVE_DELAY:
            if self.hasPlayerStateChanged:
                self.game_state_manager.save_game()
                self.last_save = self.now

        if not self.isGamePaused:
            self.world_manager.reload_chunks()
            self.moving_sprites.update()
            self.camera.update(self.player.pos)
            self.game_state_manager.update_day_night_cycle()
            self.world_manager.handle_mob_spawning()

        if self.isInventoryOpened:
            self.player.inventory.hover(self.mousePos)

        if self.input_commands:
            self.input_commands_txt.update()
    
    def draw(self):
        """Draw the game."""
        self.render_manager.draw_game()
    
    def events(self):
        """Handle game events."""
        self.input_manager.handle_events()
    
    def _handle_events(self):
        """Legacy method for compatibility."""
        self.input_manager.handle_events()
    
    # Delegate methods to managers
    def reload_chunks(self):
        return self.world_manager.reload_chunks()
    
    def load_chunk(self, data):
        return self.world_manager.load_chunk(data)
    
    def load_tile(self, i):
        return self.world_manager.load_tile(i)
    
    def getCurrentPathfind(self):
        return self.world_manager.get_current_pathfind()
    
    def getTile(self, pos, getGround):
        return self.world_manager.get_tile(pos, getGround)
    
    def changeTile(self, pos, tile, toRemove):
        return self.world_manager.change_tile(pos, tile, toRemove)
    
    def giveItem(self, itemId, quantity):
        return self.game_state_manager.give_item(itemId, quantity)
    
    def dayNigthCycle(self):
        return self.game_state_manager.update_day_night_cycle()
    
    def skipNight(self):
        return self.game_state_manager.skip_night()
    
    def sleep(self):
        return self.game_state_manager.sleep()
    
    def save(self):
        return self.game_state_manager.save_game()
    
    def show_start_screen(self):
        """Show the start screen menu."""
        m = Menu(self, 0, 0, self.game_folder)

        while not self.playing:
            # Handle events
            for event in pg.event.get():
                if event.type == pg.QUIT:
                    self.quit()

                if event.type == pg.KEYDOWN:
                    if event.key == pg.K_ESCAPE:
                        if m.Page == 0:
                            self.quit()
                        else:
                            m.toggleGui(0)

                elif event.type == pg.MOUSEBUTTONDOWN:
                    if event.button == 1:
                        m.click(pg.mouse.get_pos())

                for box in m.inputBoxes:
                    box.handle_event(event)

            # Update
            m.hover(pg.mouse.get_pos())
            for box in m.inputBoxes:
                box.update()

            # Draw
            self.screen.blit(m.image, m.rect)
            for box in m.inputBoxes:
                box.draw(self.screen)
            pg.display.flip()

    def show_go_screen(self):
        """Start the main game."""
        self.new()
        self.run()
