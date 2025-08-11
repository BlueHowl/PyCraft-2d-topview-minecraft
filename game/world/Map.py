from game.config.settings import *
import json
from game.data import DataManager


class Map:
    def __init__(self, directoryname, game_folder=None):
        # Initialize data manager if game_folder is provided
        if game_folder:
            self.data_manager = DataManager(game_folder)
            world_name = directoryname.split('/')[-1] if '/' in directoryname else directoryname.split('\\')[-1]
            
            # Try loading from new data manager first
            game_data = self.data_manager.load_game(world_name)
            if game_data:
                self._load_from_new_format(game_data)
                return
        
        # Fallback to legacy loading
        self._load_legacy_format(directoryname)
    
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
    
    def _load_legacy_format(self, directoryname):
        """Load game data from legacy format."""
        self.levelSignData = {}
        try:
            with open(directoryname + '/signs.txt', 'rt') as f:
                for line in f:
                    l = line.strip().split(':')
                    # Handle signs data if needed
        except:
            pass

        self.MobsData = {}
        try:
            with open(directoryname + '/mobs.txt', 'rt') as f:
                for line in f:
                    l = line.strip().split(':')
                    # Handle mobs data if needed
        except:
            pass

        self.floatingItemsData = []
        try:
            with open(directoryname + '/floatingItems.txt', 'rt') as f:
                self.floatingItemsData = json.loads(f.read())
        except:
            self.floatingItemsData = []

        self.chestsData = {}
        try:
            with open(directoryname + '/chests.txt', 'rt') as f:
                self.chestsData = json.loads(f.read())
        except:
            self.chestsData = {}

        self.furnacesData = {}
        try:
            with open(directoryname + '/furnaces.txt', 'rt') as f:
                self.furnacesData = json.loads(f.read())
                for furnace in self.furnacesData.values():
                    furnace[3] = 0  # Reset furnace timers
        except:
            self.furnacesData = {}

        self.levelSavedData = []
        try:
            with open(directoryname + '/level.save', 'rt') as f:
                for line in f:
                    self.levelSavedData.append(line.strip())
        except:
            # Default values if file doesn't exist
            self.levelSavedData = ['0:0:255', '[]', '0', '0:0', '0', '255']
