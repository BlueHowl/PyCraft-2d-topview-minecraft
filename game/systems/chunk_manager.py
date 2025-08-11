from perlin_noise import PerlinNoise
from random import *
from game.config.settings import *
from game.config.game_config import GameConfig
from game.utils.logger import log_debug, log_warning, log_info

#chunk_manager code from https://www.reddit.com/r/pygame/comments/h8cfl3/infinite_world_generation_algorithm/
#modified

class Chunk():

    def __init__(self, directory, _seed, data_manager=None):
        self.directory = directory
        self.data_manager = data_manager
        
        # Initialize noise generators
        self.tarrainNoise = PerlinNoise(octaves=TERRAIN_OCTAVE, seed=_seed)
        self.biomeNoise = PerlinNoise(octaves=BIOME_OCTAVE, seed=_seed + 1)
        
        self.chunks = {}
        self.loaded = []
        self.chunkname = str()
        self.unsaved = int()
        
        # Memory management
        self.chunk_access_times = {}  # Track when chunks were last accessed
        self.modified_chunks = set()  # Track chunks modified by player
        self.max_cached_chunks = GameConfig.MAX_CHUNK_CACHE_SIZE
        
        # Load chunks from new format if data_manager is available
        if data_manager:
            world_name = directory.split('/')[-1] if '/' in directory else directory.split('\\')[-1]
            world_name = world_name.replace('saves\\', '').replace('saves/', '')
            game_data = data_manager.load_game(world_name)
            if game_data and game_data.get('entities', {}).get('chunks'):
                self.chunks = game_data['entities']['chunks']
                log_info(f"Loaded {len(self.chunks)} chunks from save file")
                return

    def get_chunks(self):
        return self.chunks

    def get_loaded(self):
        return self.loaded

    # Remove given chunk from the loaded list, so it does not affect the performance
    def unload(self, chunk):
        if chunk in self.loaded:
            self.loaded.remove(chunk)
            log_debug(f"Unloaded chunk: {chunk}")

    def cleanup_distant_chunks(self, player_chunk_x: int, player_chunk_y: int):
        """Remove chunks that are too far from the player to free memory."""
        chunks_to_unload = []
        max_distance = GameConfig.CHUNK_UNLOAD_DISTANCE
        
        for chunk_name in self.chunks:
            if ',' in chunk_name:
                try:
                    chunk_x, chunk_y = map(int, chunk_name.split(','))
                    distance = max(abs(chunk_x - player_chunk_x), abs(chunk_y - player_chunk_y))
                    
                    if distance > max_distance:
                        chunks_to_unload.append(chunk_name)
                except ValueError:
                    log_warning(f"Invalid chunk name format: {chunk_name}")
        
        # Only unload from loaded list, but keep chunk data for player modifications
        unloaded_count = 0
        for chunk_name in chunks_to_unload:
            if chunk_name in self.loaded:
                self.loaded.remove(chunk_name)
                unloaded_count += 1
            # Update access time but don't delete chunk data to preserve player modifications
            if chunk_name in self.chunk_access_times:
                import time
                self.chunk_access_times[chunk_name] = time.time()
        
        if unloaded_count > 0:
            log_debug(f"Unloaded {unloaded_count} distant chunks from render list (data preserved)")
    
    def manage_chunk_memory(self):
        """Manage chunk memory by removing old unused chunks if we exceed the limit."""
        # In debug mode, be much more conservative about memory cleanup
        effective_max = self.max_cached_chunks * 2 if GameConfig.DEBUG_MODE else self.max_cached_chunks
        
        if len(self.chunks) <= effective_max:
            return
        
        import time
        current_time = time.time()
        
        # Get chunks sorted by last access time (oldest first)
        # Only consider chunks that haven't been accessed in the last 5 minutes
        old_threshold = current_time - 300  # 5 minutes
        candidate_chunks = []
        
        for name, access_time in self.chunk_access_times.items():
            # Never delete chunks that have been modified by the player
            if (access_time < old_threshold and 
                name not in self.loaded and 
                name not in self.modified_chunks):
                candidate_chunks.append((name, access_time))
        
        candidate_chunks.sort(key=lambda x: x[1])
        
        # Only remove chunks if we have many old candidates
        chunks_to_remove = min(len(candidate_chunks), max(0, len(self.chunks) - effective_max))
        removed_count = 0
        
        for i in range(chunks_to_remove):
            chunk_name = candidate_chunks[i][0]
            if chunk_name in self.chunks and chunk_name not in self.loaded:
                del self.chunks[chunk_name]
                removed_count += 1
            if chunk_name in self.chunk_access_times:
                del self.chunk_access_times[chunk_name]
        
        if removed_count > 0:
            log_debug(f"Removed {removed_count} old unused chunks due to memory limit")
    
    def access_chunk(self, chunk_name: str):
        """Mark a chunk as accessed for memory management."""
        import time
        self.chunk_access_times[chunk_name] = time.time()


    # Generate a chunk at given coordinates using pnoise2 and adding it to the chunk list
    def generate(self, chunkx, chunky):

        GRASS = '01'
        DIRT = '07'
        WATER = '00'
        STONE = '1s'
        BUSH = '111'
        ICY_GRASS = '013'
        ICE = '012'
        ICY_BUSH = '114'
        ICY_DIRT = '015'
        ROCK = '1p'
        ICY_ROCK = '116'
        IRON_ORE = '118'
        DIAMOND_ORE = '119'
        COALD_ORE = '123'

        WATER_G_B= '01a'
        WATER_G_R = '02a'
        WATER_G_T = '03a'
        WATER_G_L = '04a'

        chunk = []
        chunkname = str(chunkx) + ',' + str(chunky)

        if chunkname not in self.chunks:
            # print("Generating chunk at {}".format(chunkname))
            for y in range(chunky * CHUNKSIZE, chunky * CHUNKSIZE + CHUNKSIZE):
                line = []
                for x in range(chunkx * CHUNKSIZE, chunkx * CHUNKSIZE + CHUNKSIZE):
                    tVal = round(self.tarrainNoise([x / TERRAIN_SCALE, y / TERRAIN_SCALE]), 5)
                    bVal = round(self.biomeNoise([x / BIOME_SCALE, y / BIOME_SCALE]), 5)
                    
                    if tVal >= -0.05 and tVal <= 0.19:
                        if bVal >= 0.2:
                            #biome foret tempérée
                            if randint(0, 10) == 0:
                                line.append([GRASS, BUSH])
                            else:
                                line.append([GRASS])
                        elif bVal >= 0 and bVal < 0.2:
                            #biome plaine tempérée
                            if randint(0, 150) == 0:
                                line.append([GRASS, BUSH])
                            else:
                                line.append([GRASS])
                        elif bVal > -0.2 and bVal < 0:
                            #biome plaine neige
                            if randint(0, 150) == 0:
                                line.append([ICY_GRASS, ICY_BUSH])
                            else:
                                line.append([ICY_GRASS])
                        elif bVal <= -0.2:
                            #biome foret neige
                            if randint(0, 10) == 0:
                                line.append([ICY_GRASS, ICY_BUSH])
                            else:
                                line.append([ICY_GRASS])

                    elif tVal > 0.19 and tVal <= 0.27:
                        if bVal > 0:
                            if randint(0, 5) == 0:
                                line.append([GRASS])
                            else:
                                if randint(0, 7) == 0:
                                    line.append([DIRT, ROCK])
                                else:
                                    line.append([DIRT])
                        elif bVal < 0:
                            if randint(0, 5) == 0:
                                line.append([ICY_GRASS])
                            else:
                                if randint(0, 7) == 0:
                                    line.append([ICY_DIRT, ICY_ROCK])
                                else:
                                    line.append([ICY_DIRT])

                    elif tVal > 0.27:
                        l = []
                        if bVal >= 0:
                            l.append(DIRT)
                        elif bVal < 0:
                            l.append(ICY_DIRT)

                        if randint(0, 15) == 0 and tVal > 0.285:
                            if randint(0, 20) == 0:
                                l.append(DIAMOND_ORE)
                            elif randint(0, 3) == 0:
                                l.append(COALD_ORE)
                            else:
                                l.append(IRON_ORE)
                        else:
                            l.append(STONE)
                        
                        line.append(l)

                    elif tVal > -0.3 and tVal < -0.05 and bVal < 0:
                        line.append([ICE])
                    else:
                        line.append([WATER])

                #chunk += ":"
                chunk.append(line)

            self.chunks.update({chunkname : chunk})
            self.unsaved += 1
        # else:
        # 	print("Chunk at {} has already been generated".format(chunkname))
        # self.load(chunkx, chunky)

    # Load chunk at given coordinates
    def load(self, chunkx, chunky):
        cname = str(chunkx) + ',' + str(chunky)

        if cname not in self.chunks:
            print("Chunk at {} does not exist".format(cname))
        else:
            if cname not in self.loaded:

                # Add the chunk to the loaded chunks list
                self.loaded.append(cname)
                # print("Loading chunk at {}".format(cname))
                data = []

                # Select the chunk acording to the coordinates given
                chunktoload = self.chunks[cname]

                for y, line in enumerate(chunktoload):
                    for x, tile in enumerate(line):
                        data.append((tile, x + chunkx * CHUNKSIZE, y + chunky * CHUNKSIZE))

                return data
            # else:
            # 	print("Chunk at {} has already been loaded".format(cname))
