"""
Network Client Package for PyCraft 2D

This package contains the client-side networking implementation for multiplayer functionality.
The client handles server connection, state synchronization, and message processing.

Components:
- GameClient: Main client class handling server connection
- ClientConnection: Client-side connection management
- ClientMessageHandler: Client-side message processing
- ClientGameWorld: Client-side game world with server synchronization
- ServerProxy: Abstraction layer for server communication
"""

from .game_client import GameClient, ClientConfig
from .client_connection import ClientConnection
from .client_message_handler import ClientMessageHandler
from .client_game_world import ClientGameWorld
from .server_proxy import ServerProxy

__all__ = [
    'GameClient',
    'ClientConfig',
    'ClientConnection',
    'ClientMessageHandler',
    'ClientGameWorld',
    'ServerProxy'
]
