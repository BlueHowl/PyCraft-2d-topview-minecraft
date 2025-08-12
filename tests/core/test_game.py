"""Tests for core game functionality."""

import unittest
import pygame as pg
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from tests.test_config import BaseTestCase, MockGame
from game.core.game import Game
from game.config.settings import WIDTH, HEIGHT, FPS, TILESIZE


class TestGame(BaseTestCase):
    """Test cases for the main Game class."""
    
    def setUp(self):
        super().setUp()
        
    @patch('game.core.game.ResourceManager')
    @patch('game.core.game.WorldManager')
    @patch('game.core.game.GameStateManager')
    @patch('game.core.game.RenderManager')
    @patch('game.core.game.InputManager')
    @patch('game.ui.InputBox.InputBox')  # Mock InputBox to avoid font issues
    def test_game_initialization(self, mock_input_box, mock_input, mock_render, mock_game_state, mock_world, mock_resource):
        """Test that game initializes properly."""
        # Mock the resource manager
        mock_resource_instance = Mock()
        mock_resource.return_value = mock_resource_instance
        mock_resource_instance.load_all_resources.return_value = None
        mock_resource_instance.fonts = {
            'font_64': Mock(),
            'font_32': Mock(),
            'font_16': Mock(),
            'font_10': Mock()
        }
        mock_resource_instance.images = {}
        mock_resource_instance.audio = {}
        mock_resource_instance.data = {}
        
        # Mock InputBox
        mock_input_box.return_value = Mock()
        
        with patch('pygame.init'), \
             patch('pygame.display.set_mode'), \
             patch('pygame.time.Clock'), \
             patch('game.core.game.create_safe_audio_player'), \
             patch('game.core.game.get_performance_monitor'):
            
            game = Game()
            
            # Verify game state initialization
            self.assertTrue(game.playing)
            self.assertFalse(game.isGamePaused)
            self.assertEqual(game.now, 0)
            self.assertFalse(game.isInventoryOpened)
    
    def test_game_properties(self):
        """Test game property accessors."""
        game = self.mock_game
        
        # Test spawn point property
        test_spawn = pg.math.Vector2(100, 200)
        game.spawnPoint = test_spawn
        self.assertEqual(game.spawnPoint, test_spawn)
    
    def test_play_sound(self):
        """Test sound playing functionality."""
        game = self.mock_game
        
        # Test successful sound play
        result = game.play_sound('test_sound')
        self.assertTrue(result)
        
        # Test with volume
        result = game.play_sound('test_sound', volume=0.5)
        self.assertTrue(result)
    
    def test_sprite_group_initialization(self):
        """Test that all sprite groups are properly initialized."""
        game = self.mock_game
        
        # Check all sprite groups exist
        sprite_groups = [
            'all_sprites', 'moving_sprites', 'player_collisions',
            'grounds', 'floatingItems', 'players', 'mobs',
            'Layer1', 'projectiles', 'gui'
        ]
        
        for group_name in sprite_groups:
            self.assertTrue(hasattr(game, group_name))
            self.assertIsInstance(getattr(game, group_name), pg.sprite.Group)


class TestGameState(BaseTestCase):
    """Test cases for game state management."""
    
    def setUp(self):
        super().setUp()
    
    def test_game_pause_state(self):
        """Test game pause functionality."""
        game = self.mock_game
        
        # Initially not paused
        self.assertFalse(game.isGamePaused)
        
        # Test pause
        game.isGamePaused = True
        self.assertTrue(game.isGamePaused)
        
        # Test unpause
        game.isGamePaused = False
        self.assertFalse(game.isGamePaused)
    
    def test_inventory_state(self):
        """Test inventory open/close state."""
        game = self.mock_game
        
        # Initially closed
        self.assertFalse(game.isInventoryOpened)
        
        # Test open
        game.isInventoryOpened = True
        self.assertTrue(game.isInventoryOpened)
        
        # Test close
        game.isInventoryOpened = False
        self.assertFalse(game.isInventoryOpened)
    
    def test_time_management(self):
        """Test game time tracking."""
        game = self.mock_game
        
        # Initial time
        self.assertEqual(game.global_time, 0)
        self.assertEqual(game.day_time, 0)
        
        # Update time
        game.global_time = 1000
        game.day_time = 500
        
        self.assertEqual(game.global_time, 1000)
        self.assertEqual(game.day_time, 500)


class TestGameResourceAccess(BaseTestCase):
    """Test cases for game resource access."""
    
    def setUp(self):
        super().setUp()
    
    def test_font_access(self):
        """Test font resource access."""
        game = self.mock_game
        
        # Test font properties exist
        self.assertIsNotNone(game.fonts)
        self.assertIn('font_64', game.fonts)
        self.assertIn('font_32', game.fonts)
        self.assertIn('font_16', game.fonts)
        self.assertIn('font_10', game.fonts)
    
    def test_image_access(self):
        """Test image resource access."""
        game = self.mock_game
        
        # Test image properties exist
        self.assertIsNotNone(game.images)
        required_images = [
            'tile_images', 'player_sprite', 'hearts', 'hotbar',
            'menu', 'items', 'crosshair', 'light'
        ]
        
        for image_key in required_images:
            self.assertIn(image_key, game.images)
    
    def test_data_access(self):
        """Test game data access."""
        game = self.mock_game
        
        # Test data properties exist
        self.assertIsNotNone(game.data)
        required_data = [
            'mob_list', 'item_texture_coordinate', 'menu_map',
            'inventory_map', 'craft_list', 'item_assignment_list'
        ]
        
        for data_key in required_data:
            self.assertIn(data_key, game.data)


if __name__ == '__main__':
    unittest.main()
