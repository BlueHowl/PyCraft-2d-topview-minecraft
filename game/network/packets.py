"""
Network Packet Classes for PyCraft 2D

Defines individual packet classes for type-safe message handling.
"""

from dataclasses import dataclass, asdict
from typing import Dict, Any, List, Optional, Union
import time

from .message_types import MessageType


@dataclass
class BasePacket:
    """Base class for all network packets."""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert packet to dictionary for serialization."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        """Create packet from dictionary."""
        # Filter out extra fields that aren't in the dataclass
        valid_fields = {field.name for field in cls.__dataclass_fields__.values()}
        filtered_data = {k: v for k, v in data.items() if k in valid_fields}
        return cls(**filtered_data)


# Connection Management Packets
@dataclass
class ConnectPacket(BasePacket):
    """Client connection request."""
    player_name: str
    world_name: Optional[str] = None
    client_version: int = 1


@dataclass
class ConnectResponsePacket(BasePacket):
    """Server response to connection request."""
    success: bool
    player_id: Optional[str] = None
    error_message: Optional[str] = None
    server_info: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.server_info is None:
            self.server_info = {}


@dataclass
class DisconnectPacket(BasePacket):
    """Disconnect notification."""
    reason: str = "Disconnected"


@dataclass
class PingPacket(BasePacket):
    """Ping packet for connection keepalive."""
    ping_time: float = None
    
    def __post_init__(self):
        if self.ping_time is None:
            self.ping_time = time.time()


@dataclass
class PongPacket(BasePacket):
    """Pong response packet."""
    ping_time: float
    pong_time: float = None
    
    def __post_init__(self):
        if self.pong_time is None:
            self.pong_time = time.time()


# Player Action Packets
@dataclass
class PlayerMovePacket(BasePacket):
    """Player movement update."""
    x: float
    y: float
    vel_x: float
    vel_y: float
    direction: str


@dataclass
class PlayerUpdatePacket(BasePacket):
    """Comprehensive player state update."""
    health: int
    max_health: int
    inventory: List[Dict[str, Any]]
    position: Dict[str, float]


@dataclass
class PlayerPositionPacket(BasePacket):
    """Simple player position update."""
    x: float
    y: float


@dataclass
class PlayerHealthPacket(BasePacket):
    """Player health update."""
    health: int
    max_health: int


@dataclass
class PlayerJoinPacket(BasePacket):
    """Player join notification."""
    player_id: str
    player_name: str
    x: float
    y: float


@dataclass
class PlayerLeavePacket(BasePacket):
    """Player leave notification."""
    player_id: str
    reason: str = "Disconnected"


# World Action Packets
@dataclass
class BlockPlacePacket(BasePacket):
    """Block placement action."""
    x: int
    y: int
    block_id: int
    chunk_x: int
    chunk_y: int


@dataclass
class BlockBreakPacket(BasePacket):
    """Block break action."""
    x: int
    y: int
    chunk_x: int
    chunk_y: int


@dataclass
class BlockUpdatePacket(BasePacket):
    """Block state update."""
    x: int
    y: int
    block_id: int
    chunk_x: int
    chunk_y: int


@dataclass
class ChunkRequestPacket(BasePacket):
    """Request for chunk data."""
    chunk_x: int
    chunk_y: int


@dataclass
class ChunkDataPacket(BasePacket):
    """Chunk data transmission."""
    chunk_x: int
    chunk_y: int
    chunk_data: Dict[str, Any]


# Inventory Packets
@dataclass
class InventoryUpdatePacket(BasePacket):
    """Inventory state update."""
    inventory: List[Dict[str, Any]]
    hotbar_selection: int


@dataclass
class ItemPickupPacket(BasePacket):
    """Item pickup action."""
    item_id: str
    item_type: str
    quantity: int


@dataclass
class ItemDropPacket(BasePacket):
    """Item drop action."""
    item_type: str
    quantity: int
    x: float
    y: float


@dataclass
class ItemUsePacket(BasePacket):
    """Item use action."""
    item_type: str
    slot_index: int
    target_x: Optional[float] = None
    target_y: Optional[float] = None


@dataclass
class HotbarChangePacket(BasePacket):
    """Hotbar selection change."""
    selection: int


# Entity Packets
@dataclass
class EntitySpawnPacket(BasePacket):
    """Entity spawn notification."""
    entity_id: str
    entity_type: str
    x: float
    y: float
    data: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.data is None:
            self.data = {}


@dataclass
class EntityDespawnPacket(BasePacket):
    """Entity despawn notification."""
    entity_id: str


@dataclass
class EntityUpdatePacket(BasePacket):
    """Entity state update."""
    entity_id: str
    x: float
    y: float
    data: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.data is None:
            self.data = {}


@dataclass
class FloatingItemSpawnPacket(BasePacket):
    """Floating item spawn."""
    item_id: str
    item_type: str
    quantity: int
    x: float
    y: float


@dataclass
class FloatingItemPickupPacket(BasePacket):
    """Floating item pickup."""
    item_id: str
    player_id: str


# Mob Packets
@dataclass
class MobSpawnPacket(BasePacket):
    """Mob spawn notification."""
    mob_id: str
    mob_type: str
    x: float
    y: float
    health: int


@dataclass
class MobUpdatePacket(BasePacket):
    """Mob state update."""
    mob_id: str
    x: float
    y: float
    health: int
    state: str


@dataclass
class MobDespawnPacket(BasePacket):
    """Mob despawn notification."""
    mob_id: str


@dataclass
class MobAttackPacket(BasePacket):
    """Mob attack action."""
    mob_id: str
    target_id: str
    damage: int


# Chat Packets
@dataclass
class ChatMessagePacket(BasePacket):
    """Chat message."""
    message: str
    message_type: str = "chat"


@dataclass
class ChatBroadcastPacket(BasePacket):
    """Chat broadcast from server."""
    player_name: str
    message: str
    message_type: str = "chat"


# Server Management Packets
@dataclass
class ServerInfoPacket(BasePacket):
    """Server information."""
    server_name: str
    max_players: int
    current_players: int
    world_name: str
    protocol_version: int = 1


@dataclass
class PlayerListPacket(BasePacket):
    """List of connected players."""
    players: List[Dict[str, Any]]


@dataclass
class ServerStatusPacket(BasePacket):
    """Server status update."""
    status: str
    uptime: float
    tps: float  # Ticks per second


# World State Packets
@dataclass
class WorldTimePacket(BasePacket):
    """World time update."""
    game_time: float
    day_night_cycle: float


@dataclass
class WeatherUpdatePacket(BasePacket):
    """Weather state update."""
    weather_type: str
    intensity: float


# Crafting Packets
@dataclass
class CraftItemPacket(BasePacket):
    """Item crafting action."""
    recipe_id: str
    quantity: int


# Error Packets
@dataclass
class ErrorPacket(BasePacket):
    """Error notification."""
    error_code: str
    error_message: str


# Packet Factory
class PacketFactory:
    """Factory for creating packet instances from message type and data."""
    
    _packet_classes = {
        MessageType.CONNECT: ConnectPacket,
        MessageType.CONNECT_RESPONSE: ConnectResponsePacket,
        MessageType.DISCONNECT: DisconnectPacket,
        MessageType.PING: PingPacket,
        MessageType.PONG: PongPacket,
        
        MessageType.PLAYER_MOVE: PlayerMovePacket,
        MessageType.PLAYER_UPDATE: PlayerUpdatePacket,
        MessageType.PLAYER_POSITION: PlayerPositionPacket,
        MessageType.PLAYER_HEALTH: PlayerHealthPacket,
        MessageType.PLAYER_JOIN: PlayerJoinPacket,
        MessageType.PLAYER_LEAVE: PlayerLeavePacket,
        
        MessageType.BLOCK_PLACE: BlockPlacePacket,
        MessageType.BLOCK_BREAK: BlockBreakPacket,
        MessageType.BLOCK_UPDATE: BlockUpdatePacket,
        MessageType.CHUNK_REQUEST: ChunkRequestPacket,
        MessageType.CHUNK_DATA: ChunkDataPacket,
        
        MessageType.INVENTORY_UPDATE: InventoryUpdatePacket,
        MessageType.ITEM_PICKUP: ItemPickupPacket,
        MessageType.ITEM_DROP: ItemDropPacket,
        MessageType.ITEM_USE: ItemUsePacket,
        MessageType.HOTBAR_CHANGE: HotbarChangePacket,
        
        MessageType.ENTITY_SPAWN: EntitySpawnPacket,
        MessageType.ENTITY_DESPAWN: EntityDespawnPacket,
        MessageType.ENTITY_UPDATE: EntityUpdatePacket,
        MessageType.FLOATING_ITEM_SPAWN: FloatingItemSpawnPacket,
        MessageType.FLOATING_ITEM_PICKUP: FloatingItemPickupPacket,
        
        MessageType.MOB_SPAWN: MobSpawnPacket,
        MessageType.MOB_UPDATE: MobUpdatePacket,
        MessageType.MOB_DESPAWN: MobDespawnPacket,
        MessageType.MOB_ATTACK: MobAttackPacket,
        
        MessageType.CHAT_MESSAGE: ChatMessagePacket,
        MessageType.CHAT_BROADCAST: ChatBroadcastPacket,
        
        MessageType.SERVER_INFO: ServerInfoPacket,
        MessageType.PLAYER_LIST: PlayerListPacket,
        MessageType.SERVER_STATUS: ServerStatusPacket,
        
        MessageType.WORLD_TIME: WorldTimePacket,
        MessageType.WEATHER_UPDATE: WeatherUpdatePacket,
        
        MessageType.CRAFT_ITEM: CraftItemPacket,
        
        MessageType.ERROR: ErrorPacket,
    }
    
    @classmethod
    def create_packet(cls, message_type: MessageType, data: Dict[str, Any]) -> BasePacket:
        """
        Create a packet instance from message type and data.
        
        Args:
            message_type: The type of message
            data: The message data
            
        Returns:
            Packet instance
            
        Raises:
            ValueError: If message type is not supported
        """
        packet_class = cls._packet_classes.get(message_type)
        if packet_class is None:
            raise ValueError(f"Unsupported message type: {message_type}")
        
        try:
            return packet_class.from_dict(data)
        except Exception as e:
            raise ValueError(f"Failed to create packet for {message_type}: {e}")
    
    @classmethod
    def get_packet_class(cls, message_type: MessageType) -> type:
        """Get the packet class for a message type."""
        return cls._packet_classes.get(message_type)
    
    @classmethod
    def is_supported(cls, message_type: MessageType) -> bool:
        """Check if a message type is supported."""
        return message_type in cls._packet_classes
