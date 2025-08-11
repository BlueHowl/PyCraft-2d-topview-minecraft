from perlin_noise import PerlinNoise
from random import *
from game.config.settings import *

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
        
        # Load chunks from new format if data_manager is available
        if data_manager:
            world_name = directory.split('/')[-1] if '/' in directory else directory.split('\\')[-1]
            world_name = world_name.replace('saves\\', '').replace('saves/', '')
            game_data = data_manager.load_game(world_name)
            if game_data and game_data.get('entities', {}).get('chunks'):
                self.chunks = game_data['entities']['chunks']
                return
        
        # Fallback to legacy map.txt loading
        try:
            f = open(directory + "/map.txt", 'r+')
            file = f.read()
            if file != "":
                self.chunks = eval(file)
            f.close()
        except IOError:
            pass

    def get_chunks(self):
        return self.chunks

    def get_loaded(self):
        return self.loaded

    # remove given chunk from the loaded list, so it does not affect the performance
    def unload(self, chunk):
        self.loaded.remove(chunk)


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
