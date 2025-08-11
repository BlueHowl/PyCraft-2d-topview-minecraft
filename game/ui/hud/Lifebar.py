import pygame as pg

class Lifebar(pg.sprite.Sprite):
    def __init__(self, game, xOffset, yOffset, health):
        self.groups = game.gui #game.all_sprites, game.gui #définitions de la liste de groupes de textures
        pg.sprite.Sprite.__init__(self, self.groups) #définitions du joueur dans les groupes de textures
        self.game = game
        self.xOffset = xOffset
        self.yOffset = yOffset
        self.x = xOffset #définition de la variable x
        self.y = yOffset #définition de la variable y
        self.maxHealth = int(self.game.map.levelSavedData[0].split(':')[4])

        self.healthMatrice = [] #définition d'une matrice de coeurs
        self.updateHealth(health)

        self.image = pg.Surface((len(self.healthMatrice[0]) * 16, len(self.healthMatrice) * 16), pg.SRCALPHA, 32) #création d'une surface transparente

        self.rect = self.image.get_rect() #assignation de la variable rect
        self.rect.x = self.x #application de la position x de la surface
        self.rect.y = self.y #application de la position y de la surface

        self.updateSurface()

    def updateHealth(self, hp):
        self.healthMatrice = []
        lst = [] #définition d'une liste de coeurs
        #création de la liste de coeur en fonction du nbr health
        i = 0

        while i < self.maxHealth:
            if i % 2 == 0 and i < hp - 1:
                lst.append(2)
            elif hp % 2 != 0 and i == hp-2:
                lst.append(1)
            elif i % 2 == 0 and i >= hp:
                lst.append(0)
            i += 1

        #création de la matrice de coeur grâce à la lst
        i = 0
        for x in range(len(lst)):
            if x % 10 == 0 and x != 0:
                self.healthMatrice.append(lst[x-10:x])
                i += 1
        if len(lst) < 10:
            self.healthMatrice.append(lst)
        elif len(lst) > i * 10:
            self.healthMatrice.append(lst[i*10:])

    def updateSurface(self):
        self.image = pg.Surface((len(self.healthMatrice[0]) * 16, len(self.healthMatrice) * 16), pg.SRCALPHA, 32) #création d'une surface transparente
        for row, tiles in enumerate(self.healthMatrice): #pour chaque lignes de la matrice healthMatrice
            for col, tile in enumerate(tiles): #pour chaque infos de la liste
                self.image.blit(self.game.hearts_img.subsurface((int(tile)*16, 0*16, 16, 16)), [col*16,row*16])
