"""
World Manager - Handles chunk loading, tile management, and world state.
"""
import math
from random import randint
from game.config.settings import *
from game.config.game_config import GameConfig
from game.utils.logger import log_debug, log_warning, log_info


class WorldManager:
    """Manages world chunks, tiles, and spawning."""
    
    def __init__(self, game):
        self.game = game
        self.last_cleanup_time = 0
        
    def update(self):
        """Update world state and perform periodic cleanup."""
        current_time = self.game.now
        
        # Temporary: Disable chunk cleanup entirely to preserve player modifications
        # TODO: Implement chunk saving before cleanup
        if False:  # Disabled for now
            cleanup_interval = GameConfig.CHUNK_CLEANUP_INTERVAL
            if current_time - self.last_cleanup_time > cleanup_interval:
                self.cleanup_chunks()
                self.last_cleanup_time = current_time
    
    def cleanup_chunks(self):
        """Clean up distant chunks to manage memory."""
        if hasattr(self.game, 'player') and hasattr(self.game.player, 'chunkpos'):
            player_chunk_x = int(self.game.player.chunkpos.x)
            player_chunk_y = int(self.game.player.chunkpos.y)
            
            # Clean up distant chunks
            self.game.chunkmanager.cleanup_distant_chunks(player_chunk_x, player_chunk_y)
            
            # Manage overall chunk memory
            self.game.chunkmanager.manage_chunk_memory()
            
            log_debug(f"Chunk cleanup completed. Active chunks: {len(self.game.chunkmanager.get_chunks())}")
        
    def reload_chunks(self):
        """Reload chunks around the player."""
        from game.utils.performance import time_operation
        
        log_info(f"=== RELOAD_CHUNKS CALLED ===")
        log_info(f"Game mode: {self.game.game_mode}")
        log_info(f"Current chunks before reload: {len(self.game.chunkmanager.get_chunks())}")
        
        with time_operation("chunk_reload"):
            px = self.game.player.chunkpos.x
            py = self.game.player.chunkpos.y
            self.game.area = []

            # Use 7x7 render distance for multiplayer clients to match server chunk generation
            if self.game.game_mode == "multiplayer_client":
                render_x = 3  # 7x7 grid: (-3,-3) to (3,3)
                render_y = 3
                # Use exact range to match server: from -3 to 3 (inclusive)
                x_range = range(-render_x, render_x + 1)
                y_range = range(-render_y, render_y + 1)
            else:
                render_x = CHUNKRENDERX
                render_y = CHUNKRENDERY
                x_range = range(-render_x - 1, render_x + 1)
                y_range = range(-render_y - 1, render_y + 1)

            for y in y_range:
                for x in x_range:
                    cx = int(px + x)
                    cy = int(py + y)
                    cname = str(cx) + ',' + str(cy)
                    self.game.area.append(cname)
                    if cname not in self.game.chunkmanager.get_chunks():
                        # Only generate chunks if NOT in multiplayer client mode
                        # Multiplayer clients should receive world state from server
                        if self.game.game_mode != "multiplayer_client":
                            log_info(f"Generating chunk {cname} (game_mode: {self.game.game_mode})")
                            self.game.chunkmanager.generate(cx, cy)
                        else:
                            log_info(f"Skipping chunk generation for {cname} (multiplayer_client mode)")
                    
                    # Always try to load chunks into sprite groups, regardless of whether they were just generated
                    # This ensures existing chunks from world state are properly loaded
                    chunk_data = self.game.chunkmanager.load(cx, cy)
                    if chunk_data:
                        log_debug(f"Loading sprites for chunk {cname} (data: {len(chunk_data) if chunk_data else 'None'})")
                        self.load_chunk(chunk_data)
                    elif cname in self.game.chunkmanager.get_chunks():
                        log_warning(f"Chunk {cname} exists in manager but load() returned None - checking chunk structure")
                        # Debug the chunk structure
                        chunk_raw = self.game.chunkmanager.get_chunks().get(cname)
                        if chunk_raw:
                            log_debug(f"Chunk {cname} structure: {type(chunk_raw)} with {len(chunk_raw) if hasattr(chunk_raw, '__len__') else 'unknown'} elements")
                            if len(chunk_raw) > 0:
                                log_debug(f"First row type: {type(chunk_raw[0])}, length: {len(chunk_raw[0]) if hasattr(chunk_raw[0], '__len__') else 'unknown'}")
                                if len(chunk_raw[0]) > 0:
                                    log_debug(f"First cell type: {type(chunk_raw[0][0])}, value: {chunk_raw[0][0]}")
                    else:
                        log_debug(f"Chunk {cname} not in manager - skipping load")
            
            log_info(f"Current chunks after reload: {len(self.game.chunkmanager.get_chunks())}")
            log_info(f"=== RELOAD_CHUNKS COMPLETE ===")

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
            # Check bounds to prevent IndexError
            if 0 <= insideY < len(cInfos) and 0 <= insideX < len(cInfos[insideY]):
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
            # Check bounds to prevent IndexError
            if 0 <= insideY < len(cInfos) and 0 <= insideX < len(cInfos[insideY]):
                if toRemove:
                    if tile in cInfos[insideY][insideX]:
                        cInfos[insideY][insideX].remove(tile)
                else:
                    if tile == '025' or tile == '026':
                        cInfos[insideY][insideX].insert(0, tile)
                    else:
                        cInfos[insideY][insideX].append(tile)

                # Mark this chunk as modified by player to prevent cleanup deletion
                self.game.chunkmanager.modified_chunks.add(cname)
                self.game.chunkmanager.access_chunk(cname)  # Update access time

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
        """Handle mob spawning logic with improved boundary checking."""
        from game.entities.mobs.Mob import Mob
        
        # Convert player chunk positions to integers to avoid float issues
        player_chunk_x = int(self.game.player.chunkpos.x)
        player_chunk_y = int(self.game.player.chunkpos.y)
        
        # Generate random spawn position within extended chunk render distance
        x = randint((player_chunk_x - CHUNKRENDERX - 1) * CHUNKSIZE,
                    (player_chunk_x + CHUNKRENDERX + 1) * CHUNKSIZE)
        y = randint((player_chunk_y - CHUNKRENDERY - 1) * CHUNKSIZE,
                    (player_chunk_y + CHUNKRENDERY + 1) * CHUNKSIZE)

        # Fix the boundary checking logic with proper parentheses
        # Spawn outside the inner safe zone but within the extended zone
        
        # Define safe zone boundaries (closer to player)
        safe_zone_left = (player_chunk_x - CHUNKRENDERX + 2) * CHUNKSIZE
        safe_zone_right = (player_chunk_x + CHUNKRENDERX - 2) * CHUNKSIZE
        safe_zone_top = (player_chunk_y - CHUNKRENDERY + 1) * CHUNKSIZE
        safe_zone_bottom = (player_chunk_y + CHUNKRENDERY - 1) * CHUNKSIZE
        
        # Check if spawn position is outside the safe zone
        outside_safe_zone = (x < safe_zone_left or x > safe_zone_right or 
                            y < safe_zone_top or y > safe_zone_bottom)
        
        if outside_safe_zone:
            tile = self.get_tile(vec(x * TILESIZE, y * TILESIZE), False)
            if tile and len(tile) > 0 and tile[0] == '0' and tile != '00':
                if self.game.isNight:
                    if self.game.hostile_mobs_amount < MAX_HOSTILE_MOBS:
                        canSpawn = True
                        # Check for nearby torches that prevent spawning
                        for ground in self.game.grounds:
                            if ground.name == 'torch_block':
                                distance = math.hypot(
                                    ground.x * TILESIZE - x * TILESIZE, 
                                    ground.y * TILESIZE - y * TILESIZE)
                                if distance <= 5 * TILESIZE:
                                    canSpawn = False
                                    break
                        
                        if canSpawn:
                            mobId = randint(3, 5)  # Hostile mobs
                            Mob(self.game, x, y, mobId)
                else:
                    if self.game.friendly_mobs_amount < MAX_FRIENDLY_MOBS:
                        mobId = randint(0, 2)  # Friendly mobs
                        Mob(self.game, x, y, mobId)
