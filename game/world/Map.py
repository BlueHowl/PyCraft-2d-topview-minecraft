from game.config.settings import *
import json
from game.data import DataManager


class Map:
    def __init__(self, directoryname, game_folder=None):
        # Initialize data manager if game_folder is provided
        if game_folder:
            self.data_manager = DataManager(game_folder)
            world_name = directoryname.split('/')[-1] if '/' in directoryname else directoryname.split('\\')[-1]
            
            # Load from new data manager
            game_data = self.data_manager.load_game(world_name)
            if game_data:
                self._load_from_new_format(game_data)
                return
        
        # Create default state if no valid save data found
        self._create_default_state()
    
    def _load_from_new_format(self, game_data):
        """Load game data from new JSON format."""
        entities = game_data.get('entities', {})
        
        self.levelSignData = entities.get('signs', {})
        self.MobsData = entities.get('mobs', {})
        self.floatingItemsData = entities.get('floating_items', [])
        self.chestsData = entities.get('chests', {})
        self.furnacesData = entities.get('furnaces', {})
        
        # Reset furnace timers
        for furnace in self.furnacesData.values():
            if len(furnace) > 3:
                furnace[3] = 0
        
        # Convert player and world state to legacy format for compatibility
        player_state = game_data.get('player_state', {})
        world_state = game_data.get('world_state', {})
        
        pos_health = f"{player_state.get('position', (0, 0))[0]}:{player_state.get('position', (0, 0))[1]}:0:{player_state.get('health', 20)}:{player_state.get('max_health', 20)}"
        inventory_json = json.dumps(player_state.get('inventory', []))
        seed = world_state.get('seed', '')
        spawn = f"{world_state.get('spawn_point', (0, 0))[0]}:{world_state.get('spawn_point', (0, 0))[1]}"
        global_time = str(world_state.get('global_time', 0))
        night_shade = str(world_state.get('night_shade', 255))
        
        self.levelSavedData = [pos_health, inventory_json, seed, spawn, global_time, night_shade]
    
    def _create_default_state(self):
        """Create default state for new worlds or when save data is unavailable."""
        self.levelSignData = {}
        self.MobsData = {}
        self.floatingItemsData = []
        self.chestsData = {}
        self.furnacesData = {}
        
        # Default values for level data: [position:health, inventory, seed, spawn, time, night_shade]
        self.levelSavedData = ['0:0:0:20:20', '[]', '0', '0:0', '0', '255']
