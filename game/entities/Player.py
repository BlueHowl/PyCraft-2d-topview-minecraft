import json
from random import randint, uniform
import pygame as pg

from game.entities.FloatingItem import FloatingItem
from game.entities.Projectile import Projectile
from game.entities.mobs.Mob import Mob
from game.ui.hud.Hotbar import Hotbar
from game.ui.hud.Lifebar import Lifebar
from game.ui.Inventory import Inventory
vec = pg.math.Vector2
import math
from math import atan2, degrees, pi
from game.config.settings import ANIMATE_SPEED_DIVIDER, CHUNKSIZE, HEIGHT, MELEEREACH, PROJECTILE_OFFSET, STACK, TILESIZE, WALK_SPEED, REGENSPEED, WATER_SPEED_DIVIDER, WIDTH


class Player(pg.sprite.Sprite): #classe du joueur
    def __init__(self, game, x, y, lws):
        self.groups = game.all_sprites, game.moving_sprites, game.players #définitions de la liste de groupes de textures
        pg.sprite.Sprite.__init__(self, self.groups) #définitions du joueur dans les groupes de textures
        self.game = game #récupération de l'instance de la classe principale du jeu
        self.image = pg.Surface((TILESIZE, TILESIZE), pg.SRCALPHA, 32) #création d'un surface transparente (32*32)
        #self.image.blit(game.player_sprite.subsurface((1*TILESIZE, 0*TILESIZE, TILESIZE, TILESIZE)), (0, 0))
        self.rect = self.image.get_rect() #assignation de la variable rect
        self.vel = vec(0, 0) #assignation de la variable vel(velocité) par un vecteur 2d nul
        self.pos = vec(x, y) #assignation de la variable pos(position) par un vecteur 2d au positions

        self.tilepos = vec(int(self.pos.x / TILESIZE), int(self.pos.y / TILESIZE))
        self.chunkpos = self.tilepos * CHUNKSIZE

        # Parse health from the correct position in legacy format: x:y:0:health:maxhealth
        pos_data = self.game.map.levelSavedData[0].split(':')
        if len(pos_data) >= 5:
            self.health = int(pos_data[3])  # Health is at index 3
        elif len(pos_data) >= 3:
            self.health = int(pos_data[2])  # Fallback for old format
        else:
            self.health = 20  # Default health
        #self.maxHealth = PLAYER_MAXLIFE #définition de la variable maxHealth à PLAYER_MAXLIFE

        self.forwardIdle = game.player_sprite.subsurface((0*TILESIZE, 0*TILESIZE, TILESIZE, TILESIZE)).copy() #définition de la texture au repos vers l'avant
        self.backwardIdle = game.player_sprite.subsurface((0*TILESIZE, 1*TILESIZE, TILESIZE, TILESIZE)).copy() #définition de la texture au repos vers l'arrière
        self.leftIdle = game.player_sprite.subsurface((0*TILESIZE, 2*TILESIZE, TILESIZE, TILESIZE)).copy() #définition de la texture au repos vers la gauche
        self.rightIdle = game.player_sprite.subsurface((0*TILESIZE, 3*TILESIZE, TILESIZE, TILESIZE)).copy() #définition de la texture au repos vers la droite

        self.walkForward = [game.player_sprite.subsurface((1*TILESIZE, 1*TILESIZE, TILESIZE, TILESIZE)).copy(), game.player_sprite.subsurface((2*TILESIZE, 1*TILESIZE, TILESIZE, TILESIZE)).copy()] #définition de la liste de texture de marche avant
        self.walkBackward = [game.player_sprite.subsurface((1*TILESIZE, 0*TILESIZE, TILESIZE, TILESIZE)).copy(), game.player_sprite.subsurface((2*TILESIZE, 0*TILESIZE, TILESIZE, TILESIZE)).copy()] #définition de la liste de texture de marche arrière
        self.walkLeft = [game.player_sprite.subsurface((1*TILESIZE, 2*TILESIZE, TILESIZE, TILESIZE)).copy(), game.player_sprite.subsurface((2*TILESIZE, 2*TILESIZE, TILESIZE, TILESIZE))] #définition de la liste de texture de marche à gauche
        self.walkRight = [game.player_sprite.subsurface((1*TILESIZE, 3*TILESIZE, TILESIZE, TILESIZE)).copy(), game.player_sprite.subsurface((2*TILESIZE, 3*TILESIZE, TILESIZE, TILESIZE)).copy()] #définition de la liste de texture de marche à droite

        self.lastWalkStatement = lws #définition de la variable lastWalkStatement par lws(valeur parametres)
        self.canMove = True #définition de la variable canMove à True
        self.speed = WALK_SPEED
        #self.facingSign = False
        self.isDialog = False #définition de la variable isDialog à False

        self.last_attack = self.game.now
        self.last_hit = self.game.now
        self.last_regen = self.game.now
        self.last_blocked = self.game.now

        self.harvest_clicks = 1
        self.last_cell_click = vec(0, 0)

        self.dead = False

        self.lifebar = Lifebar(game, 10, 10, self.health)

        #items = [[1, 1], [19, 1], [2, STACK], [0, 0], [9, 4],[4, 8], [14, 1], [11, 8], [3, 10]]
        items = json.loads(self.game.map.levelSavedData[1])
        self.hotbar = Hotbar(game, (WIDTH - 9*32) // 2, HEIGHT-32, game.hotbar_img.subsurface((0*TILESIZE, 0*TILESIZE, 9*TILESIZE, TILESIZE)).copy(), game.hotbar_img.subsurface((0*TILESIZE, 1*TILESIZE, 9*TILESIZE, TILESIZE)).copy(), 0, items)

        self.inventory = Inventory(game, 32, 32)

    def get_keys(self):
        self.vel = vec(0, 0) #reinitialisation de la variable vel

        keys = pg.key.get_pressed() #récupération des touches pressées

        speed = self.speed
        ground = self.game.getTile(vec(self.pos.x + 16, self.pos.y + 16), True)
        if ground == '00':
            speed /= WATER_SPEED_DIVIDER

        if keys[pg.K_LEFT] or keys[pg.K_q]: #si appui de la fleche gauche ou de la touche a
            self.vel.x = -speed #application d'une velocité de - 4*32 sur l'axe x
        elif keys[pg.K_RIGHT] or keys[pg.K_d]: #si appui de la fleche droite ou de la touche d
            self.vel.x = speed #application d'une velocité de 4*32 sur l'axe x
        elif keys[pg.K_UP] or keys[pg.K_z]: #si appui de la fleche haut ou de la touche w
            self.vel.y = -speed #application d'une velocité de - 4*32 sur l'axe y
        elif keys[pg.K_DOWN] or keys[pg.K_s]: #si appui de la fleche bas ou de la touche s
            self.vel.y = speed #application d'une velocité de 4*32 sur l'axe y
        #if self.vel.x != 0 and self.vel.y != 0:
            #self.vel *= DIAGONAL_MALUS

    def collide_with_walls(self, dir):
        hasCollided = False
        if dir == 'x': #si dir == x
            hits = pg.sprite.spritecollide(self, self.game.player_collisions, False) #récupération des collisions
            if hits: #si il y a des collisions
                if self.vel.x > 0: #si la vélocité sur l'axe x est plus grande que 0
                    self.pos.x = hits[0].rect.left - self.rect.width #application de la position, collision gauche
                if self.vel.x < 0: #si la vélocité sur l'axe x est plus petite que 0
                    self.pos.x = hits[0].rect.right #application de la position, collision droite
                self.vel.x = 0 #reinitialisation de la valeur x de la variable vel
                self.rect.x = self.pos.x #application de la position x sur le joueur

                hasCollided = True

        if dir == 'y': #si dir == y
            hits = pg.sprite.spritecollide(self, self.game.player_collisions, False) #récupération des collisions
            if hits: #si il y a des collisions
                if self.vel.y > 0: #si la vélocité sur l'axe y est plus grande que 0
                    self.pos.y = hits[0].rect.top - self.rect.height #application de la position, collision bas
                if self.vel.y < 0: #si la vélocité sur l'axe y est plus petite que 0
                    self.pos.y = hits[0].rect.bottom #application de la position, collision haut
                self.vel.y = 0 #reinitialisation de la valeur y de la variable vel
                self.rect.y = self.pos.y #application de la position y sur le joueur

                hasCollided = True

        if self.game.now > self.last_blocked + 500 and hasCollided:
            pg.mixer.Sound.play(self.game.audioList.get('block')) #joue le son préchargée
            self.last_blocked = self.game.now

    def update(self):
        if self.canMove: #si canMove == true
            self.get_keys() #appel la fonction get_keys
        self.pos += self.vel * self.game.dt #application de la vélocité
        self.rect.x = self.pos.x #application de la position x
        self.animate() #appel de la fonction animate
        self.collide_with_walls('x') #appel de la fonction collide_with_walls param 'x'
        self.rect.y = self.pos.y #application de la position y
        self.collide_with_walls('y') #appel de la fonction collide_with_walls param 'y'
        self.tilepos = vec(int(self.pos.x / TILESIZE), int(self.pos.y / TILESIZE))
        self.chunkpos = vec(int(self.tilepos.x / CHUNKSIZE), int(self.tilepos.y / CHUNKSIZE))
        #self.regen()
        self.gatherItem()

    def regen(self):
        if self.game.now > self.last_hit + 3500:
            if self.game.now - self.last_regen > REGENSPEED:
                self.last_regen = self.game.now
                if self.health < self.lifebar.maxHealth:
                    self.health += 1
                    self.lifebar.updateHealth(self.health)
                    self.lifebar.updateSurface()

    def gatherItem(self):
        for floatItem in self.game.floatingItems:
            itemInfos = self.game.itemTextureCoordinate.get(floatItem.item[0])
            distance = math.hypot(floatItem.pos.x - self.pos.x, floatItem.pos.y - self.pos.y)
            if distance <= 16:
                for item in self.hotbar.itemList:
                    if item[0] == 0:
                        item[0] = floatItem.item[0]
                        item[1] = 0
                        #pg.mixer.Sound.play(self.game.audioList.get('drop_item')) #joue le son préchargée
                    if item[0] == floatItem.item[0]:
                        if item[1] + floatItem.item[1] <= STACK:
                            if itemInfos[2] == 1:
                                item[1] += floatItem.item[1]
                                floatItem.kill()
                                self.hotbar.updateSelector(self.hotbar.index)
                                pg.mixer.Sound.play(self.game.audioList.get('drop_item')) #joue le son préchargée

                                self.game.hasPlayerStateChanged = True #autorise la sauvegarde du joueur
                                break
                            elif item[1] == 0:
                                item[1] = 1
                                floatItem.kill()
                                self.hotbar.updateSelector(self.hotbar.index)
                                pg.mixer.Sound.play(self.game.audioList.get('drop_item')) #joue le son préchargée

                                self.game.hasPlayerStateChanged = True #autorise la sauvegarde du joueur
                                break
                        elif item[1] + floatItem.item[1] > STACK:
                            floatItem.item[1] -= (STACK - item[1])
                            item[1] = STACK

    def animate(self):
        self.image = pg.Surface((TILESIZE, TILESIZE), pg.SRCALPHA, 32) #redéfintion dela surface image en transparente (32*32)

        if self.vel.x < 0: #si la vélocité sur l'axe x est plus petite que 0
            #self.image.blit(self.walkLeft[int((WALK_SPEED // self.game.dt) % len(self.walkLeft))], (0, 0))
            self.image.blit(self.walkLeft[int(self.game.now // WALK_SPEED * ANIMATE_SPEED_DIVIDER) % len(self.walkLeft)], (0, 0)) #application de la texture de marche à gauche en fonction du temps
            #pg.display.set_icon(self.walkLeft[int(self.game.now // WALK_SPEED * ANIMATE_SPEED_DIVIDER) % len(self.walkLeft)]) #application de la texture de marche à gauche sur l'icone en fonction du temps
            self.lastWalkStatement = 2 #définition de la variable lastWalkStatement à 2
        elif self.vel.x > 0: #si la vélocité sur l'axe x est plus grande que 0
            self.image.blit(self.walkRight[int(self.game.now // WALK_SPEED * ANIMATE_SPEED_DIVIDER) % len(self.walkRight)], (0, 0)) #application de la texture de marche à droite en fonction du temps
            #pg.display.set_icon(self.walkRight[int(self.game.now // WALK_SPEED * ANIMATE_SPEED_DIVIDER) % len(self.walkRight)]) #application de la texture de marche à droite sur l'icone en fonction du temps
            self.lastWalkStatement = 3 #définition de la variable lastWalkStatement à 3
        elif self.vel.y < 0: #si la vélocité sur l'axe y est plus petite que 0
            self.image.blit(self.walkForward[int(self.game.now // WALK_SPEED * ANIMATE_SPEED_DIVIDER) % len(self.walkForward)], (0, 0)) #application de la texture de marche avant en fonction du temps
            #pg.display.set_icon(self.walkForward[int(self.game.now // WALK_SPEED * ANIMATE_SPEED_DIVIDER) % len(self.walkForward)]) #application de la texture de marche avant sur l'icone en fonction du temps
            self.lastWalkStatement = 0 #définition de la variable lastWalkStatement à 0
        elif self.vel.y > 0: #si la vélocité sur l'axe y est plus grande que 0
            self.image.blit(self.walkBackward[int(self.game.now // WALK_SPEED * ANIMATE_SPEED_DIVIDER) % len(self.walkBackward)], (0, 0)) #application de la texture de marche arrière en fonction du temps
            #pg.display.set_icon(self.walkBackward[int(self.game.now // WALK_SPEED * ANIMATE_SPEED_DIVIDER) % len(self.walkBackward)]) #application de la texture de marche arrière sur l'icone en fonction du temps
            self.lastWalkStatement = 1 #définition de la variable lastWalkStatement à 1
        else:
            if self.lastWalkStatement == 0: #si lastWalkStatement == 0
                self.image.blit(self.backwardIdle, (0, -abs(math.sin(self.game.now // (8*60) )) * 3)) #application de la texture au repos vers l'arrière + animation de respiration avec sinus
            elif self.lastWalkStatement == 1: #si lastWalkStatement == 1
                self.image.blit(self.forwardIdle, (0, -abs(math.sin(self.game.now // (8*60) )) * 2)) #application de la texture au repos vers l'avant + animation de respiration avec sinus
            elif self.lastWalkStatement == 2: #si lastWalkStatement == 2
                self.image.blit(self.leftIdle, (0, -abs(math.sin(self.game.now // (8*60) )) * 2)) #application de la texture au repos vers la gauche + animation de respiration avec sinus
            elif self.lastWalkStatement == 3: #si lastWalkStatement == 3
                self.image.blit(self.rightIdle, (0, -abs(math.sin(self.game.now // (8*60) )) * 2)) #application de la texture au repos vers la droite + animation de respiration avec sinus

    def action(self, target):
            currentItem = self.hotbar.itemList[self.hotbar.index]
            distance = math.hypot(target.x  - self.pos.x, target.y - self.pos.y)
            #case = self.game.map.layer1Data[int(target.y // 32)][int(target.x // 32)]
            tile = self.game.getTile(target, False)

            cell_x = int(target.x // 32)
            cell_y = int(target.y // 32)
            if cell_x != self.last_cell_click.x or cell_y != self.last_cell_click.y:
                self.harvest_clicks = 1

            self.last_cell_click = vec(cell_x, cell_y)

            if tile != '.': #si case n'est pas vide
                cell_infos = self.game.textureCoordinate.get(tile)

            if currentItem[0] == 1: #bow
                hasArrow = False

                for item in self.hotbar.itemList:
                    if item[0] == 2:
                        if item[1] > 1:
                            item[1] -= 1
                            hasArrow = True
                        elif item[1] == 1:
                            item[0] = 0
                            item[1] = 0
                            hasArrow = True

                        self.hotbar.updateSelector(self.hotbar.index)

                        self.game.hasPlayerStateChanged = True #autorise la sauvegarde du joueur
                        break

                if hasArrow:
                    #now = self.game.now
                    #if now - self.last_attack > FIRE_RATE:
                        #self.last_attack = now
                    pg.mixer.Sound.play(self.game.audioList.get('arrow_shot')) #joue le son préchargée

                    dx = target.x - self.pos.x + 10
                    dy = target.y - self.pos.y + 5
                    rads = atan2(-dy,dx)
                    rads %= 2*pi
                    deg = degrees(rads)

                    if deg >= 55 and deg < 130:
                        self.lastWalkStatement = 0
                    elif deg >= 130 and deg < 215:
                        self.lastWalkStatement = 2
                    elif deg >= 215 and deg < 315:
                        self.lastWalkStatement = 1
                    elif deg >= 315 or deg < 55:
                        self.lastWalkStatement = 3

                    newPos = vec(self.pos.x + 10, self.pos.y + 5) + PROJECTILE_OFFSET.rotate(-deg - 55)

                    dx = target.x - newPos.x
                    dy = target.y - newPos.y
                    rads = atan2(-dy,dx)
                    rads %= 2*pi
                    deg = degrees(rads)

                    Projectile(self.game, newPos, deg, 1, math.hypot(dx, dy), 3)

            else:
                itemAssign = self.game.itemAssignementList.get(currentItem[0])
                if itemAssign: #si itemAssign n'est pas vide
                    if itemAssign[0] == '0':
                        if distance <= MELEEREACH:
                            if tile[0] == '0' and tile != '00' and self.game.getTile(target, True) != '025' and self.game.getTile(target, True) != '026':
                                if (self.pos.x // TILESIZE) > (target.x // TILESIZE) or (self.pos.x // TILESIZE) < (target.x // TILESIZE) or (self.pos.y // TILESIZE) > (target.y // TILESIZE) or (self.pos.y // TILESIZE) < (target.y // TILESIZE):
                                    self.hotbar.substractItem(currentItem)
                                    #infos = self.game.textureCoordinate.get(itemAssign[1]) #récupération des coordonées de la sous texture ainsi que son nom grâce à l'id
                                    name = f"{int(target.x // TILESIZE)}:{int(target.y // TILESIZE)}"
                                    if itemAssign[1] == '120':
                                        self.game.map.chestsData[name] = [[0, 0]] * 45
                                    elif itemAssign[1] == '117':
                                        self.game.map.furnacesData[name] = [[[0, 0]] * 3, 0, 0, 0]
                                    elif itemAssign[1] == '026':
                                        # Sleeping bag placed - spawn point will be set when player sleeps in it
                                        pass

                                    self.game.changeTile(target, itemAssign[1], False)

                                    pg.mixer.Sound.play(self.game.audioList.get(itemAssign[2])) #joue le son préchargée

                    elif itemAssign[0] == '1' or itemAssign[0] == '2' or itemAssign[0] == '3':
                        if distance <= MELEEREACH:
                            for mob in self.game.mobs:
                                if mob.rect.collidepoint(target.x, target.y):
                                    mob.takeDamage(int(itemAssign[1]))
                                    pg.mixer.Sound.play(self.game.audioList.get('blade_hit')) #joue le son préchargée
                                    break

                            if itemAssign[0] == '1':
                                if tile == '1p' or tile == '116':
                                    pg.mixer.Sound.play(self.game.audioList.get(itemAssign[4])) #joue le son préchargée
                                    if self.harvest_clicks % int(itemAssign[2]) == 0:
                                        if randint(0, 16) == 0:
                                            self.hotbar.addItem(26, 1)
                                        else:
                                            self.hotbar.addItem(10, 1)
                                        self.breakBlock(tile, 1, cell_infos[6], target)
                                    self.harvest_clicks += 1
                                elif tile != '.': #si case n'est pas vide
                                    if cell_infos[4] == 2 or (cell_infos[4] == 3 and (currentItem[0] == 14 or currentItem[0] == 15)):
                                        self.breakBlock(tile, int(itemAssign[3]), cell_infos[6], target)
                                        pg.mixer.Sound.play(self.game.audioList.get(itemAssign[4])) #joue le son préchargée

                            elif itemAssign[0] == '2':
                                if tile == '1d' or tile == '1e' or tile == '1f' or tile == '111' or tile == '114':
                                    pg.mixer.Sound.play(self.game.audioList.get(itemAssign[4])) #joue le son préchargée
                                    if self.harvest_clicks % int(itemAssign[2]) == 0:
                                        self.hotbar.addItem(4, 1)
                                        self.breakBlock(tile, 1, cell_infos[6], target)
                                    self.harvest_clicks += 1
                                elif tile != '.': #si case n'est pas vide
                                    if cell_infos[4] == 1:
                                        self.breakBlock(tile, int(itemAssign[3]), cell_infos[6], target)
                                        pg.mixer.Sound.play(self.game.audioList.get(itemAssign[4])) #joue le son préchargée

                    elif itemAssign[0] == '4':
                        if tile[0] == '0' and tile != '00':
                            self.hotbar.substractItem(currentItem)
                            Mob(self.game, target.x // TILESIZE, target.y // TILESIZE, int(itemAssign[1]))

                else:
                    if distance <= MELEEREACH:
                        for mob in self.game.mobs:
                            if mob.rect.collidepoint(target.x, target.y):
                                mob.takeDamage(1)
                                pg.mixer.Sound.play(self.game.audioList.get('punch')) #joue le son préchargée
                                break

                        if tile == '1d' or tile == '1e' or tile == '1f' or tile == '111' or tile == '114':
                            pg.mixer.Sound.play(self.game.audioList.get('axe_harvest')) #joue le son préchargée
                            if self.harvest_clicks % 10 == 0:
                                self.hotbar.addItem(4, 1)
                            self.harvest_clicks += 1
                        elif tile != '.': #si case n'est pas vide
                            if cell_infos[4] == 1:
                                self.breakBlock(tile, 2, cell_infos[6], target)
                                pg.mixer.Sound.play(self.game.audioList.get('axe_harvest')) #joue le son préchargée

    def breakBlock(self, tile, damage, item, target):
        if tile[0] == '1':
            for layer1_obj in self.game.Layer1:
                if layer1_obj.rect.collidepoint(target.x, target.y) and layer1_obj.health != -1:
                    if layer1_obj.health > 0:
                        layer1_obj.health -= damage
                        if layer1_obj.health < 0:
                            layer1_obj.health = 0
                    else:
                        if item[0] != 0:
                            self.hotbar.addItem(item[0], item[1])

                        if tile == '120':
                            chestId = f"{int(target.x // TILESIZE)}:{int(target.y // TILESIZE)}"
                            chest = self.game.map.chestsData.get(chestId)
                            if chest:
                                for _item in chest:
                                    if _item[0] != 0 and _item[1] != 0:
                                        FloatingItem(self.game, target.x - 16 - uniform(-16, 16), target.y - 16 - uniform(-16, 16), _item)


                        layer1_obj.kill()
                        self.game.changeTile(target, tile, True)
                    #pg.mixer.Sound.play(self.game.audioList.get('axe_harvest')) #joue le son préchargée
                    break
        elif tile[0] == '0':
            for ground in self.game.grounds:
                if ground.rect.collidepoint(target.x, target.y) and ground.health != -1:
                    if ground.health > 0:
                        ground.health -= damage
                        if ground.health < 0:
                            ground.health = 0
                    else:
                        if item[0] != 0:
                            self.hotbar.addItem(item[0], item[1])

                        ground.kill()
                        self.game.changeTile(target, tile, True)
                    #pg.mixer.Sound.play(self.game.audioList.get('axe_harvest')) #joue le son préchargée
                    break

    def die(self):
        self.game.player.dead = True
        self.game.isGamePaused = True
        pg.mouse.set_visible(True)

        for i, item in enumerate(self.hotbar.itemList):
            if item[0] != 0 and item[1] != 0:
                FloatingItem(self.game, self.pos.x - 16 - uniform(-24, 24), self.pos.y - 16 - uniform(-24, 24), item)
            self.hotbar.itemList[i] = [0, 0]
        
        self.hotbar.updateSelector(0)

        self.game.save()

    def respawn(self):
        self.game.player.dead = False
        self.game.isGamePaused = False
        pg.mouse.set_visible(False)

        # spawnPoint is already in pixel coordinates, use directly
        self.pos = vec(self.game.spawnPoint.x, self.game.spawnPoint.y)  # Create a COPY, don't share the same object!

        self.health = self.lifebar.maxHealth
        self.lifebar.updateHealth(self.health)
        self.lifebar.updateSurface()