"""
Game State Manager - Handles game mechanics like day/night cycle, saving, etc.
"""
import pygame as pg
import threading
from os import path
from game.config.settings import *
from game.data import DataManager


class GameStateManager:
    """Manages game state including day/night cycle, saving, and items."""
    
    def __init__(self, game):
        self.game = game
        self.data_manager = DataManager(game.game_folder)
        
    def update_day_night_cycle(self):
        """Update the day/night cycle."""
        self.game.global_time = round(self.game.global_time + self.game.dt * 1000)
        self.game.day_time = (self.game.global_time % DAY_LENGTH)
        
        if self.game.day_time > DAY_LENGTH - (DAY_LENGTH // 3) and self.game.day_time < DAY_LENGTH:
            self.game.isNight = True
            if self.game.day_time > self.game.last_day_time + SHADE_SPEED:
                if self.game.night_shade > MIN_NIGHT_SHADE:
                    self.game.night_shade -= 1
                    self.game.last_day_time = self.game.day_time
                else:
                    self.game.last_day_time = 0
        else:
            self.game.isNight = False
            if self.game.day_time > self.game.last_day_time + SHADE_SPEED:
                if self.game.night_shade < 255:
                    self.game.night_shade += 1
                    self.game.last_day_time = self.game.day_time
                else:
                    self.game.last_day_time = 0

    def skip_night(self):
        """Skip the night."""
        self.game.global_time += DAY_LENGTH - self.game.day_time
        self.game.night_shade = 255

    def sleep(self):
        """Handle player sleeping."""
        if self.game.isNight:
            self.game.player.pos = vec(self.game.spawnPoint.x, self.game.spawnPoint.y)  # Create a COPY, don't share the same object!
            self.skip_night()
            self.game.player.health = self.game.player.lifebar.maxHealth
            self.game.player.lifebar.updateHealth(self.game.player.health)
            self.game.player.lifebar.updateSurface()

    def give_item(self, itemId, quantity):
        """Give item to player."""
        rest = quantity % STACK
        stack_Number = (quantity - rest) // STACK

        if quantity < 64:
            self.game.player.hotbar.addItem(itemId, quantity)
        else:
            for i in range(stack_Number):
                self.game.player.hotbar.addItem(itemId, STACK)
            if rest != 0:
                self.game.player.hotbar.addItem(itemId, rest)

        self.game.play_sound('drop_item')

    def save_game(self):
        """Save the game state using the new data manager."""
        # Prepare player state data
        player_state = {
            'position': (int(self.game.player.pos.x // TILESIZE), int(self.game.player.pos.y // TILESIZE)),
            'health': self.game.player.health,
            'max_health': getattr(self.game.player.lifebar, 'maxHealth', 255),
            'inventory': self.game.player.hotbar.itemList
        }
        
        # Prepare world state data
        world_state = {
            'seed': getattr(self.game.map, 'levelSavedData', ['', '', '0'])[2] if hasattr(self.game, 'map') else '0',
            'spawn_point': (int(self.game.spawnPoint.x // TILESIZE), int(self.game.spawnPoint.y // TILESIZE)),  # Convert to tile coords
            'global_time': self.game.global_time,
            'night_shade': self.game.night_shade
        }
        
        # Prepare entity data
        floating_items_list = []
        for item in self.game.floatingItems:
            floating_items_list.append([round(item.pos.x, 2), round(item.pos.y, 2), item.item])
        
        entities = {
            'floating_items': floating_items_list,
            'chests': getattr(self.game.map, 'chestsData', {}),
            'furnaces': getattr(self.game.map, 'furnacesData', {}),
            'mobs': getattr(self.game.map, 'MobsData', {}),
            'signs': getattr(self.game.map, 'levelSignData', {}),
            'chunks': getattr(self.game.chunkmanager, 'chunks', {}) if hasattr(self.game, 'chunkmanager') else {}
        }
        
        # Save using the new data manager
        success = self.data_manager.save_game(
            world_name=self.game.worldName,
            player_state=player_state,
            world_state=world_state,
            entities=entities
        )
        
        if success:
            self.game.hasPlayerStateChanged = False
            # Reset unsaved chunk counter
            if hasattr(self.game, 'chunkmanager'):
                self.game.chunkmanager.unsaved = 0
            
            print(f"Game saved successfully to {self.game.worldName}")
        else:
            print(f"Failed to save game {self.game.worldName}")
        
        return success
