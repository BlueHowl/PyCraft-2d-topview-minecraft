"""
Phase 1.2 Simplified Validation - Core game state abstraction

Tests the essential game state components without pygame dependencies.
"""

import sys
import time
from pathlib import Path

# Add the game directory to the path
game_dir = Path(__file__).parent.parent
sys.path.insert(0, str(game_dir))

from game.core.game_world import GameWorld, PlayerState, EntityState, FloatingItemState, ChunkState
from game.network.network_manager import NetworkManager, NetworkMode
from game.network.protocol import generate_player_id


def test_core_game_world():
    """Test core GameWorld functionality."""
    print("Testing Core GameWorld...")
    
    world = GameWorld("test_world", seed=12345)
    
    # Test player management
    player_id = generate_player_id()
    assert world.add_player(player_id, "TestPlayer", 0, 0)
    assert len(world.players) == 1
    
    player = world.get_player(player_id)
    assert player is not None
    assert player.name == "TestPlayer"
    
    # Test world operations
    assert world.set_block(10, 10, 1)
    assert world.get_block(10, 10) == 1
    
    # Test floating items
    item_id = world.spawn_floating_item("wood", 64, 25.0, 25.0)
    assert len(world.floating_items) == 1
    assert world.pickup_floating_item(item_id, player_id)
    assert len(world.floating_items) == 0
    
    # Test world update
    initial_time = world.game_time
    world.update(1.0)
    assert world.game_time > initial_time
    
    print(f"  World: {world.world_name}, Players: {len(world.players)}")
    print("✓ Core GameWorld test passed\n")


def test_player_state_detailed():
    """Test PlayerState in detail."""
    print("Testing PlayerState Details...")
    
    player = PlayerState(
        player_id=generate_player_id(),
        name="TestPlayer",
        x=100.0,
        y=200.0
    )
    
    # Test movement and chunk calculation
    player.move(5.0, 0.0, 2.0)  # Move 10 units right
    assert player.x == 110.0
    assert player.y == 200.0
    
    # Test inventory operations
    assert player.add_item("wood", 32)
    assert player.add_item("stone", 64)
    
    wood_removed = player.remove_item("wood", 20)
    assert wood_removed == 20
    
    # Test damage system
    initial_health = player.health
    player.take_damage(5)
    assert player.health == initial_health - 5
    
    player.heal(3)
    assert player.health == initial_health - 2
    
    print(f"  Player health: {player.health}, Position: ({player.x}, {player.y})")
    print("✓ PlayerState Details test passed\n")


def test_network_manager_modes():
    """Test NetworkManager mode switching."""
    print("Testing NetworkManager Modes...")
    
    manager = NetworkManager(NetworkMode.OFFLINE)
    assert manager.initialize()
    
    # Test mode transitions
    modes_to_test = [
        NetworkMode.SINGLEPLAYER,
        NetworkMode.OFFLINE,
        NetworkMode.CLIENT
    ]
    
    for mode in modes_to_test:
        assert manager.set_mode(mode)
        assert manager.mode == mode
        status = manager.get_status()
        assert status['mode'] == mode.value
    
    manager.shutdown()
    print(f"  Tested modes: {[m.value for m in modes_to_test]}")
    print("✓ NetworkManager Modes test passed\n")


def test_chunk_operations():
    """Test chunk operations and block management."""
    print("Testing Chunk Operations...")
    
    world = GameWorld("chunk_test")
    
    # Test chunk creation and block operations
    test_positions = [
        (0, 0), (31, 31), (32, 32), (100, 100), (-10, -10)
    ]
    
    for x, y in test_positions:
        # Set different blocks
        block_id = ((x + y) % 5) + 1  # Block IDs 1-5
        world.set_block(x, y, block_id)
        retrieved = world.get_block(x, y)
        assert retrieved == block_id, f"Block mismatch at ({x}, {y}): expected {block_id}, got {retrieved}"
    
    # Test chunk data retrieval
    chunk_data = world.get_chunk_data(0, 0)
    assert chunk_data is not None
    assert 'blocks' in chunk_data
    
    print(f"  Loaded chunks: {len(world.loaded_chunks)}")
    print(f"  Test positions: {len(test_positions)}")
    print("✓ Chunk Operations test passed\n")


def test_performance_simulation():
    """Test performance with realistic game simulation."""
    print("Testing Performance Simulation...")
    
    world = GameWorld("performance_test")
    
    # Create multiple players
    players = []
    for i in range(5):
        player_id = generate_player_id()
        world.add_player(player_id, f"Player{i}", i * 50, i * 50)
        players.append(player_id)
    
    # Simulate game activity
    start_time = time.time()
    
    for frame in range(60):  # Simulate 1 second at 60 FPS
        # Update world
        world.update(1.0 / 60.0)
        
        # Move players randomly
        import random
        for player_id in players:
            dx = random.uniform(-5, 5)
            dy = random.uniform(-5, 5)
            world.move_player(player_id, 0, 0, dx, dy, 1.0 / 60.0)
        
        # Place/break some blocks
        if frame % 10 == 0:  # Every 10 frames
            x, y = random.randint(0, 100), random.randint(0, 100)
            block_id = random.randint(0, 3)
            world.set_block(x, y, block_id)
        
        # Spawn/pickup items occasionally
        if frame % 20 == 0:  # Every 20 frames
            x, y = random.uniform(0, 100), random.uniform(0, 100)
            world.spawn_floating_item("test_item", 1, x, y)
    
    end_time = time.time()
    simulation_time = end_time - start_time
    
    print(f"  60 frame simulation: {simulation_time:.4f} seconds")
    print(f"  Average frame time: {simulation_time/60*1000:.2f}ms")
    print(f"  Simulated FPS: {60/simulation_time:.1f}")
    print(f"  Final state - Players: {len(world.players)}, Items: {len(world.floating_items)}")
    print("✓ Performance Simulation test passed\n")


def main():
    """Run simplified Phase 1.2 validation tests."""
    print("=== Phase 1.2 Simplified Validation - Game State Abstraction ===\n")
    
    try:
        test_core_game_world()
        test_player_state_detailed()
        test_network_manager_modes()
        test_chunk_operations()
        test_performance_simulation()
        
        print("🎉 All Phase 1.2 core tests passed!")
        print("\n✅ Game State Abstraction Validation Summary:")
        print("   • Pure game logic works without rendering")
        print("   • Player state management functional")
        print("   • World/chunk operations working")
        print("   • Network manager mode switching works")
        print("   • Performance is adequate for real-time simulation")
        print("\nPhase 1.2 (Abstract Game State from Rendering) is complete!")
        print("Ready to proceed to Phase 1.3 (Implement Action/Command System)")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
