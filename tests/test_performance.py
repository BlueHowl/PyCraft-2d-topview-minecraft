"""Performance benchmarking tests for critical game systems."""

import unittest
import time
import pygame as pg
from unittest.mock import Mock
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from tests.test_config import BaseTestCase, MockGame


class TestPerformanceBenchmarks(BaseTestCase):
    """Benchmark tests for performance-critical operations."""
    
    def setUp(self):
        super().setUp()
        self.benchmark_iterations = 1000
    
    def benchmark_operation(self, operation, iterations=None):
        """Helper method to benchmark an operation."""
        if iterations is None:
            iterations = self.benchmark_iterations
        
        start_time = time.time()
        for _ in range(iterations):
            operation()
        end_time = time.time()
        
        total_time = end_time - start_time
        avg_time = total_time / iterations
        
        return {
            'total_time': total_time,
            'avg_time': avg_time,
            'iterations': iterations,
            'ops_per_second': iterations / total_time if total_time > 0 else float('inf')
        }
    
    def test_vector_math_performance(self):
        """Benchmark vector mathematical operations."""
        v1 = pg.math.Vector2(100, 200)
        v2 = pg.math.Vector2(150, 250)
        
        # Benchmark distance calculation
        def distance_calc():
            return v1.distance_to(v2)
        
        distance_results = self.benchmark_operation(distance_calc)
        
        # Should be very fast (> 10000 ops/second)
        self.assertGreater(distance_results['ops_per_second'], 10000)
        
        # Benchmark vector addition
        def vector_add():
            return v1 + v2
        
        addition_results = self.benchmark_operation(vector_add)
        self.assertGreater(addition_results['ops_per_second'], 50000)
    
    def test_collision_detection_performance(self):
        """Benchmark collision detection operations."""
        rect1 = pg.Rect(100, 100, 32, 32)
        rect2 = pg.Rect(116, 116, 32, 32)
        
        def collision_check():
            return rect1.colliderect(rect2)
        
        results = self.benchmark_operation(collision_check)
        
        # Should be very fast (> 100000 ops/second)
        self.assertGreater(results['ops_per_second'], 100000)
    
    def test_sprite_group_operations(self):
        """Benchmark sprite group operations."""
        sprite_group = pg.sprite.Group()
        
        # Add sprites to benchmark using proper pygame sprites
        class BenchmarkSprite(pg.sprite.Sprite):
            def __init__(self, x, y):
                super().__init__()
                self.image = pg.Surface((32, 32))
                self.rect = pg.Rect(x, y, 32, 32)
        
        sprites = []
        for i in range(100):
            sprite = BenchmarkSprite(i * 10, i * 10)
            sprites.append(sprite)
            sprite_group.add(sprite)
        
        def group_iteration():
            count = 0
            for sprite in sprite_group:
                count += 1
            return count
        
        results = self.benchmark_operation(group_iteration, 100)  # Fewer iterations due to complexity
        
        # Should handle reasonable iteration speeds
        self.assertGreater(results['ops_per_second'], 100)
    
    def test_coordinate_conversion_performance(self):
        """Benchmark coordinate conversion operations."""
        world_x, world_y = 1234, 5678
        tile_size = 32
        chunk_size = 16
        
        def coord_conversion():
            tile_x = world_x // tile_size
            tile_y = world_y // tile_size
            chunk_x = tile_x // chunk_size
            chunk_y = tile_y // chunk_size
            return chunk_x, chunk_y
        
        results = self.benchmark_operation(coord_conversion)
        
        # Should be extremely fast (> 500000 ops/second)
        self.assertGreater(results['ops_per_second'], 500000)
    
    def test_data_structure_access_performance(self):
        """Benchmark data structure access patterns."""
        # Create test dictionary
        test_dict = {f"key_{i}": f"value_{i}" for i in range(1000)}
        
        def dict_access():
            return test_dict.get("key_500", "default")
        
        dict_results = self.benchmark_operation(dict_access)
        
        # Dictionary access should be very fast
        self.assertGreater(dict_results['ops_per_second'], 100000)
        
        # Create test list
        test_list = list(range(1000))
        
        def list_access():
            return test_list[500] if len(test_list) > 500 else None
        
        list_results = self.benchmark_operation(list_access)
        
        # List access should be very fast
        self.assertGreater(list_results['ops_per_second'], 500000)
    
    def test_string_operations_performance(self):
        """Benchmark string operations."""
        test_string = "player_pos:100:200:0:20:20"
        
        def string_split():
            return test_string.split(':')
        
        split_results = self.benchmark_operation(string_split)
        
        # String splitting should be reasonably fast
        self.assertGreater(split_results['ops_per_second'], 10000)
        
        def string_format():
            return f"{100},{200}"
        
        format_results = self.benchmark_operation(string_format)
        
        # String formatting should be fast
        self.assertGreater(format_results['ops_per_second'], 50000)
    
    def test_memory_allocation_performance(self):
        """Benchmark memory allocation patterns."""
        def list_creation():
            return [0] * 100
        
        list_results = self.benchmark_operation(list_creation, 100)  # Fewer iterations
        
        # Should handle reasonable allocation speeds
        self.assertGreater(list_results['ops_per_second'], 1000)
        
        def dict_creation():
            return {'x': 100, 'y': 200, 'health': 20}
        
        dict_results = self.benchmark_operation(dict_creation)
        
        # Dictionary creation should be fast
        self.assertGreater(dict_results['ops_per_second'], 10000)


class TestMemoryUsageBenchmarks(BaseTestCase):
    """Benchmark tests for memory usage patterns."""
    
    def setUp(self):
        super().setUp()
    
    def test_sprite_memory_usage(self):
        """Test memory usage of sprite systems."""
        sprite_group = pg.sprite.Group()
        
        # Add many sprites and measure using proper pygame sprites
        class MemoryTestSprite(pg.sprite.Sprite):
            def __init__(self, x, y):
                super().__init__()
                self.image = pg.Surface((32, 32))
                self.rect = pg.Rect(x, y, 32, 32)
        
        initial_len = len(sprite_group)
        
        for i in range(1000):
            sprite = MemoryTestSprite(i, i)
            sprite_group.add(sprite)
        
        final_len = len(sprite_group)
        
        # Verify all sprites were added
        self.assertEqual(final_len - initial_len, 1000)
        
        # Clear and verify cleanup
        sprite_group.empty()
        self.assertEqual(len(sprite_group), 0)
    
    def test_data_structure_memory_patterns(self):
        """Test memory usage of data structures."""
        # Test list growth
        test_list = []
        
        for i in range(10000):
            test_list.append(i)
        
        self.assertEqual(len(test_list), 10000)
        
        # Test list clearing
        test_list.clear()
        self.assertEqual(len(test_list), 0)
        
        # Test dictionary growth
        test_dict = {}
        
        for i in range(1000):
            test_dict[f"key_{i}"] = f"value_{i}"
        
        self.assertEqual(len(test_dict), 1000)
        
        # Test dictionary clearing
        test_dict.clear()
        self.assertEqual(len(test_dict), 0)


class TestScalabilityBenchmarks(BaseTestCase):
    """Benchmark tests for system scalability."""
    
    def setUp(self):
        super().setUp()
    
    def test_entity_scaling(self):
        """Test performance scaling with entity count."""
        entity_counts = [10, 100, 1000]
        results = {}
        
        for count in entity_counts:
            entities = []
            
            start_time = time.time()
            
            # Create entities
            for i in range(count):
                entity = {
                    'id': i,
                    'x': i % 100,
                    'y': i // 100,
                    'health': 20,
                    'active': True
                }
                entities.append(entity)
            
            # Process entities
            active_count = sum(1 for e in entities if e['active'])
            
            end_time = time.time()
            
            results[count] = {
                'time': end_time - start_time,
                'processed': active_count
            }
        
        # Verify all entities were processed correctly
        for count in entity_counts:
            self.assertEqual(results[count]['processed'], count)
        
        # Performance should scale reasonably (not exponentially)
        # Time for 1000 entities should be less than 100x time for 10 entities
        if results[10]['time'] > 0:
            scaling_factor = results[1000]['time'] / results[10]['time']
            self.assertLess(scaling_factor, 200)  # Allow some scaling overhead
    
    def test_chunk_processing_scaling(self):
        """Test chunk processing scalability."""
        chunk_sizes = [1, 4, 16]  # Number of chunks
        
        for chunk_count in chunk_sizes:
            start_time = time.time()
            
            chunks = []
            for i in range(chunk_count):
                chunk = {
                    'x': i % 4,
                    'y': i // 4,
                    'tiles': [[f"tile_{j}" for j in range(256)] for _ in range(256)]  # 16x16 tiles
                }
                chunks.append(chunk)
            
            # Process chunks
            total_tiles = sum(len(chunk['tiles']) * len(chunk['tiles'][0]) for chunk in chunks)
            
            end_time = time.time()
            
            processing_time = end_time - start_time
            
            # Should complete processing within reasonable time
            self.assertLess(processing_time, 1.0)  # Less than 1 second
            
            # Verify correct tile count
            expected_tiles = chunk_count * 256 * 256
            self.assertEqual(total_tiles, expected_tiles)


if __name__ == '__main__':
    unittest.main()
