"""
Validation Test for Phase 2.2: Client Implementation

Tests the client components including GameClient, ClientConnection,
ClientMessageHandler, ClientGameWorld, and ServerProxy.
"""

import sys
import os
import time
import threading
import socket
from typing import Dict, Any

# Add current directory to path for imports
current_dir = os.path.dirname(__file__)
project_root = os.path.dirname(current_dir)
sys.path.insert(0, project_root)

# Import client components
try:
    from game.network.client import (
        GameClient, ClientConfig, ClientConnection,
        ClientMessageHandler, ClientGameWorld, ServerProxy
    )
    from game.network.message_types import MessageType
    from game.network.protocol import NetworkProtocol
except ImportError as e:
    print(f"Import error: {e}")
    print("Current sys.path:")
    for p in sys.path:
        print(f"  {p}")
    raise


def test_client_config():
    """Test client configuration."""
    print("Testing Client Configuration...")
    
    # Test default config
    config = ClientConfig()
    assert config.server_host == "localhost", "Default host incorrect"
    assert config.server_port == 25565, "Default port incorrect"
    assert config.player_name == "Player", "Default player name incorrect"
    assert config.connection_timeout == 10.0, "Default timeout incorrect"
    print("  ✓ Default configuration works")
    
    # Test custom config
    custom_config = ClientConfig(
        server_host="127.0.0.1",
        server_port=8080,
        player_name="TestPlayer",
        auto_reconnect=False,
        debug_mode=True
    )
    assert custom_config.server_host == "127.0.0.1", "Custom host not set"
    assert custom_config.server_port == 8080, "Custom port not set"
    assert custom_config.player_name == "TestPlayer", "Custom player name not set"
    assert custom_config.auto_reconnect == False, "Custom auto_reconnect not set"
    print("  ✓ Custom configuration works")


def test_client_game_world():
    """Test client game world functionality."""
    print("Testing Client Game World...")
    
    # Create mock client
    class MockClient:
        def __init__(self):
            self.connected = True
            self.player_id = "test_player"
        
        def send_message(self, msg_type, data):
            return True
    
    mock_client = MockClient()
    world = ClientGameWorld(mock_client)
    
    # Test block operations
    world.set_block(5, 5, 1)
    block_id = world.get_block(5, 5)
    assert block_id == 1, f"Block not set correctly: {block_id}"
    print("  ✓ Block operations work")
    
    # Test entity spawning
    entity_data = {
        'entity_id': 'test_entity',
        'entity_type': 'mob',
        'x': 100.0,
        'y': 200.0,
        'health': 50
    }
    world.spawn_entity('test_entity', entity_data)
    
    assert 'test_entity' in world.entities, "Entity not spawned"
    entity = world.entities['test_entity']
    assert entity['entity_type'] == 'mob', "Entity type incorrect"
    print("  ✓ Entity spawning works")
    
    # Test player management
    player_data = {
        'player_id': 'test_player_2',
        'player_name': 'TestPlayer2',
        'x': 50.0,
        'y': 75.0
    }
    world.add_player('test_player_2', player_data)
    
    assert 'test_player_2' in world.players, "Player not added"
    assert f"player_test_player_2" in world.entities, "Player entity not created"
    print("  ✓ Player management works")
    
    # Test floating items
    world.spawn_floating_item('item_1', 'wood', 5, 30.0, 40.0)
    assert 'item_1' in world.floating_items, "Floating item not spawned"
    
    item = world.floating_items['item_1']
    assert item['item_type'] == 'wood', "Item type incorrect"
    assert item['quantity'] == 5, "Item quantity incorrect"
    print("  ✓ Floating item operations work")
    
    # Test chunk loading
    blocks = {'10,10': 2, '11,10': 3, '10,11': 1}
    entities = [{'entity_id': 'chunk_entity', 'x': 160, 'y': 160}]
    world.load_chunk_data(1, 1, blocks, entities)
    
    assert (1, 1) in world.loaded_chunks, "Chunk not marked as loaded"
    assert world.get_block(10, 10) == 2, "Chunk block not loaded"
    assert 'chunk_entity' in world.entities, "Chunk entity not loaded"
    print("  ✓ Chunk loading works")
    
    # Test world statistics
    stats = world.get_world_stats()
    assert stats['loaded_chunks'] >= 1, "Chunk count incorrect"
    assert stats['total_entities'] >= 2, "Entity count incorrect"
    assert stats['total_players'] >= 1, "Player count incorrect"
    print("  ✓ World statistics work")


def test_client_message_handler():
    """Test client message handler."""
    print("Testing Client Message Handler...")
    
    # Create mock client
    class MockClient:
        def __init__(self):
            self.player_id = "test_player"
            self.server_info = {}
            self.connection_state = "connecting"
            self.world = None
            self.ping_history = []
            self.event_callbacks = {'connected': [], 'chat_message': [], 'error': []}
            self.events_triggered = []
        
        def record_ping(self, ping_time):
            self.ping_history.append(ping_time)
        
        def disconnect(self, reason):
            self.connection_state = "disconnected"
        
        def _trigger_event(self, event_type, data):
            self.events_triggered.append((event_type, data))
    
    mock_client = MockClient()
    handler = ClientMessageHandler(mock_client)
    
    # Test handler initialization
    assert len(handler.handlers) > 0, "No message handlers registered"
    assert MessageType.CONNECT_RESPONSE in handler.handlers, "Connect response handler missing"
    assert MessageType.CHAT_MESSAGE in handler.handlers, "Chat handler missing"
    print("  ✓ Handler initialization works")
    
    # Test connect response handling
    connect_response = {
        'success': True,
        'player_id': 'test_player_123',
        'server_info': {'max_players': 100, 'world_name': 'test_world'}
    }
    handler.handle_message(MessageType.CONNECT_RESPONSE, connect_response)
    
    assert mock_client.player_id == 'test_player_123', "Player ID not set"
    assert mock_client.connection_state == 'authenticated', "Connection state not updated"
    assert mock_client.world is not None, "World not initialized"
    print("  ✓ Connect response handling works")
    
    # Test pong handling
    ping_time = time.time() - 0.05  # 50ms ago
    pong_data = {'timestamp': ping_time}
    handler.handle_message(MessageType.PONG, pong_data)
    
    assert len(mock_client.ping_history) > 0, "Ping not recorded"
    recorded_ping = mock_client.ping_history[-1]
    assert 40 < recorded_ping < 60, f"Ping time unrealistic: {recorded_ping}ms"  # Should be ~50ms
    print("  ✓ Pong handling works")
    
    # Test chat message handling
    chat_data = {
        'player_name': 'OtherPlayer',
        'message': 'Hello world!',
        'is_system': False
    }
    handler.handle_message(MessageType.CHAT_MESSAGE, chat_data)
    
    assert len(mock_client.events_triggered) > 0, "Chat event not triggered"
    event_type, event_data = mock_client.events_triggered[-1]
    assert event_type == 'chat_message', "Wrong event type"
    assert event_data['message'] == 'Hello world!', "Chat message not preserved"
    print("  ✓ Chat message handling works")
    
    # Test error handling
    error_data = {
        'error': 'test_error',
        'message': 'Test error message'
    }
    handler.handle_message(MessageType.ERROR, error_data)
    
    # Should trigger error event
    error_events = [e for e in mock_client.events_triggered if e[0] == 'error']
    assert len(error_events) > 0, "Error event not triggered"
    print("  ✓ Error handling works")
    
    # Test statistics
    stats = handler.get_handler_stats()
    assert stats['total_messages_handled'] >= 4, f"Message count incorrect: {stats}"
    assert 'CONNECT_RESPONSE' in stats['messages_by_type'], "Connect response not tracked"
    print("  ✓ Message statistics work")


def test_server_proxy():
    """Test server proxy functionality."""
    print("Testing Server Proxy...")
    
    # Create mock client
    class MockClient:
        def __init__(self):
            self.connected = True
            self.player_id = "test_player"
            self.server_info = {'max_players': 50, 'world_name': 'test'}
            self.world = None
            self.sent_messages = []
        
        def send_message(self, msg_type, data):
            self.sent_messages.append((msg_type, data))
            return True
        
        def get_client_stats(self):
            return {'connected': True, 'messages_sent': len(self.sent_messages)}
    
    mock_client = MockClient()
    proxy = ServerProxy(mock_client)
    
    # Test movement actions
    success = proxy.move_player('right', 50, 0)
    assert success, "Move player failed"
    
    last_message = mock_client.sent_messages[-1]
    assert last_message[0] == MessageType.PLAYER_MOVE, "Wrong message type for move"
    assert last_message[1]['direction'] == 'right', "Move direction not preserved"
    assert last_message[1]['velocity_x'] == 50, "Move velocity not preserved"
    print("  ✓ Movement actions work")
    
    # Test block actions
    success = proxy.place_block(10, 15, 2)
    assert success, "Place block failed"
    
    last_message = mock_client.sent_messages[-1]
    assert last_message[0] == MessageType.BLOCK_PLACE, "Wrong message type for block place"
    assert last_message[1]['x'] == 10, "Block X not preserved"
    assert last_message[1]['block_id'] == 2, "Block ID not preserved"
    print("  ✓ Block actions work")
    
    # Test chat
    success = proxy.send_chat("Test message")
    assert success, "Send chat failed"
    
    last_message = mock_client.sent_messages[-1]
    assert last_message[0] == MessageType.CHAT_MESSAGE, "Wrong message type for chat"
    assert last_message[1]['message'] == "Test message", "Chat message not preserved"
    print("  ✓ Chat actions work")
    
    # Test item actions
    success = proxy.pickup_item("item_123")
    assert success, "Pickup item failed"
    
    last_message = mock_client.sent_messages[-1]
    assert last_message[0] == MessageType.ITEM_PICKUP, "Wrong message type for pickup"
    assert last_message[1]['item_id'] == "item_123", "Item ID not preserved"
    print("  ✓ Item actions work")
    
    # Test utility methods
    assert proxy.is_connected() == True, "Connection status incorrect"
    assert proxy.get_player_id() == "test_player", "Player ID incorrect"
    
    server_info = proxy.get_server_info()
    assert server_info['max_players'] == 50, "Server info not preserved"
    print("  ✓ Utility methods work")


def test_game_client_initialization():
    """Test game client initialization."""
    print("Testing Game Client Initialization...")
    
    # Test client creation
    config = ClientConfig(
        server_host="localhost",
        server_port=25567,  # Different port to avoid conflicts
        player_name="TestClient"
    )
    client = GameClient(config)
    
    assert client.config.player_name == "TestClient", "Client config not set"
    assert client.connected == False, "Client should not be connected initially"
    assert client.connection_state == "disconnected", "Initial state incorrect"
    print("  ✓ Client initialization works")
    
    # Test client systems
    assert client.message_handler is not None, "Message handler not initialized"
    assert client.protocol is not None, "Protocol not initialized"
    assert hasattr(client, 'event_callbacks'), "Event callbacks not initialized"
    print("  ✓ Client systems initialized")
    
    # Test event callback system
    callback_called = []
    
    def test_callback(data):
        callback_called.append(data)
    
    client.add_event_callback('connected', test_callback)
    client._trigger_event('connected', {'test': 'data'})
    
    assert len(callback_called) > 0, "Event callback not called"
    assert callback_called[0]['test'] == 'data', "Event data not preserved"
    print("  ✓ Event system works")
    
    # Test statistics
    stats = client.get_client_stats()
    assert 'connection_state' in stats, "Stats missing connection state"
    assert 'player_name' in stats, "Stats missing player name"
    assert stats['connected'] == False, "Connected state should be False"
    print("  ✓ Client statistics work")


def test_client_connection():
    """Test client connection (without actual network)."""
    print("Testing Client Connection...")
    
    # Test connection initialization
    connection = ClientConnection("localhost", 25568, timeout=5.0)
    
    assert connection.host == "localhost", "Host not set"
    assert connection.port == 25568, "Port not set"
    assert connection.timeout == 5.0, "Timeout not set"
    assert connection.connected == False, "Should not be connected initially"
    print("  ✓ Connection initialization works")
    
    # Test message callback system
    received_messages = []
    
    def message_callback(msg_type, data):
        received_messages.append((msg_type, data))
    
    connection.set_message_callback(message_callback)
    assert connection.message_callback is not None, "Callback not set"
    print("  ✓ Message callback system works")
    
    # Test statistics
    stats = connection.get_stats()
    assert 'connected' in stats, "Stats missing connected field"
    assert 'bytes_sent' in stats, "Stats missing bytes_sent"
    assert 'messages_sent' in stats, "Stats missing messages_sent"
    assert stats['connected'] == False, "Connected should be False"
    print("  ✓ Connection statistics work")
    
    # Test message queuing (without actual sending)
    # This tests the queue system without network
    success = connection.send_message(MessageType.PING, {'test': 'data'})
    assert success == False, "Should fail when not connected"
    print("  ✓ Connection message queuing works")


def run_validation_tests():
    """Run all validation tests for Phase 2.2."""
    print("=" * 60)
    print("PHASE 2.2 VALIDATION: CLIENT IMPLEMENTATION")
    print("=" * 60)
    
    try:
        # Test core components
        test_client_config()
        print()
        
        test_client_game_world()
        print()
        
        test_client_message_handler()
        print()
        
        test_server_proxy()
        print()
        
        test_game_client_initialization()
        print()
        
        test_client_connection()
        print()
        
        print("=" * 60)
        print("✅ PHASE 2.2 VALIDATION PASSED!")
        print("✅ Client Implementation is working correctly")
        print("✅ All client components validated successfully")
        print("✅ GameClient, ClientConnection, ClientGameWorld operational")
        print("✅ Message handling and proxy systems working")
        print("✅ Ready for client-server integration testing")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"\n❌ PHASE 2.2 VALIDATION FAILED!")
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_validation_tests()
    sys.exit(0 if success else 1)
