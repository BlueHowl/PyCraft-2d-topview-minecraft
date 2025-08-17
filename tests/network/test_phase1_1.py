"""
Phase 1.1 Validation - Network Protocol Layer

Tests the basic networking protocol components to ensure they work correctly.
"""

import sys
import json
import time
from pathlib import Path

# Add the game directory to the path
game_dir = Path(__file__).parent.parent
sys.path.insert(0, str(game_dir))

from game.network.message_types import MessageType, get_message_priority, get_message_category
from game.network.protocol import NetworkProtocol, generate_player_id
from game.network.packets import PacketFactory, ConnectPacket, PlayerMovePacket


def test_message_types():
    """Test message type enumeration and utilities."""
    print("Testing Message Types...")
    
    # Test basic message types
    assert MessageType.CONNECT.value > 0
    assert MessageType.PLAYER_MOVE.value > 0
    assert MessageType.CHAT_MESSAGE.value > 0
    
    # Test priority system
    connect_priority = get_message_priority(MessageType.CONNECT)
    move_priority = get_message_priority(MessageType.PLAYER_MOVE)
    
    print(f"  CONNECT priority: {connect_priority}")
    print(f"  PLAYER_MOVE priority: {move_priority}")
    
    # Test category system
    connect_category = get_message_category(MessageType.CONNECT)
    move_category = get_message_category(MessageType.PLAYER_MOVE)
    
    print(f"  CONNECT category: {connect_category}")
    print(f"  PLAYER_MOVE category: {move_category}")
    
    print("✓ Message Types test passed\n")


def test_protocol():
    """Test the network protocol."""
    print("Testing Network Protocol...")
    
    protocol = NetworkProtocol()
    
    # Test basic message packing/unpacking
    test_data = {
        'player_name': 'TestPlayer',
        'world_name': 'TestWorld'
    }
    
    # Pack message
    packed = protocol.pack_message(MessageType.CONNECT, test_data)
    print(f"  Packed message size: {len(packed)} bytes")
    
    # Unpack message
    unpacked = protocol.unpack_message(packed)
    assert unpacked is not None
    assert unpacked['message_type'] == MessageType.CONNECT
    assert unpacked['data']['player_name'] == 'TestPlayer'
    
    print(f"  Unpacked message type: {unpacked['message_type']}")
    print(f"  Unpacked player name: {unpacked['data']['player_name']}")
    
    # Test specific message creators
    connect_msg = protocol.create_connect_message('TestPlayer', 'TestWorld')
    ping_msg = protocol.create_ping_message()
    
    print(f"  Connect message size: {len(connect_msg)} bytes")
    print(f"  Ping message size: {len(ping_msg)} bytes")
    
    # Test message size calculation
    size_estimate = protocol.get_message_size(MessageType.CONNECT, test_data)
    print(f"  Size estimate: {size_estimate} bytes (actual: {len(packed)})")
    
    # Test message validation
    is_valid = protocol.validate_message_data(MessageType.CONNECT, test_data)
    assert is_valid
    
    invalid_data = {'invalid': 'data'}
    is_invalid = protocol.validate_message_data(MessageType.CONNECT, invalid_data)
    assert not is_invalid
    
    print("✓ Network Protocol test passed\n")


def test_packets():
    """Test packet classes."""
    print("Testing Packet Classes...")
    
    # Test packet creation
    connect_packet = ConnectPacket(
        player_name='TestPlayer',
        world_name='TestWorld',
        client_version=1
    )
    
    # Test packet serialization
    packet_dict = connect_packet.to_dict()
    print(f"  Connect packet dict: {packet_dict}")
    
    # Test packet deserialization
    restored_packet = ConnectPacket.from_dict(packet_dict)
    assert restored_packet.player_name == 'TestPlayer'
    assert restored_packet.world_name == 'TestWorld'
    
    # Test packet factory
    factory_packet = PacketFactory.create_packet(MessageType.CONNECT, packet_dict)
    assert isinstance(factory_packet, ConnectPacket)
    assert factory_packet.player_name == 'TestPlayer'
    
    # Test movement packet
    move_packet = PlayerMovePacket(
        x=100.0,
        y=200.0,
        vel_x=5.0,
        vel_y=0.0,
        direction='right'
    )
    
    move_dict = move_packet.to_dict()
    print(f"  Move packet dict: {move_dict}")
    
    # Test unsupported message type
    try:
        PacketFactory.create_packet(MessageType.INVALID_MESSAGE, {})
        assert False, "Should have raised ValueError"
    except ValueError:
        pass  # Expected
    
    print("✓ Packet Classes test passed\n")


def test_utility_functions():
    """Test utility functions."""
    print("Testing Utility Functions...")
    
    # Test ID generation
    player_id1 = generate_player_id()
    player_id2 = generate_player_id()
    
    print(f"  Generated player ID 1: {player_id1}")
    print(f"  Generated player ID 2: {player_id2}")
    
    # IDs should be unique
    assert player_id1 != player_id2
    assert len(player_id1) > 0
    assert len(player_id2) > 0
    
    print("✓ Utility Functions test passed\n")


def test_performance():
    """Test basic performance characteristics."""
    print("Testing Performance...")
    
    protocol = NetworkProtocol()
    
    # Test packing speed
    test_data = {
        'player_name': 'TestPlayer',
        'x': 123.45,
        'y': 678.90,
        'inventory': [{'item': 'wood', 'quantity': 64} for _ in range(36)]
    }
    
    start_time = time.time()
    for _ in range(1000):
        packed = protocol.pack_message(MessageType.PLAYER_UPDATE, test_data)
    pack_time = time.time() - start_time
    
    print(f"  1000 pack operations: {pack_time:.4f} seconds")
    print(f"  Pack rate: {1000/pack_time:.1f} messages/second")
    
    # Test unpacking speed
    start_time = time.time()
    for _ in range(1000):
        unpacked = protocol.unpack_message(packed)
    unpack_time = time.time() - start_time
    
    print(f"  1000 unpack operations: {unpack_time:.4f} seconds")
    print(f"  Unpack rate: {1000/unpack_time:.1f} messages/second")
    
    print("✓ Performance test passed\n")


def main():
    """Run all Phase 1.1 validation tests."""
    print("=== Phase 1.1 Validation - Network Protocol Layer ===\n")
    
    try:
        test_message_types()
        test_protocol()
        test_packets()
        test_utility_functions()
        test_performance()
        
        print("🎉 All Phase 1.1 tests passed!")
        print("\nPhase 1.1 (Network Protocol Layer) is complete and validated.")
        print("Ready to proceed to Phase 1.2 (Abstract Game State from Rendering)")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
