import math
import pygame as pg

from game.entities.FloatingItem import FloatingItem
from game.config.settings import MELEEREACH, STACK, TILESIZE, WHITE

class Hotbar(pg.sprite.Sprite):
    def __init__(self, game, xOffset, yOffset, bar, selector, index, itemList):
        self.groups = game.gui #game.all_sprites, game.gui
        pg.sprite.Sprite.__init__(self, self.groups)
        self.game = game
        self.xOffset = xOffset
        self.yOffset = yOffset
        self.x = xOffset #définition de la variable x
        self.y = yOffset #définition de la variable y

        self.index = index
        self.bar = bar
        self.selector = selector

        self.itemList = itemList

        self.updateSelector(index)

        self.rect = self.image.get_rect() #assignation de la variable rect
        self.rect.x = self.x #application de la position x de la surface
        self.rect.y = self.y #application de la position y de la surface

    def updateSelector(self, i):
        self.index = i % 9
        self.image = pg.Surface((9*TILESIZE,1*TILESIZE), pg.SRCALPHA, 32) #création d'une surface transparente

        self.image.blit(self.bar, [0, 0])

        for i, item in enumerate(self.itemList):
            itemInfos = self.game.itemTextureCoordinate.get(item[0])
            if itemInfos != None:
                self.image.blit(self.game.items_img.subsurface((itemInfos[0]*TILESIZE, itemInfos[1]*TILESIZE, TILESIZE, TILESIZE)), [i*TILESIZE, 0])
                if itemInfos[2] == 1:
                    if item[1] < 10:
                        self.image.blit(self.game.font_10.render(str(item[1]), True, WHITE), [i*TILESIZE + 22, 18])
                    else:
                        self.image.blit(self.game.font_10.render(str(item[1]), True, WHITE), [i*TILESIZE + 16, 18])

        self.image.blit(self.selector, [self.index*TILESIZE, 0])

    def addItem(self, itemId, amount):
        itemInfos = self.game.itemTextureCoordinate.get(itemId)
        isItemAdded = False
        for item in self.itemList:
            if item[0] == 0:
                item[0] = itemId
                item[1] = 0
            if item[0] == itemId and item[1] <= STACK - amount:
                if itemInfos[2] == 1:
                    item[1] += amount
                    self.updateSelector(self.index)
                    isItemAdded = True
                    break
                elif item[1] == 0:
                    item[1] = 1
                    print("dura")
                    self.updateSelector(self.index)
                    isItemAdded = True
                    break

        if not isItemAdded:
            hasStacked = False
            if itemInfos[2] == 1:
                for floatItem in self.game.floatingItems:
                    distance = math.hypot(floatItem.pos.x  - self.game.player.pos.x, floatItem.pos.y - self.game.player.pos.y)
                    if distance <= MELEEREACH and itemId == floatItem.item[0]:
                        if floatItem.item[1] <= STACK - amount:
                            floatItem.item[1] += amount
                            hasStacked = True
                            break

            if not hasStacked:
                FloatingItem(self.game, self.game.player.pos.x, self.game.player.pos.y, [itemId, amount])

        else:
            self.game.hasPlayerStateChanged = True #autorise la sauvegarde du joueur

    def substractItem(self, currentItem):
        if currentItem[1] <= 1:
            currentItem[0] = 0
            currentItem[1] = 0
        else:
            currentItem[1] -= 1

        self.updateSelector(self.index)

        self.game.hasPlayerStateChanged = True #autorise la sauvegarde du joueur

    def getCurrentSelectedItem(self):
        itemInfos = self.game.itemTextureCoordinate.get(self.itemList[self.index][0])
        if itemInfos != None:
            return itemInfos
        else:
            return [0, 0, 0, 0, 'none']