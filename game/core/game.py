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
from game.config.game_config import GameConfig
from game.utils.logger import log_info, log_error, log_warning, log_debug, log_game_event
from game.utils.performance import get_performance_monitor, time_operation
from game.utils.audio_utils import create_safe_audio_player
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
        """Initialize the game with comprehensive error handling."""
        log_info("Initializing Game...")
        
        try:
            self.game_folder = path.dirname(path.dirname(path.dirname(__file__)))  # Go up one level from game/core
            log_debug(f"Game folder: {self.game_folder}")

            self._init_pygame()
            self._init_display()
            self._init_game_state()
            self._init_sprite_groups()
            
            # Load all resources with error handling
            log_info("Loading game resources...")
            self.resource_manager = ResourceManager(self.game_folder)
            self.resource_manager.load_all_resources()
            
            # Create safe audio player
            self.safe_audio = create_safe_audio_player(self.resource_manager.audio)
            log_debug("Safe audio player created")
            
            # Initialize performance monitoring
            self.performance_monitor = get_performance_monitor()
            
            # Initialize managers
            log_debug("Initializing game managers...")
            self.world_manager = WorldManager(self)
            self.game_state_manager = GameStateManager(self)
            self.render_manager = RenderManager(self)
            self.input_manager = InputManager(self)
            
            # Create input box
            self.input_commands_txt = InputBox(
                self, 20, HEIGHT - 60, 600, 40, limit=999)
            
            log_info("Game initialization completed successfully")
            log_game_event("game_initialized", {
                "debug_mode": GameConfig.DEBUG_MODE,
                "audio_enabled": len(self.resource_manager.audio) > 0
            })
            
        except Exception as e:
            log_error(f"Failed to initialize game: {e}")
            raise
        
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
        
        # Track player's current chunk for efficient chunk reloading
        self.last_player_chunk = None
        
        # Multiplayer game modes
        self.game_mode = "menu"  # "menu", "singleplayer", "multiplayer_client", "multiplayer_host"
        self.network_manager = None
        self.multiplayer_players = pg.sprite.Group()  # For remote players
        
        # Setup network message handlers
        self._setup_network_handlers()
        
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
    
    # Spawn point property
    @property
    def spawnPoint(self):
        """Get the current spawn point."""
        return getattr(self, '_spawnPoint', vec(0, 0))
    
    @spawnPoint.setter
    def spawnPoint(self, value):
        """Set spawn point."""
        self._spawnPoint = value
    
    # Utility methods for improved game management
    def play_sound(self, sound_name: str, volume: float = None) -> bool:
        """Safely play a sound effect."""
        if hasattr(self, 'safe_audio'):
            return self.safe_audio.play_sound(sound_name, volume)
        else:
            # Fallback for legacy audio system
            try:
                if sound_name in self.audioList:
                    pg.mixer.Sound.play(self.audioList[sound_name])
                    return True
            except Exception as e:
                log_warning(f"Failed to play sound {sound_name}: {e}")
            return False
    
    def play_sound_positional(self, sound_name: str, sound_pos: tuple, max_distance: float = 300.0) -> bool:
        """Play a sound with positional audio based on player distance."""
        if hasattr(self, 'safe_audio') and hasattr(self, 'player'):
            player_pos = (self.player.pos.x, self.player.pos.y)
            return self.safe_audio.play_sound_positional(sound_name, player_pos, sound_pos, max_distance)
        return False
    
    def cleanup_floating_items(self):
        """Clean up old floating items to prevent memory leaks."""
        if len(self.floatingItems) > GameConfig.MAX_FLOATING_ITEMS:
            # Remove oldest items first
            items_to_remove = len(self.floatingItems) - GameConfig.MAX_FLOATING_ITEMS
            for i, item in enumerate(self.floatingItems):
                if i >= items_to_remove:
                    break
                item.kill()
            log_debug(f"Cleaned up {items_to_remove} floating items")
    
    def get_performance_info(self) -> dict:
        """Get current performance information."""
        if self.performance_monitor:
            return self.performance_monitor.get_performance_report()
        return {}
        
        
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
    def player_sprite(self):  # Keep the typo for compatibility
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
        log_info(f"Starting new game in {self.game_mode} mode")
        if hasattr(self, 'network_manager') and self.network_manager:
            log_info(f"Network manager status at start of new(): {self.network_manager.is_connected()}")
        
        pg.mouse.set_visible(False)
        
        # For multiplayer client, create a minimal map without loading from disk
        if self.game_mode == "multiplayer_client":
            log_info("Creating client-side map for multiplayer")
            # Create a minimal map for multiplayer client
            from game.world.Map import Map
            # Use a dummy path that won't load any data
            self.map = Map("__client_temp__", None)  # None game_folder prevents loading
        else:
            # Create map with game folder for new data manager
            self.map = Map(path.join(self.game_folder, 'saves/' + self.worldName), self.game_folder)
        
        # Create pathfinding matrix
        self.pathfind = [vec(0, 0), [[1] * (CHUNKRENDERX * 2 + 2) * CHUNKSIZE] * (
            CHUNKRENDERY * 2 + 2) * CHUNKSIZE]
        
        # Create chunk manager
        if self.game_mode == "multiplayer_client":
            # For multiplayer client, create chunk manager without loading from disk
            self.chunkmanager = Chunk("__client_temp__", 0, None)
        else:
            self.chunkmanager = Chunk(path.join(
                self.game_folder, 'saves/' + self.worldName), int(self.map.levelSavedData[2]), self.game_state_manager.data_manager)
        
        # Create player
        if self.game_mode == "multiplayer_client":
            # For multiplayer client, use default spawn position (server will update)
            player_x = 0 * TILESIZE
            player_y = 0 * TILESIZE
            self.spawnPoint = vec(0 * TILESIZE, 0 * TILESIZE)
        else:
            playerState = self.map.levelSavedData[0].split(':')
            # Convert tile coordinates to pixel coordinates
            player_x = int(playerState[0]) * TILESIZE
            player_y = int(playerState[1]) * TILESIZE
            # Set spawn point (convert from tile coordinates to pixel coordinates)
            spawn = self.map.levelSavedData[3].split(':')
            self.spawnPoint = vec(int(spawn[0]) * TILESIZE, int(spawn[1]) * TILESIZE)
        
        self.player = Player(self, player_x, player_y, 0)  # lws = 0 as default
        
        # Load saved game state
        if self.game_mode == "multiplayer_client":
            # For multiplayer client, use default values (server will sync)
            self.global_time = 0
            self.night_shade = 255
        else:
            self.global_time = int(self.map.levelSavedData[4])
            self.night_shade = int(self.map.levelSavedData[5])
        
        # Create camera
        self.camera = Camera(WIDTH, HEIGHT)
        
        # Load floating items (only for non-multiplayer client)
        if self.game_mode != "multiplayer_client":
            for item in self.map.floatingItemsData:
                FloatingItem(self, item[0], item[1], item[2])
        
        # Initialize networking if needed
        if self.game_mode in ["multiplayer_client", "multiplayer_host"] and self.network_manager:
            log_info("Initializing network functionality")
            log_info(f"Network manager status at end of new(): {self.network_manager.is_connected()}")
            # The network manager should already be configured by the menu
        
        # Apply pending world state if we're a multiplayer client
        if self.game_mode == "multiplayer_client" and hasattr(self, 'pending_world_state'):
            log_info("Applying pending world state after game initialization")
            world_state = self.pending_world_state
            delattr(self, 'pending_world_state')  # Clean up
            self._handle_world_state(world_state)
        
        log_info("Game initialization completed successfully")
    
    def run(self):
        """Main game loop with performance monitoring."""
        log_info("Starting main game loop")
        
        while self.playing:
            # Start frame timing
            if self.performance_monitor:
                self.performance_monitor.start_frame()
            
            # Update delta time
            self.dt = self.clock.tick(FPS) / 1000
            
            # Update FPS monitoring
            if self.performance_monitor:
                self.performance_monitor.update_fps(self.clock)
            
            # Process events
            with time_operation("events"):
                self.events()
            
            # Update game state
            with time_operation("update"):
                self.update()
            
            # Render frame
            with time_operation("render"):
                self.draw()
            
            # Periodic cleanup
            if self.now % GameConfig.ITEM_CLEANUP_INTERVAL < self.dt * 1000:
                self.cleanup_floating_items()
        
        log_info("Main game loop ended")
    
    def quit(self):
        """Quit the game with proper cleanup."""
        log_info("Shutting down game...")
        
        try:
            # Save game if needed
            if hasattr(self, 'hasPlayerStateChanged') and self.hasPlayerStateChanged:
                log_info("Auto-saving before quit...")
                try:
                    self.save()
                    log_info("Auto-save completed")
                except Exception as e:
                    log_error(f"Failed to save before quit: {e}")
            
            # Log performance info if available
            if GameConfig.DEBUG_MODE and self.performance_monitor:
                perf_info = self.get_performance_info()
                log_info(f"Final performance stats: {perf_info}")
            
            # Log game session info
            log_game_event("game_shutdown", {
                "world_name": getattr(self, 'worldName', 'unknown'),
                "playtime_seconds": getattr(self, 'global_time', 0) / 1000.0
            })
            
        except Exception as e:
            log_error(f"Error during cleanup: {e}")
        finally:
            log_info("Game shutdown complete")
            pg.quit()
            sys.exit()
    
    def update(self):
        """Update game state."""
        self.now = pg.time.get_ticks()
        self.mousePos = pg.mouse.get_pos()

        # Update network manager if in multiplayer mode
        if hasattr(self, 'network_manager') and self.network_manager:
            # Ensure network manager is running in multiplayer modes
            if self.game_mode in ["multiplayer_client", "multiplayer_host"] and not self.network_manager.running:
                log_info("Network manager not running, re-initializing...")
                self.network_manager.initialize()
            self.network_manager.update(self.dt)

        # Auto-save logic
        if self.now >= self.last_save + SAVE_DELAY:
            if self.hasPlayerStateChanged:
                self.game_state_manager.save_game()
                self.last_save = self.now

        if not self.isGamePaused:
            # Only reload chunks when player moves to a different chunk
            if hasattr(self, 'player') and hasattr(self.player, 'chunkpos'):
                current_chunk = (int(self.player.chunkpos.x), int(self.player.chunkpos.y))
                if self.last_player_chunk != current_chunk:
                    log_debug(f"Player moved to new chunk: {current_chunk}")
                    self.world_manager.reload_chunks()
                    self.last_player_chunk = current_chunk
            
            self.world_manager.update()  # Call world manager update for chunk cleanup
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
    
    def show_multiplayer_menu(self):
        """Show the multiplayer menu."""
        from game.ui.MultiplayerMenu import MultiplayerMenu
        
        # Initialize multiplayer ready flag
        self.multiplayer_ready = False
        m = MultiplayerMenu(self, 0, 0, self.game_folder)
        
        while not self.playing:
            # Handle events
            for event in pg.event.get():
                if event.type == pg.QUIT:
                    self.quit()
                    
                if event.type == pg.KEYDOWN:
                    if event.key == pg.K_ESCAPE:
                        if m.page == 0:
                            # Go back to main menu
                            self.show_start_screen()
                            return
                        else:
                            m.toggle_gui(0)
                    
                    # Handle key events for input boxes
                    m.handle_key_event(event)
                    
                elif event.type == pg.MOUSEBUTTONDOWN:
                    if event.button == 1:
                        if not m.handle_click(pg.mouse.get_pos()):
                            # No UI element was clicked, check for menu navigation
                            if m.page != 0:
                                m.toggle_gui(0)
            
            # Update
            m.update()
            
            # Check if multiplayer connection is ready
            if hasattr(self, 'multiplayer_ready') and self.multiplayer_ready:
                log_info("Multiplayer connection ready, starting client game...")
                # Clean up GUI elements before starting the game
                m.kill()  # Remove from sprite groups
                # Clear any remaining GUI elements from multiplayer menu
                for sprite in list(self.gui):
                    if hasattr(sprite, 'game') and sprite.game == self:
                        sprite.kill()
                self.start_multiplayer_client(self.network_manager)
                break
            
            # Draw
            self.screen.fill((50, 50, 50))
            self.screen.blit(m.image, m.rect)
            m.draw_input_boxes(self.screen)
            pg.display.flip()
        
        # Clean up any remaining GUI elements when exiting the menu
        if m and m.alive():
            m.kill()
        # Clear any remaining GUI elements from multiplayer menu
        for sprite in list(self.gui):
            if hasattr(sprite, 'game') and sprite.game == self:
                sprite.kill()
    
    def start_multiplayer_client(self, network_manager):
        """Start the game as a multiplayer client."""
        log_info("Setting up multiplayer client mode...")
        self.game_mode = "multiplayer_client"
        self.network_manager = network_manager
        # Ensure we have a world name set
        if not hasattr(self, 'worldName') or not self.worldName:
            self.worldName = "Server World"
        log_info(f"Starting multiplayer client game with world: {self.worldName}")
        log_info(f"Network manager connection status: {self.network_manager.is_connected()}")
        
        # Remove the sleep and see if it helps
        # import time
        # time.sleep(0.1)
        
        # Set playing to True to exit menu loop, then new() and run() will be called by show_go_screen()
        self.playing = True
        log_info("Multiplayer client setup complete, exiting menu...")
        log_info(f"Network manager connection status after setup: {self.network_manager.is_connected()}")
    
    def start_multiplayer_host(self, network_manager):
        """Start the game as a multiplayer host."""
        self.game_mode = "multiplayer_host"
        self.network_manager = network_manager
        # Ensure we have a world name set
        if not hasattr(self, 'worldName') or not self.worldName:
            self.worldName = "Host World"
        log_info(f"Starting multiplayer host game with world: {self.worldName}")
        # Set playing to False to exit menu loop, then new() and run() will be called by show_go_screen()
        self.playing = False
    
    def start_singleplayer_with_networking(self):
        """Start singleplayer game using client-server architecture."""
        from game.network.network_manager import NetworkManager, NetworkMode
        
        try:
            # Create network manager in local server mode
            self.network_manager = NetworkManager(NetworkMode.LOCAL_SERVER)
            
            # Start local server for singleplayer
            if self.network_manager.start_local_server(25565, 1):
                # Connect to our own server
                if self.network_manager.connect_to_server("localhost", 25565, "Player", self.worldName):
                    self.game_mode = "singleplayer"
                    self.playing = True
                    log_info("Started singleplayer game with networking")
                    return
            
            log_error("Failed to start singleplayer networking")
            # Fallback to regular singleplayer
            self.game_mode = "singleplayer"
            self.playing = True
                
        except Exception as e:
            log_error(f"Singleplayer networking error: {e}")
            # Fallback to regular singleplayer
            self.game_mode = "singleplayer"
            self.playing = True

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
        
        # Clean up GUI elements when exiting the menu
        if m and m.alive():
            m.kill()
        # Clear any remaining GUI elements from start menu
        for sprite in list(self.gui):
            if hasattr(sprite, 'game') and sprite.game == self:
                sprite.kill()

    def show_go_screen(self):
        """Start the main game based on the current game mode."""
        log_info(f"Starting game mode: {self.game_mode}")
        if hasattr(self, 'network_manager') and self.network_manager:
            log_info(f"Network manager status before game start: {self.network_manager.is_connected()}")
        
        if self.game_mode == "singleplayer":
            # Start singleplayer with client-server architecture
            self.start_singleplayer_with_networking()
            
        if self.game_mode in ["singleplayer", "multiplayer_client", "multiplayer_host"]:
            log_info("Calling new() to initialize game state...")
            if hasattr(self, 'network_manager') and self.network_manager:
                log_info(f"Network manager status before new(): {self.network_manager.is_connected()}")
            self.new()
            if hasattr(self, 'network_manager') and self.network_manager:
                log_info(f"Network manager status after new(): {self.network_manager.is_connected()}")
            log_info("Calling run() to start game loop...")
            if hasattr(self, 'network_manager') and self.network_manager:
                log_info(f"Network manager status before run(): {self.network_manager.is_connected()}")
            self.run()
        else:
            # Default behavior for backward compatibility
            self.new()
            self.run()
    
    def _setup_network_handlers(self):
        """Setup network message handlers for multiplayer."""
        self.network_message_handlers = {
            "WORLD_STATE": self._handle_world_state,
            "PLAYER_SPAWN_DATA": self._handle_player_spawn_data,
            "PLAYER_UPDATE": self._handle_player_update,
            "BLOCK_UPDATE": self._handle_block_update,
        }
    
    def setup_network_manager(self, network_manager):
        """Setup network manager and its callbacks."""
        self.network_manager = network_manager
        if network_manager:
            # Set the message callback to our handler
            network_manager.on_message = self._handle_network_message
    
    def _handle_network_message(self, message_type, data, player_id):
        """Handle incoming network messages."""
        try:
            from game.network.message_types import MessageType
            
            log_debug(f"Received network message: {message_type}")
            
            # Convert MessageType to string for easier handling
            message_type_name = message_type.name if hasattr(message_type, 'name') else str(message_type)
            
            handler = self.network_message_handlers.get(message_type_name)
            if handler:
                handler(data)
            else:
                log_debug(f"No handler for message type: {message_type_name}")
                
        except Exception as e:
            log_error(f"Error handling network message {message_type}: {e}")
    
    def _handle_world_state(self, data):
        """Handle world state synchronization from server."""
        log_info("=== WORLD STATE HANDLER CALLED ===")
        log_info(f"Game mode: {self.game_mode}")
        log_info(f"Current chunks in chunkmanager: {len(self.chunkmanager.get_chunks()) if hasattr(self, 'chunkmanager') and self.chunkmanager else 'None'}")
        
        # If chunk manager isn't initialized yet, store the world state for later
        if not hasattr(self, 'chunkmanager') or not self.chunkmanager:
            log_info("Chunk manager not initialized yet, storing world state for later application")
            self.pending_world_state = data
            return
        
        # Apply world state to the client game
        chunks = data.get('chunks', {})
        floating_items = data.get('floating_items', {})
        world_name = data.get('world_name', 'Unknown')
        
        log_info(f"Applying world state: {len(chunks)} chunks, {len(floating_items)} items")
        log_info(f"First few chunk keys: {list(chunks.keys())[:5]}")
        
        # Debug player position if player exists
        if hasattr(self, 'player') and self.player:
            log_info(f"Player position: ({self.player.pos.x}, {self.player.pos.y})")
            log_info(f"Player tile position: ({self.player.tilepos.x}, {self.player.tilepos.y})")
            log_info(f"Player chunk position: ({self.player.chunkpos.x}, {self.player.chunkpos.y})")
        
        # Update the client's chunk manager with the server's world data
        if hasattr(self, 'chunkmanager') and self.chunkmanager:
            # Clear any existing client-side chunks
            log_info("Clearing existing chunks...")
            self.chunkmanager.clearChunks()
            log_info(f"Chunks after clear: {len(self.chunkmanager.get_chunks())}")
            
            # Convert server chunks to client chunk manager format
            log_info("Converting and applying server chunks...")
            chunk_count = 0
            block_count = 0
            
            for chunk_key, chunk_blocks in chunks.items():
                chunk_x, chunk_y = map(int, chunk_key.split(','))
                
                # Create a 2D array for this chunk (client format)
                # Each cell contains a list of tile IDs (for layering support)
                from game.config.settings import CHUNKSIZE
                chunk_2d = [[[str(0).zfill(2)] for _ in range(CHUNKSIZE)] for _ in range(CHUNKSIZE)]
                
                # Convert server blocks to client format
                for block_key, block_id in chunk_blocks.items():
                    x, y = map(int, block_key.split(','))
                    
                    # Calculate chunk-local coordinates properly handling negative values
                    local_x = x - (chunk_x * CHUNKSIZE)
                    local_y = y - (chunk_y * CHUNKSIZE)
                    
                    # Ensure coordinates are within chunk bounds
                    if 0 <= local_x < CHUNKSIZE and 0 <= local_y < CHUNKSIZE:
                        # Handle block_id which comes as a list from the server
                        if isinstance(block_id, list):
                            # Use the block list directly as sent from server
                            chunk_2d[local_y][local_x] = block_id
                        else:
                            # Convert single block ID to tile string format (pad with zero if needed)
                            tile_str = f"{block_id:02d}"
                            chunk_2d[local_y][local_x] = [tile_str]
                        block_count += 1
                        
                    # Debug: Verify coordinate conversion for first few blocks
                    if chunk_count == 0 and block_count <= 5:
                        log_debug(f"Block at world ({x},{y}) -> chunk ({chunk_x},{chunk_y}) local ({local_x},{local_y}) = {block_id}")
                
                # Store the chunk in the client's chunk manager
                chunk_name = f"{chunk_x},{chunk_y}"
                self.chunkmanager.chunks[chunk_name] = chunk_2d
                
                # Mark the chunk as accessed for memory management
                self.chunkmanager.access_chunk(chunk_name)
                
                chunk_count += 1
                
                log_debug(f"Converted chunk ({chunk_x}, {chunk_y}) with {len(chunk_blocks)} blocks")
            
            log_info(f"Applied {chunk_count} chunks with {block_count} blocks")
            log_info(f"Final chunks in chunkmanager: {len(self.chunkmanager.get_chunks())}")
        
        # Clear and spawn floating items
        if hasattr(self, 'floatingItems'):
            for item in self.floatingItems:
                item.kill()
            self.floatingItems.empty()
        
        # Spawn server floating items
        for item_id, item_data in floating_items.items():
            FloatingItem(self, 
                        item_data['x'], 
                        item_data['y'], 
                        item_data['item_type'],
                        item_data['quantity'])
        
        log_info("=== WORLD STATE APPLIED SUCCESSFULLY ===")
        log_info(f"Final chunks in chunkmanager: {len(self.chunkmanager.get_chunks()) if hasattr(self, 'chunkmanager') and self.chunkmanager else 'None'}")
    
    def _handle_player_spawn_data(self, data):
        """Handle player spawn data from server."""
        player_id = data.get('player_id')
        player_name = data.get('player_name', 'Unknown')
        x = data.get('x', 0)
        y = data.get('y', 0)
        health = data.get('health', 100)
        max_health = data.get('max_health', 100)
        facing_direction = data.get('facing_direction', 'right')
        
        log_info(f"Spawning player: {player_name} at ({x}, {y})")
        
        # If this is our own player, update our position
        if hasattr(self, 'network_manager') and self.network_manager and player_id == self.network_manager.player_id:
            if hasattr(self, 'player'):
                self.player.pos.x = x
                self.player.pos.y = y
                self.player.health = health
        else:
            # Spawn other player entity
            # Create multiplayer player representation
            remote_player = Player(self, x, y, 0)
            remote_player.player_id = player_id
            remote_player.player_name = player_name
            remote_player.health = health
            # Add to multiplayer players group
            self.multiplayer_players.add(remote_player)
            log_info(f"Added remote player {player_name} to multiplayer_players group")
    
    def _handle_player_update(self, data):
        """Handle player position updates from server."""
        player_id = data.get('player_id')
        x = data.get('x', 0)
        y = data.get('y', 0)
        health = data.get('health', 100)
        facing_direction = data.get('facing_direction', 'right')
        
        # Update remote player position
        for remote_player in self.multiplayer_players:
            if hasattr(remote_player, 'player_id') and remote_player.player_id == player_id:
                remote_player.pos.x = x
                remote_player.pos.y = y
                remote_player.health = health
                break
    
    def _handle_block_update(self, data):
        """Handle block updates from server."""
        x = data.get('x', 0)
        y = data.get('y', 0)
        block_id = data.get('block_id', 0)
        
        # Apply block change to local world
        if hasattr(self, 'chunkmanager'):
            self.chunkmanager.set_block(x, y, block_id)
