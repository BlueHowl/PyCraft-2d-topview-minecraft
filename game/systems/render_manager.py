"""
Render Manager - Handles all rendering and drawing operations.
"""
import pygame as pg
from game.config.settings import *
from game.config.game_config import GameConfig


class RenderManager:
    """Manages game rendering and drawing operations."""
    
    def __init__(self, game):
        self.game = game
        
    def draw_game(self):
        """Main drawing method."""
        self.game.screen.fill(BLACK)
        
        # Create night screen overlay if needed
        nightScreen = None
        if self.game.night_shade != 255:
            nightScreen = pg.Surface((WIDTH, HEIGHT))
            nightScreen.fill((self.game.night_shade, self.game.night_shade,
                             min(self.game.night_shade + 20, 255)))

        # Draw ground sprites
        self._draw_grounds(nightScreen)
        
        # Draw layer 1 objects
        self._draw_layer1()
        
        # Draw floating items
        self._draw_floating_items()
        
        # Draw players
        self._draw_players()
        
        # Draw mobs
        self._draw_mobs()
        
        # Draw projectiles
        self._draw_projectiles()

        # Apply night overlay
        if nightScreen:
            self.game.screen.blit(nightScreen, (0, 0), special_flags=pg.BLEND_MULT)

        # Draw crosshair
        self._draw_crosshair()
        
        # Draw GUI
        self._draw_gui()
        
        # Draw debug info
        if GameConfig.DEBUG_MODE or self.game.input_commands:
            self._draw_debug_info()
            
        # Draw saving indicator
        if self.game.isSaving:
            self.game.screen.blit(self.game.menu_img.subsurface(
                0*TILESIZE, 4*TILESIZE, TILESIZE, TILESIZE), [WIDTH - 36, 4])

        # Draw death screen
        if self.game.player.dead:
            self._draw_death_screen()

        pg.display.flip()
    
    def _draw_grounds(self, nightScreen):
        """Draw ground sprites and torch lighting."""
        for sprite in self.game.grounds:
            self.game.screen.blit(sprite.image, self.game.camera.apply(sprite))
            if sprite.name == 'torch_block' and nightScreen:
                pos = self.game.camera.apply(sprite)
                nightScreen.blit(self.game.light, (pos.x + 16 - (self.game.light.get_width() / 2),
                                 pos.y + 16 - (self.game.light.get_height() / 2)))
    
    def _draw_layer1(self):
        """Draw layer 1 objects."""
        for sprite in self.game.Layer1:
            self.game.screen.blit(sprite.image, self.game.camera.apply(sprite))
    
    def _draw_floating_items(self):
        """Draw floating items."""
        for sprite in self.game.floatingItems:
            self.game.screen.blit(sprite.image, self.game.camera.apply(sprite))
            if GameConfig.SHOW_HITBOXES or self.game.hitboxDebug:
                pg.draw.rect(self.game.screen, GREEN, self.game.camera.apply(sprite), 1)
    
    def _draw_players(self):
        """Draw player sprites."""
        for sprite in self.game.players:
            self.game.screen.blit(sprite.image, self.game.camera.apply(sprite))
            if GameConfig.SHOW_HITBOXES or self.game.hitboxDebug:
                pg.draw.rect(self.game.screen, GREEN, self.game.camera.apply(sprite), 1)
        
        # Draw multiplayer players
        if hasattr(self.game, 'multiplayer_players'):
            for sprite in self.game.multiplayer_players:
                self.game.screen.blit(sprite.image, self.game.camera.apply(sprite))
                if GameConfig.SHOW_HITBOXES or self.game.hitboxDebug:
                    pg.draw.rect(self.game.screen, GREEN, self.game.camera.apply(sprite), 1)
                
                # Draw player name above the player
                if hasattr(sprite, 'player_name'):
                    name_surface = self.game.font_16.render(sprite.player_name, True, (255, 255, 255))
                    name_rect = name_surface.get_rect()
                    player_rect = self.game.camera.apply(sprite)
                    name_rect.centerx = player_rect.centerx
                    name_rect.bottom = player_rect.top - 5
                    self.game.screen.blit(name_surface, name_rect)
    
    def _draw_mobs(self):
        """Draw mob sprites."""
        for sprite in self.game.mobs:
            self.game.screen.blit(sprite.image, self.game.camera.apply(sprite))
            if GameConfig.SHOW_HITBOXES or self.game.hitboxDebug:
                pg.draw.rect(self.game.screen, GREEN, self.game.camera.apply(sprite), 1)
    
    def _draw_projectiles(self):
        """Draw projectile sprites."""
        for sprite in self.game.projectiles:
            self.game.screen.blit(sprite.image, self.game.camera.apply(sprite))
            if GameConfig.SHOW_HITBOXES or self.game.hitboxDebug:
                pg.draw.rect(self.game.screen, GREEN, self.game.camera.apply(sprite), 1)
    
    def _draw_crosshair(self):
        """Draw the crosshair cursor."""
        if not self.game.isInventoryOpened and not self.game.input_commands:
            itemCursor = self.game.player.hotbar.getCurrentSelectedItem()[3]
            
            if itemCursor == 1:
                self.game.screen.blit(self.game.crosshair_img.subsurface(0*TILESIZE, 0*TILESIZE, TILESIZE,
                                     TILESIZE), (self.game.mousePos[0] - 16, self.game.mousePos[1] - 16))
            elif itemCursor == 2:
                self.game.screen.blit(self.game.crosshair_img.subsurface(1*TILESIZE, 0*TILESIZE, TILESIZE, TILESIZE),
                                     (self.game.mousePos[0] - 16, self.game.mousePos[1] - 16))
            elif itemCursor == 3:
                self.game.screen.blit(self.game.crosshair_img.subsurface(2*TILESIZE, 0*TILESIZE, TILESIZE,
                                     TILESIZE), (self.game.mousePos[0] - 16, self.game.mousePos[1] - 16))
            else:
                self.game.screen.blit(self.game.crosshair_img.subsurface(0*TILESIZE, 1*TILESIZE, TILESIZE,
                                     TILESIZE), (self.game.mousePos[0] - 16, self.game.mousePos[1] - 16))
    
    def _draw_gui(self):
        """Draw GUI elements."""
        for sprite in self.game.gui:
            self.game.screen.blit(sprite.image, sprite.rect)
    
    def _draw_debug_info(self):
        """Draw debug information."""
        self.game.input_commands_txt.draw(self.game.screen)
        debug_surface = pg.Surface((200, 160), pg.SRCALPHA)
        debug_surface.fill((255, 255, 255, 128))

        # FPS
        debug_surface.blit(self.game.font_16.render(
            f'Fps : {round(self.game.clock.get_fps())}/{FPS}', False, BLACK), (10, 10))
        
        # Position
        debug_surface.blit(self.game.font_16.render(
            f'X : {round(self.game.player.pos.x / TILESIZE, 6)}, Y : {round(self.game.player.pos.y / TILESIZE, 6)}', False, BLACK), (10, 30))

        # Chunk info
        insideX = int(self.game.player.tilepos.x - ((self.game.player.tilepos.x // CHUNKSIZE) * CHUNKSIZE))
        insideY = int(self.game.player.tilepos.y - ((self.game.player.tilepos.y // CHUNKSIZE) * CHUNKSIZE))
        debug_surface.blit(self.game.font_16.render(
            f'Chunk : {insideX}:{insideY} in {round(self.game.player.chunkpos.x)}:{round(self.game.player.chunkpos.y)}', False, BLACK), (10, 50))

        # Facing direction
        directions = {0: 'North', 1: 'South', 2: 'West', 3: 'East'}
        direction = directions.get(self.game.player.lastWalkStatement, 'Unknown')
        debug_surface.blit(self.game.font_16.render(
            f'Facing : {self.game.player.lastWalkStatement}, {direction}', False, BLACK), (10, 70))

        # Time
        hour = self.game.day_time * 96 // 3600000
        minutes = (self.game.day_time * 96 // 60000) % 60
        time_period = 'Night' if self.game.isNight else 'Day'
        debug_surface.blit(self.game.font_16.render(
            f'Day : {self.game.global_time // DAY_LENGTH}, {hour:02d}:{minutes:02d} {time_period}', False, BLACK), (10, 90))

        # Cursor position
        cursor_x = round((self.game.camera.getCamClickTopLeft()[0] + self.game.mousePos[0]) / TILESIZE, 2)
        cursor_y = round((self.game.camera.getCamClickTopLeft()[1] + self.game.mousePos[1]) / TILESIZE, 2)
        debug_surface.blit(self.game.font_16.render(
            f'Cursor : {cursor_x} : {cursor_y}', False, BLACK), (10, 110))

        # Mob counts
        debug_surface.blit(self.game.font_16.render(
            f'Mobs : F {self.game.friendly_mobs_amount}/{MAX_FRIENDLY_MOBS}, H {self.game.hostile_mobs_amount}/{MAX_HOSTILE_MOBS}', False, BLACK), (10, 130))

        self.game.screen.blit(debug_surface, (0, 0))
    
    def _draw_death_screen(self):
        """Draw the death/respawn screen."""
        respawn_surface = pg.Surface((WIDTH, HEIGHT), pg.SRCALPHA)
        respawn_surface.fill((0, 0, 0, 128))

        title = self.game.font_64.render('You Died', False, WHITE)
        respawn_surface.blit(title, ((WIDTH / 2) - (title.get_width() / 2) - 8, 50))

        respawnTxt = self.game.font_32.render('Respawn', False, WHITE)
        respawn_surface.blit(respawnTxt, ((WIDTH / 2) - (respawnTxt.get_width() / 2), 
                                         (HEIGHT / 2) - (respawnTxt.get_height() / 2)))
        
        self.game.respawn_rect = (((WIDTH / 2) - (respawnTxt.get_width() / 2) - 5, 
                                  (HEIGHT / 2) - (respawnTxt.get_height() / 2) - 5, 
                                  respawnTxt.get_width() + 10, respawnTxt.get_height() + 5))
        pg.draw.rect(respawn_surface, WHITE, self.game.respawn_rect, 2)

        self.game.screen.blit(respawn_surface, (0, 0))
