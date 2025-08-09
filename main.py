import pygame as pg
import sys
import threading
import json
from os import path
from random import *
#from settings import *
from sprites import *
from tilemap import *
from chunk_manager import *


class Game:  # classe principale Game
    def __init__(self):  # constructeur de la classe Game
        pg.init()  # initialisation de pygame
        pg.font.init()  # initialisation du module de gestion de polices d'écriture de pygame
        pg.mixer.init()  # initialisation du mixer audio pygame
        # limite les evenements (optimisation)
        pg.event.set_allowed(
            [pg.QUIT, pg.KEYDOWN, pg.KEYUP, pg.MOUSEBUTTONDOWN])
        # pg.FULLSCREEN | pg.HWSURFACE| pg.DOUBLEBUF) #définition de la taille de l'écran
        self.screen = pg.display.set_mode((WIDTH, HEIGHT))
        # self.screen = pg.display.set_mode((WIDTH, HEIGHT), pg.FULLSCREEN)
        pg.display.set_caption(TITLE)  # initialisation du titre
        self.clock = pg.time.Clock()  # définition de la variable clock
        # permet de repeter l'action d'une touche toute les 100ms aprés l'avoir enfoncée 500ms
        pg.key.set_repeat(500, 100)
        self.playing = True  # définition de la variable playing à true
        self.load_data()  # appel la fonction load_data
        # self.writeMode = False #définition de la variable writeMode à false
        # self.writeTile = False #définition de la variable writeTile à false
        self.isGamePaused = False
        self.topleftCam = (0, 0)  # définition du tuple topleftCam à (0, 0)
        self.now = 0
        self.mousePos = pg.mouse.get_pos()
        self.isTabPressed = False
        self.isEPressed = False
        self.isPowerPressed = False
        self.isInventoryOpened = False

        self.hitboxDebug = False

        self.input_commands_txt = InputBox(
            self, 20, HEIGHT - 60, 600, 40, limit=999)
        self.input_commands = False
        # self.layer1Str = ''
        # self.pathfindingStr = ''
        self.hasPlayerStateChanged = False
        self.last_save = 0
        self.isSaving = False

        self.lastChestId = ""  # json format --> ""
        self.lastFurnaceId = ""  # json format --> ""
        # pg.mouse.set_visible(False) #rend la souris invisible
        pg.mouse.set_visible(True)  # rend la souris invisible
        # définition du tuple selectedTileToWritePos à (0, 0)
        self.selectedTileToWritePos = (0, 0)

        # self.loaded_tiles = []
        self.area = []

        self.worldName = ''

        self.global_time = 0
        self.day_time = 0
        self.last_day_time = 0
        self.night_shade = 255
        self.isNight = False

        self.hostile_mobs_amount = 0
        self.friendly_mobs_amount = 0

        self.respawn_rect = (0, 0, 0, 0)

        # création des différents groupes de textures
        self.all_sprites = pg.sprite.Group()
        self.moving_sprites = pg.sprite.Group()
        self.player_collisions = pg.sprite.Group()

        self.grounds = pg.sprite.Group()
        self.floatingItems = pg.sprite.Group()
        self.players = pg.sprite.Group()
        self.mobs = pg.sprite.Group()
        self.Layer1 = pg.sprite.Group()
        self.projectiles = pg.sprite.Group()
        self.gui = pg.sprite.Group()

    def load_data(self):
        # définition du chemin d'acces
        self.game_folder = path.dirname(__file__)

        # try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        # self.game_folder = sys._MEIPASS
        # except Exception:
        # self.game_folder = path.abspath(".")

        # définition de la police d'écriture en 64
        self.font_64 = pg.font.Font(
            path.join(self.game_folder, 'Pixellari.ttf'), 64)
        # définition de la police d'écriture en 32
        self.font_32 = pg.font.Font(
            path.join(self.game_folder, 'Pixellari.ttf'), 32)
        # définition de la police d'écriture en 16
        self.font_16 = pg.font.Font(
            path.join(self.game_folder, 'Pixellari.ttf'), 16)
        # définition de la police d'écriture en 10
        self.font_10 = pg.font.Font(
            path.join(self.game_folder, 'Pixellari.ttf'), 10)

        self.mobList = []  # définition de la liste mobList vide
        # ouverture du document mobTextures.list en lecture
        with open(path.join(self.game_folder, 'data/mobs.list'), 'rt') as f:
            for line in f:  # pour chaque lignes dans le document
                l = line.strip().split('|')
                item = l[2].split(',')
                self.mobList.append((pg.image.load(path.join(self.game_folder, l[1])).convert_alpha(), (int(item[0]), int(item[1])), int(
                    l[3]), int(l[4]), int(l[5]), int(l[6]), l[0]))  # ajout de la texture convertie en alpha dans la liste mobList

        self.itemTextureCoordinate = {}  # définition de la liste itemTextureCoordinate vide
        # ouverture du document item.list en lecture
        with open(path.join(self.game_folder, 'data/item.list'), 'rt') as f:
            for line in f:  # pour chaque lignes dans le document
                l = line.strip().split(':')  # création d'une liste à partir de la ligne
                self.itemTextureCoordinate[int(l[0])] = (int(l[1]), int(l[2]), int(
                    l[3]), int(l[4]), l[5])  # ajout des infos d'une texture dans la liste

        self.audioList = {}  # définition de la liste audioList vide
        # ouverture du document audio.list en lecture
        with open(path.join(self.game_folder, 'data/audio.list'), 'rt') as f:
            for line in f:  # pour chaque lignes dans le document
                l = line.strip().split(':')  # création d'une liste à partir de la ligne
                # ajout des infos d'une texture dans la liste
                self.audioList[l[0]] = pg.mixer.Sound(
                    path.join(self.game_folder, l[1]))

        self.menuData = []  # définition de la liste menuData vide
        # ouverture du document menu.map en lecture
        with open(path.join(self.game_folder, 'data/ui_maps/menu.map'), 'rt') as f:
            for line in f:  # pour chaque lignes dans le document
                # ajout de la ligne dans la liste
                self.menuData.append(line.strip())

        self.inventoryMap = []  # définition de la liste inventoryMap vide
        # ouverture du document inventory.map en lecture
        with open(path.join(self.game_folder, 'data/ui_maps/inventory.map'), 'rt') as f:
            for line in f:  # pour chaque lignes dans le document
                # ajout de la ligne dans la liste
                self.inventoryMap.append(line.strip())

        self.furnaceUiMap = []  # définition de la liste furnaceUiMap vide
        # ouverture du document furnaceUi.map en lecture
        with open(path.join(self.game_folder, 'data/ui_maps/furnaceUi.map'), 'rt') as f:
            for line in f:  # pour chaque lignes dans le document
                # ajout de la ligne dans la liste
                self.furnaceUiMap.append(line.strip())

        self.chestUiMap = []  # définition de la liste chestUiMap vide
        # ouverture du document furnaceUi.map en lecture
        with open(path.join(self.game_folder, 'data/ui_maps/chestUi.map'), 'rt') as f:
            for line in f:  # pour chaque lignes dans le document
                # ajout de la ligne dans la liste
                self.chestUiMap.append(line.strip())

        self.craftList = []  # définition de la liste craftList vide
        # ouverture du document craft.list en lecture
        with open(path.join(self.game_folder, 'data/craft.list'), 'rt') as f:
            for line in f:  # pour chaque lignes dans le document
                l = line.strip().split('|')
                self.craftList.append(l)  # ajout de la ligne dans la liste
        self.itemAssignementList = {}  # définition de la liste itemAssignementList vide
        # ouverture du document itemAssignement.list en lecture
        with open(path.join(self.game_folder, 'data/item_assignement.list'), 'rt') as f:
            for line in f:  # pour chaque lignes dans le document
                l = line.strip().split(':')
                # ajout de la ligne dans la liste
                self.itemAssignementList[int(l[0])] = l[1:]

        self.furnaceFuelList = {}  # définition de la liste itemAssignementList vide
        # ouverture du document furnace_fuels.list en lecture
        with open(path.join(self.game_folder, 'data/furnace_fuels.list'), 'rt') as f:
            for line in f:  # pour chaque lignes dans le document
                l = line.strip().split(':')
                # ajout de la ligne dans la liste
                self.furnaceFuelList[int(l[0])] = l[1:]

        self.textureCoordinate = {}  # définition de la liste textureCoordinate vide
        # ouverture du document texCoords.txt en lecture
        with open(path.join(self.game_folder, 'data/texCoords.txt'), 'rt') as f:
            self.textureCoordinate = json.loads(f.read())

        self.tileImage = []
        # chargement du fichier de texture du jeu
        self.tileImage.append(pg.image.load(
            path.join(self.game_folder, 'textures/map/natureTileset.png')).convert_alpha())
        # chargement du fichier de texture du jeu
        self.tileImage.append(pg.image.load(
            path.join(self.game_folder, 'textures/map/IceTileset.png')).convert_alpha())

        # chargement du fichier de texture du joueur
        self.palyer_sprite = pg.image.load(
            path.join(self.game_folder, 'textures/' + PLAYER_SPRITE)).convert_alpha()
        pg.display.set_icon(self.palyer_sprite.subsurface(
            (0*TILESIZE, 0*TILESIZE, TILESIZE, TILESIZE)))  # initialisation de l'icone

        # chargement du fichier de texture des coeurs
        self.hearts_img = pg.image.load(
            path.join(self.game_folder, 'textures/gui/hearts.png')).convert_alpha()
        # chargement du fichier de texture de la hotbar
        self.hotbar_img = pg.image.load(
            path.join(self.game_folder, 'textures/gui/hotbar.png')).convert_alpha()
        # chargement du fichier de texture des menus
        self.menu_img = pg.image.load(
            path.join(self.game_folder, 'textures/gui/menu.png')).convert_alpha()
        # chargement du fichier de texture des items
        self.items_img = pg.image.load(
            path.join(self.game_folder, 'textures/items.png')).convert_alpha()
        # chargement du fichier de texture du crosshair
        self.crosshair_img = pg.image.load(
            path.join(self.game_folder, 'textures/crosshair.png')).convert_alpha()
        # chargement du fichier de texture de la lumière
        self.light = pg.transform.scale(pg.image.load(path.join(
            self.game_folder, 'textures/light_.png')).convert_alpha(), (550, 550))

    def new(self):
        pg.mouse.set_visible(False)  # rend la souris invisible

        # création d'une nouvelle instance de la classe Map
        self.map = Map(path.join(self.game_folder, 'saves/' + self.worldName))

        self.pathfind = [vec(0, 0), [[1] * (CHUNKRENDERX * 2 + 2) * CHUNKSIZE] * (
            CHUNKRENDERY * 2 + 2) * CHUNKSIZE]  # création de la matrice de pathfinding

        self.chunkmanager = Chunk(path.join(
            self.game_folder, 'saves/' + self.worldName), int(self.map.levelSavedData[2]))

        playerState = self.map.levelSavedData[0].split(':')
        self.player = Player(self, int(playerState[0]), int(playerState[1]), int(
            playerState[2]))  # création d'une nouvelle instance de joueur

        spawn = self.map.levelSavedData[3].split(':')
        self.spawnPoint = vec(int(spawn[0]), int(spawn[1]))

        self.global_time = int(self.map.levelSavedData[4])

        self.night_shade = int(self.map.levelSavedData[5])

        self.camera = Camera(WIDTH, HEIGHT)

        for item in self.map.floatingItemsData:
            FloatingItem(self, item[0], item[1], item[2])

    def run(self):
        # game loop - set self.playing = False to end the game
        while self.playing:  # tant que playing == true
            # définition de la variable dt(delta time)
            self.dt = self.clock.tick(FPS) / 1000
            self.events()  # appel de la fonction events
            self.update()  # appel de la fonction update
            self.draw()  # appel de la fonction draw

    def quit(self):
        pg.quit()  # quitte le module pygame
        sys.exit()  # quitte le module system
        # pass

    def update(self):
        self.now = pg.time.get_ticks()  # définition de la variable now
        self.mousePos = pg.mouse.get_pos()

        if self.now >= self.last_save + SAVE_DELAY:
            if self.hasPlayerStateChanged:
                self.save()
                self.last_save = self.now

        if not self.isGamePaused:  # si isGamePaused == False
            self.reload_chunks()
            self.moving_sprites.update()  # mise à jour du groupe de sprite non statiques
            # appel de la fonction update de la classe Camera
            self.camera.update(self.player.pos)
            self.dayNigthCycle()

            x = randint((self.player.chunkpos.x - CHUNKRENDERX - 1) * CHUNKSIZE,
                        (self.player.chunkpos.x + CHUNKRENDERX + 1) * CHUNKSIZE)
            y = randint((self.player.chunkpos.y - CHUNKRENDERY - 1) * CHUNKSIZE,
                        (self.player.chunkpos.y + CHUNKRENDERY + 1) * CHUNKSIZE)

            if x < (self.player.chunkpos.x - CHUNKRENDERX + 2) * CHUNKSIZE or x > (self.player.chunkpos.x + CHUNKRENDERX - 2) * CHUNKSIZE and y < (self.player.chunkpos.y - CHUNKRENDERY + 1) * CHUNKSIZE or y > (self.player.chunkpos.y + CHUNKRENDERY - 1) * CHUNKSIZE:
                tile = self.getTile(vec(x * TILESIZE, y * TILESIZE), False)
                if tile[0] == '0' and tile != '00':
                    if self.isNight:
                        if self.hostile_mobs_amount < MAX_HOSTILE_MOBS:
                            canSpawn = True
                            for ground in self.grounds:
                                if ground.name == 'torch_block':
                                    distance = math.hypot(
                                        ground.x * TILESIZE - x * TILESIZE, ground.y * TILESIZE - y * TILESIZE)
                                    if distance <= 5 * TILESIZE:
                                        canSpawn = False
                                        break
                            if canSpawn:
                                mobId = randint(3, 5)
                                Mob(self, x, y, mobId)
                    else:
                        if self.friendly_mobs_amount < MAX_FRIENDLY_MOBS:
                            mobId = randint(0, 2)
                            Mob(self, x, y, mobId)

        if self.isInventoryOpened:
            self.player.inventory.hover(self.mousePos)

        if self.input_commands:
            self.input_commands_txt.update()

    # Load the sprites from the chunk given by the ChunkManager loader
    def load_chunk(self, data):
        if data != None:
            # parse the data
            for i in data:
                self.load_tile(i)

    def load_tile(self, i):
        tiles = i[0]
        x = i[1]
        y = i[2]
        # self.loaded_tiles.append(i)
        for tile in reversed(tiles):
            # récupération des coordonées de la sous texture ainsi que son nom grâce à l'id
            infos = self.textureCoordinate.get(tile)
            if infos != None:  # si la variable infos n'est pas vide
                if tile[0] == '0':
                    if tile == '00':
                        if self.getTile(vec((x - 1) * TILESIZE, y * TILESIZE), True) == '01' and self.getTile(vec(x * TILESIZE, (y - 1) * TILESIZE), True) == '01':
                            infos = self.textureCoordinate.get('09a')
                        elif self.getTile(vec((x - 1) * TILESIZE, y * TILESIZE), True) == '01' and self.getTile(vec(x * TILESIZE, (y + 1) * TILESIZE), True) == '01':
                            infos = self.textureCoordinate.get('00b')
                        elif self.getTile(vec((x + 1) * TILESIZE, y * TILESIZE), True) == '01' and self.getTile(vec(x * TILESIZE, (y + 1) * TILESIZE), True) == '01':
                            infos = self.textureCoordinate.get('0c')
                        elif self.getTile(vec((x + 1) * TILESIZE, y * TILESIZE), True) == '01' and self.getTile(vec(x * TILESIZE, (y - 1) * TILESIZE), True) == '01':
                            infos = self.textureCoordinate.get('00a')

                        elif self.getTile(vec((x + 1) * TILESIZE, y * TILESIZE), True) == '01':
                            infos = self.textureCoordinate.get('02a')
                        elif self.getTile(vec((x - 1) * TILESIZE, y * TILESIZE), True) == '01':
                            infos = self.textureCoordinate.get('04a')
                        elif self.getTile(vec(x * TILESIZE, (y + 1) * TILESIZE), True) == '01':
                            infos = self.textureCoordinate.get('01a')
                        elif self.getTile(vec(x * TILESIZE, (y - 1) * TILESIZE), True) == '01':
                            infos = self.textureCoordinate.get('03a')

                        elif self.getTile(vec((x - 1) * TILESIZE, (y - 1) * TILESIZE), True) == '01':
                            infos = self.textureCoordinate.get('08a')
                        elif self.getTile(vec((x + 1) * TILESIZE, (y + 1) * TILESIZE), True) == '01':
                            infos = self.textureCoordinate.get('05a')
                        elif self.getTile(vec((x + 1) * TILESIZE, (y - 1) * TILESIZE), True) == '01':
                            infos = self.textureCoordinate.get('07a')
                        elif self.getTile(vec((x - 1) * TILESIZE, (y + 1) * TILESIZE), True) == '01':
                            infos = self.textureCoordinate.get('06a')

                    Ground(self, x, y, self.tileImage[infos[0]].subsurface(
                        (infos[2]*TILESIZE, infos[3]*TILESIZE, TILESIZE, TILESIZE)), infos[5], infos[7])  # nouvelle instance de la classe Ground
                elif tile[0] == '1':
                    Layer1_objs(self, x, y, self.tileImage[infos[0]].subsurface(
                        (infos[2]*TILESIZE, infos[3]*TILESIZE, TILESIZE, TILESIZE)), infos[5], infos[7])  # nouvelle instance de la classe layer1_objs

                if infos[1] == 1 and '025' not in tiles and '026' not in tiles:
                    break

    def reload_chunks(self):
        # Define render area
        px = self.player.chunkpos.x
        py = self.player.chunkpos.y
        self.area = []

        for y in range(-CHUNKRENDERY - 1, CHUNKRENDERY + 1):
            for x in range(-CHUNKRENDERX - 1, CHUNKRENDERX + 1):
                cx = int(px + x)
                cy = int(py + y)
                cname = str(cx) + ',' + str(cy)
                self.area.append(cname)
                if cname not in self.chunkmanager.get_chunks():
                    self.chunkmanager.generate(cx, cy)
                self.load_chunk(self.chunkmanager.load(cx, cy))

        for cname in self.chunkmanager.get_chunks():
            chunk = cname.split(',')
            chunk = (int(chunk[0]), int(chunk[1]))
            if cname not in self.area and cname in self.chunkmanager.get_loaded():
                for sprite in self.all_sprites:
                    if sprite != self.player and sprite not in self.floatingItems:
                        if sprite.chunkpos == chunk:
                            if sprite in self.mobs:
                                if sprite.isEnemy == 1:
                                    self.hostile_mobs_amount -= 1
                                else:
                                    self.friendly_mobs_amount -= 1
                            sprite.kill()
                self.chunkmanager.unload(cname)

    def getCurrentPathfind(self):
        offset = vec(self.player.chunkpos.x - CHUNKRENDERX - 1,
                     self.player.chunkpos.y - CHUNKRENDERY - 1) * CHUNKSIZE

        tempPathfinding = []
        for y in range((CHUNKRENDERY * 2 + 2) * CHUNKSIZE):
            tempLst = []
            for x in range((CHUNKRENDERX * 2 + 2) * CHUNKSIZE):
                name = self.area[((y // CHUNKSIZE) *
                                  (CHUNKRENDERX * 2 + 2)) + (x // CHUNKSIZE)]
                cInfos = self.chunkmanager.get_chunks().get(name)

                if cInfos:
                    cell = cInfos[y % CHUNKSIZE][x % CHUNKSIZE]
                    if len(cell) > 1 or cell[0] == '00':
                        tempLst.append(0)
                    else:
                        tempLst.append(1)

            tempPathfinding.append(tempLst)

        return [offset, tempPathfinding]

    def getTile(self, pos, getGround):
        tilePos = vec(pos.x, pos.y) // TILESIZE
        insideX = int(tilePos.x - ((tilePos.x // CHUNKSIZE) * CHUNKSIZE))
        insideY = int(tilePos.y - ((tilePos.y // CHUNKSIZE) * CHUNKSIZE))

        # si prblm essayer math.floor ou round à la place de int
        cname = str(int(tilePos.x // CHUNKSIZE)) + ',' + \
            str(int(tilePos.y // CHUNKSIZE))
        cInfos = self.chunkmanager.get_chunks().get(cname)
        if cInfos:
            cell = cInfos[insideY][insideX]
            if cell:
                if '025' in cell:
                    return '025'
                elif '026' in cell:
                    return '026'
                elif getGround:
                    return cell[0]
                else:
                    return cell[-1]

        return '.'

    def changeTile(self, pos, tile, toRemove):
        tilePos = vec(pos.x, pos.y) // TILESIZE
        insideX = int(tilePos.x - ((tilePos.x // CHUNKSIZE) * CHUNKSIZE))
        insideY = int(tilePos.y - ((tilePos.y // CHUNKSIZE) * CHUNKSIZE))

        # si prblm essayer math.floor ou round à la place de int
        cname = str(int(tilePos.x // CHUNKSIZE)) + ',' + \
            str(int(tilePos.y // CHUNKSIZE))
        cInfos = self.chunkmanager.get_chunks().get(cname)
        if cInfos:
            if toRemove:
                if tile in cInfos[insideY][insideX]:
                    cInfos[insideY][insideX].remove(tile)
            else:
                if tile == '025' or tile == '026':
                    cInfos[insideY][insideX].insert(0, tile)
                else:
                    cInfos[insideY][insideX].append(tile)

            self.load_tile([cInfos[insideY][insideX],
                           int(tilePos.x), int(tilePos.y)])

            self.chunkmanager.unsaved += 1

    def giveItem(self, itemId, quantity):
        rest = quantity % STACK
        stack_Number = (quantity - rest) // STACK

        if quantity < 64:
            self.player.hotbar.addItem(itemId, quantity)
        else:
            for i in range(stack_Number):
                self.player.hotbar.addItem(itemId, STACK)
            if rest != 0:
                self.player.hotbar.addItem(itemId, rest)

        pg.mixer.Sound.play(self.audioList.get(
            'drop_item'))  # joue le son préchargée

    def dayNigthCycle(self):
        self.global_time = round(self.global_time + self.dt * 1000)
        # print(self.global_time)
        self.day_time = (self.global_time % DAY_LENGTH)
        if self.day_time > DAY_LENGTH - (DAY_LENGTH // 3) and self.day_time < DAY_LENGTH:
            self.isNight = True
            if self.day_time > self.last_day_time + SHADE_SPEED:
                if self.night_shade > MIN_NIGHT_SHADE:
                    self.night_shade -= 1
                    self.last_day_time = self.day_time
                else:
                    self.last_day_time = 0
        else:
            self.isNight = False
            if self.day_time > self.last_day_time + SHADE_SPEED:
                if self.night_shade < 255:
                    self.night_shade += 1
                    self.last_day_time = self.day_time
                else:
                    self.last_day_time = 0

    def skipNight(self):  # fonction passage de la nuit
        # ajout du temps restant pour completer le cycle jour/nuit
        self.global_time += DAY_LENGTH - self.day_time
        self.night_shade = 255  # remise à 0(255) de l'écran de nuit

    def sleep(self):  # fonction dormir
        if self.isNight:  # si c'est la nuit
            # remise de la position du joueur sur celle du spawnpoint(lit)
            self.player.pos = self.spawnPoint * TILESIZE
            self.skipNight()  # appel de la fonction "passer la nuit"

            # remise à 100% de la vie du joueur
            self.player.health = self.player.lifebar.maxHealth
            self.player.lifebar.updateHealth(self.player.health)
            self.player.lifebar.updateSurface()

    def draw(self):
        self.screen.fill(BLACK)  # affichage du sprite relatif à la camera

        if self.night_shade != 255:
            nightScreen = pg.Surface((WIDTH, HEIGHT))
            nightScreen.fill((self.night_shade, self.night_shade,
                             min(self.night_shade + 20, 255)))

        for sprite in self.grounds:  # pour chaque sprites du groupe grounds
            # affichage du sprite relatif à la camera
            self.screen.blit(sprite.image, self.camera.apply(sprite))
            if sprite.name == 'torch_block' and self.night_shade != 255:
                pos = self.camera.apply(sprite)
                nightScreen.blit(self.light, (pos.x + 16 - (self.light.get_width() / 2),
                                 pos.y + 16 - (self.light.get_height() / 2)))

        for sprite in self.Layer1:  # pour chaque sprites du groupe Layer1
            # affichage du sprite relatif à la camera
            self.screen.blit(sprite.image, self.camera.apply(sprite))

        for sprite in self.floatingItems:  # pour chaque sprites du groupe floatingItems
            # affichage du sprite relatif à la camera
            self.screen.blit(sprite.image, self.camera.apply(sprite))
            if self.hitboxDebug:
                pg.draw.rect(self.screen, WHITE, self.camera.apply(sprite),  1)

        for sprite in self.players:  # pour chaque sprites du players
            # affichage du sprite relatif à la camera
            self.screen.blit(sprite.image, self.camera.apply(sprite))
            if self.hitboxDebug:
                pg.draw.rect(self.screen, WHITE, self.camera.apply(sprite),  1)

        for sprite in self.mobs:  # pour chaque sprites du groupe mobs
            # affichage du sprite relatif à la camera
            self.screen.blit(sprite.image, self.camera.apply(sprite))
            if self.hitboxDebug:
                pg.draw.rect(self.screen, WHITE, self.camera.apply(sprite),  1)

        for sprite in self.projectiles:  # pour chaque sprites du groupe Layer1
            # affichage du sprite relatif à la camera
            self.screen.blit(sprite.image, self.camera.apply(sprite))
            if self.hitboxDebug:
                pg.draw.rect(self.screen, WHITE, self.camera.apply(sprite),  1)

        if self.night_shade != 255:
            self.screen.blit(nightScreen, (0, 0), special_flags=pg.BLEND_MULT)

        if not self.isInventoryOpened and not self.input_commands:
            # currentItem = self.player.hotbar.itemList[self.player.hotbar.index]
            itemCursor = self.player.hotbar.getCurrentSelectedItem()[3]

            if itemCursor == 1:
                self.screen.blit(self.crosshair_img.subsurface(0*TILESIZE, 0*TILESIZE, TILESIZE,
                                 TILESIZE), (self.mousePos[0] - 16, self.mousePos[1] - 16))  # bow aim crosshair
            elif itemCursor == 2:
                self.screen.blit(self.crosshair_img.subsurface(1*TILESIZE, 0*TILESIZE, TILESIZE, TILESIZE),
                                 (self.mousePos[0] - 16, self.mousePos[1] - 16))  # place block crosshair
            elif itemCursor == 3:
                self.screen.blit(self.crosshair_img.subsurface(2*TILESIZE, 0*TILESIZE, TILESIZE,
                                 TILESIZE), (self.mousePos[0] - 16, self.mousePos[1] - 16))  # melee crosshair
            else:
                self.screen.blit(self.crosshair_img.subsurface(0*TILESIZE, 1*TILESIZE, TILESIZE,
                                 TILESIZE), (self.mousePos[0] - 16, self.mousePos[1] - 16))  # point crosshaird

        # afficher le gui au 1er plan
        for sprite in self.gui:  # pour chaque sprites dans tout le niveau
            self.screen.blit(sprite.image, sprite.rect)  # affichage du sprite

        if self.input_commands:
            self.input_commands_txt.draw(self.screen)
            debug_surface = pg.Surface((200, 160), pg.SRCALPHA)
            debug_surface.fill((255, 255, 255, 128))

            debug_surface.blit(self.font_16.render(
                f'Fps : {round(self.clock.get_fps())}/{FPS}', False, BLACK), (10, 10))
            debug_surface.blit(self.font_16.render(
                f'X : {round(self.player.pos.x / TILESIZE, 6)}, Y : {round(self.player.pos.y / TILESIZE, 6)}', False, BLACK), (10, 30))

            insideX = int(self.player.tilepos.x -
                          ((self.player.tilepos.x // CHUNKSIZE) * CHUNKSIZE))
            insideY = int(self.player.tilepos.y -
                          ((self.player.tilepos.y // CHUNKSIZE) * CHUNKSIZE))
            debug_surface.blit(self.font_16.render(
                f'Chunk : {insideX}:{insideY} in {round(self.player.chunkpos.x)}:{round(self.player.chunkpos.y)}', False, BLACK), (10, 50))

            if self.player.lastWalkStatement == 0:
                debug_surface.blit(self.font_16.render(
                    f'Facing : {self.player.lastWalkStatement}, North', False, BLACK), (10, 70))
            elif self.player.lastWalkStatement == 1:
                debug_surface.blit(self.font_16.render(
                    f'Facing : {self.player.lastWalkStatement}, South', False, BLACK), (10, 70))
            elif self.player.lastWalkStatement == 2:
                debug_surface.blit(self.font_16.render(
                    f'Facing : {self.player.lastWalkStatement}, West', False, BLACK), (10, 70))
            elif self.player.lastWalkStatement == 3:
                debug_surface.blit(self.font_16.render(
                    f'Facing : {self.player.lastWalkStatement}, East', False, BLACK), (10, 70))

            hour = self.day_time * 96 // 3600000
            minutes = (self.day_time * 96 // 60000) % 60
            if self.isNight:
                debug_surface.blit(self.font_16.render(
                    f'Day : {self.global_time // DAY_LENGTH}, {hour if len(str(hour)) > 1 else "0" + str(hour)}:{minutes if len(str(minutes)) > 1 else "0" + str(minutes)} Night', False, BLACK), (10, 90))
            else:
                debug_surface.blit(self.font_16.render(
                    f'Day : {self.global_time // DAY_LENGTH}, {hour if len(str(hour)) > 1 else "0" + str(hour)}:{minutes if len(str(minutes)) > 1 else "0" + str(minutes)} Day', False, BLACK), (10, 90))

            debug_surface.blit(self.font_16.render(
                f'Cursor : {round((self.camera.getCamClickTopLeft()[0] + self.mousePos[0]) / TILESIZE, 2)} : {round((self.camera.getCamClickTopLeft()[1] + self.mousePos[1]) / TILESIZE, 2)}', False, BLACK), (10, 110))

            debug_surface.blit(self.font_16.render(
                f'Mobs : F {self.friendly_mobs_amount}/{MAX_FRIENDLY_MOBS}, H {self.hostile_mobs_amount}/{MAX_HOSTILE_MOBS}', False, BLACK), (10, 130))

            self.screen.blit(debug_surface, (0, 0))

        if self.isSaving:
            self.screen.blit(self.menu_img.subsurface(
                0*TILESIZE, 4*TILESIZE, TILESIZE, TILESIZE), [WIDTH - 36, 4])

        if self.player.dead:
            respawn_surface = pg.Surface((WIDTH, HEIGHT), pg.SRCALPHA)
            respawn_surface.fill((0, 0, 0, 128))

            title = self.font_64.render('You Died', False, WHITE)
            respawn_surface.blit(
                title, ((WIDTH / 2) - (title.get_width() / 2) - 8, 50))

            respawnTxt = self.font_32.render('Respawn', False, WHITE)
            respawn_surface.blit(respawnTxt, ((
                WIDTH / 2) - (respawnTxt.get_width() / 2), (HEIGHT / 2) - (respawnTxt.get_height() / 2)))
            self.respawn_rect = (((WIDTH / 2) - (respawnTxt.get_width() / 2) - 5, (HEIGHT / 2) - (
                respawnTxt.get_height() / 2) - 5, respawnTxt.get_width() + 10, respawnTxt.get_height() + 5))
            pg.draw.rect(respawn_surface, WHITE, self.respawn_rect, 2)

            self.screen.blit(respawn_surface, (0, 0))

        pg.display.flip()  # met à jour l'écran
        # pg.display.update(self.screen.get_rect())

    def events(self):
        for event in pg.event.get():  # pour chaque evenements detecté (clavier souris)
            if event.type == pg.QUIT:  # si l'evenement correspond à QUIT
                self.quit()  # appel la fonction quit

            if event.type == pg.KEYDOWN:  # si l'evenement correspond à une touche pressée
                if event.key == pg.K_ESCAPE:  # si la touche correspond à escape
                    if self.input_commands:
                        self.input_commands = False
                        self.isGamePaused = False
                        self.input_commands_txt.active = False
                        self.input_commands_txt.color = BLACK
                        pg.mouse.set_visible(False)
                    elif self.isInventoryOpened:
                        if self.player.inventory.craftPage == 9:
                            self.map.furnacesData.get(self.lastFurnaceId)[
                                3] = self.now
                            self.player.inventory.openedFurnace = False
                        self.isInventoryOpened = False
                        self.player.inventory.toggleGui(False, 0)
                        pg.mouse.set_visible(False)
                    else:
                        self.quit()  # appel de la fonction quit
                elif event.key == pg.K_1 and not self.isGamePaused:
                    self.player.hotbar.updateSelector(0)
                elif event.key == pg.K_2 and not self.isGamePaused:
                    self.player.hotbar.updateSelector(1)
                elif event.key == pg.K_3 and not self.isGamePaused:
                    self.player.hotbar.updateSelector(2)
                elif event.key == pg.K_4 and not self.isGamePaused:
                    self.player.hotbar.updateSelector(3)
                elif event.key == pg.K_5 and not self.isGamePaused:
                    self.player.hotbar.updateSelector(4)
                elif event.key == pg.K_6 and not self.isGamePaused:
                    self.player.hotbar.updateSelector(5)
                elif event.key == pg.K_7 and not self.isGamePaused:
                    self.player.hotbar.updateSelector(6)
                elif event.key == pg.K_8 and not self.isGamePaused:
                    self.player.hotbar.updateSelector(7)
                elif event.key == pg.K_9 and not self.isGamePaused:
                    self.player.hotbar.updateSelector(8)
                elif event.key == pg.K_a and not self.isGamePaused:

                    currentItem = self.player.hotbar.itemList[self.player.hotbar.index]
                    itemInfos = self.itemTextureCoordinate.get(currentItem[0])

                    keys = pg.key.get_pressed()

                    dropOffset = vec(
                        self.player.pos.x + uniform(-4, 4), self.player.pos.y + uniform(-4, 4))

                    if self.player.lastWalkStatement == 0:
                        dropOffset.y -= 32
                    elif self.player.lastWalkStatement == 1:
                        dropOffset.y += 32
                    elif self.player.lastWalkStatement == 2:
                        dropOffset.x -= 32
                    elif self.player.lastWalkStatement == 3:
                        dropOffset.x += 32

                    if currentItem[0] != 0:
                        if keys[pg.K_LCTRL]:
                            FloatingItem(self, dropOffset.x, dropOffset.y, [
                                         currentItem[0], currentItem[1]])

                            currentItem[0] = 0
                            currentItem[1] = 0

                            self.player.hotbar.updateSelector(
                                self.player.hotbar.index)
                            pg.mixer.Sound.play(self.audioList.get(
                                'drop_item'))  # joue le son préchargée

                            self.hasPlayerStateChanged = True  # autorise la sauvegarde du joueur
                        else:
                            hasStacked = False

                            if itemInfos[2] == 1:
                                for floatItem in self.floatingItems:
                                    distance = math.hypot(
                                        floatItem.pos.x - self.player.pos.x, floatItem.pos.y - self.player.pos.y)
                                    if distance <= MELEEREACH and currentItem[0] == floatItem.item[0]:
                                        if floatItem.item[1] < STACK:
                                            floatItem.item[1] += 1

                                            self.player.hotbar.substractItem(
                                                currentItem)
                                            pg.mixer.Sound.play(self.audioList.get(
                                                'drop_item'))  # joue le son préchargée

                                            hasStacked = True
                                            self.hasPlayerStateChanged = True  # autorise la sauvegarde du joueur
                                            break

                            if not hasStacked:
                                FloatingItem(self, dropOffset.x,
                                             dropOffset.y, [currentItem[0], 1])

                                self.player.hotbar.substractItem(currentItem)
                                pg.mixer.Sound.play(self.audioList.get(
                                    'drop_item'))  # joue le son préchargée

                # si appui sur "e" et que le personnage ne bouge pas
                elif event.key == pg.K_e and self.player.vel.x == 0 and self.player.vel.y == 0 and not self.isGamePaused and not self.isEPressed:
                    self.isEPressed = True
                    # convertissage de la position x en pixel à la position x sur la grille
                    x = int((self.player.pos.x + 16) // TILESIZE)
                    # convertissage de la position y en pixel à la position y sur la grille
                    y = int((self.player.pos.y + 16) // TILESIZE)

                    currentItem = self.player.hotbar.itemList[self.player.hotbar.index]

                    canDraw = False  # définition de la variable canDraw à False
                    txt = []  # définition de la liste txt vide

                    if currentItem[0] == 5 and self.player.health < self.player.lifebar.maxHealth:
                        self.player.hotbar.substractItem(currentItem)

                        self.player.health = self.player.lifebar.maxHealth
                        self.player.lifebar.updateHealth(self.player.health)
                        self.player.lifebar.updateSurface()

                        pg.mixer.Sound.play(self.audioList.get(
                            'heal_bonus'))  # joue le son préchargée
                    elif currentItem[0] == 9 and self.player.health < self.player.lifebar.maxHealth:
                        self.player.hotbar.substractItem(currentItem)

                        if self.player.health + 4 > self.player.lifebar.maxHealth:
                            self.player.health = self.player.lifebar.maxHealth
                        else:
                            self.player.health += 4
                        self.player.lifebar.updateHealth(self.player.health)
                        self.player.lifebar.updateSurface()

                        pg.mixer.Sound.play(self.audioList.get(
                            'heal_bonus'))  # joue le son préchargée
                    elif currentItem[0] == 6:
                        self.player.hotbar.substractItem(currentItem)

                        self.player.lifebar.maxHealth += 2
                        self.player.lifebar.updateHealth(self.player.health)
                        self.player.lifebar.updateSurface()

                        pg.mixer.Sound.play(self.audioList.get(
                            'max_health_bonus'))  # joue le son préchargée
                    else:
                        rightTile = self.getTile(
                            vec((x + 1) * 32, y * 32), False)
                        leftTile = self.getTile(
                            vec((x - 1) * 32, y * 32), False)
                        topTile = self.getTile(
                            vec(x * 32, (y + 1) * 32), False)
                        bottomTile = self.getTile(
                            vec(x * 32, (y - 1) * 32), False)

                        # si un panneau est à droite du personnage et que le personnage regarde vers le panneau
                        if rightTile != '.' and self.player.lastWalkStatement == 3:
                            if rightTile == '10':
                                canDraw = True  # définition de la variable canDraw à true
                                for l in self.map.levelSignData:  # pour chaque lignes dans levelSignData
                                    # si les coordonnées du fichier correspondent à celle de la pancarte
                                    if int(l[0]) == x + 1 and int(l[1]) == y:
                                        # définition du texte de la pancarte à la variable txt
                                        txt = l[2].split('-|-')
                            elif rightTile == '117':
                                self.isInventoryOpened = True
                                pg.mouse.set_visible(self.isInventoryOpened)
                                self.lastFurnaceId = f"{int(x + 1)}:{int(y)}"
                                self.player.inventory.toggleGui(True, 9)
                            elif rightTile == '120':
                                self.isInventoryOpened = True
                                pg.mouse.set_visible(self.isInventoryOpened)
                                self.lastChestId = f"{int(x + 1)}:{int(y)}"
                                self.player.inventory.toggleGui(True, 10)
                            elif rightTile == '026':
                                self.sleep()
                        # si un panneau est à gauche du personnage et que le personnage regarde vers le panneau
                        elif leftTile != '.' and self.player.lastWalkStatement == 2:
                            if leftTile == '10':
                                canDraw = True  # définition de la variable canDraw à true
                                for l in self.map.levelSignData:  # pour chaque lignes dans levelSignData
                                    # si les coordonnées du fichier correspondent à celle de la pancarte
                                    if int(l[0]) == x - 1 and int(l[1]) == y:
                                        # définition du texte de la pancarte à la variable txt
                                        txt = l[2].split('-|-')
                            elif leftTile == '117':
                                self.isInventoryOpened = True
                                pg.mouse.set_visible(self.isInventoryOpened)
                                self.lastFurnaceId = f"{int(x - 1)}:{int(y)}"
                                self.player.inventory.toggleGui(True, 9)
                            elif leftTile == '120':
                                self.isInventoryOpened = True
                                pg.mouse.set_visible(self.isInventoryOpened)
                                self.lastChestId = f"{int(x - 1)}:{int(y)}"
                                self.player.inventory.toggleGui(True, 10)
                            elif leftTile == '026':
                                self.sleep()
                        # si un panneau est en haut du personnage et que le personnage regarde vers le panneau
                        elif topTile != '.' and self.player.lastWalkStatement == 1:
                            if topTile == '10':
                                canDraw = True  # définition de la variable canDraw à true
                                for l in self.map.levelSignData:  # pour chaque lignes dans levelSignData
                                    # si les coordonnées du fichier correspondent à celle de la pancarte
                                    if int(l[0]) == x and int(l[1]) == y + 1:
                                        # définition du texte de la pancarte à la variable txt
                                        txt = l[2].split('-|-')
                            elif topTile == '117':
                                self.isInventoryOpened = True
                                pg.mouse.set_visible(self.isInventoryOpened)
                                self.lastFurnaceId = f"{int(x)}:{int(y + 1)}"
                                self.player.inventory.toggleGui(True, 9)
                            elif topTile == '120':
                                self.isInventoryOpened = True
                                pg.mouse.set_visible(self.isInventoryOpened)
                                self.lastChestId = f"{int(x)}:{int(y + 1)}"
                                self.player.inventory.toggleGui(True, 10)
                            elif topTile == '026':
                                self.sleep()
                        # si un panneau est en bas du personnage et que le personnage regarde vers le panneau
                        elif bottomTile != '.' and self.player.lastWalkStatement == 0:
                            if bottomTile == '10':
                                canDraw = True  # définition de la variable canDraw à true
                                for l in self.map.levelSignData:  # pour chaque lignes dans levelSignData
                                    # si les coordonnées du fichier correspondent à celle de la pancarte
                                    if int(l[0]) == x and int(l[1]) == y - 1:
                                        # définition du texte de la pancarte à la variable txt
                                        txt = l[2].split('-|-')
                            elif bottomTile == '117':
                                self.isInventoryOpened = True
                                pg.mouse.set_visible(self.isInventoryOpened)
                                self.lastFurnaceId = f"{int(x)}:{int(y - 1)}"
                                self.player.inventory.toggleGui(True, 9)
                            elif bottomTile == '120':
                                self.isInventoryOpened = True
                                pg.mouse.set_visible(self.isInventoryOpened)
                                self.lastChestId = f"{int(x)}:{int(y - 1)}"
                                self.player.inventory.toggleGui(True, 10)
                            elif bottomTile == '026':
                                self.sleep()

                    if canDraw:  # si canDraw == true
                        pg.mixer.Sound.play(self.audioList.get(
                            'menu_click'))  # joue le son préchargée
                        if not self.player.isDialog:  # si la variable isDialog du joueur n'est pas == True
                            self.currentDialog = TextObject(self, self.camera.getCamTopLeft()[0], self.camera.getCamTopLeft(
                            )[1] + HEIGHT - (HEIGHT / 6), WIDTH, HEIGHT, txt, False)  # création d'une nouvelle instance de la classe textObject
                            self.player.isDialog = True  # définition de la variable isDialog du joueur à True
                            self.player.canMove = False  # définition de la variable canMove du joueur à False
                        else:
                            # si la variable i de l'instance de la classe textObject est plus petite que le nombres de pages de texte
                            if self.currentDialog.i < len(txt):
                                # appel de la fonction nextLine dans l'instance de la classe textObject
                                self.currentDialog.nextLine()
                            else:
                                # appel de la fonction delete dans l'instance de la classe textObject
                                self.currentDialog.delete()
                                self.player.isDialog = False  # définition de la variable isDialog du joueur à False
                                self.player.canMove = True  # définition de la variable canMove du joueur à True
                elif event.key == pg.K_TAB and not self.isTabPressed:
                    self.isTabPressed = True
                    self.isInventoryOpened = not self.isInventoryOpened
                    pg.mouse.set_visible(self.isInventoryOpened)
                    self.player.inventory.toggleGui(self.isInventoryOpened, 0)

                elif event.key == 178 and not self.isPowerPressed:
                    if not self.input_commands_txt.active and self.input_commands:
                        self.input_commands = False
                        self.isGamePaused = False
                        self.input_commands_txt.active = False
                        self.input_commands_txt.color = BLACK
                    else:
                        self.isPowerPressed = True
                        self.input_commands = True
                        # self.isGamePaused = True
                        self.input_commands_txt.txt = ''

                    pg.mouse.set_visible(self.input_commands)

                elif self.input_commands and event.key == pg.K_RETURN:
                    if self.input_commands_txt.active:
                        command = self.input_commands_txt.text.lower().split(' ')
                        if len(command) > 0:
                            if command[0] == '/give':
                                if len(command) > 2:
                                    if command[2].isdigit():
                                        if command[1].isdigit():
                                            if int(command[1]) in self.itemTextureCoordinate:
                                                self.giveItem(
                                                    int(command[1]), int(command[2]))
                                        else:
                                            for itemId, name in self.itemTextureCoordinate.items():
                                                if command[1] in name:
                                                    self.giveItem(
                                                        itemId, int(command[2]))
                                                    break
                            elif command[0] == '/tp':
                                if len(command) > 2:
                                    if command[1].isdigit() and command[2].isdigit():
                                        self.player.pos = vec(
                                            int(command[1]) * TILESIZE, int(command[2]) * TILESIZE)

                                        self.input_commands = False
                                        pg.mouse.set_visible(
                                            self.input_commands)
                                        self.isGamePaused = False
                                        self.input_commands_txt.active = False
                                        self.input_commands_txt.color = BLACK
                            elif command[0] == '/speed':
                                if len(command) > 1:
                                    if command[1].isdigit():
                                        self.player.speed = int(
                                            command[1]) * TILESIZE
                            elif command[0] == '/regen':
                                self.player.health = self.player.lifebar.maxHealth
                                self.player.lifebar.updateHealth(
                                    self.player.health)
                                self.player.lifebar.updateSurface()
                            elif command[0] == '/maxhealth':
                                if len(command) > 1:
                                    self.player.lifebar.maxHealth = int(
                                        command[1])
                                    self.player.health = self.player.lifebar.maxHealth
                                    self.player.lifebar.updateHealth(
                                        self.player.health)
                                    self.player.lifebar.updateSurface()
                            elif command[0] == '/save':
                                self.save()
                            elif command[0] == '/hitbox':
                                if len(command) > 1:
                                    if command[1].isdigit():
                                        if int(command[1]) == 0:
                                            self.hitboxDebug = False
                                        elif int(command[1]) == 1:
                                            self.hitboxDebug = True
                                else:
                                    self.hitboxDebug = True
                            elif command[0] == '/spawnpoint':
                                if len(command) > 2:
                                    if command[1].isdigit() and command[2].isdigit():
                                        self.spawnPoint = vec(
                                            int(command[1]), int(command[2]))
                            elif command[0] == '/time':
                                if len(command) > 2:
                                    if command[1] == 'add':
                                        if command[2].isdigit():
                                            self.global_time += int(command[2])
                                    elif command[1] == 'set':
                                        if command[2].isdigit():
                                            self.global_time -= self.day_time
                                            self.global_time += int(
                                                command[2]) % DAY_LENGTH
                                        elif command[2] == 'day':
                                            self.skipNight()
                                        elif command[2] == 'night':
                                            self.global_time -= self.day_time
                                            self.global_time += DAY_LENGTH - \
                                                (DAY_LENGTH // 3)

                                    self.input_commands = False
                                    pg.mouse.set_visible(self.input_commands)
                                    self.isGamePaused = False
                                    self.input_commands_txt.active = False
                                    self.input_commands_txt.color = BLACK
                            elif command[0] == '/spawn':
                                if len(command) > 3:
                                    if command[1].isdigit() and command[2].isdigit() and command[3].isdigit():
                                        mobId = max(
                                            min(int(command[1]), len(self.mobList) - 1), 0)
                                        Mob(self, int(command[2]), int(
                                            command[3]), mobId)
                                    elif command[2].isdigit() and command[3].isdigit():
                                        mobId = -1
                                        for mob in self.mobList:
                                            mobId += 1
                                            if mob[5] == command[1]:
                                                break
                                        if mobId != -1:
                                            Mob(self, int(command[2]), int(
                                                command[3]), mobId)
                            elif command[0] == '/clear':
                                if len(command) > 1:
                                    if command[1] == 'inventory':
                                        for i in range(len(self.player.hotbar.itemList)):
                                            self.player.hotbar.itemList[i] = [
                                                0, 0]
                                        self.player.hotbar.updateSelector(0)
                                    elif command[1] == 'items':
                                        for floatItem in self.floatingItems:
                                            floatItem.kill()
                                    elif command[1] == 'entities':
                                        for mob in self.mobs:
                                            mob.kill()
                                        self.friendly_mobs_amount = 0
                                        self.hostile_mobs_amount = 0

                                        for projectile in self.projectiles:
                                            projectile.kill()

                                        for floatItem in self.floatingItems:
                                            floatItem.kill()
                            elif command[0] == '/kill':
                                self.player.die()

                        self.input_commands_txt.text = ''

            elif event.type == pg.KEYUP:
                if event.key == pg.K_TAB:
                    self.isTabPressed = False
                elif event.key == pg.K_e:
                    self.isEPressed = False
                elif event.key == 178:
                    self.isPowerPressed = False

            elif event.type == pg.MOUSEBUTTONDOWN:
                if event.button == 1:
                    if not self.isGamePaused:
                        self.player.action(vec(self.camera.getCamClickTopLeft()[
                                           0] + self.mousePos[0], self.camera.getCamClickTopLeft()[1] + self.mousePos[1]))
                    elif self.isInventoryOpened:
                        self.player.inventory.click(self.mousePos, 0)
                    elif self.player.dead:
                        if self.mousePos[0] > self.respawn_rect[0] and self.mousePos[0] < self.respawn_rect[0] + self.respawn_rect[2] and self.mousePos[1] > self.respawn_rect[1] and self.mousePos[1] < self.respawn_rect[1] + self.respawn_rect[3]:
                            self.player.respawn()
                elif event.button == 3:
                    if self.isInventoryOpened:
                        self.player.inventory.click(self.mousePos, 1)
                elif event.button == 4 and not self.isGamePaused:
                    self.player.hotbar.updateSelector(
                        self.player.hotbar.index - 1)
                elif event.button == 5 and not self.isGamePaused:
                    self.player.hotbar.updateSelector(
                        self.player.hotbar.index + 1)

            if self.input_commands:
                self.input_commands_txt.handle_event(event)

    def show_start_screen(self):
        m = Menu(self, 0, 0)

        while not self.playing:
            # event
            for event in pg.event.get():  # pour chaque evenements detecté (clavier souris)
                if event.type == pg.QUIT:  # si l'evenement correspond à QUIT
                    self.quit()  # appel la fonction quit

                if event.type == pg.KEYDOWN:
                    if event.key == pg.K_ESCAPE:  # si la touche correspond à escape
                        if m.Page == 0:
                            self.quit()  # appel de la fonction quit
                        else:
                            m.toggleGui(0)

                elif event.type == pg.MOUSEBUTTONDOWN:
                    if event.button == 1:
                        m.click(pg.mouse.get_pos())

                for box in m.inputBoxes:
                    box.handle_event(event)

            # update
            m.hover(pg.mouse.get_pos())

            for box in m.inputBoxes:
                box.update()

            # draw
            self.screen.blit(m.image, m.rect)  # affichage du sprite

            for box in m.inputBoxes:
                box.draw(self.screen)

            pg.display.flip()  # met à jour l'écran

    def show_go_screen(self):
        g.new()  # appel de la fonction new
        g.run()  # appel de la fonction run

    def save(self):
        lst = []
        playerState = str(int(self.player.pos.x)) + ':' + str(int(self.player.pos.y)) + ':' + str(
            self.player.lastWalkStatement) + ':' + str(self.player.health) + ':' + str(self.player.lifebar.maxHealth)
        lst.append((playerState + '\n' + str(self.player.hotbar.itemList) + '\n' + self.map.levelSavedData[2] + '\n' + str(int(self.spawnPoint.x)) + ':' + str(int(
            self.spawnPoint.y)) + '\n' + str(self.global_time) + '\n' + str(self.night_shade), path.join(self.game_folder, 'saves/' + self.worldName + '/level.save')))
        self.hasPlayerStateChanged = False

        floatingItemsList = []
        for item in self.floatingItems:
            floatingItemsList.append(
                [round(item.pos.x, 2), round(item.pos.y, 2), item.item])

        lst.append((str(floatingItemsList), path.join(
            self.game_folder, 'saves/' + self.worldName + '/floatingItems.txt')))
        lst.append((str(self.map.chestsData).replace("'", '"'), path.join(
            self.game_folder, 'saves/' + self.worldName + '/chests.txt')))
        lst.append((str(self.map.furnacesData).replace("'", '"'), path.join(
            self.game_folder, 'saves/' + self.worldName + '/furnaces.txt')))

        save = AsyncWrite(self, lst)
        save.start()


class AsyncWrite(threading.Thread):
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


# ---main----
g = Game()  # création d'une nouvelle instance de la classe Game

while True:
    g.playing = False
    g.show_start_screen()  # appel de la fonction show_start_screen

    g.show_go_screen()  # appel de la fonction show_go_screen
