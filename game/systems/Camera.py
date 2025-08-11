import pygame as pg
from game.config.settings import *

class Camera:
    def __init__(self, width, height):
        self.camera = pg.Rect(0, 0, width, height) #définition de la variable camera
        self.width = width #définition de la variable width
        self.height = height #définition de la variable height
        self.topleft = (0, 0) #définition de la topleft (coordonnées de la camera)
        self.clickTopleft = (0, 0)

    def apply(self, entity):
        return entity.rect.move(self.camera.topleft) #application du déplacement de la camera
    
    def update(self, target):
        x = -target.x + int(WIDTH / 2) #calcul du x de la camera par rapport à celui du joueur
        y = -target.y + int(HEIGHT / 2) #calcul du y de la camera par rapport à celui du joueur
        self.topleft = (x, y)#(abs(x), abs(y)) #calcul des nouvelles coordonnées de la camera

        self.camera = pg.Rect(x, y, self.width, self.height) #déplacement de la camera
        '''
        x = min(0, x) #limite gauche
        y = min(0, y) #limite haut
        x = max(-(self.width - WIDTH), x) #limite droite
        y = max(-(self.height - HEIGHT), y) #limite bas
        '''

        x = target.x - int(WIDTH / 2) #calcul du x de la camera par rapport à celui du joueur
        y = target.y - int(HEIGHT / 2) #calcul du y de la camera par rapport à celui du joueur
        self.clickTopleft = (x, y)#(abs(x), abs(y)) #calcul des nouvelles coordonnées de la camera
    
    def getCamTopLeft(self):
        return self.topleft #renvoie des coordonnées de la camera

    def getCamClickTopLeft(self):
        return self.clickTopleft #renvoie des coordonnées de la camera
