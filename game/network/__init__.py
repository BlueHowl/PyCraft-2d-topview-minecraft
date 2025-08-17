"""
PyCraft 2D Networking Module

This module provides networking capabilities for multiplayer gameplay.
"""

__version__ = "1.0.0"
__author__ = "PyCraft 2D Team"

# Network Constants
DEFAULT_PORT = 25565
PROTOCOL_VERSION = 1
MAX_PACKET_SIZE = 1024 * 64  # 64KB max packet size
CONNECTION_TIMEOUT = 30.0  # seconds
HEARTBEAT_INTERVAL = 5.0  # seconds

# Import main networking classes for easy access
from .message_types import MessageType
from .protocol import NetworkProtocol

__all__ = [
    'MessageType',
    'NetworkProtocol',
    'DEFAULT_PORT',
    'PROTOCOL_VERSION',
    'MAX_PACKET_SIZE',
    'CONNECTION_TIMEOUT',
    'HEARTBEAT_INTERVAL'
]
