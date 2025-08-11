import math
import pygame as pg

from game.config.settings import BLACK, ITEM_DESPAWN_TIME, TILESIZE
vec = pg.math.Vector2

class FloatingItem(pg.sprite.Sprite):
    def __init__(self, game, x, y, item):
        self.groups = game.all_sprites, game.moving_sprites, game.floatingItems
        pg.sprite.Sprite.__init__(self, self.groups)
        self.game = game
        self.pos = vec(x, y)
        self.item = item
        self.spawn_time = self.game.now

        self.image = pg.Surface((TILESIZE, TILESIZE), pg.SRCALPHA, 32) #création d'un surface transparente (32*32)

        itemInfos = self.game.itemTextureCoordinate.get(item[0])
        if itemInfos != None:
            self.tex = pg.transform.scale(self.game.items_img.subsurface((itemInfos[0]*TILESIZE, itemInfos[1]*TILESIZE, TILESIZE, TILESIZE)), (24, 24))

        self.rect = self.image.get_rect() #assignation de la variable rect

        self.rect.x = self.pos.x #application de la position x de la surface
        self.rect.y = self.pos.y #application de la position y de la surface

    def update(self):
        if self.game.now - self.spawn_time > ITEM_DESPAWN_TIME:
            self.kill()

        hits = pg.sprite.spritecollide(self, self.game.Layer1, False) #récupération des collisions

        if hits:
            playerPos = self.game.player.pos
            playerLWS = self.game.player.lastWalkStatement

            if playerLWS == 2 or playerLWS == 3: #si il y a des collisions
                self.collideX(playerPos, hits)
                self.collideY(playerPos, hits)

            if playerLWS == 0 or playerLWS == 1: #si il y a des collisions
                self.collideY(playerPos, hits)
                self.collideX(playerPos, hits)

        self.image = pg.Surface((TILESIZE, TILESIZE), pg.SRCALPHA, 32) #redéfintion dela surface image en transparente (32*32)

        itemInfos = self.game.itemTextureCoordinate.get(self.item[0])

        if itemInfos != None:
            yOffset = abs(math.sin(self.game.now // (8*60) )) * 3
            self.image.blit(self.tex, (0, yOffset))
            if itemInfos[2] == 1:
                if self.item[1] < 10:
                    self.image.blit(self.game.font_10.render(str(self.item[1]), True, BLACK), (20, yOffset + 14))
                else:
                    self.image.blit(self.game.font_10.render(str(self.item[1]), True, BLACK), (14, yOffset + 14))

    def collideX(self, playerPos, hits):
        if self.pos.x > playerPos.x: #si la position est plus grande que la pos du joueur
            self.pos.x = hits[0].rect.left - self.rect.width #application de la position, collision gauche
        if self.pos.x < playerPos.x: #si la position est plus petite que la pos du joueur
            self.pos.x = hits[0].rect.right #application de la position, collision droite

        self.rect.x = self.pos.x #application de la position x sur le joueur

    def collideY(self, playerPos, hits):
        if self.pos.y > playerPos.y: #si la position est plus grande que la pos du joueur
            self.pos.y = hits[0].rect.top - self.rect.height #application de la position, collision bas
        if self.pos.y < playerPos.y: #si la position est plus petite que la pos du joueur
            self.pos.y = hits[0].rect.bottom #application de la position, collision haut

        self.rect.y = self.pos.y #application de la position y sur le joueur
