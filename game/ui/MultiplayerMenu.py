"""
Multiplayer Menu - Handles multiplayer game options.

This module provides the user interface for multiplayer game options including
joining servers, hosting games, and configuring multiplayer settings.
"""

import pygame as pg
import time
from typing import Optional, Callable

from game.ui.InputBox import InputBox
from game.config.settings import *
from game.utils.logger import log_info, log_error, log_debug
from game.network.network_manager import NetworkManager, NetworkMode, NetworkMode


class MultiplayerMenu(pg.sprite.Sprite):
    """Multiplayer menu interface for hosting and joining games."""
    
    def __init__(self, game, xOffset, yOffset, game_folder):
        """Initialize the multiplayer menu."""
        self.groups = game.gui
        pg.sprite.Sprite.__init__(self, self.groups)
        self.game = game
        self.gameFolder = game_folder
        
        self.image = pg.Surface((len(game.menuData[0]) * TILESIZE, len(game.menuData) * TILESIZE), pg.SRCALPHA, 32)
        
        # Menu state
        self.page = 0  # 0: main multiplayer menu, 1: join server, 2: host server
        self.ui_list = []
        self.input_boxes = []
        self.status_message = ""
        self.status_color = WHITE
        
        # Network manager
        self.network_manager = NetworkManager(NetworkMode.CLIENT)
        
        # Join server settings
        self.server_address = "localhost:25565"
        self.player_name = "Player"
        
        # Host server settings  
        self.world_name = f"World-{str(time.time())[-5:]}"
        self.max_players = "10"
        self.server_port = "25565"
        
        self.rect = self.image.get_rect()
        self.xOffset = xOffset
        self.yOffset = yOffset
        self.rect.x = xOffset
        self.rect.y = yOffset
        
        self.toggle_gui(0)
    
    def toggle_gui(self, page):
        """Switch between different menu pages."""
        self.page = page
        self.ui_list = []
        self.input_boxes = []
        self.status_message = ""
        
        # Clear the surface
        self.image.fill((0, 0, 0, 0))
        
        # Draw menu background
        self._draw_menu_background()
        
        if page == 0:
            self._draw_main_multiplayer_menu()
        elif page == 1:
            self._draw_join_server_menu()
        elif page == 2:
            self._draw_host_server_menu()
    
    def _draw_menu_background(self):
        """Draw the menu background using the game's menu data."""
        for row, tiles in enumerate(self.game.menuData):
            for col, tile in enumerate(tiles):
                if tile != '.':
                    if tile == '0':
                        self.image.blit(self.game.menu_img.subsurface((1*TILESIZE, 1*TILESIZE, TILESIZE, TILESIZE)), (col*TILESIZE, row*TILESIZE))
                    elif tile == '1':
                        self.image.blit(self.game.menu_img.subsurface((0*TILESIZE, 0*TILESIZE, TILESIZE, TILESIZE)), (col*TILESIZE, row*TILESIZE))
                    elif tile == '2':
                        self.image.blit(self.game.menu_img.subsurface((1*TILESIZE, 0*TILESIZE, TILESIZE, TILESIZE)), (col*TILESIZE, row*TILESIZE))
                    elif tile == '3':
                        self.image.blit(self.game.menu_img.subsurface((2*TILESIZE, 0*TILESIZE, TILESIZE, TILESIZE)), (col*TILESIZE, row*TILESIZE))
                    elif tile == '4':
                        self.image.blit(self.game.menu_img.subsurface((2*TILESIZE, 1*TILESIZE, TILESIZE, TILESIZE)), (col*TILESIZE, row*TILESIZE))
                    elif tile == '5':
                        self.image.blit(self.game.menu_img.subsurface((2*TILESIZE, 2*TILESIZE, TILESIZE, TILESIZE)), (col*TILESIZE, row*TILESIZE))
                    elif tile == '6':
                        self.image.blit(self.game.menu_img.subsurface((1*TILESIZE, 2*TILESIZE, TILESIZE, TILESIZE)), (col*TILESIZE, row*TILESIZE))
                    elif tile == '7':
                        self.image.blit(self.game.menu_img.subsurface((0*TILESIZE, 2*TILESIZE, TILESIZE, TILESIZE)), (col*TILESIZE, row*TILESIZE))
                    elif tile == '8':
                        self.image.blit(self.game.menu_img.subsurface((0*TILESIZE, 1*TILESIZE, TILESIZE, TILESIZE)), (col*TILESIZE, row*TILESIZE))
    
    def _draw_main_multiplayer_menu(self):
        """Draw the main multiplayer menu options."""
        # Title
        title = self.game.font_64.render('Multiplayer', True, BLACK)
        self.image.blit(title, ((WIDTH / 2) - (title.get_width() / 2), 40))
        
        # Join Server button
        txt = self.game.font_32.render('Join Server', True, BLACK)
        x = (WIDTH / 2) - (txt.get_width() / 2)
        self.image.blit(txt, (x, 200))
        self.ui_list.append((x, 200, txt.get_width(), txt.get_height(), 1))
        
        # Host Server button
        txt = self.game.font_32.render('Host Server', True, BLACK)
        x = (WIDTH / 2) - (txt.get_width() / 2)
        self.image.blit(txt, (x, 250))
        self.ui_list.append((x, 250, txt.get_width(), txt.get_height(), 2))
        
        # Back button
        txt = self.game.font_32.render('Back', True, BLACK)
        x = (WIDTH / 2) - (txt.get_width() / 2)
        self.image.blit(txt, (x, 350))
        self.ui_list.append((x, 350, txt.get_width(), txt.get_height(), 0))
    
    def _draw_join_server_menu(self):
        """Draw the join server menu with input fields."""
        # Title
        title = self.game.font_32.render('Join Server', True, BLACK)
        self.image.blit(title, ((WIDTH / 2) - (title.get_width() / 2), 40))
        
        # Server Address label and input
        label = self.game.font_16.render('Server Address:', True, BLACK)
        self.image.blit(label, (100, 150))
        
        server_input = InputBox(self.game, 100, 180, 300, 32, self.server_address)
        self.input_boxes.append(("server_address", server_input))
        
        # Player Name label and input
        label = self.game.font_16.render('Player Name:', True, BLACK)
        self.image.blit(label, (100, 230))
        
        name_input = InputBox(self.game, 100, 260, 300, 32, self.player_name)
        self.input_boxes.append(("player_name", name_input))
        
        # Connect button
        txt = self.game.font_32.render('Connect', True, BLACK)
        x = (WIDTH / 2) - (txt.get_width() / 2)
        self.image.blit(txt, (x, 320))
        self.ui_list.append((x, 320, txt.get_width(), txt.get_height(), 3))
        
        # Back button
        txt = self.game.font_16.render('Back', True, BLACK)
        x = 100
        self.image.blit(txt, (x, 380))
        self.ui_list.append((x, 380, txt.get_width(), txt.get_height(), 0))
        
        # Status message
        if self.status_message:
            status = self.game.font_16.render(self.status_message, True, self.status_color)
            x = (WIDTH / 2) - (status.get_width() / 2)
            self.image.blit(status, (x, 420))
    
    def _draw_host_server_menu(self):
        """Draw the host server menu with input fields."""
        # Title
        title = self.game.font_32.render('Host Server', True, BLACK)
        self.image.blit(title, ((WIDTH / 2) - (title.get_width() / 2), 40))
        
        # World Name label and input
        label = self.game.font_16.render('World Name:', True, BLACK)
        self.image.blit(label, (100, 130))
        
        world_input = InputBox(self.game, 100, 160, 300, 32, self.world_name)
        self.input_boxes.append(("world_name", world_input))
        
        # Max Players label and input
        label = self.game.font_16.render('Max Players:', True, BLACK)
        self.image.blit(label, (100, 200))
        
        players_input = InputBox(self.game, 100, 230, 100, 32, self.max_players)
        self.input_boxes.append(("max_players", players_input))
        
        # Server Port label and input
        label = self.game.font_16.render('Port:', True, BLACK)
        self.image.blit(label, (250, 200))
        
        port_input = InputBox(self.game, 250, 230, 100, 32, self.server_port)
        self.input_boxes.append(("server_port", port_input))
        
        # Start Server button
        txt = self.game.font_32.render('Start Server', True, BLACK)
        x = (WIDTH / 2) - (txt.get_width() / 2)
        self.image.blit(txt, (x, 300))
        self.ui_list.append((x, 300, txt.get_width(), txt.get_height(), 4))
        
        # Back button
        txt = self.game.font_16.render('Back', True, BLACK)
        x = 100
        self.image.blit(txt, (x, 360))
        self.ui_list.append((x, 360, txt.get_width(), txt.get_height(), 0))
        
        # Status message
        if self.status_message:
            status = self.game.font_16.render(self.status_message, True, self.status_color)
            x = (WIDTH / 2) - (status.get_width() / 2)
            self.image.blit(status, (x, 400))
    
    def handle_click(self, mouse_pos):
        """Handle mouse clicks on menu elements."""
        mx, my = mouse_pos
        mx -= self.xOffset
        my -= self.yOffset
        
        # Handle UI button clicks
        for ui_element in self.ui_list:
            x, y, w, h, action = ui_element
            if x <= mx <= x + w and y <= my <= y + h:
                if action == 0:  # Back
                    self.toggle_gui(0)
                elif action == 1:  # Join Server (from main menu)
                    self.toggle_gui(1)
                elif action == 2:  # Host Server (from main menu)
                    self.toggle_gui(2)
                elif action == 3:  # Connect (from join menu)
                    self.connect_to_server()
                elif action == 4:  # Start Server (from host menu)
                    self.start_server()
                return True
        
        # Handle input box clicks
        for name, input_box in self.input_boxes:
            if input_box.rect.collidepoint(mouse_pos):
                # Deactivate all other input boxes first
                for _, other_box in self.input_boxes:
                    other_box.active = False
                    other_box.color = BLACK
                
                # Activate this input box
                input_box.active = True
                input_box.color = WHITE
                return True
        
        return False
    
    def handle_key_event(self, event):
        """Handle keyboard events for input boxes."""
        for name, input_box in self.input_boxes:
            input_box.handle_event(event)
            
            # Update our stored values
            if name == "server_address":
                self.server_address = input_box.text
            elif name == "player_name":
                self.player_name = input_box.text
            elif name == "world_name":
                self.world_name = input_box.text
            elif name == "max_players":
                self.max_players = input_box.text
            elif name == "server_port":
                self.server_port = input_box.text
    
    def connect_to_server(self):
        """Attempt to connect to a multiplayer server."""
        try:
            if not self.server_address or not self.player_name:
                self.status_message = "Please fill in all fields"
                self.status_color = (255, 100, 100)
                self.toggle_gui(1)  # Refresh display
                return
            
            # Parse server address
            if ':' in self.server_address:
                host, port = self.server_address.split(':')
                port = int(port)
            else:
                host = self.server_address
                port = 25565
            
            self.status_message = "Connecting..."
            self.status_color = (255, 255, 100)
            self.toggle_gui(1)  # Refresh display
            
            log_info(f"Attempting to connect to {host}:{port} as {self.player_name}")
            
            # Set the network manager reference before connecting
            self.game.setup_network_manager(self.network_manager)
            
            # Set up connection callback to handle successful authentication
            def on_connect_success(player_id):
                log_info(f"Connection and authentication successful for player {player_id}")
                # Set a flag instead of immediately starting the game
                self.game.multiplayer_ready = True
                self.game.worldName = "Server World"
                # Don't reassign network_manager here - it's already set
                # self.game.network_manager = self.network_manager
                self.game.game_mode = "multiplayer_client"
            
            # Set the callback
            self.network_manager.on_connect = on_connect_success
            
            # Connect to server using network manager
            if self.network_manager.connect_to_server(host, port, self.player_name, "Server World"):
                log_info("Connection and authentication successful")
            else:
                self.status_message = "Failed to connect to server"
                self.status_color = (255, 100, 100)
                self.toggle_gui(1)  # Refresh display
                
        except Exception as e:
            log_error(f"Connection error: {e}")
            self.status_message = f"Connection error: {str(e)}"
            self.status_color = (255, 100, 100)
            self.toggle_gui(1)  # Refresh display
    
    def start_server(self):
        """Start hosting a multiplayer server."""
        try:
            if not self.world_name or not self.max_players or not self.server_port:
                self.status_message = "Please fill in all fields"
                self.status_color = (255, 100, 100)
                self.toggle_gui(2)  # Refresh display
                return
            
            self.status_message = "Starting server..."
            self.status_color = (255, 255, 100)
            self.toggle_gui(2)  # Refresh display
            
            port = int(self.server_port)
            max_players = int(self.max_players)
            
            log_info(f"Starting server on port {port} with max {max_players} players")
            
            # Create a local server network manager
            from game.network.network_manager import NetworkMode
            server_network_manager = NetworkManager(NetworkMode.LOCAL_SERVER)
            
            # Start local server
            if server_network_manager.start_local_server(port, max_players):
                # Connect to our own server as host
                if server_network_manager.connect_to_server("localhost", port, "Host", self.world_name):
                    log_info("Successfully started server and connected as host")
                    # Set world name for host
                    self.game.worldName = self.world_name
                    # Start multiplayer host game
                    self.game.start_multiplayer_host(server_network_manager)
                else:
                    self.status_message = "Failed to connect to local server"
                    self.status_color = (255, 100, 100)
                    self.toggle_gui(2)  # Refresh display
            else:
                self.status_message = "Failed to start server"
                self.status_color = (255, 100, 100)
                self.toggle_gui(2)  # Refresh display
                
        except Exception as e:
            log_error(f"Server start error: {e}")
            self.status_message = f"Server error: {str(e)}"
            self.status_color = (255, 100, 100)
            self.toggle_gui(2)  # Refresh display
    
    def update(self):
        """Update input boxes."""
        for name, input_box in self.input_boxes:
            input_box.update()
    
    def draw_input_boxes(self, screen):
        """Draw all input boxes on the screen."""
        for name, input_box in self.input_boxes:
            input_box.draw(screen)
