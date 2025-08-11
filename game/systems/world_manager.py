"""
World Manager - Handles chunk loading, tile management, and world state.
"""
import math
from random import randint
from game.config.settings import *


class WorldManager:
    """Manages world chunks, tiles, and spawning."""
    
    def __init__(self, game):
        self.game = game
        
    def reload_chunks(self):
        """Reload chunks around the player."""
        px = self.game.player.chunkpos.x
        py = self.game.player.chunkpos.y
        self.game.area = []

        for y in range(-CHUNKRENDERY - 1, CHUNKRENDERY + 1):
            for x in range(-CHUNKRENDERX - 1, CHUNKRENDERX + 1):
                cx = int(px + x)
                cy = int(py + y)
                cname = str(cx) + ',' + str(cy)
                self.game.area.append(cname)
                if cname not in self.game.chunkmanager.get_chunks():
                    self.game.chunkmanager.generate(cx, cy)
                self.load_chunk(self.game.chunkmanager.load(cx, cy))

        for cname in self.game.chunkmanager.get_chunks():
            chunk = cname.split(',')
            chunk = (int(chunk[0]), int(chunk[1]))
            if cname not in self.game.area and cname in self.game.chunkmanager.get_loaded():
                for sprite in self.game.all_sprites:
                    if sprite != self.game.player and sprite not in self.game.floatingItems:
                        if sprite.chunkpos == chunk:
                            if sprite in self.game.mobs:
                                if sprite.isEnemy == 1:
                                    self.game.hostile_mobs_amount -= 1
                                else:
                                    self.game.friendly_mobs_amount -= 1
                            sprite.kill()
                self.game.chunkmanager.unload(cname)
    
    def load_chunk(self, data):
        """Load sprites from chunk data."""
        if data != None:
            for i in data:
                self.load_tile(i)

    def load_tile(self, i):
        """Load a specific tile."""
        from game.world.Ground import Ground
        from game.world.Layer1_Objs import Layer1_objs
        
        tiles = i[0]
        x = i[1]
        y = i[2]
        
        for tile in reversed(tiles):
            infos = self.game.textureCoordinate.get(tile)
            if infos != None:
                if tile[0] == '0':
                    if tile == '00':
                        # Handle tile connections
                        infos = self._get_tile_connection_info(tile, x, y)

                    Ground(self.game, x, y, 
                          self.game.tileImage[infos[0]].subsurface(
                              (infos[2]*TILESIZE, infos[3]*TILESIZE, TILESIZE, TILESIZE)), 
                          infos[5], infos[7])
                          
                elif tile[0] == '1':
                    Layer1_objs(self.game, x, y, 
                               self.game.tileImage[infos[0]].subsurface(
                                   (infos[2]*TILESIZE, infos[3]*TILESIZE, TILESIZE, TILESIZE)), 
                               infos[5], infos[7])

                if infos[1] == 1 and '025' not in tiles and '026' not in tiles:
                    break
    
    def _get_tile_connection_info(self, tile, x, y):
        """Get tile connection information for proper rendering."""
        if self.get_tile(vec((x - 1) * TILESIZE, y * TILESIZE), True) == '01' and self.get_tile(vec(x * TILESIZE, (y - 1) * TILESIZE), True) == '01':
            return self.game.textureCoordinate.get('09a')
        elif self.get_tile(vec((x - 1) * TILESIZE, y * TILESIZE), True) == '01' and self.get_tile(vec(x * TILESIZE, (y + 1) * TILESIZE), True) == '01':
            return self.game.textureCoordinate.get('00b')
        elif self.get_tile(vec((x + 1) * TILESIZE, y * TILESIZE), True) == '01' and self.get_tile(vec(x * TILESIZE, (y + 1) * TILESIZE), True) == '01':
            return self.game.textureCoordinate.get('0c')
        elif self.get_tile(vec((x + 1) * TILESIZE, y * TILESIZE), True) == '01' and self.get_tile(vec(x * TILESIZE, (y - 1) * TILESIZE), True) == '01':
            return self.game.textureCoordinate.get('00a')
        elif self.get_tile(vec((x + 1) * TILESIZE, y * TILESIZE), True) == '01':
            return self.game.textureCoordinate.get('02a')
        elif self.get_tile(vec((x - 1) * TILESIZE, y * TILESIZE), True) == '01':
            return self.game.textureCoordinate.get('04a')
        elif self.get_tile(vec(x * TILESIZE, (y + 1) * TILESIZE), True) == '01':
            return self.game.textureCoordinate.get('01a')
        elif self.get_tile(vec(x * TILESIZE, (y - 1) * TILESIZE), True) == '01':
            return self.game.textureCoordinate.get('03a')
        elif self.get_tile(vec((x - 1) * TILESIZE, (y - 1) * TILESIZE), True) == '01':
            return self.game.textureCoordinate.get('08a')
        elif self.get_tile(vec((x + 1) * TILESIZE, (y + 1) * TILESIZE), True) == '01':
            return self.game.textureCoordinate.get('05a')
        elif self.get_tile(vec((x + 1) * TILESIZE, (y - 1) * TILESIZE), True) == '01':
            return self.game.textureCoordinate.get('07a')
        elif self.get_tile(vec((x - 1) * TILESIZE, (y + 1) * TILESIZE), True) == '01':
            return self.game.textureCoordinate.get('06a')
        else:
            return self.game.textureCoordinate.get(tile)
    
    def get_tile(self, pos, getGround):
        """Get tile at position."""
        tilePos = vec(pos.x, pos.y) // TILESIZE
        insideX = int(tilePos.x - ((tilePos.x // CHUNKSIZE) * CHUNKSIZE))
        insideY = int(tilePos.y - ((tilePos.y // CHUNKSIZE) * CHUNKSIZE))

        cname = str(int(tilePos.x // CHUNKSIZE)) + ',' + str(int(tilePos.y // CHUNKSIZE))
        cInfos = self.game.chunkmanager.get_chunks().get(cname)
        if cInfos:
            cell = cInfos[insideY][insideX]
            if cell:
                if '025' in cell:
                    return '025'
                elif '026' in cell:
                    return '026'
                elif getGround:
                    return cell[0]
                else:
                    return cell[-1]
        return '.'

    def change_tile(self, pos, tile, toRemove):
        """Change tile at position."""
        tilePos = vec(pos.x, pos.y) // TILESIZE
        insideX = int(tilePos.x - ((tilePos.x // CHUNKSIZE) * CHUNKSIZE))
        insideY = int(tilePos.y - ((tilePos.y // CHUNKSIZE) * CHUNKSIZE))

        cname = str(int(tilePos.x // CHUNKSIZE)) + ',' + str(int(tilePos.y // CHUNKSIZE))
        cInfos = self.game.chunkmanager.get_chunks().get(cname)
        if cInfos:
            if toRemove:
                if tile in cInfos[insideY][insideX]:
                    cInfos[insideY][insideX].remove(tile)
            else:
                if tile == '025' or tile == '026':
                    cInfos[insideY][insideX].insert(0, tile)
                else:
                    cInfos[insideY][insideX].append(tile)

            self.load_tile([cInfos[insideY][insideX], int(tilePos.x), int(tilePos.y)])
            self.game.chunkmanager.unsaved += 1
    
    def get_current_pathfind(self):
        """Get current pathfinding data."""
        offset = vec(self.game.player.chunkpos.x - CHUNKRENDERX - 1,
                     self.game.player.chunkpos.y - CHUNKRENDERY - 1) * CHUNKSIZE

        tempPathfinding = []
        for y in range((CHUNKRENDERY * 2 + 2) * CHUNKSIZE):
            tempLst = []
            for x in range((CHUNKRENDERX * 2 + 2) * CHUNKSIZE):
                name = self.game.area[((y // CHUNKSIZE) * (CHUNKRENDERX * 2 + 2)) + (x // CHUNKSIZE)]
                cInfos = self.game.chunkmanager.get_chunks().get(name)

                if cInfos:
                    cell = cInfos[y % CHUNKSIZE][x % CHUNKSIZE]
                    if len(cell) > 1 or cell[0] == '00':
                        tempLst.append(0)
                    else:
                        tempLst.append(1)
            tempPathfinding.append(tempLst)

        return [offset, tempPathfinding]
    
    def handle_mob_spawning(self):
        """Handle mob spawning logic."""
        from game.entities.mobs.Mob import Mob
        
        x = randint((self.game.player.chunkpos.x - CHUNKRENDERX - 1) * CHUNKSIZE,
                    (self.game.player.chunkpos.x + CHUNKRENDERX + 1) * CHUNKSIZE)
        y = randint((self.game.player.chunkpos.y - CHUNKRENDERY - 1) * CHUNKSIZE,
                    (self.game.player.chunkpos.y + CHUNKRENDERY + 1) * CHUNKSIZE)

        if x < (self.game.player.chunkpos.x - CHUNKRENDERX + 2) * CHUNKSIZE or x > (self.game.player.chunkpos.x + CHUNKRENDERX - 2) * CHUNKSIZE and y < (self.game.player.chunkpos.y - CHUNKRENDERY + 1) * CHUNKSIZE or y > (self.game.player.chunkpos.y + CHUNKRENDERY - 1) * CHUNKSIZE:
            tile = self.get_tile(vec(x * TILESIZE, y * TILESIZE), False)
            if tile[0] == '0' and tile != '00':
                if self.game.isNight:
                    if self.game.hostile_mobs_amount < MAX_HOSTILE_MOBS:
                        canSpawn = True
                        for ground in self.game.grounds:
                            if ground.name == 'torch_block':
                                distance = math.hypot(
                                    ground.x * TILESIZE - x * TILESIZE, ground.y * TILESIZE - y * TILESIZE)
                                if distance <= 5 * TILESIZE:
                                    canSpawn = False
                                    break
                        if canSpawn:
                            mobId = randint(3, 5)
                            Mob(self.game, x, y, mobId)
                else:
                    if self.game.friendly_mobs_amount < MAX_FRIENDLY_MOBS:
                        mobId = randint(0, 2)
                        Mob(self.game, x, y, mobId)
