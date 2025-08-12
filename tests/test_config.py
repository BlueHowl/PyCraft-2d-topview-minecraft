"""
Test configuration and utilities for the PyCraft test suite.
"""
import os
import sys
import unittest
import pygame as pg
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

# Add the game directory to Python path for imports
GAME_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(GAME_DIR))

# Import game modules
from game.config.settings import *
from game.config.game_config import GameConfig


class MockGame:
    """Mock game object for testing without full initialization."""
    
    def __init__(self):
        self.now = 0
        self.mousePos = (0, 0)
        self.isGamePaused = False
        self.isInventoryOpened = False
        self.playing = True
        self.global_time = 0
        self.day_time = 0
        self.night_shade = 255
        self.worldName = "test_world"
        self.spawnPoint = pg.math.Vector2(0, 0)
        
        # Mock sprite groups
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
        
        # Mock managers
        self.world_manager = Mock()
        self.game_state_manager = Mock()
        self.render_manager = Mock()
        self.input_manager = Mock()
        self.camera = Mock()
        self.map = Mock()
        self.player = Mock()
        
        # Mock resource properties
        self._mock_resources()
        
    def _mock_resources(self):
        """Setup mock resources."""
        self._fonts = {
            'font_64': Mock(),
            'font_32': Mock(),
            'font_16': Mock(),
            'font_10': Mock()
        }
        
        self._images = {
            'tile_images': Mock(),
            'player_sprite': Mock(),
            'hearts': Mock(),
            'hotbar': Mock(),
            'menu': Mock(),
            'items': Mock(),
            'crosshair': Mock(),
            'light': Mock()
        }
        
        self._audio = {}
        
        self._data = {
            'mob_list': [],
            'item_texture_coordinate': {},
            'menu_map': [],
            'inventory_map': [],
            'furnaceUi_map': [],
            'chestUi_map': [],
            'craft_list': [],
            'item_assignment_list': [],
            'furnace_fuel_list': [],
            'texture_coordinate': {}
        }
    
    @property
    def fonts(self):
        return self._fonts
    
    @property
    def images(self):
        return self._images
    
    @property
    def audio(self):
        return self._audio
    
    @property
    def data(self):
        return self._data
    
    def play_sound(self, sound_name, volume=None):
        """Mock sound playing."""
        return True
    
    def changeTile(self, pos, tile, toRemove):
        """Mock tile changing."""
        pass


class BaseTestCase(unittest.TestCase):
    """Base test case with common setup for pygame tests."""
    
    @classmethod
    def setUpClass(cls):
        """Setup pygame for testing."""
        pg.init()
        pg.display.set_mode((WIDTH, HEIGHT), pg.HIDDEN)
    
    @classmethod
    def tearDownClass(cls):
        """Cleanup pygame after testing."""
        pg.quit()
    
    def setUp(self):
        """Setup common test fixtures."""
        self.mock_game = MockGame()
        
    def tearDown(self):
        """Cleanup after each test."""
        # Clear all sprite groups
        for group in [self.mock_game.all_sprites, self.mock_game.moving_sprites,
                     self.mock_game.player_collisions, self.mock_game.grounds,
                     self.mock_game.floatingItems, self.mock_game.players,
                     self.mock_game.mobs, self.mock_game.Layer1,
                     self.mock_game.projectiles, self.mock_game.gui]:
            group.empty()


def create_mock_surface(width=32, height=32):
    """Create a mock pygame surface for testing."""
    return pg.Surface((width, height))


def create_mock_rect(x=0, y=0, width=32, height=32):
    """Create a mock pygame rect for testing."""
    return pg.Rect(x, y, width, height)


# Test data constants
TEST_PLAYER_POS = pg.math.Vector2(100, 100)
TEST_TILE_SIZE = TILESIZE
TEST_WORLD_SIZE = 10
