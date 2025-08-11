"""
JSON serializer for game data.
"""

import json
import os
from typing import Any, Dict, List, Optional
from dataclasses import asdict


class JSONSerializer:
    """Handles JSON serialization and deserialization of game data."""
    
    @staticmethod
    def save_to_file(data: Any, file_path: str) -> bool:
        """Save data to JSON file."""
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            # Convert dataclasses to dict if needed
            if hasattr(data, '__dataclass_fields__'):
                data = asdict(data)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Error saving to {file_path}: {e}")
            return False
    
    @staticmethod
    def load_from_file(file_path: str) -> Optional[Dict[str, Any]]:
        """Load data from JSON file."""
        try:
            if not os.path.exists(file_path):
                return None
                
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading from {file_path}: {e}")
            return None
    
    @staticmethod
    def save_multiple(data_dict: Dict[str, Any], base_path: str) -> bool:
        """Save multiple data items to separate JSON files."""
        success = True
        for filename, data in data_dict.items():
            file_path = os.path.join(base_path, f"{filename}.json")
            if not JSONSerializer.save_to_file(data, file_path):
                success = False
        return success
    
    @staticmethod
    def load_multiple(filenames: List[str], base_path: str) -> Dict[str, Any]:
        """Load multiple JSON files from a directory."""
        result = {}
        for filename in filenames:
            # Handle both .json extension and without
            if not filename.endswith('.json'):
                filename += '.json'
            
            file_path = os.path.join(base_path, filename)
            data = JSONSerializer.load_from_file(file_path)
            if data is not None:
                # Remove .json extension from key
                key = filename.replace('.json', '')
                result[key] = data
        return result
    
    @staticmethod
    def backup_file(file_path: str) -> bool:
        """Create a backup of an existing file."""
        try:
            if os.path.exists(file_path):
                backup_path = f"{file_path}.backup"
                import shutil
                shutil.copy2(file_path, backup_path)
                return True
            return False
        except Exception as e:
            print(f"Error creating backup of {file_path}: {e}")
            return False
