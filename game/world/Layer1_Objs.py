import math
import pygame as pg
vec = pg.math.Vector2

from game.config.settings import CHUNKSIZE, CHUNKTILESIZE, TILESIZE

class Layer1_objs(pg.sprite.Sprite):
    def __init__(self, game, x, y, tile, health, name):
        self.groups = game.all_sprites, game.Layer1, game.player_collisions
        pg.sprite.Sprite.__init__(self, self.groups)
        self.name = name
        self.health = health
        #self.game = game
        self.image = pg.Surface((TILESIZE, TILESIZE), pg.SRCALPHA, 32)
        self.image.blit(tile, [0, 0])
        self.rect = self.image.get_rect()
        self.x = x
        self.y = y
        self.rect.x = x * TILESIZE
        self.rect.y = y * TILESIZE

        self.chunkpos = vec(math.floor(x / CHUNKSIZE), math.floor(y / CHUNKSIZE))
        self.chunkrect = pg.Rect(self.rect.x, self.rect.y, CHUNKTILESIZE, CHUNKTILESIZE)
