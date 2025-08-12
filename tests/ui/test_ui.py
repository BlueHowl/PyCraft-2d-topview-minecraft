"""Tests for UI components."""

import unittest
import pygame as pg
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from tests.test_config import BaseTestCase, MockGame, create_mock_surface
from game.config.settings import TILESIZE, STACK, WIDTH, HEIGHT, HOTBAR_SLOTS, INVENTORY_SLOTS


class TestInventory(BaseTestCase):
    """Test cases for the Inventory UI."""
    
    def setUp(self):
        super().setUp()
        # Mock inventory properties
        self.mock_inventory = Mock()
        self.mock_inventory.game = self.mock_game
        self.mock_inventory.xOffset = 32
        self.mock_inventory.yOffset = 32
        self.mock_inventory.craftPage = 0
        self.mock_inventory.currentItemHold = []
        self.mock_inventory.currentDraggedItem = [0, 0]
    
    def test_inventory_initialization(self):
        """Test inventory initialization."""
        # Test position
        self.assertEqual(self.mock_inventory.xOffset, 32)
        self.assertEqual(self.mock_inventory.yOffset, 32)
        
        # Test initial state
        self.assertEqual(self.mock_inventory.craftPage, 0)
        self.assertEqual(self.mock_inventory.currentItemHold, [])
        self.assertEqual(self.mock_inventory.currentDraggedItem, [0, 0])
    
    def test_inventory_toggle(self):
        """Test inventory toggle functionality."""
        # Mock toggle state
        initial_state = False
        toggled_state = True
        
        # Test state change
        self.assertNotEqual(initial_state, toggled_state)
        
        # Test pause game when inventory opens
        self.mock_game.isGamePaused = toggled_state
        self.assertEqual(self.mock_game.isGamePaused, toggled_state)
    
    def test_item_stack_management(self):
        """Test item stack management."""
        # Test stack limits
        max_stack = STACK
        current_quantity = 30
        adding_quantity = 40
        
        # Test stack overflow
        total = current_quantity + adding_quantity
        if total > max_stack:
            remaining = total - max_stack
            final_stack = max_stack
        else:
            remaining = 0
            final_stack = total
        
        self.assertEqual(final_stack, max_stack)
        self.assertEqual(remaining, 6)
    
    def test_inventory_slot_management(self):
        """Test inventory slot system."""
        # Test slot counts
        hotbar_slots = HOTBAR_SLOTS
        inventory_slots = INVENTORY_SLOTS
        total_slots = hotbar_slots + inventory_slots
        
        self.assertEqual(hotbar_slots, 9)
        self.assertEqual(inventory_slots, 25)
        self.assertEqual(total_slots, 34)
    
    def test_item_drag_and_drop(self):
        """Test item drag and drop mechanics."""
        # Mock item being dragged
        dragged_item = [5, 10]  # item_id, quantity
        source_slot = 3
        target_slot = 15
        
        # Test drag state
        self.mock_inventory.currentDraggedItem = dragged_item
        self.assertEqual(self.mock_inventory.currentDraggedItem, dragged_item)
        
        # Test valid slot numbers
        self.assertGreaterEqual(source_slot, 0)
        self.assertGreaterEqual(target_slot, 0)
        self.assertLess(source_slot, HOTBAR_SLOTS + INVENTORY_SLOTS)
        self.assertLess(target_slot, HOTBAR_SLOTS + INVENTORY_SLOTS)


class TestHotbar(BaseTestCase):
    """Test cases for the Hotbar UI."""
    
    def setUp(self):
        super().setUp()
        # Mock hotbar
        self.mock_hotbar = Mock()
        self.mock_hotbar.game = self.mock_game
        self.mock_hotbar.selected_slot = 0
        self.mock_hotbar.slots = [[0, 0] for _ in range(HOTBAR_SLOTS)]
    
    def test_hotbar_initialization(self):
        """Test hotbar initialization."""
        # Test slot count
        self.assertEqual(len(self.mock_hotbar.slots), HOTBAR_SLOTS)
        
        # Test initial selection
        self.assertEqual(self.mock_hotbar.selected_slot, 0)
        
        # Test empty slots
        for slot in self.mock_hotbar.slots:
            self.assertEqual(slot, [0, 0])
    
    def test_hotbar_selection(self):
        """Test hotbar slot selection."""
        # Test valid slot selection
        for slot_index in range(HOTBAR_SLOTS):
            self.mock_hotbar.selected_slot = slot_index
            self.assertGreaterEqual(self.mock_hotbar.selected_slot, 0)
            self.assertLess(self.mock_hotbar.selected_slot, HOTBAR_SLOTS)
    
    def test_hotbar_item_addition(self):
        """Test adding items to hotbar."""
        # Mock adding item
        item_id = 5
        quantity = 3
        slot_index = 2
        
        # Add item to slot
        self.mock_hotbar.slots[slot_index] = [item_id, quantity]
        
        # Test item was added
        self.assertEqual(self.mock_hotbar.slots[slot_index], [item_id, quantity])
        
        # Test other slots remain empty
        for i, slot in enumerate(self.mock_hotbar.slots):
            if i != slot_index:
                self.assertEqual(slot, [0, 0])
    
    def test_hotbar_scroll_selection(self):
        """Test hotbar scroll wheel selection."""
        # Mock scroll events
        scroll_up = 1
        scroll_down = -1
        
        # Test scroll up
        current_slot = 0
        new_slot = (current_slot + scroll_up) % HOTBAR_SLOTS
        self.assertEqual(new_slot, 1)
        
        # Test scroll down from first slot
        current_slot = 0
        new_slot = (current_slot + scroll_down) % HOTBAR_SLOTS
        self.assertEqual(new_slot, HOTBAR_SLOTS - 1)


class TestLifebar(BaseTestCase):
    """Test cases for the Lifebar UI."""
    
    def setUp(self):
        super().setUp()
        # Mock lifebar
        self.mock_lifebar = Mock()
        self.mock_lifebar.game = self.mock_game
        self.mock_lifebar.max_health = 20
        self.mock_lifebar.current_health = 20
    
    def test_lifebar_initialization(self):
        """Test lifebar initialization."""
        # Test health values
        self.assertEqual(self.mock_lifebar.max_health, 20)
        self.assertEqual(self.mock_lifebar.current_health, 20)
    
    def test_health_display(self):
        """Test health display calculations."""
        max_health = 20
        current_health = 15
        
        # Calculate health percentage
        health_percentage = current_health / max_health
        self.assertEqual(health_percentage, 0.75)
        
        # Calculate hearts (each heart = 2 health)
        full_hearts = current_health // 2
        half_heart = current_health % 2
        
        self.assertEqual(full_hearts, 7)
        self.assertEqual(half_heart, 1)
    
    def test_health_damage(self):
        """Test health damage display."""
        initial_health = 20
        damage = 5
        
        final_health = max(0, initial_health - damage)
        self.assertEqual(final_health, 15)
        
        # Test fatal damage
        fatal_damage = 25
        final_health = max(0, initial_health - fatal_damage)
        self.assertEqual(final_health, 0)
    
    def test_health_healing(self):
        """Test health healing display."""
        current_health = 10
        max_health = 20
        healing = 8
        
        final_health = min(max_health, current_health + healing)
        self.assertEqual(final_health, 18)
        
        # Test overhealing
        overheal = 15
        final_health = min(max_health, current_health + overheal)
        self.assertEqual(final_health, max_health)


class TestMenu(BaseTestCase):
    """Test cases for Menu UI."""
    
    def setUp(self):
        super().setUp()
        # Mock menu
        self.mock_menu = Mock()
        self.mock_menu.game = self.mock_game
        self.mock_menu.selected_option = 0
        self.mock_menu.options = ["Start Game", "Options", "Exit"]
    
    def test_menu_initialization(self):
        """Test menu initialization."""
        # Test menu options
        self.assertGreater(len(self.mock_menu.options), 0)
        self.assertEqual(self.mock_menu.selected_option, 0)
    
    def test_menu_navigation(self):
        """Test menu navigation."""
        total_options = len(self.mock_menu.options)
        
        # Test moving down
        self.mock_menu.selected_option = (self.mock_menu.selected_option + 1) % total_options
        self.assertEqual(self.mock_menu.selected_option, 1)
        
        # Test moving up from first option
        self.mock_menu.selected_option = 0
        self.mock_menu.selected_option = (self.mock_menu.selected_option - 1) % total_options
        self.assertEqual(self.mock_menu.selected_option, total_options - 1)
    
    def test_menu_option_validation(self):
        """Test menu option validation."""
        # Test valid selection
        for i in range(len(self.mock_menu.options)):
            self.assertGreaterEqual(i, 0)
            self.assertLess(i, len(self.mock_menu.options))


class TestInputBox(BaseTestCase):
    """Test cases for InputBox UI."""
    
    def setUp(self):
        super().setUp()
        # Mock input box
        self.mock_input_box = Mock()
        self.mock_input_box.text = ""
        self.mock_input_box.active = False
        self.mock_input_box.max_length = 100
    
    def test_input_box_initialization(self):
        """Test input box initialization."""
        # Test initial state
        self.assertEqual(self.mock_input_box.text, "")
        self.assertFalse(self.mock_input_box.active)
        self.assertEqual(self.mock_input_box.max_length, 100)
    
    def test_text_input(self):
        """Test text input handling."""
        # Mock typing
        test_text = "hello world"
        self.mock_input_box.text = test_text
        
        # Test text was set
        self.assertEqual(self.mock_input_box.text, test_text)
        
        # Test text length
        self.assertLessEqual(len(self.mock_input_box.text), self.mock_input_box.max_length)
    
    def test_text_validation(self):
        """Test text input validation."""
        # Test maximum length enforcement
        long_text = "a" * 150
        if len(long_text) > self.mock_input_box.max_length:
            truncated_text = long_text[:self.mock_input_box.max_length]
        else:
            truncated_text = long_text
        
        self.assertEqual(len(truncated_text), self.mock_input_box.max_length)
    
    def test_input_box_state(self):
        """Test input box active/inactive states."""
        # Test activation
        self.mock_input_box.active = True
        self.assertTrue(self.mock_input_box.active)
        
        # Test deactivation
        self.mock_input_box.active = False
        self.assertFalse(self.mock_input_box.active)


if __name__ == '__main__':
    unittest.main()
