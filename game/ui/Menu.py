from datetime import datetime
import os
from random import randint
import time
import pygame as pg

from game.ui.InputBox import InputBox
from game.config.settings import BLACK, TILESIZE, TITLE, TOTAL_SLOTS, WHITE, WIDTH
from game.data import DataManager


class Menu(pg.sprite.Sprite):
    def __init__(self, game, xOffset, yOffset, game_folder):
        self.groups = game.gui #game.all_sprites, game.gui
        pg.sprite.Sprite.__init__(self, self.groups)
        self.game = game
        self.gameFolder = game_folder
        
        # Initialize data manager for world operations
        self.data_manager = DataManager(game_folder)

        self.image = pg.Surface((len(game.menuData[0]) * TILESIZE, len(game.menuData) * TILESIZE), pg.SRCALPHA, 32)

        self.Page = 0

        self.UiList = []
        self.last_Ui = 0
        self.current = []
        self.inputBoxes = []

        self.seed = str(time.time()).replace('.', '')
        self.world_name = 'World-' + str(time.time())[-5:]

        self.worlds_list = []

        # Load worlds using the new data manager
        worlds = self.data_manager.list_worlds()
        for world in worlds:
            world_path = os.path.join(self.gameFolder, 'saves', world)
            if os.path.exists(world_path):
                timestamp = os.path.getmtime(world_path)
                self.worlds_list.append((world, str(datetime.fromtimestamp(timestamp))))

        self.rect = self.image.get_rect() #assignation de la variable rect

        self.xOffset = xOffset
        self.yOffset = yOffset
        self.rect.x = xOffset #application de la position x de la surface
        self.rect.y = yOffset #application de la position y de la surface

        self.toggleGui(0)

    def toggleGui(self, page):
        self.Page = page
        #self.current = []

        for row, tiles in enumerate(self.game.menuData): #pour chaque lignes de la liste layer1Data
            for col, tile in enumerate(tiles): #pour chaque caracteres de la ligne
                if tile != '.': #si l'id n'est pas égale à "."
                    if tile == '0':
                        self.image.blit(self.game.menu_img.subsurface((1*TILESIZE, 1*TILESIZE, TILESIZE, TILESIZE)), (col*TILESIZE, row*TILESIZE))
                    elif tile == '1':
                        self.image.blit(self.game.menu_img.subsurface((0*TILESIZE, 0*TILESIZE, TILESIZE, TILESIZE)), (col*TILESIZE, row*TILESIZE))
                    elif tile == '2':
                        self.image.blit(self.game.menu_img.subsurface((1*TILESIZE, 0*TILESIZE, TILESIZE, TILESIZE)), (col*TILESIZE, row*TILESIZE))
                    elif tile == '3':
                        self.image.blit(self.game.menu_img.subsurface((2*TILESIZE, 0*TILESIZE, TILESIZE, TILESIZE)), (col*TILESIZE, row*TILESIZE))
                    elif tile == '4':
                        self.image.blit(self.game.menu_img.subsurface((2*TILESIZE, 1*TILESIZE, TILESIZE, TILESIZE)), (col*TILESIZE, row*TILESIZE))
                    elif tile == '5':
                        self.image.blit(self.game.menu_img.subsurface((2*TILESIZE, 2*TILESIZE, TILESIZE, TILESIZE)), (col*TILESIZE, row*TILESIZE))
                    elif tile == '6':
                        self.image.blit(self.game.menu_img.subsurface((1*TILESIZE, 2*TILESIZE, TILESIZE, TILESIZE)), (col*TILESIZE, row*TILESIZE))
                    elif tile == '7':
                        self.image.blit(self.game.menu_img.subsurface((0*TILESIZE, 2*TILESIZE, TILESIZE, TILESIZE)), (col*TILESIZE, row*TILESIZE))
                    elif tile == '8':
                        self.image.blit(self.game.menu_img.subsurface((0*TILESIZE, 1*TILESIZE, TILESIZE, TILESIZE)), (col*TILESIZE, row*TILESIZE))


            title = self.game.font_64.render(TITLE, True, BLACK)
            self.image.blit(title, ((WIDTH / 2) - (title.get_width() / 2), 40))

            self.UiList = []
            self.inputBoxes = []

            if page == 0:
                txt = self.game.font_32.render('Singleplayer', True, BLACK)
                x = (WIDTH / 2) - (txt.get_width() / 2)
                self.image.blit(txt, (x, 180))
                self.UiList.append((x, 180, txt.get_width(), txt.get_height(), 1))

                txt = self.game.font_32.render('Multiplayer', True, BLACK)
                x = (WIDTH / 2) - (txt.get_width() / 2)
                self.image.blit(txt, (x, 230))
                self.UiList.append((x, 230, txt.get_width(), txt.get_height(), 5))

                txt = self.game.font_32.render('Load Game', True, BLACK)
                x = (WIDTH / 2) - (txt.get_width() / 2)
                self.image.blit(txt, (x, 280))
                self.UiList.append((x, 280, txt.get_width(), txt.get_height(), 2))

                txt = self.game.font_32.render('Settings', True, BLACK)
                x = (WIDTH / 2) - (txt.get_width() / 2)
                self.image.blit(txt, (x, 330))
                self.UiList.append((x, 330, txt.get_width(), txt.get_height(), 3))
            elif page == 1:
                txt = self.game.font_32.render('Create Singleplayer World', True, BLACK)
                x = (WIDTH / 2) - (txt.get_width() / 2)
                self.image.blit(txt, (x, 120))
                
                txt = self.game.font_32.render('World Name', True, BLACK)
                x = (WIDTH / 2) - (txt.get_width() / 2)
                self.image.blit(txt, (x, 200))
                self.input_name = InputBox(self.game, (WIDTH / 2) - 200, 240, 400, 40, text=self.world_name, limit=12, expandTwoWay=True)
                self.inputBoxes.append(self.input_name)

                txt = self.game.font_32.render('World Seed', True, BLACK)
                x = (WIDTH / 2) - (txt.get_width() / 2)
                self.image.blit(txt, (x, 300))
                self.input_seed = InputBox(self.game, (WIDTH / 2) - 150, 340, 300, 40, text=self.seed, limit=25, expandTwoWay=True)
                self.inputBoxes.append(self.input_seed)

                txt = self.game.font_32.render('Create World', True, BLACK)
                x = (WIDTH / 2) - (txt.get_width() / 2)
                self.image.blit(txt, (x, 420))
                pg.draw.rect(self.image, BLACK, (x - 5, 415, txt.get_width() + 10, txt.get_height() + 5), 4)
                self.UiList.append((x, 420, txt.get_width(), txt.get_height(), 4))
            elif page == 2:
                x = 0
                y = 2
                if self.worlds_list:
                    for world in self.worlds_list:
                        txt = self.game.font_32.render(world[0], True, BLACK)
                        self.image.blit(txt, (x * 230 + 30, y * 60 + 10))

                        txt1 = self.game.font_16.render(world[1], True, BLACK)
                        self.image.blit(txt1, (x * 230 + 32, y * 60 + 43))

                        pg.draw.rect(self.image, BLACK, (x * 230 + 25, y * 60 + 5, max(txt1.get_width(), txt.get_width()) + 10, txt.get_height() + txt1.get_height() + 5), 4)
                        self.UiList.append((x * 230 + 30, y * 60 + 10, max(txt1.get_width(), txt.get_width()), txt.get_height() + txt1.get_height(), world[0]))

                        y += 1
                        if y % 8 == 0 and y != 0:
                            x += 1
                            y = 2

    def hover(self, pos):
        if self.Page == 1:
            self.world_name = self.input_name.text.rstrip().lstrip()
            self.seed = self.input_seed.text

        isOverUi = False
        i = 0
        _current = []
        if self.UiList:
            for _i, Ui in enumerate(self.UiList):
                if self.calculateClick(pos, (Ui[0], Ui[1], Ui[2] + 32, Ui[3])):
                    isOverUi = True
                    i = _i + 1
                    _current.append(Ui[4])
                    pg.draw.rect(self.image, WHITE, (Ui[0] - 5, Ui[1] - 5, Ui[2] + 10, Ui[3] + 5), 2)
                    break

            if not isOverUi or self.last_Ui != i:
                self.current = _current
                if self.last_Ui != i:
                    self.toggleGui(self.Page)
                    if i != 0:
                        self.game.play_sound('menu_hover')  # Use safe audio system
            self.last_Ui = i

    def click(self, pos):
        if self.current: #si la liste n'est pas vide
            if type(self.current[0]) == str:
                self.game.worldName = self.current[0]
                self.game.playing = True
                self.kill()
            else:
                if self.current[0] < 4:
                    self.toggleGui(self.current[0])
                elif self.current[0] == 4:
                    # Create new world using the data manager
                    x = randint(-9999, 9999)
                    y = randint(-9999, 9999)
                    spawn_point = (x, y)
                    
                    # Create the new world using data manager
                    success = self.data_manager.create_new_world(
                        world_name=self.world_name,
                        seed=str(abs(hash(self.seed))),
                        spawn_point=spawn_point
                    )
                    
                    if success:
                        self.game.worldName = self.world_name
                        self.game.playing = True
                        self.game.game_mode = "singleplayer"  # Set singleplayer mode
                        self.kill()
                    else:
                        print(f"Failed to create world: {self.world_name}")
                elif self.current[0] == 5:
                    # Open multiplayer menu
                    self.game.show_multiplayer_menu()
                    self.kill()

            self.game.play_sound('menu_click')  # Use safe audio system

    def calculateClick(self, pos, box):
        if pos[0] > box[0] and pos[0] < box[0] + box[2] and pos[1] > box[1] and pos[1] < box[1] + box[3]:
            return True
        else:
            return False
