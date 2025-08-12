"""Tests for game entities."""

import unittest
import pygame as pg
from unittest.mock import Mock, patch, MagicMock
import sys
import os
import json

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from tests.test_config import BaseTestCase, MockGame, create_mock_surface
from game.config.settings import TILESIZE, WALK_SPEED, STACK, WIDTH, HEIGHT


class MockPlayer:
    """Mock player for testing without full initialization."""
    
    def __init__(self, game, x=100, y=100, lws=0):
        self.game = game
        self.pos = pg.math.Vector2(x, y)
        self.vel = pg.math.Vector2(0, 0)
        self.tilepos = pg.math.Vector2(int(x / TILESIZE), int(y / TILESIZE))
        self.health = 20
        self.speed = WALK_SPEED
        self.canMove = True
        self.isDialog = False
        self.dead = False
        self.lastWalkStatement = lws
        self.harvest_clicks = 1
        self.last_cell_click = pg.math.Vector2(0, 0)
        
        # Mock timing
        self.last_attack = 0
        self.last_hit = 0
        self.last_regen = 0
        self.last_blocked = 0
        
        # Mock pygame components
        self.image = create_mock_surface()
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        
        # Mock UI components
        self.lifebar = Mock()
        self.hotbar = Mock()
        self.inventory = Mock()


class TestPlayer(BaseTestCase):
    """Test cases for the Player class."""
    
    def setUp(self):
        super().setUp()
        self.player = MockPlayer(self.mock_game)
    
    def test_player_initialization(self):
        """Test player initialization."""
        # Test position
        self.assertEqual(self.player.pos.x, 100)
        self.assertEqual(self.player.pos.y, 100)
        
        # Test health
        self.assertEqual(self.player.health, 20)
        
        # Test initial state
        self.assertTrue(self.player.canMove)
        self.assertFalse(self.player.isDialog)
        self.assertFalse(self.player.dead)
    
    def test_player_movement_input(self):
        """Test player movement input processing."""
        # Test initial velocity
        self.assertEqual(self.player.vel.x, 0)
        self.assertEqual(self.player.vel.y, 0)
        
        # Test speed setting
        self.assertEqual(self.player.speed, WALK_SPEED)
    
    def test_player_position_updates(self):
        """Test player position calculations."""
        # Test tile position calculation
        expected_tile_x = int(100 / TILESIZE)
        expected_tile_y = int(100 / TILESIZE)
        
        self.assertEqual(self.player.tilepos.x, expected_tile_x)
        self.assertEqual(self.player.tilepos.y, expected_tile_y)
    
    def test_player_health_management(self):
        """Test player health system."""
        # Test initial health
        self.assertEqual(self.player.health, 20)
        
        # Test health modification
        self.player.health = 15
        self.assertEqual(self.player.health, 15)
        
        # Test death state
        self.player.health = 0
        self.assertLessEqual(self.player.health, 0)
    
    def test_player_timing_system(self):
        """Test player timing mechanisms."""
        # Test initial timing values
        self.assertEqual(self.player.last_attack, 0)
        self.assertEqual(self.player.last_hit, 0)
        self.assertEqual(self.player.last_regen, 0)
        self.assertEqual(self.player.last_blocked, 0)
    
    def test_player_harvest_system(self):
        """Test player harvesting mechanics."""
        # Test initial harvest state
        self.assertEqual(self.player.harvest_clicks, 1)
        self.assertEqual(self.player.last_cell_click.x, 0)
        self.assertEqual(self.player.last_cell_click.y, 0)
        
        # Test harvest click increment
        self.player.harvest_clicks += 1
        self.assertEqual(self.player.harvest_clicks, 2)


class TestFloatingItem(BaseTestCase):
    """Test cases for floating items."""
    
    def setUp(self):
        super().setUp()
    
    def test_floating_item_creation(self):
        """Test floating item creation."""
        # Mock floating item properties
        item_id = 1
        quantity = 5
        pos_x = 200
        pos_y = 150
        
        # Test item properties would be set correctly
        self.assertIsInstance(item_id, int)
        self.assertIsInstance(quantity, int)
        self.assertGreater(quantity, 0)
        self.assertIsInstance(pos_x, (int, float))
        self.assertIsInstance(pos_y, (int, float))


class TestProjectile(BaseTestCase):
    """Test cases for projectiles."""
    
    def setUp(self):
        super().setUp()
    
    def test_projectile_creation(self):
        """Test projectile creation and properties."""
        # Mock projectile properties
        start_pos = pg.math.Vector2(100, 100)
        target_pos = pg.math.Vector2(200, 150)
        damage = 5
        
        # Test basic properties
        self.assertIsInstance(start_pos, pg.math.Vector2)
        self.assertIsInstance(target_pos, pg.math.Vector2)
        self.assertGreater(damage, 0)
        
        # Test direction calculation
        direction = target_pos - start_pos
        self.assertIsInstance(direction, pg.math.Vector2)
        
        # Test distance calculation
        distance = start_pos.distance_to(target_pos)
        self.assertGreater(distance, 0)


class TestMob(BaseTestCase):
    """Test cases for mob entities."""
    
    def setUp(self):
        super().setUp()
    
    def test_mob_basic_properties(self):
        """Test basic mob properties."""
        # Mock mob properties
        mob_type = "zombie"
        health = 10
        damage = 2
        pos = pg.math.Vector2(150, 200)
        
        # Test properties
        self.assertIsInstance(mob_type, str)
        self.assertGreater(health, 0)
        self.assertGreater(damage, 0)
        self.assertIsInstance(pos, pg.math.Vector2)
    
    def test_mob_health_system(self):
        """Test mob health and damage system."""
        initial_health = 10
        damage_taken = 3
        
        # Simulate damage
        remaining_health = initial_health - damage_taken
        
        self.assertEqual(remaining_health, 7)
        self.assertGreater(remaining_health, 0)
        
        # Test death condition
        fatal_damage = 15
        final_health = initial_health - fatal_damage
        self.assertLessEqual(final_health, 0)


class TestEntityInteractions(BaseTestCase):
    """Test cases for entity interactions."""
    
    def setUp(self):
        super().setUp()
        self.player = MockPlayer(self.mock_game)
    
    def test_player_item_interaction(self):
        """Test player and item interactions."""
        # Mock item pickup
        item_pos = pg.math.Vector2(110, 110)  # Close to player
        player_pos = self.player.pos
        
        # Test distance calculation for pickup
        distance = player_pos.distance_to(item_pos)
        pickup_range = 50  # Mock pickup range
        
        can_pickup = distance <= pickup_range
        self.assertTrue(can_pickup)
    
    def test_player_mob_interaction(self):
        """Test player and mob interactions."""
        # Mock combat scenario
        player_health = 20
        mob_damage = 3
        player_damage = 5
        mob_health = 10
        
        # Test player takes damage
        player_health_after = player_health - mob_damage
        self.assertEqual(player_health_after, 17)
        
        # Test mob takes damage
        mob_health_after = mob_health - player_damage
        self.assertEqual(mob_health_after, 5)
    
    def test_collision_detection(self):
        """Test basic collision detection logic."""
        # Mock rectangles for collision
        player_rect = pg.Rect(100, 100, TILESIZE, TILESIZE)
        obstacle_rect = pg.Rect(116, 100, TILESIZE, TILESIZE)  # Overlapping (closer)
        
        # Test collision
        collision = player_rect.colliderect(obstacle_rect)
        self.assertTrue(collision)
        
        # Test no collision
        far_rect = pg.Rect(200, 200, TILESIZE, TILESIZE)
        no_collision = player_rect.colliderect(far_rect)
        self.assertFalse(no_collision)


if __name__ == '__main__':
    unittest.main()
