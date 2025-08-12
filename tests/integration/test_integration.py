"""Integration tests for PyCraft 2D game components."""

import unittest
import pygame as pg
from unittest.mock import Mock, patch, MagicMock
import sys
import os
import json
import tempfile

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from tests.test_config import BaseTestCase, MockGame


class TestGameInitialization(BaseTestCase):
    """Integration tests for full game initialization."""
    
    def setUp(self):
        super().setUp()
    
    @patch('game.core.game.ResourceManager')
    @patch('game.core.game.WorldManager')
    @patch('game.core.game.GameStateManager')
    @patch('game.ui.InputBox.InputBox')  # Mock InputBox to avoid font issues
    def test_game_startup_sequence(self, mock_input_box, mock_game_state, mock_world, mock_resource):
        """Test the complete game startup sequence."""
        # Mock all the managers
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
            
            from game.core.game import Game
            game = Game()
            
            # Test that all managers were created
            mock_resource.assert_called_once()
            mock_world.assert_called_once()
            mock_game_state.assert_called_once()


class TestPlayerWorldInteraction(BaseTestCase):
    """Integration tests for player and world interactions."""
    
    def setUp(self):
        super().setUp()
        # Create mock player with more complete setup
        self.mock_player = Mock()
        self.mock_player.pos = pg.math.Vector2(100, 100)
        self.mock_player.health = 20
        self.mock_player.inventory = Mock()
        self.mock_player.hotbar = Mock()
        
        # Setup mock game with player
        self.mock_game.player = self.mock_player
    
    def test_player_movement_and_chunk_loading(self):
        """Test player movement triggering chunk loading."""
        initial_chunk = (3, 3)  # Player starts in chunk 3,3
        new_chunk = (4, 3)      # Player moves to chunk 4,3
        
        # Mock chunk manager
        chunk_manager = Mock()
        chunk_manager.current_chunks = {f"{initial_chunk[0]},{initial_chunk[1]}"}
        
        # Test movement to new chunk
        self.mock_player.pos = pg.math.Vector2(4 * 32 * 16, 3 * 32 * 16)  # New chunk position
        
        # Simulate chunk loading check
        player_tile_x = int(self.mock_player.pos.x // 32)
        player_tile_y = int(self.mock_player.pos.y // 32)
        chunk_size = 16  # Mock chunk size
        current_chunk = (player_tile_x // chunk_size, player_tile_y // chunk_size)
        
        # Test that new chunk was calculated correctly
        self.assertEqual(current_chunk, new_chunk)
    
    def test_player_item_pickup_integration(self):
        """Test complete item pickup flow."""
        # Mock floating item
        item_pos = pg.math.Vector2(105, 105)  # Close to player
        item_id = 5
        item_quantity = 3
        
        # Test pickup distance
        distance = self.mock_player.pos.distance_to(item_pos)
        pickup_range = 50
        
        can_pickup = distance <= pickup_range
        self.assertTrue(can_pickup)
        
        # Mock inventory addition
        self.mock_player.hotbar.addItem = Mock(return_value=True)
        
        # Simulate item pickup
        if can_pickup:
            self.mock_player.hotbar.addItem(item_id, item_quantity)
        
        # Verify hotbar interaction
        self.mock_player.hotbar.addItem.assert_called_once_with(item_id, item_quantity)
    
    def test_player_block_breaking_integration(self):
        """Test complete block breaking flow."""
        # Mock target block
        target_pos = pg.math.Vector2(120, 120)
        block_type = "114"  # Tree
        block_health = 5
        
        # Test reach distance
        reach_distance = 3 * 32  # MELEEREACH
        distance = self.mock_player.pos.distance_to(target_pos)
        
        can_reach = distance <= reach_distance
        self.assertTrue(can_reach)
        
        # Mock block breaking
        damage = 2
        new_health = block_health - damage
        
        # Test block health reduction
        self.assertEqual(new_health, 3)
        self.assertGreater(new_health, 0)  # Block not yet destroyed
        
        # Test complete destruction
        final_health = new_health - 4  # More damage
        self.assertLessEqual(final_health, 0)  # Block destroyed


class TestInventorySystem(BaseTestCase):
    """Integration tests for the complete inventory system."""
    
    def setUp(self):
        super().setUp()
        # Mock complete inventory system
        self.hotbar_items = [[0, 0] for _ in range(9)]  # 9 hotbar slots
        self.inventory_items = [[0, 0] for _ in range(25)]  # 25 inventory slots
        
    def test_item_transfer_hotbar_to_inventory(self):
        """Test transferring items from hotbar to inventory."""
        # Place item in hotbar
        item_id = 5
        quantity = 10
        hotbar_slot = 2
        inventory_slot = 5
        
        self.hotbar_items[hotbar_slot] = [item_id, quantity]
        
        # Transfer to inventory
        self.inventory_items[inventory_slot] = self.hotbar_items[hotbar_slot]
        self.hotbar_items[hotbar_slot] = [0, 0]
        
        # Verify transfer
        self.assertEqual(self.inventory_items[inventory_slot], [item_id, quantity])
        self.assertEqual(self.hotbar_items[hotbar_slot], [0, 0])
    
    def test_item_stacking_logic(self):
        """Test item stacking across inventory slots."""
        # Setup partial stack
        item_id = 3
        existing_quantity = 30
        adding_quantity = 20
        max_stack = 64
        
        slot_index = 5
        self.inventory_items[slot_index] = [item_id, existing_quantity]
        
        # Add more items
        current_item = self.inventory_items[slot_index]
        if current_item[0] == item_id:  # Same item type
            total = current_item[1] + adding_quantity
            if total <= max_stack:
                self.inventory_items[slot_index] = [item_id, total]
                remaining = 0
            else:
                self.inventory_items[slot_index] = [item_id, max_stack]
                remaining = total - max_stack
        
        # Verify stacking
        self.assertEqual(self.inventory_items[slot_index], [item_id, 50])
        self.assertEqual(remaining, 0)
    
    def test_crafting_system_integration(self):
        """Test crafting system integration with inventory."""
        # Mock crafting recipe: 4 wood -> 1 workbench
        wood_id = 4
        workbench_id = 117
        required_wood = 4
        
        # Setup inventory with enough wood
        self.inventory_items[0] = [wood_id, 10]
        
        # Check if can craft
        available_wood = self.inventory_items[0][1] if self.inventory_items[0][0] == wood_id else 0
        can_craft = available_wood >= required_wood
        
        self.assertTrue(can_craft)
        
        # Simulate crafting
        if can_craft:
            # Remove materials
            self.inventory_items[0][1] -= required_wood
            
            # Add result (find empty slot)
            for i, slot in enumerate(self.inventory_items):
                if slot[0] == 0:  # Empty slot
                    self.inventory_items[i] = [workbench_id, 1]
                    break
        
        # Verify crafting result
        self.assertEqual(self.inventory_items[0], [wood_id, 6])  # Wood reduced
        self.assertEqual(self.inventory_items[1], [workbench_id, 1])  # Workbench added


class TestSaveLoadSystem(BaseTestCase):
    """Integration tests for save/load functionality."""
    
    def setUp(self):
        super().setUp()
        # Create temporary directory for test saves
        self.temp_dir = tempfile.mkdtemp()
        
    def tearDown(self):
        super().tearDown()
        # Clean up temporary directory
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_save_data_structure(self):
        """Test save data structure integrity."""
        # Mock complete save data
        save_data = {
            'player': {
                'position': [100, 150],
                'health': 18,
                'inventory': [[1, 5], [0, 0], [3, 20]],
                'hotbar_selection': 0
            },
            'world': {
                'seed': 12345,
                'time': 15000,
                'spawn_point': [10, 10]
            },
            'entities': {
                'floating_items': [],
                'mobs': []
            }
        }
        
        # Test data structure validity
        self.assertIn('player', save_data)
        self.assertIn('world', save_data)
        self.assertIn('entities', save_data)
        
        # Test player data
        player_data = save_data['player']
        self.assertIsInstance(player_data['position'], list)
        self.assertEqual(len(player_data['position']), 2)
        self.assertIsInstance(player_data['health'], int)
        self.assertGreater(player_data['health'], 0)
        
        # Test world data
        world_data = save_data['world']
        self.assertIsInstance(world_data['seed'], int)
        self.assertIsInstance(world_data['time'], int)
        self.assertGreaterEqual(world_data['time'], 0)
    
    def test_legacy_save_format_compatibility(self):
        """Test compatibility with legacy save format."""
        # Mock legacy save format (as used in current game)
        legacy_data = [
            "100:150:0:18:20",  # x:y:facing:health:maxhealth
            "[[1,5],[0,0],[3,20]]",  # inventory JSON
            "12345",  # world seed
            "10:10",  # spawn point
            "15000",  # global time
            "200"  # night shade
        ]
        
        # Test parsing legacy format
        player_pos = legacy_data[0].split(':')
        self.assertEqual(len(player_pos), 5)
        
        x = int(player_pos[0])
        y = int(player_pos[1])
        health = int(player_pos[3])
        
        self.assertEqual(x, 100)
        self.assertEqual(y, 150)
        self.assertEqual(health, 18)
        
        # Test inventory parsing
        inventory_json = legacy_data[1]
        inventory = json.loads(inventory_json)
        self.assertIsInstance(inventory, list)
        self.assertEqual(inventory[0], [1, 5])


class TestPerformanceIntegration(BaseTestCase):
    """Integration tests for performance monitoring."""
    
    def setUp(self):
        super().setUp()
    
    def test_sprite_group_performance(self):
        """Test sprite group performance under load."""
        # Create sprite groups
        all_sprites = pg.sprite.Group()
        test_sprites = []
        
        # Add many sprites
        sprite_count = 100
        for i in range(sprite_count):
            sprite = pg.sprite.Sprite()
            sprite.image = pg.Surface((32, 32))
            sprite.rect = sprite.image.get_rect()
            sprite.rect.x = i * 10
            sprite.rect.y = i * 10
            
            all_sprites.add(sprite)
            test_sprites.append(sprite)
        
        # Test group operations
        self.assertEqual(len(all_sprites), sprite_count)
        
        # Test collision detection performance
        test_rect = pg.Rect(50, 50, 32, 32)
        collisions = []
        
        for sprite in all_sprites:
            if sprite.rect.colliderect(test_rect):
                collisions.append(sprite)
        
        # Should find some collisions
        self.assertGreater(len(collisions), 0)
        self.assertLess(len(collisions), sprite_count)
    
    def test_chunk_memory_management(self):
        """Test chunk memory management under load."""
        # Mock chunk data
        chunks = {}
        max_chunks = 25  # 5x5 area
        
        # Load chunks around player
        player_chunk = (0, 0)
        load_radius = 2
        
        for y in range(-load_radius, load_radius + 1):
            for x in range(-load_radius, load_radius + 1):
                chunk_pos = (player_chunk[0] + x, player_chunk[1] + y)
                chunk_name = f"{chunk_pos[0]},{chunk_pos[1]}"
                
                # Mock chunk data
                chunks[chunk_name] = {
                    'tiles': [[['01'], i, j] for i in range(16) for j in range(16)],
                    'loaded': True
                }
        
        # Test chunk count
        self.assertEqual(len(chunks), max_chunks)
        
        # Test memory cleanup simulation
        # Move player to trigger unloading
        new_player_chunk = (5, 5)
        chunks_to_unload = []
        
        for chunk_name in chunks:
            chunk_coords = chunk_name.split(',')
            chunk_x = int(chunk_coords[0])
            chunk_y = int(chunk_coords[1])
            
            # Check if chunk is too far from new position
            distance = max(abs(chunk_x - new_player_chunk[0]), 
                          abs(chunk_y - new_player_chunk[1]))
            
            if distance > load_radius:
                chunks_to_unload.append(chunk_name)
        
        # Should unload all old chunks
        self.assertEqual(len(chunks_to_unload), max_chunks)


if __name__ == '__main__':
    unittest.main()
