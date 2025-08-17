"""
Network Message Types for PyCraft 2D

Defines all message types used in client-server communication.
"""

from enum import Enum, auto


class MessageType(Enum):
    """Enumeration of all network message types."""
    
    # Connection Management
    CONNECT = auto()
    CONNECT_RESPONSE = auto()
    DISCONNECT = auto()
    PING = auto()
    PONG = auto()
    HANDSHAKE = auto()
    HANDSHAKE_RESPONSE = auto()
    
    # Player Actions
    PLAYER_MOVE = auto()
    PLAYER_STOP = auto()
    PLAYER_ATTACK = auto()
    PLAYER_INTERACT = auto()
    PLAYER_RESPAWN = auto()
    
    # World Actions
    BLOCK_PLACE = auto()
    BLOCK_BREAK = auto()
    BLOCK_UPDATE = auto()
    CHUNK_REQUEST = auto()
    CHUNK_DATA = auto()
    CHUNK_UNLOAD = auto()
    WORLD_STATE = auto()
    WORLD_UPDATE = auto()
    
    # Inventory Actions
    INVENTORY_UPDATE = auto()
    ITEM_PICKUP = auto()
    ITEM_DROP = auto()
    ITEM_USE = auto()
    HOTBAR_CHANGE = auto()
    
    # Entity Management
    ENTITY_SPAWN = auto()
    ENTITY_DESPAWN = auto()
    ENTITY_UPDATE = auto()
    ENTITY_MOVE = auto()
    ENTITY_DAMAGE = auto()
    
    # Player State
    PLAYER_UPDATE = auto()
    PLAYER_HEALTH = auto()
    PLAYER_POSITION = auto()
    PLAYER_INVENTORY = auto()
    PLAYER_JOIN = auto()
    PLAYER_LEAVE = auto()
    PLAYER_STATE_SYNC = auto()
    PLAYER_SPAWN_DATA = auto()
    
    # World State
    WORLD_TIME = auto()
    WEATHER_UPDATE = auto()
    FLOATING_ITEM_SPAWN = auto()
    FLOATING_ITEM_PICKUP = auto()
    
    # Chat System
    CHAT_MESSAGE = auto()
    CHAT_BROADCAST = auto()
    
    # Server Management
    SERVER_STATUS = auto()
    PLAYER_LIST = auto()
    SERVER_INFO = auto()
    
    # Error Handling
    ERROR = auto()
    INVALID_MESSAGE = auto()
    
    # Crafting
    CRAFT_ITEM = auto()
    
    # Mob Actions
    MOB_SPAWN = auto()
    MOB_UPDATE = auto()
    MOB_DESPAWN = auto()
    MOB_ATTACK = auto()


# Message priority levels for network optimization
class MessagePriority(Enum):
    """Priority levels for network messages."""
    
    LOW = 1         # Non-critical updates (mob AI, distant entities)
    NORMAL = 2      # Standard gameplay messages (player movement, blocks)
    HIGH = 3        # Important updates (health, inventory)
    CRITICAL = 4    # Connection management, errors


# Map message types to their priorities
MESSAGE_PRIORITIES = {
    # Critical priority
    MessageType.CONNECT: MessagePriority.CRITICAL,
    MessageType.CONNECT_RESPONSE: MessagePriority.CRITICAL,
    MessageType.DISCONNECT: MessagePriority.CRITICAL,
    MessageType.ERROR: MessagePriority.CRITICAL,
    MessageType.HANDSHAKE: MessagePriority.CRITICAL,
    MessageType.HANDSHAKE_RESPONSE: MessagePriority.CRITICAL,
    
    # High priority
    MessageType.PLAYER_HEALTH: MessagePriority.HIGH,
    MessageType.PLAYER_RESPAWN: MessagePriority.HIGH,
    MessageType.INVENTORY_UPDATE: MessagePriority.HIGH,
    MessageType.ITEM_PICKUP: MessagePriority.HIGH,
    MessageType.PLAYER_JOIN: MessagePriority.HIGH,
    MessageType.PLAYER_LEAVE: MessagePriority.HIGH,
    
    # Normal priority
    MessageType.PLAYER_MOVE: MessagePriority.NORMAL,
    MessageType.PLAYER_UPDATE: MessagePriority.NORMAL,
    MessageType.BLOCK_PLACE: MessagePriority.NORMAL,
    MessageType.BLOCK_BREAK: MessagePriority.NORMAL,
    MessageType.CHUNK_DATA: MessagePriority.NORMAL,
    MessageType.CHAT_MESSAGE: MessagePriority.NORMAL,
    MessageType.PING: MessagePriority.NORMAL,
    MessageType.PONG: MessagePriority.NORMAL,
    
    # Low priority
    MessageType.MOB_UPDATE: MessagePriority.LOW,
    MessageType.ENTITY_UPDATE: MessagePriority.LOW,
    MessageType.WEATHER_UPDATE: MessagePriority.LOW,
    MessageType.WORLD_TIME: MessagePriority.LOW,
}


def get_message_priority(message_type: MessageType) -> MessagePriority:
    """Get the priority level for a message type."""
    return MESSAGE_PRIORITIES.get(message_type, MessagePriority.NORMAL)


# Message type categories for filtering and routing
class MessageCategory(Enum):
    """Categories for organizing message types."""
    
    CONNECTION = auto()
    PLAYER = auto()
    WORLD = auto()
    ENTITY = auto()
    INVENTORY = auto()
    CHAT = auto()
    SERVER = auto()
    ERROR = auto()


# Map message types to categories
MESSAGE_CATEGORIES = {
    # Connection
    MessageType.CONNECT: MessageCategory.CONNECTION,
    MessageType.CONNECT_RESPONSE: MessageCategory.CONNECTION,
    MessageType.DISCONNECT: MessageCategory.CONNECTION,
    MessageType.PING: MessageCategory.CONNECTION,
    MessageType.PONG: MessageCategory.CONNECTION,
    MessageType.HANDSHAKE: MessageCategory.CONNECTION,
    MessageType.HANDSHAKE_RESPONSE: MessageCategory.CONNECTION,
    
    # Player
    MessageType.PLAYER_MOVE: MessageCategory.PLAYER,
    MessageType.PLAYER_STOP: MessageCategory.PLAYER,
    MessageType.PLAYER_ATTACK: MessageCategory.PLAYER,
    MessageType.PLAYER_INTERACT: MessageCategory.PLAYER,
    MessageType.PLAYER_RESPAWN: MessageCategory.PLAYER,
    MessageType.PLAYER_UPDATE: MessageCategory.PLAYER,
    MessageType.PLAYER_HEALTH: MessageCategory.PLAYER,
    MessageType.PLAYER_POSITION: MessageCategory.PLAYER,
    MessageType.PLAYER_JOIN: MessageCategory.PLAYER,
    MessageType.PLAYER_LEAVE: MessageCategory.PLAYER,
    
    # World
    MessageType.BLOCK_PLACE: MessageCategory.WORLD,
    MessageType.BLOCK_BREAK: MessageCategory.WORLD,
    MessageType.BLOCK_UPDATE: MessageCategory.WORLD,
    MessageType.CHUNK_REQUEST: MessageCategory.WORLD,
    MessageType.CHUNK_DATA: MessageCategory.WORLD,
    MessageType.CHUNK_UNLOAD: MessageCategory.WORLD,
    MessageType.WORLD_TIME: MessageCategory.WORLD,
    MessageType.WEATHER_UPDATE: MessageCategory.WORLD,
    
    # Inventory
    MessageType.INVENTORY_UPDATE: MessageCategory.INVENTORY,
    MessageType.ITEM_PICKUP: MessageCategory.INVENTORY,
    MessageType.ITEM_DROP: MessageCategory.INVENTORY,
    MessageType.ITEM_USE: MessageCategory.INVENTORY,
    MessageType.HOTBAR_CHANGE: MessageCategory.INVENTORY,
    MessageType.PLAYER_INVENTORY: MessageCategory.INVENTORY,
    MessageType.CRAFT_ITEM: MessageCategory.INVENTORY,
    
    # Entity
    MessageType.ENTITY_SPAWN: MessageCategory.ENTITY,
    MessageType.ENTITY_DESPAWN: MessageCategory.ENTITY,
    MessageType.ENTITY_UPDATE: MessageCategory.ENTITY,
    MessageType.ENTITY_MOVE: MessageCategory.ENTITY,
    MessageType.ENTITY_DAMAGE: MessageCategory.ENTITY,
    MessageType.FLOATING_ITEM_SPAWN: MessageCategory.ENTITY,
    MessageType.FLOATING_ITEM_PICKUP: MessageCategory.ENTITY,
    MessageType.MOB_SPAWN: MessageCategory.ENTITY,
    MessageType.MOB_UPDATE: MessageCategory.ENTITY,
    MessageType.MOB_DESPAWN: MessageCategory.ENTITY,
    MessageType.MOB_ATTACK: MessageCategory.ENTITY,
    
    # Chat
    MessageType.CHAT_MESSAGE: MessageCategory.CHAT,
    MessageType.CHAT_BROADCAST: MessageCategory.CHAT,
    
    # Server
    MessageType.SERVER_STATUS: MessageCategory.SERVER,
    MessageType.PLAYER_LIST: MessageCategory.SERVER,
    MessageType.SERVER_INFO: MessageCategory.SERVER,
    
    # Error
    MessageType.ERROR: MessageCategory.ERROR,
    MessageType.INVALID_MESSAGE: MessageCategory.ERROR,
}


def get_message_category(message_type: MessageType) -> MessageCategory:
    """Get the category for a message type."""
    return MESSAGE_CATEGORIES.get(message_type, MessageCategory.ERROR)
