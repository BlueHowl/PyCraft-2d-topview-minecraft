import math
import pygame as pg

from game.entities.FloatingItem import FloatingItem
from game.config.settings import BLACK, DARKGREY, HOTBAR_SLOTS, INVENTORY_SLOTS, MELEEREACH, MELTING_SPEED, RED, STACK, TILESIZE, WHITE, YELLOW

class Inventory(pg.sprite.Sprite):
    def __init__(self, game, xOffset, yOffset):
        self.groups = game.gui #game.all_sprites, game.gui
        pg.sprite.Sprite.__init__(self, self.groups)
        self.game = game
        self.image = pg.Surface((len(game.inventoryMap[0]) * TILESIZE, len(game.inventoryMap) * TILESIZE + TILESIZE), pg.SRCALPHA, 32)

        self.uiList = []
        self.craftPage = 0
        self.last_craftUi = 0
        self.currentCraft = []
        self.currentItemHold = []
        self.currentDraggedItem = [0, 0]
        self.last_mouse_btn = 0

        self.rect = self.image.get_rect() #assignation de la variable rect

        self.xOffset = xOffset
        self.yOffset = yOffset
        self.rect.x = xOffset #application de la position x de la surface
        self.rect.y = yOffset #application de la position y de la surface

        self.last_fuel = 0
        self.last_burn = 0
        self.openedFurnace = False

    def toggleGui(self, toggle, craftPage):
        self.game.isGamePaused = toggle
        self.craftPage = craftPage

        self.image = pg.Surface((len(self.game.inventoryMap[0]) * TILESIZE, len(self.game.inventoryMap) * TILESIZE + TILESIZE), pg.SRCALPHA, 32)

        if toggle:
            self.uiList = []
            if craftPage == 9:
                for row, tiles in enumerate(self.game.furnaceUiMap): #pour chaque lignes de la liste layer1Data
                    for col, tile in enumerate(tiles): #pour chaque caracteres de la ligne
                        if tile != '.': #si l'id n'est pas égale à "."
                            self.blitTile(tile, col, row)

                pg.draw.line(self.image, BLACK, (544, 447), (544 + 5*TILESIZE, 447), 1)
                pg.draw.line(self.image, BLACK, (703, 447), (703, 447 - 5*TILESIZE), 1)

                #furnace
                furnace = self.game.map.furnacesData.get(self.game.lastFurnaceId)
                if furnace:
                    in_0 = furnace[0][0]
                    in_1 = furnace[0][1]
                    out = furnace[0][2]

                    recipe = []

                    for craft in self.game.craftList:
                        if int(craft[0][1]) == craftPage:
                            r = craft[1].split(';')
                            if int(r[0].split(',')[0]) == in_0[0]:
                                recipe = r
                                break

                    burn_time = 0
                    fuel_time = 0
                    max_fuel_time = 10 * 1000

                    itemAssign = self.game.furnaceFuelList.get(furnace[0][1][0])
                    if itemAssign:
                        max_fuel_time = int(itemAssign[1]) * 1000

                    if in_1[0] != 0 and recipe and out[1] < STACK:
                        #fuel_time = furnace[1]
                        #self.burn_time = furnace[2]

                        laps = self.game.now - furnace[3]

                        fuel_time = laps % max_fuel_time
                        burn_time = laps % MELTING_SPEED

                        if not self.openedFurnace and furnace[3] != 0: #à l'ouverture du four
                            self.last_fuel = 0
                            self.last_burn = 0

                            used_fuel = (laps - fuel_time) // max_fuel_time
                            melted_items = (laps - burn_time) // MELTING_SPEED

                            if melted_items > in_0[1]:
                                melted_items = in_0[1]
                                used_fuel = (in_0[1] * MELTING_SPEED) // max_fuel_time

                            if used_fuel > in_1[1]:
                                used_fuel = in_1[1]
                                melted_items = (in_1[1] * max_fuel_time) // MELTING_SPEED

                            #remove fuel
                            if used_fuel >= in_1[1]:
                                furnace[0][1] = [0, 0]
                            else:
                                furnace[0][1][1] -= used_fuel

                            #remove melted
                            if melted_items >= in_0[1]:
                                furnace[0][0] = [0, 0]
                            else:
                                furnace[0][0][1] -= melted_items

                            #add melted result
                            if out[0] == 0 and melted_items > 0:
                                furnace[0][2][0] = int(recipe[1].split(',')[0])

                            furnace[0][2][1] += melted_items

                            self.openedFurnace = True

                        else:
                            if self.last_fuel < laps // max_fuel_time:
                                if in_1[1] > 1:
                                    furnace[0][1][1] -= 1
                                else:
                                    furnace[0][1] = [0, 0]
                                self.last_fuel = laps // max_fuel_time

                            if self.last_burn < laps // MELTING_SPEED:
                                if in_0[1] > 1:
                                    furnace[0][0][1] -= 1
                                else:
                                    furnace[0][0] = [0, 0]

                                #add melted result
                                if out[0] == 0:
                                    furnace[0][2][0] = int(recipe[1].split(',')[0])
                                furnace[0][2][1] += 1

                                self.last_burn = laps // MELTING_SPEED

                    else:
                        #if in_0[1] > 0 and in_1[1] > 0: #si les deux inputs ne sont pas vide
                        self.game.map.furnacesData.get(self.game.lastFurnaceId)[3] = self.game.now
                        self.last_fuel = 0
                        self.last_burn = 0


                self.displayItem(in_0, 3 * TILESIZE, 3 * TILESIZE)
                self.uiList.append((3 * TILESIZE, 4 * TILESIZE, 32, 31, ['furnaceItem', 0, in_0]))

                self.displayItem(in_1, 3 * TILESIZE, 5 * TILESIZE)
                self.uiList.append((3 * TILESIZE, 6 * TILESIZE, 32, 31, ['furnaceItem', 1, in_1]))

                self.displayItem(out, 7 * TILESIZE, 3 * TILESIZE)
                self.uiList.append((7 * TILESIZE, 4 * TILESIZE, 32, 31, ['furnaceItem', 2, out]))

                pg.draw.line(self.image, DARKGREY, (4.7*TILESIZE, 4*TILESIZE), (4.7*TILESIZE + 50, 4*TILESIZE), 4)
                if burn_time != 0:
                    pg.draw.line(self.image, YELLOW, (4.7*TILESIZE, 4*TILESIZE), (4.7*TILESIZE + (burn_time // 40), 4*TILESIZE), 4)

                pg.draw.line(self.image, DARKGREY, (4*TILESIZE + 4, 4*TILESIZE), (4*TILESIZE + 4, 4*TILESIZE + 32), 4)
                burn_load = int((fuel_time / max_fuel_time) * 32)
                if burn_load != 0:
                    pg.draw.line(self.image, RED, (4*TILESIZE + 4, 5*TILESIZE), (4*TILESIZE + 4, 4*TILESIZE + burn_load), 4)

            elif craftPage == 10:
                for row, tiles in enumerate(self.game.chestUiMap): #pour chaque lignes de la liste layer1Data
                    for col, tile in enumerate(tiles): #pour chaque caracteres de la ligne
                        if tile != '.': #si l'id n'est pas égale à "."
                            self.blitTile(tile, col, row)

                pg.draw.line(self.image, BLACK, (544, 447), (544 + 5*TILESIZE, 447), 1)
                pg.draw.line(self.image, BLACK, (703, 447), (703, 447 - 5*TILESIZE), 1)

                pg.draw.line(self.image, BLACK, (0, 447), (0 + 9*TILESIZE, 447), 1)
                pg.draw.line(self.image, BLACK, (0, 447), (0, 447 - 5*TILESIZE), 1)

                #chest
                chest = self.game.map.chestsData.get(self.game.lastChestId)
                if chest:
                    y_offset = 9 * TILESIZE
                    i, x, y = 0, 0, 0

                    while i < 45:
                        if i % 9 == 0 and i != 0:
                            y += 1
                            x = 0
                        item = chest[i]
                        self.displayItem(item, x * TILESIZE, y_offset + y * TILESIZE)
                        self.uiList.append((x * TILESIZE, y_offset + (y + 1) * TILESIZE, 32, 31, ['chestItem', i, item]))

                        x += 1
                        i += 1
            else:
                for row, tiles in enumerate(self.game.inventoryMap): #pour chaque lignes de la liste layer1Data
                    for col, tile in enumerate(tiles): #pour chaque caracteres de la ligne
                        if tile != '.': #si l'id n'est pas égale à "."
                            self.blitTile(tile, col, row)

                pg.draw.line(self.image, BLACK, (544, 447), (544 + 5*TILESIZE, 447), 1)
                pg.draw.line(self.image, BLACK, (703, 447), (703, 447 - 5*TILESIZE), 1)

                if craftPage == 0:
                    pg.draw.line(self.image, WHITE, (1, 60), (4*TILESIZE+15, 60), 2)
                    pg.draw.line(self.image, WHITE, (4*TILESIZE+15, 60), (4*TILESIZE+15, 1), 3)
                elif craftPage == 1:
                    pg.draw.line(self.image, WHITE, (4*TILESIZE+20, 60), (8*TILESIZE+15, 60), 2)
                    pg.draw.line(self.image, WHITE, (8*TILESIZE+15, 60), (8*TILESIZE+15, 1), 3)
                elif craftPage == 2:
                    pg.draw.line(self.image, WHITE, (8*TILESIZE+20, 60), (12*TILESIZE+15, 60), 2)
                    pg.draw.line(self.image, WHITE, (12*TILESIZE+15, 60), (12*TILESIZE+15, 1), 3)
                elif craftPage == 3:
                    pg.draw.line(self.image, WHITE, (12*TILESIZE+20, 60), (16*TILESIZE+27, 60), 2)
                    pg.draw.line(self.image, WHITE, (16*TILESIZE+27, 60), (16*TILESIZE+27, 1), 3)

                self.image.blit(pg.transform.rotate(self.game.items_img.subsurface((18*TILESIZE, 0*TILESIZE, TILESIZE, TILESIZE)), 90), (12, 18))
                self.image.blit(self.game.items_img.subsurface((12*TILESIZE, 0*TILESIZE, TILESIZE, TILESIZE)), (22, 18))
                self.image.blit(self.game.font_32.render('Tools', True, BLACK), (54, 20))

                self.image.blit(self.game.items_img.subsurface((2*TILESIZE, 0*TILESIZE, TILESIZE, TILESIZE)), (146, 18))
                self.image.blit(self.game.font_32.render('Blocks', True, BLACK), (174, 20))

                self.image.blit(self.game.items_img.subsurface((10*TILESIZE, 0*TILESIZE, TILESIZE, TILESIZE)), (280, 18))
                self.image.blit(self.game.font_32.render('Items', True, BLACK), (310, 20))

                self.image.blit(self.game.items_img.subsurface((4*TILESIZE, 0*TILESIZE, TILESIZE, TILESIZE)), (408, 18))
                self.image.blit(self.game.font_32.render('Health', True, BLACK), (440, 20))

                i = 2
                for craft in self.game.craftList:
                    if int(craft[0][1]) == craftPage:
                        if craft[0][0] == '0':
                            if self.showCraft(craft, i):
                                i += 1
                        elif craft[0][0] == '1':
                            for layer1_obj in self.game.Layer1:
                                distance = math.hypot(layer1_obj.x * TILESIZE  - self.game.player.pos.x, layer1_obj.y * TILESIZE - self.game.player.pos.y)
                                if layer1_obj.name == 'workbench' and distance <= MELEEREACH:
                                    if self.showCraft(craft, i):
                                        i += 1
                                    break

            #hotbar
            x_offset = 6.5 * TILESIZE
            y_offset = 15 * TILESIZE
            i = 0

            while i < HOTBAR_SLOTS:
                item = self.game.player.hotbar.itemList[i]
                self.uiList.append((x_offset + i * TILESIZE, y_offset, 32, 31, ['item', i, item]))
                i += 1

            #inventory
            x_offset = 17 * TILESIZE
            y_offset = 9 * TILESIZE
            i, x, y = 0, 0, 0

            while i < INVENTORY_SLOTS:
                if i % 5 == 0 and i != 0:
                    y += 1
                    x = 0
                item = self.game.player.hotbar.itemList[HOTBAR_SLOTS + i]
                self.displayItem(item, x_offset + x * TILESIZE, y_offset + y * TILESIZE)
                self.uiList.append((x_offset + x * TILESIZE, y_offset + (y + 1) * TILESIZE, 32, 31, ['item', HOTBAR_SLOTS + i, item]))

                x += 1
                i += 1

        else:
            itemDragged = self.currentDraggedItem
            if itemDragged[0] != 0:
                itemInfos = self.game.itemTextureCoordinate.get(itemDragged[0])

                hasStacked = False
                if itemInfos[2] == 1:
                    for floatItem in self.game.floatingItems:
                        distance = math.hypot(floatItem.pos.x  - self.game.player.pos.x, floatItem.pos.y - self.game.player.pos.y)
                        if distance <= MELEEREACH and itemDragged[0] == floatItem.item[0]:
                            if floatItem.item[1] <= STACK - itemDragged[1]:
                                floatItem.item[1] += itemDragged[1]
                                hasStacked = True
                                break

                if not hasStacked:
                    FloatingItem(self.game, self.game.player.pos.x, self.game.player.pos.y, itemDragged)

                self.currentDraggedItem = [0, 0]

    def blitTile(self, tile, col, row):
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
        elif tile == '9':
            self.image.blit(self.game.menu_img.subsurface((1*TILESIZE, 4*TILESIZE, TILESIZE, TILESIZE)), (col*TILESIZE, row*TILESIZE))
        elif tile == 'a':
            self.image.blit(self.game.menu_img.subsurface((2*TILESIZE, 4*TILESIZE, TILESIZE, TILESIZE)), (col*TILESIZE, row*TILESIZE))
        elif tile == 'b':
            self.image.blit(self.game.menu_img.subsurface((2*TILESIZE, 3*TILESIZE, TILESIZE, TILESIZE)), (col*TILESIZE, row*TILESIZE))
        elif tile == 'c':
            self.image.blit(self.game.menu_img.subsurface((1*TILESIZE, 1*TILESIZE, TILESIZE, TILESIZE)), (col*TILESIZE, row*TILESIZE))
            self.image.blit(self.game.menu_img.subsurface((0*TILESIZE, 3*TILESIZE, TILESIZE, TILESIZE)), (col * TILESIZE, row * TILESIZE))
        elif tile == 'd':
            self.image.blit(self.game.menu_img.subsurface((1*TILESIZE, 1*TILESIZE, TILESIZE, TILESIZE)), (col*TILESIZE, row*TILESIZE))
            self.image.blit(self.game.menu_img.subsurface((1*TILESIZE, 3*TILESIZE, TILESIZE, TILESIZE)), (col * TILESIZE, row * TILESIZE))

    def showCraft(self, craft, i):
        c = craft[1].split(';')
        recipe = c[0].split(':')

        canCraft = False
        recipeList = []
        x = 0

        if i > 22:
            x = 10
            i -= 21
        elif i > 11:
            x = 5
            i -= 10

        for r in recipe:
            canCraft = False
            infos = r.split(',')
            item = [int(infos[0]), int(infos[1])]

            for inv_item in self.game.player.hotbar.itemList:
                if inv_item[0] == item[0] and inv_item[1] >= item[1]:
                    canCraft = True

            if canCraft:
                recipeList.append([item, x * TILESIZE + 16, i * TILESIZE + 12])
                x += 1
            else:
                break

        if canCraft:
            for item in recipeList:
                self.displayItem(item[0], item[1], item[2])

            self.image.blit(self.game.menu_img.subsurface((0*TILESIZE, 3*TILESIZE, TILESIZE, TILESIZE)), (x * TILESIZE + 12, i * TILESIZE + 12))

            infos = c[1].split(',')
            item = [int(infos[0]), int(infos[1])]
            self.displayItem(item, x * TILESIZE + 40, i * TILESIZE + 12)

            self.uiList.append((18, (i+1) * TILESIZE + 14, x * TILESIZE + 56, 30, c))

        return canCraft

    def displayItem(self, item, x, y):
        itemInfos = self.game.itemTextureCoordinate.get(item[0])
        if itemInfos != None:
            self.image.blit(self.game.items_img.subsurface((itemInfos[0]*TILESIZE, itemInfos[1]*TILESIZE, TILESIZE, TILESIZE)), [x, y])
            if itemInfos[2] == 1:
                if item[1] < 10:
                    self.image.blit(self.game.font_10.render(str(item[1]), True, BLACK), [x + 23, y + 20])
                else:
                    self.image.blit(self.game.font_10.render(str(item[1]), True, BLACK), [x + 17, y + 20])

    def hover(self, pos):
        isOverUi = False
        i = 0
        _current = []
        for _i, ui in enumerate(self.uiList):
            if self.calculateClick(pos, (ui[0], ui[1], ui[2] + 32, ui[3])):
                isOverUi = True
                i = _i + 1
                _current = ui[4]
                self.toggleGui(True, self.craftPage)
                pg.draw.rect(self.image, WHITE, (ui[0], ui[1] - TILESIZE, ui[2], ui[3]), 2)
                break

        if not isOverUi or self.last_craftUi != i:
            self.toggleGui(True, self.craftPage)
            self.currentCraft = []
            self.currentItemHold = []
            if _current:
                if _current[0] == 'item' or _current[0] == 'chestItem' or _current[0] == 'furnaceItem':
                    self.currentItemHold = _current
                else:
                    self.currentCraft = _current
            if i != 0:
                pg.mixer.Sound.play(self.game.audioList.get('menu_hover')) #joue le son préchargée
        self.last_craftUi = i

        self.displayItem(self.currentDraggedItem, pos[0] - 48, pos[1] - 48)

    def click(self, pos, btn):
        hasClickedBtn = False

        if self.craftPage != 9 and self.craftPage != 10:
            if self.calculateClick(pos, (1 * TILESIZE, 1 * TILESIZE, 5 * TILESIZE - 16, 2 * TILESIZE)):
                self.toggleGui(True, 0)
                hasClickedBtn = True
            elif self.calculateClick(pos, (6 * TILESIZE - 16, 1 * TILESIZE, 4 * TILESIZE, 2 * TILESIZE)):
                self.toggleGui(True, 1)
                hasClickedBtn = True
            elif self.calculateClick(pos, (9 * TILESIZE + 16, 1 * TILESIZE, 4 * TILESIZE, 2 * TILESIZE)):
                self.toggleGui(True, 2)
                hasClickedBtn = True
            elif self.calculateClick(pos, (13 * TILESIZE + 16, 1 * TILESIZE, 4 * TILESIZE + 16, 2 * TILESIZE)):
                self.toggleGui(True, 3)
                hasClickedBtn = True

        if hasClickedBtn:
            pg.mixer.Sound.play(self.game.audioList.get('menu_click')) #joue le son préchargée

        if self.currentCraft: #si la liste n'est pas vide
            for recipe in self.currentCraft[0].split(':'):
                r = recipe.split(',')

                for item in self.game.player.hotbar.itemList:
                    if item[0] == int(r[0]):
                        if item[1] > int(r[1]):
                            item[1] -= int(r[1])
                        else:
                            item[0] = 0
                            item[1] = 0
                        break

                self.game.player.hotbar.updateSelector(self.game.player.hotbar.index)

            newItem = self.currentCraft[1].split(',')
            self.game.player.hotbar.addItem(int(newItem[0]), int(newItem[1]))

            pg.mixer.Sound.play(self.game.audioList.get('craft')) #joue le son préchargée

            self.toggleGui(True, self.craftPage)

        elif self.currentItemHold:
            currentHolder = self.currentItemHold[0]
            i = self.currentItemHold[1]
            item = self.currentItemHold[2]

            chest = self.game.map.chestsData.get(self.game.lastChestId)
            furnace = self.game.map.furnacesData.get(self.game.lastFurnaceId)
            if (chest or self.craftPage != 10) or (furnace or self.craftPage != 9):
                if btn == 0:
                    if self.last_mouse_btn == 0:
                        if item[0] == self.currentDraggedItem[0] and item[0] != 0:
                            itemInfos = self.game.itemTextureCoordinate.get(item[0])
                            if itemInfos[2] == 1:
                                if item[1] + self.currentDraggedItem[1] <= STACK:
                                    item[1] += self.currentDraggedItem[1]
                                    self.currentDraggedItem = [0, 0]
                                else:
                                    self.currentDraggedItem[1] = (item[1] + self.currentDraggedItem[1]) % STACK
                                    item[1] = STACK

                        _currentDragged = [self.currentDraggedItem[0], self.currentDraggedItem[1]]
                        if currentHolder == 'item':
                            #if item[0] == _currentDragged[0] and item[0] != 0:
                            self.game.player.hotbar.itemList[i] = _currentDragged
                            self.currentDraggedItem = [item[0], item[1]]
                        elif currentHolder == 'chestItem':
                            chest[i] = _currentDragged
                            self.currentDraggedItem = [item[0], item[1]]
                        elif currentHolder == 'furnaceItem':
                            if i == 1:
                                itemAssign = self.game.furnaceFuelList.get(_currentDragged[0])
                                if itemAssign:
                                    if itemAssign[0] == '4':
                                        furnace[0][i] = _currentDragged
                                        self.currentDraggedItem = [item[0], item[1]]
                                elif _currentDragged[0] == 0:
                                    furnace[0][i] = _currentDragged
                                    self.currentDraggedItem = [item[0], item[1]]
                            else:
                                furnace[0][i] = _currentDragged
                                self.currentDraggedItem = [item[0], item[1]]

                    self.last_mouse_btn = 0
                    self.currentItemHold = []
                elif btn == 1:
                    if self.currentDraggedItem[1] > 0:
                        hasAddItem = False
                        if currentHolder == 'item' and self.game.player.hotbar.itemList[i][1] < STACK:
                            self.game.player.hotbar.itemList[i] = [self.currentDraggedItem[0], self.game.player.hotbar.itemList[i][1] + 1]
                            hasAddItem = True
                        elif currentHolder == 'chestItem' and chest[i][1] < STACK:
                            chest[i] = [self.currentDraggedItem[0], chest[i][1] + 1]
                            hasAddItem = True
                        elif currentHolder == 'furnaceItem' and furnace[0][i][1] < STACK:
                            if i == 1:
                                itemAssign = self.game.furnaceFuelList.get(self.currentDraggedItem[0])
                                if itemAssign:
                                    if itemAssign[0] == '4':
                                        furnace[0][i] = [self.currentDraggedItem[0], furnace[0][i][1] + 1]
                                        hasAddItem = True
                                elif self.currentDraggedItem[0] == 0:
                                    furnace[0][i] = [self.currentDraggedItem[0], furnace[0][i][1] + 1]
                                    hasAddItem = True
                            else:
                                furnace[0][i] = [self.currentDraggedItem[0], furnace[0][i][1] + 1]
                                hasAddItem = True

                        if hasAddItem:
                            if self.currentDraggedItem[1] > 1:
                                self.currentDraggedItem[1] -= 1
                            else:
                                self.currentDraggedItem = [0, 0]

                        self.last_mouse_btn = 1

                if i >= HOTBAR_SLOTS or currentHolder == 'chestItem' or currentHolder == 'furnaceItem':
                    self.toggleGui(True, self.craftPage)
                else:
                    self.game.player.hotbar.updateSelector(self.game.player.hotbar.index)

    def calculateClick(self, pos, box):
        if pos[0] > box[0] and pos[0] < box[0] + box[2] and pos[1] > box[1] and pos[1] < box[1] + box[3]:
            return True
        else:
            return False