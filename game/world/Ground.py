import math
import pygame as pg
vec = pg.math.Vector2

from game.config.settings import CHUNKSIZE, CHUNKTILESIZE, TILESIZE

class Ground(pg.sprite.Sprite): #classe ground
    def __init__(self, game, x, y, tile, health, name):
        self.groups = game.all_sprites, game.grounds #définitions de la liste de groupes de textures
        pg.sprite.Sprite.__init__(self, self.groups) #définitions du joueur dans les groupes de textures
        self.name = name #récupération de la variable name
        self.health = health
        self.image = pg.Surface((TILESIZE, TILESIZE), pg.SRCALPHA, 32) #création d'une surface (32*32)
        #self.image.fill(GREEN)
        self.image.blit(tile, [0, 0]) #application de la texture sur la surface
        self.rect = self.image.get_rect() #assignation de la variable rect
        self.x = x #définition de la variable x
        self.y = y #définition de la variable y
        self.rect.x = x * TILESIZE #application de la position x de la surface
        self.rect.y = y * TILESIZE #application de la position y de la surface

        self.chunkpos = vec(math.floor(x / CHUNKSIZE), math.floor(y / CHUNKSIZE))
        self.chunkrect = pg.Rect(self.rect.x, self.rect.y, CHUNKTILESIZE, CHUNKTILESIZE)