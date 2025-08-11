"""
Game State Manager - Handles game mechanics like day/night cycle, saving, etc.
"""
import pygame as pg
import threading
from os import path
from game.config.settings import *


class GameStateManager:
    """Manages game state including day/night cycle, saving, and items."""
    
    def __init__(self, game):
        self.game = game
        
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
            self.game.player.pos = self.game.spawnPoint * TILESIZE
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

        pg.mixer.Sound.play(self.game.audioList.get('drop_item'))

    def save_game(self):
        """Save the game state."""
        playerState = str(int(self.game.player.pos.x // TILESIZE)) + ':' + str(int(self.game.player.pos.y // TILESIZE)) + ':' + str(self.game.player.health)
        
        lst = []
        lst.append((playerState + '\n' + str(self.game.player.hotbar.itemList) + '\n' + self.game.map.levelSavedData[2] + '\n' + str(int(self.game.spawnPoint.x)) + ':' + str(int(
            self.game.spawnPoint.y)) + '\n' + str(self.game.global_time) + '\n' + str(self.game.night_shade), path.join(self.game.game_folder, 'saves/' + self.game.worldName + '/level.save')))
        self.game.hasPlayerStateChanged = False

        floatingItemsList = []
        for item in self.game.floatingItems:
            floatingItemsList.append([round(item.pos.x, 2), round(item.pos.y, 2), item.item])

        lst.append((str(floatingItemsList), path.join(
            self.game.game_folder, 'saves/' + self.game.worldName + '/floatingItems.txt')))
        lst.append((str(self.game.map.chestsData).replace("'", '"'), path.join(
            self.game.game_folder, 'saves/' + self.game.worldName + '/chests.txt')))
        lst.append((str(self.game.map.furnacesData).replace("'", '"'), path.join(
            self.game.game_folder, 'saves/' + self.game.worldName + '/furnaces.txt')))

        save = AsyncWrite(self.game, lst)
        save.start()


class AsyncWrite(threading.Thread):
    """Asynchronous write thread for saving game data."""
    
    def __init__(self, game, lst):
        threading.Thread.__init__(self)
        self.game = game
        self.lst = lst

    def run(self):
        self.game.isSaving = True
        for s in self.lst:
            with open(s[1], 'wt') as f:
                f.write(s[0])

        if self.game.chunkmanager.unsaved != 0:
            f = open(path.join(self.game.game_folder, 'saves/' +
                     self.game.worldName + "/map.txt"), 'w+')
            f.seek(0)
            f.truncate()
            f.write(str(self.game.chunkmanager.chunks))
            print("Saved {} chunks".format(self.game.chunkmanager.unsaved))
            self.game.chunkmanager.unsaved = 0
            f.close()

        self.game.isSaving = False
