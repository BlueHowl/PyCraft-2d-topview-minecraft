from game.config.settings import *
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
