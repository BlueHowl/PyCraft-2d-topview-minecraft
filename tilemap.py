import pygame as pg
from settings import *
import json

class Map:
    def __init__(self, directoryname):
        self.levelSignData = {} #définition de la liste levelSignData vide
        with open(directoryname + '/signs.txt', 'rt') as f: #ouverture du document signs.txt en lecture
            for line in f: #pour chaque lignes dans le document
                l = line.strip().split(':') #création d'une liste à partir de la ligne
                #self.levelSignData.append(l) #ajout de la liste temporaire à la liste levelSignData

        self.MobsData = {} #définition de la liste MobsData vide
        with open(directoryname + '/mobs.txt', 'rt') as f: #ouverture du document mobs.txt en lecture
            for line in f: #pour chaque lignes dans le document
                l = line.strip().split(':') #création d'une liste à partir de la ligne
                #self.MobsData.append(l) #ajout de la liste temporaire à la liste MobsData

        self.floatingItemsData = [] #définition de la liste floatingItemsData vide
        with open(directoryname + '/floatingItems.txt', 'rt') as f: #ouverture du document floatingItems.txt en lecture
            self.floatingItemsData = json.loads(f.read()) #ajout de la liste temporaire à la liste floatingItemsData

        self.chestsData = {} #définition de la liste floatingItemsData vide
        with open(directoryname + '/chests.txt', 'rt') as f: #ouverture du document chests.txt en lecture
            self.chestsData = json.loads(f.read()) #ajout de la liste temporaire à la liste chestsData

        self.furnacesData = {} #définition de la liste floatingItemsData vide
        with open(directoryname + '/furnaces.txt', 'rt') as f: #ouverture du document furnaces.txt en lecture
            self.furnacesData = json.loads(f.read()) #ajout de la liste temporaire à la liste furnacesData
            for furnace in self.furnacesData.values():
                furnace[3] = 0 #remise 0 timers furnaces

        self.levelSavedData = [] #définition de la liste levelSavedData vide
        with open(directoryname + '/level.save', 'rt') as f: #ouverture du document level.save en lecture
            for line in f: #pour chaque lignes dans le document
                self.levelSavedData.append(line.strip()) #ajout de la ligne dans la liste

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
