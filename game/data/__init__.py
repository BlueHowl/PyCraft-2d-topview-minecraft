"""
Data package - Handles all data persistence and management.
"""

from .data_manager import DataManager
from .models import *
from .repositories import *
from .serializers import *

__all__ = ['DataManager']
