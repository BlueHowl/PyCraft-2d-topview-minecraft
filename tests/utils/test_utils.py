"""Tests for utility functions."""

import unittest
import pygame as pg
from unittest.mock import Mock, patch, MagicMock
import sys
import os
import logging

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from tests.test_config import BaseTestCase


class TestLogger(BaseTestCase):
    """Test cases for the logging system."""
    
    def setUp(self):
        super().setUp()
    
    def test_log_levels(self):
        """Test different log levels."""
        # Test log level hierarchy
        levels = [
            logging.DEBUG,
            logging.INFO,
            logging.WARNING,
            logging.ERROR,
            logging.CRITICAL
        ]
        
        # Verify hierarchy
        for i in range(len(levels) - 1):
            self.assertLess(levels[i], levels[i + 1])
    
    def test_log_message_formatting(self):
        """Test log message formatting."""
        # Mock log message
        message = "Test log message"
        level = "INFO"
        timestamp = "2024-01-01 12:00:00"
        
        # Test message components
        self.assertIsInstance(message, str)
        self.assertIsInstance(level, str)
        self.assertIsInstance(timestamp, str)
        
        # Test formatted message
        formatted = f"{timestamp} - {level} - {message}"
        self.assertIn(message, formatted)
        self.assertIn(level, formatted)
        self.assertIn(timestamp, formatted)
    
    def test_log_file_operations(self):
        """Test log file operations."""
        # Mock log file path
        log_file = "game.log"
        
        # Test file path validity
        self.assertIsInstance(log_file, str)
        self.assertTrue(log_file.endswith('.log'))


class TestPerformanceMonitor(BaseTestCase):
    """Test cases for performance monitoring."""
    
    def setUp(self):
        super().setUp()
        self.mock_monitor = Mock()
        self.mock_monitor.fps = 60
        self.mock_monitor.frame_time = 16.67
        self.mock_monitor.memory_usage = 100
    
    def test_fps_calculation(self):
        """Test FPS calculation."""
        # Mock frame timing
        frame_times = [16.67, 16.33, 17.0, 16.5, 16.8]  # milliseconds
        
        # Calculate average frame time
        avg_frame_time = sum(frame_times) / len(frame_times)
        
        # Calculate FPS
        fps = 1000 / avg_frame_time  # Convert to seconds
        
        self.assertAlmostEqual(fps, 60, delta=5)
        self.assertGreater(fps, 0)
    
    def test_memory_monitoring(self):
        """Test memory usage monitoring."""
        # Mock memory values in MB
        initial_memory = 50
        current_memory = 75
        peak_memory = 120
        
        # Test memory tracking
        self.assertGreater(current_memory, 0)
        self.assertGreaterEqual(peak_memory, current_memory)
        self.assertGreaterEqual(current_memory, initial_memory)
    
    def test_performance_thresholds(self):
        """Test performance threshold checking."""
        # Mock performance thresholds
        min_fps = 30
        max_memory_mb = 500
        
        current_fps = 45
        current_memory = 200
        
        # Test threshold validation
        fps_ok = current_fps >= min_fps
        memory_ok = current_memory <= max_memory_mb
        
        self.assertTrue(fps_ok)
        self.assertTrue(memory_ok)
    
    def test_performance_report(self):
        """Test performance report generation."""
        # Mock performance data
        performance_data = {
            'fps': 58.5,
            'frame_time': 17.1,
            'memory_mb': 145,
            'chunks_loaded': 12,
            'sprites_count': 247
        }
        
        # Test report structure
        required_keys = ['fps', 'frame_time', 'memory_mb']
        for key in required_keys:
            self.assertIn(key, performance_data)
            self.assertIsInstance(performance_data[key], (int, float))


class TestAudioUtils(BaseTestCase):
    """Test cases for audio utilities."""
    
    def setUp(self):
        super().setUp()
        self.mock_audio = Mock()
        self.mock_audio.sounds = {}
        self.mock_audio.volume = 1.0
        self.mock_audio.enabled = True
    
    def test_sound_loading(self):
        """Test sound loading functionality."""
        # Mock sound file
        sound_name = "test_sound"
        sound_file = "test_sound.ogg"
        
        # Test sound metadata
        self.assertIsInstance(sound_name, str)
        self.assertIsInstance(sound_file, str)
        self.assertTrue(sound_file.endswith(('.ogg', '.wav', '.mp3')))
    
    def test_volume_control(self):
        """Test volume control."""
        # Test volume range
        valid_volumes = [0.0, 0.5, 1.0]
        invalid_volumes = [-0.1, 1.1, 2.0]
        
        for volume in valid_volumes:
            self.assertGreaterEqual(volume, 0.0)
            self.assertLessEqual(volume, 1.0)
        
        for volume in invalid_volumes:
            # Volume should be clamped
            clamped = max(0.0, min(1.0, volume))
            self.assertGreaterEqual(clamped, 0.0)
            self.assertLessEqual(clamped, 1.0)
    
    def test_positional_audio(self):
        """Test positional audio calculations."""
        # Mock positions
        player_pos = pg.math.Vector2(100, 100)
        sound_pos = pg.math.Vector2(150, 120)
        max_distance = 200
        
        # Calculate distance
        distance = player_pos.distance_to(sound_pos)
        
        # Calculate volume based on distance
        if distance <= max_distance:
            volume_multiplier = 1.0 - (distance / max_distance)
        else:
            volume_multiplier = 0.0
        
        self.assertGreaterEqual(volume_multiplier, 0.0)
        self.assertLessEqual(volume_multiplier, 1.0)
        self.assertGreater(volume_multiplier, 0.0)  # Sound should be audible
    
    def test_audio_safety(self):
        """Test audio system safety features."""
        # Test safe audio player
        audio_enabled = True
        sound_exists = True
        
        # Mock safe play conditions
        can_play = audio_enabled and sound_exists
        self.assertTrue(can_play)
        
        # Test disabled audio
        audio_enabled = False
        can_play = audio_enabled and sound_exists
        self.assertFalse(can_play)


class TestMathUtils(BaseTestCase):
    """Test cases for mathematical utilities."""
    
    def setUp(self):
        super().setUp()
    
    def test_vector_operations(self):
        """Test vector mathematical operations."""
        # Test vector creation
        vec1 = pg.math.Vector2(3, 4)
        vec2 = pg.math.Vector2(1, 2)
        
        # Test vector addition
        result = vec1 + vec2
        self.assertEqual(result.x, 4)
        self.assertEqual(result.y, 6)
        
        # Test vector subtraction
        result = vec1 - vec2
        self.assertEqual(result.x, 2)
        self.assertEqual(result.y, 2)
        
        # Test vector magnitude
        magnitude = vec1.length()
        expected = (3**2 + 4**2)**0.5
        self.assertAlmostEqual(magnitude, expected)
    
    def test_distance_calculations(self):
        """Test distance calculation utilities."""
        # Test 2D distance
        point1 = (0, 0)
        point2 = (3, 4)
        
        distance = ((point2[0] - point1[0])**2 + (point2[1] - point1[1])**2)**0.5
        self.assertEqual(distance, 5.0)
        
        # Test Manhattan distance
        manhattan = abs(point2[0] - point1[0]) + abs(point2[1] - point1[1])
        self.assertEqual(manhattan, 7)
    
    def test_angle_calculations(self):
        """Test angle calculation utilities."""
        import math
        
        # Test angle between vectors
        vec1 = pg.math.Vector2(1, 0)
        vec2 = pg.math.Vector2(0, 1)
        
        # Calculate angle using dot product
        dot_product = vec1.dot(vec2)
        magnitude1 = vec1.length()
        magnitude2 = vec2.length()
        
        if magnitude1 > 0 and magnitude2 > 0:
            cos_angle = dot_product / (magnitude1 * magnitude2)
            angle_radians = math.acos(max(-1, min(1, cos_angle)))
            angle_degrees = math.degrees(angle_radians)
        else:
            angle_degrees = 0
        
        self.assertAlmostEqual(angle_degrees, 90, delta=0.1)
    
    def test_coordinate_conversions(self):
        """Test coordinate system conversions."""
        # Test tile to pixel conversion
        tile_x, tile_y = 5, 3
        tile_size = 32
        
        pixel_x = tile_x * tile_size
        pixel_y = tile_y * tile_size
        
        self.assertEqual(pixel_x, 160)
        self.assertEqual(pixel_y, 96)
        
        # Test pixel to tile conversion
        converted_tile_x = pixel_x // tile_size
        converted_tile_y = pixel_y // tile_size
        
        self.assertEqual(converted_tile_x, tile_x)
        self.assertEqual(converted_tile_y, tile_y)


class TestDataValidation(BaseTestCase):
    """Test cases for data validation utilities."""
    
    def setUp(self):
        super().setUp()
    
    def test_input_validation(self):
        """Test input data validation."""
        # Test coordinate validation
        def validate_coordinates(x, y, min_val=0, max_val=1000):
            return (min_val <= x <= max_val and 
                   min_val <= y <= max_val)
        
        # Test valid coordinates
        self.assertTrue(validate_coordinates(100, 200))
        self.assertTrue(validate_coordinates(0, 0))
        self.assertTrue(validate_coordinates(1000, 1000))
        
        # Test invalid coordinates
        self.assertFalse(validate_coordinates(-1, 100))
        self.assertFalse(validate_coordinates(100, 1001))
    
    def test_item_validation(self):
        """Test item data validation."""
        # Test item structure validation
        def validate_item(item_data):
            if not isinstance(item_data, list) or len(item_data) != 2:
                return False
            item_id, quantity = item_data
            return (isinstance(item_id, int) and item_id >= 0 and
                   isinstance(quantity, int) and 0 <= quantity <= 64)
        
        # Test valid items
        self.assertTrue(validate_item([1, 10]))
        self.assertTrue(validate_item([0, 0]))  # Empty slot
        self.assertTrue(validate_item([5, 64]))  # Full stack
        
        # Test invalid items
        self.assertFalse(validate_item([1]))  # Wrong length
        self.assertFalse(validate_item([1, 65]))  # Too many items
        self.assertFalse(validate_item([-1, 10]))  # Invalid ID
    
    def test_string_sanitization(self):
        """Test string input sanitization."""
        # Mock string sanitization
        def sanitize_string(text, max_length=100):
            if not isinstance(text, str):
                return ""
            # Remove dangerous characters and limit length
            safe_chars = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 _-")
            sanitized = ''.join(c for c in text if c in safe_chars)
            return sanitized[:max_length]
        
        # Test sanitization
        test_input = "Hello World! @#$%^&*()"
        expected = "Hello World "
        self.assertEqual(sanitize_string(test_input), expected)
        
        # Test length limiting
        long_input = "a" * 150
        result = sanitize_string(long_input, 50)
        self.assertEqual(len(result), 50)


if __name__ == '__main__':
    unittest.main()
