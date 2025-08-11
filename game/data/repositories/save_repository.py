"""
Save repository - Handles game save operations.
"""

import os
from typing import Optional, List
from ..models import GameSave, PlayerState, WorldState
from ..serializers import JSONSerializer


class SaveRepository:
    """Repository for managing game saves."""
    
    def __init__(self, game_folder: str):
        self.game_folder = game_folder
        self.saves_path = os.path.join(game_folder, 'saves')
        
    def save_game(self, game_save: GameSave) -> bool:
        """Save complete game state to JSON format."""
        world_path = os.path.join(self.saves_path, game_save.world_name)
        
        # Prepare data for saving
        save_data = {
            'player_state': {
                'position': game_save.player_state.position,
                'health': game_save.player_state.health,
                'max_health': game_save.player_state.max_health,
                'inventory': game_save.player_state.inventory
            },
            'world_state': {
                'seed': game_save.world_state.seed,
                'spawn_point': game_save.world_state.spawn_point,
                'global_time': game_save.world_state.global_time,
                'night_shade': game_save.world_state.night_shade
            },
            'floating_items': game_save.floating_items,
            'chests': game_save.chests,
            'furnaces': game_save.furnaces,
            'mobs': game_save.mobs,
            'signs': game_save.signs,
            'chunks': game_save.chunks
        }
        
        # Save main save file
        main_save_path = os.path.join(world_path, 'save.json')
        return JSONSerializer.save_to_file(save_data, main_save_path)
    
    def load_game(self, world_name: str) -> Optional[GameSave]:
        """Load complete game state from JSON format."""
        world_path = os.path.join(self.saves_path, world_name)
        main_save_path = os.path.join(world_path, 'save.json')
        
        # Try loading new JSON format first
        save_data = JSONSerializer.load_from_file(main_save_path)
        if save_data:
            return self._create_game_save_from_json(world_name, save_data)
        
        # Fallback to legacy format
        return self._load_legacy_save(world_name)
    
    def _create_game_save_from_json(self, world_name: str, save_data: dict) -> GameSave:
        """Create GameSave object from JSON data."""
        player_data = save_data.get('player_state', {})
        world_data = save_data.get('world_state', {})
        
        player_state = PlayerState(
            position=tuple(player_data.get('position', (0, 0))),
            health=player_data.get('health', 255),
            max_health=player_data.get('max_health', 255),
            inventory=player_data.get('inventory', [])
        )
        
        world_state = WorldState(
            seed=world_data.get('seed', ''),
            spawn_point=tuple(world_data.get('spawn_point', (0, 0))),
            global_time=world_data.get('global_time', 0),
            night_shade=world_data.get('night_shade', 255)
        )
        
        return GameSave(
            world_name=world_name,
            player_state=player_state,
            world_state=world_state,
            floating_items=save_data.get('floating_items', []),
            chests=save_data.get('chests', {}),
            furnaces=save_data.get('furnaces', {}),
            mobs=save_data.get('mobs', {}),
            signs=save_data.get('signs', {}),
            chunks=save_data.get('chunks', {})
        )
    
    def _load_legacy_save(self, world_name: str) -> Optional[GameSave]:
        """Load game from legacy format and convert to new format."""
        world_path = os.path.join(self.saves_path, world_name)
        
        try:
            # Load legacy files
            level_save_path = os.path.join(world_path, 'level.save')
            if not os.path.exists(level_save_path):
                return None
            
            # Read level.save
            with open(level_save_path, 'r') as f:
                level_data = [line.strip() for line in f.readlines()]
            
            # Create player and world state from legacy data
            player_state = PlayerState.from_legacy_data(level_data)
            world_state = WorldState.from_legacy_data(level_data)
            
            # Load other legacy files
            floating_items = self._load_legacy_json_file(world_path, 'floatingItems.txt')
            chests = self._load_legacy_json_file(world_path, 'chests.txt')
            furnaces = self._load_legacy_json_file(world_path, 'furnaces.txt')
            mobs = self._load_legacy_json_file(world_path, 'mobs.txt')
            signs = self._load_legacy_json_file(world_path, 'signs.txt')
            chunks = self._load_legacy_json_file(world_path, 'map.txt')
            
            game_save = GameSave(
                world_name=world_name,
                player_state=player_state,
                world_state=world_state,
                floating_items=floating_items or [],
                chests=chests or {},
                furnaces=furnaces or {},
                mobs=mobs or {},
                signs=signs or {},
                chunks=chunks or {}
            )
            
            # Save in new format for future loads
            self.save_game(game_save)
            
            return game_save
            
        except Exception as e:
            print(f"Error loading legacy save {world_name}: {e}")
            return None
    
    def _load_legacy_json_file(self, world_path: str, filename: str) -> Optional[dict]:
        """Load a legacy JSON file."""
        file_path = os.path.join(world_path, filename)
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r') as f:
                    content = f.read().strip()
                    if content:
                        import json
                        return json.loads(content)
            except Exception as e:
                print(f"Error loading legacy file {filename}: {e}")
        return None
    
    def list_saves(self) -> List[str]:
        """List all available save worlds."""
        if not os.path.exists(self.saves_path):
            return []
        
        saves = []
        for item in os.listdir(self.saves_path):
            world_path = os.path.join(self.saves_path, item)
            if os.path.isdir(world_path):
                # Check if it has either new or legacy save format
                new_save = os.path.join(world_path, 'save.json')
                legacy_save = os.path.join(world_path, 'level.save')
                if os.path.exists(new_save) or os.path.exists(legacy_save):
                    saves.append(item)
        return saves
    
    def delete_save(self, world_name: str) -> bool:
        """Delete a save world."""
        world_path = os.path.join(self.saves_path, world_name)
        if os.path.exists(world_path):
            try:
                import shutil
                shutil.rmtree(world_path)
                return True
            except Exception as e:
                print(f"Error deleting save {world_name}: {e}")
        return False
    
    def create_new_save(self, world_name: str, seed: str, spawn_point: tuple) -> GameSave:
        """Create a new save with default values."""
        from ..models import PlayerState, WorldState
        
        player_state = PlayerState(
            position=spawn_point,
            health=20,  # Default health should be 20, not 255
            max_health=20,  # Default max health should be 20
            inventory=[[0, 0] for _ in range(34)]  # Default empty inventory
        )
        
        world_state = WorldState(
            seed=seed,
            spawn_point=spawn_point,
            global_time=0,
            night_shade=255
        )
        
        game_save = GameSave(
            world_name=world_name,
            player_state=player_state,
            world_state=world_state
        )
        
        # Save the new world
        self.save_game(game_save)
        return game_save
