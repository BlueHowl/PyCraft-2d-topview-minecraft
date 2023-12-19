import pygame as pg
from settings import *
vec = pg.math.Vector2
from random import *
import math
from math import atan2, degrees, pi
import json
import time
from datetime import datetime
import os

from pathfinding.core.diagonal_movement import DiagonalMovement
from pathfinding.core.grid import Grid
from pathfinding.finder.a_star import AStarFinder

class Player(pg.sprite.Sprite): #classe du joueur
    def __init__(self, game, x, y, lws):
        self.groups = game.all_sprites, game.moving_sprites, game.players #définitions de la liste de groupes de textures
        pg.sprite.Sprite.__init__(self, self.groups) #définitions du joueur dans les groupes de textures
        self.game = game #récupération de l'instance de la classe principale du jeu
        self.image = pg.Surface((TILESIZE, TILESIZE), pg.SRCALPHA, 32) #création d'un surface transparente (32*32)
        #self.image.blit(game.palyer_sprite.subsurface((1*TILESIZE, 0*TILESIZE, TILESIZE, TILESIZE)), (0, 0))
        self.rect = self.image.get_rect() #assignation de la variable rect
        self.vel = vec(0, 0) #assignation de la variable vel(velocité) par un vecteur 2d nul
        self.pos = vec(x, y) #assignation de la variable pos(position) par un vecteur 2d au positions

        self.tilepos = vec(int(self.pos.x / TILESIZE), int(self.pos.y / TILESIZE))
        self.chunkpos = self.tilepos * CHUNKSIZE

        self.health = int(self.game.map.levelSavedData[0].split(':')[3]) #PLAYER_MAXLIFE #définition de la variable health à PLAYER_MAXLIFE
        #self.maxHealth = PLAYER_MAXLIFE #définition de la variable maxHealth à PLAYER_MAXLIFE

        self.forwardIdle = game.palyer_sprite.subsurface((0*TILESIZE, 0*TILESIZE, TILESIZE, TILESIZE)).copy() #définition de la texture au repos vers l'avant
        self.backwardIdle = game.palyer_sprite.subsurface((0*TILESIZE, 1*TILESIZE, TILESIZE, TILESIZE)).copy() #définition de la texture au repos vers l'arrière
        self.leftIdle = game.palyer_sprite.subsurface((0*TILESIZE, 2*TILESIZE, TILESIZE, TILESIZE)).copy() #définition de la texture au repos vers la gauche
        self.rightIdle = game.palyer_sprite.subsurface((0*TILESIZE, 3*TILESIZE, TILESIZE, TILESIZE)).copy() #définition de la texture au repos vers la droite

        self.walkForward = [game.palyer_sprite.subsurface((1*TILESIZE, 1*TILESIZE, TILESIZE, TILESIZE)).copy(), game.palyer_sprite.subsurface((2*TILESIZE, 1*TILESIZE, TILESIZE, TILESIZE)).copy()] #définition de la liste de texture de marche avant
        self.walkBackward = [game.palyer_sprite.subsurface((1*TILESIZE, 0*TILESIZE, TILESIZE, TILESIZE)).copy(), game.palyer_sprite.subsurface((2*TILESIZE, 0*TILESIZE, TILESIZE, TILESIZE)).copy()] #définition de la liste de texture de marche arrière
        self.walkLeft = [game.palyer_sprite.subsurface((1*TILESIZE, 2*TILESIZE, TILESIZE, TILESIZE)).copy(), game.palyer_sprite.subsurface((2*TILESIZE, 2*TILESIZE, TILESIZE, TILESIZE))] #définition de la liste de texture de marche à gauche
        self.walkRight = [game.palyer_sprite.subsurface((1*TILESIZE, 3*TILESIZE, TILESIZE, TILESIZE)).copy(), game.palyer_sprite.subsurface((2*TILESIZE, 3*TILESIZE, TILESIZE, TILESIZE)).copy()] #définition de la liste de texture de marche à droite

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
                                        self.game.spawnPoint = target // 32

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

        self.pos = self.game.spawnPoint * TILESIZE

        self.health = self.lifebar.maxHealth
        self.lifebar.updateHealth(self.health)
        self.lifebar.updateSurface()

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

class Ground(pg.sprite.Sprite): #classe ground
    def __init__(self, game, x, y, tile, health, name):
        self.groups = game.all_sprites, game.grounds #définitions de la liste de groupes de textures
        pg.sprite.Sprite.__init__(self, self.groups) #définitions du joueur dans les groupes de textures
        self.name = name #récupération de la variable name
        self.health = health
        self.image = pg.Surface((TILESIZE, TILESIZE), pg.SRCALPHA, 32) #création d'une surface (32*32)
        #self.image.fill(GREEN)
        self.image.blit(tile, [0, 0]) #application de la texture sur la surface
        self.rect = self.image.get_rect() #assignation de la variable rect
        self.x = x #définition de la variable x
        self.y = y #définition de la variable y
        self.rect.x = x * TILESIZE #application de la position x de la surface
        self.rect.y = y * TILESIZE #application de la position y de la surface

        self.chunkpos = vec(math.floor(x / CHUNKSIZE), math.floor(y / CHUNKSIZE))
        self.chunkrect = pg.Rect(self.rect.x, self.rect.y, CHUNKTILESIZE, CHUNKTILESIZE)

class Layer1_objs(pg.sprite.Sprite):
    def __init__(self, game, x, y, tile, health, name):
        self.groups = game.all_sprites, game.Layer1, game.player_collisions;
        pg.sprite.Sprite.__init__(self, self.groups)
        self.name = name
        self.health = health
        #self.game = game
        self.image = pg.Surface((TILESIZE, TILESIZE), pg.SRCALPHA, 32)
        self.image.blit(tile, [0, 0])
        self.rect = self.image.get_rect()
        self.x = x
        self.y = y
        self.rect.x = x * TILESIZE
        self.rect.y = y * TILESIZE

        self.chunkpos = vec(math.floor(x / CHUNKSIZE), math.floor(y / CHUNKSIZE))
        self.chunkrect = pg.Rect(self.rect.x, self.rect.y, CHUNKTILESIZE, CHUNKTILESIZE)

class TextObject(pg.sprite.Sprite):
    def __init__(self, game, x, y, sizeX, sizeY, text, clearMode):
        self.groups = game.all_sprites, game.gui
        pg.sprite.Sprite.__init__(self, self.groups)
        self.game = game
        self.text = text
        self.image = pg.Surface((sizeX, sizeY))

        self.image.fill(WHITE)

        self.image.blit(self.game.font_32.render(text[0], True, BLACK), [5, 10])
        if len(text) > 1:
            self.image.blit(self.game.font_32.render(text[1], True, BLACK), [5, 50])

        if len(text) > 2:
            self.image.blit(pg.transform.rotate(self.game.font_32.render('^', True, BLACK), 180), [sizeX - 24, -8])
        elif len(text) <= 2:
            self.image.blit(self.game.font_32.render('x', True, BLACK), [sizeX - 24, 0])

        self.i = 2

        self.rect = self.image.get_rect()

        self.x = x
        self.y = y

        self.rect.x = x
        self.rect.y = y

        if clearMode:
            self.delete()

    def nextLine(self):
        self.image.fill(WHITE)
        self.image.blit(self.game.font_32.render(self.text[self.i], True, BLACK), [5, 10])
        if len(self.text) > self.i + 1:
            self.image.blit(self.game.font_32.render(self.text[self.i + 1], True, BLACK), [5, 50])

        if len(self.text) > self.i + 2:
            self.image.blit(pg.transform.rotate(self.game.font_32.render('^', True, BLACK), 180), [WIDTH - 24, -8])
        elif len(self.text) <= self.i + 2:
            self.image.blit(self.game.font_32.render('x', True, BLACK), [WIDTH - 24, 0])

        self.i += 2

    def delete(self):
        self.kill()

class Mob(pg.sprite.Sprite):
    def __init__(self, game, x, y, mobId):
        self.groups = game.all_sprites, game.moving_sprites, game.player_collisions, game.mobs
        pg.sprite.Sprite.__init__(self, self.groups)
        self.game = game
        self.name = game.mobList[mobId][6]
        #self.autoPath = ['w=2000']
        self.currentMove = (0, 250)
        self.hasCollided = False

        self.isEnemy = game.mobList[mobId][2]
        if self.isEnemy == 1:
            self.game.hostile_mobs_amount += 1
        else:
            self.game.friendly_mobs_amount += 1

        self.droppedItem = game.mobList[mobId][1]
        self.health = game.mobList[mobId][5]
        self.Attacktype = game.mobList[mobId][3]
        self.stopDistance = game.mobList[mobId][4]
        self.path = []
        self.image = pg.Surface((TILESIZE, TILESIZE), pg.SRCALPHA, 32)
        #self.image.blit(game.palyer_sprite.subsurface((1*TILESIZE, 0*TILESIZE, TILESIZE, TILESIZE)), (0, 0))
        self.rect = self.image.get_rect()
        self.vel = vec(0, 0)
        self.pos = vec(x * TILESIZE, y * TILESIZE) #* TILESIZE

        self.tilepos = vec(int(self.pos.x / TILESIZE), int(self.pos.y / TILESIZE))
        self.chunkpos = self.tilepos * CHUNKSIZE

        self.currentPathfind = []

        self.canMove = True

        self.targetPlayer = False
        self.hasTarget = False
        self.pathdirection = ''

        self.lastPlayerHit = self.game.now
        self.isHit = False

        self.last_attack = self.game.now

        self.lastWalkStatement = 1

        self.i = 0
        self.startPos = (x * TILESIZE, y * TILESIZE)
        self.lastPos = self.startPos
        self.lastTemp = self.game.now

        self.staticForwardIdle = game.mobList[mobId][0].subsurface((0*TILESIZE, 0*TILESIZE, TILESIZE, TILESIZE)).copy()
        self.staticBackwardIdle = game.mobList[mobId][0].subsurface((0*TILESIZE, 1*TILESIZE, TILESIZE, TILESIZE)).copy()
        self.staticLeftIdle = game.mobList[mobId][0].subsurface((0*TILESIZE, 2*TILESIZE, TILESIZE, TILESIZE)).copy()
        self.staticRightIdle = game.mobList[mobId][0].subsurface((0*TILESIZE, 3*TILESIZE, TILESIZE, TILESIZE)).copy()

        self.staticWalkForward = [game.mobList[mobId][0].subsurface((1*TILESIZE, 1*TILESIZE, TILESIZE, TILESIZE)).copy(), game.mobList[mobId][0].subsurface((3*TILESIZE, 1*TILESIZE, TILESIZE, TILESIZE)).copy()]
        self.staticWalkBackward = [game.mobList[mobId][0].subsurface((1*TILESIZE, 0*TILESIZE, TILESIZE, TILESIZE)).copy(), game.mobList[mobId][0].subsurface((3*TILESIZE, 0*TILESIZE, TILESIZE, TILESIZE)).copy()]
        self.staticWalkLeft = [game.mobList[mobId][0].subsurface((1*TILESIZE, 2*TILESIZE, TILESIZE, TILESIZE)).copy(), game.mobList[mobId][0].subsurface((3*TILESIZE, 2*TILESIZE, TILESIZE, TILESIZE))]
        self.staticWalkRight = [game.mobList[mobId][0].subsurface((1*TILESIZE, 3*TILESIZE, TILESIZE, TILESIZE)).copy(), game.mobList[mobId][0].subsurface((3*TILESIZE, 3*TILESIZE, TILESIZE, TILESIZE)).copy()]

        self.forwardIdle = self.staticForwardIdle
        self.backwardIdle = self.staticBackwardIdle
        self.leftIdle = self.staticLeftIdle
        self.rightIdle = self.staticRightIdle

        self.walkForward = [self.staticWalkForward[0], self.staticWalkForward[1]]
        self.walkBackward = [self.staticWalkBackward[0], self.staticWalkBackward[1]]
        self.walkLeft = [self.staticWalkLeft[0], self.staticWalkLeft[1]]
        self.walkRight = [self.staticWalkRight[0], self.staticWalkRight[1]]

    def collide_with_walls(self, dir):
        if dir == 'x':
            hits = pg.sprite.spritecollide(self, self.game.players, False)
            if hits:
                if self.vel.x > 0:
                    self.pos.x = hits[0].rect.left - self.rect.width
                if self.vel.x < 0:
                    self.pos.x = hits[0].rect.right
                self.vel.x = 0
                self.rect.x = self.pos.x

                self.hasCollided = True

            hits = pg.sprite.spritecollide(self, self.game.Layer1, False)
            if hits:
                if self.vel.x > 0:
                    self.pos.x = hits[0].rect.left - self.rect.width
                if self.vel.x < 0:
                    self.pos.x = hits[0].rect.right
                self.vel.x = 0
                self.rect.x = self.pos.x

                self.hasCollided = True

            hits = pg.sprite.spritecollide(self, self.game.grounds, False)
            if hits:
                if hits[0].name == 'water':
                    if self.vel.x > 0:
                        self.pos.x = hits[0].rect.left - self.rect.width
                    if self.vel.x < 0:
                        self.pos.x = hits[0].rect.right
                    self.vel.x = 0
                    self.rect.x = self.pos.x

                    self.hasCollided = True

        if dir == 'y':
            hits = pg.sprite.spritecollide(self, self.game.players, False)
            if hits:
                if self.vel.y > 0:
                    self.pos.y = hits[0].rect.top - self.rect.height
                if self.vel.y < 0:
                    self.pos.y = hits[0].rect.bottom
                self.vel.y = 0
                self.rect.y = self.pos.y

                self.hasCollided = True

            hits = pg.sprite.spritecollide(self, self.game.Layer1, False)
            if hits:
                if self.vel.y > 0:
                    self.pos.y = hits[0].rect.top - self.rect.height
                if self.vel.y < 0:
                    self.pos.y = hits[0].rect.bottom
                self.vel.y = 0
                self.rect.y = self.pos.y

                self.hasCollided = True

            hits = pg.sprite.spritecollide(self, self.game.grounds, False)
            if hits:
                if hits[0].name == 'water':
                    if self.vel.y > 0:
                        self.pos.y = hits[0].rect.top - self.rect.height
                    if self.vel.y < 0:
                        self.pos.y = hits[0].rect.bottom
                    self.vel.y = 0
                    self.rect.y = self.pos.y

                    self.hasCollided = True

    def update(self):
        if self.canMove:
            self.wander()

            if self.isEnemy == 1:
                self.target(self.game.player)

        self.pos += self.vel * self.game.dt
        self.rect.x = self.pos.x
        self.collide_with_walls('x')
        self.rect.y = self.pos.y
        self.collide_with_walls('y')

        self.tilepos = vec(int(self.pos.x / TILESIZE), int(self.pos.y / TILESIZE))
        self.chunkpos = vec(int(self.tilepos.x / CHUNKSIZE), int(self.tilepos.y / CHUNKSIZE))

        if self.isHit:
            if self.game.now >= self.lastPlayerHit + 50:
                self.changeAllSpriteColor((0, 0, 0), 255)
                self.isHit = False

        self.animate()

    def animate(self):
        self.image = pg.Surface((TILESIZE, TILESIZE), pg.SRCALPHA, 32)

        if self.vel.x < 0:
            self.image.blit(self.walkLeft[int(self.game.now // MOB_WALK_SPEED * ANIMATE_SPEED_DIVIDER) % len(self.walkLeft)], (0, 0))
            self.lastWalkStatement = 2
        elif self.vel.x > 0:
            self.image.blit(self.walkRight[int(self.game.now // MOB_WALK_SPEED * ANIMATE_SPEED_DIVIDER) % len(self.walkRight)], (0, 0))
            self.lastWalkStatement = 3
        elif self.vel.y < 0:
            self.image.blit(self.walkForward[int(self.game.now // MOB_WALK_SPEED * ANIMATE_SPEED_DIVIDER) % len(self.walkForward)], (0, 0))
            self.lastWalkStatement = 0
        elif self.vel.y > 0:
            self.image.blit(self.walkBackward[int(self.game.now // MOB_WALK_SPEED * ANIMATE_SPEED_DIVIDER) % len(self.walkBackward)], (0, 0))
            self.lastWalkStatement = 1
        else:
            if self.lastWalkStatement == 0:
                self.image.blit(self.backwardIdle, (0, -abs(math.sin(self.game.now // (8*60) )) * 3))
            elif self.lastWalkStatement == 1:
                self.image.blit(self.forwardIdle, (0, -abs(math.sin(self.game.now // (8*60) )) * 2))
            elif self.lastWalkStatement == 2:
                self.image.blit(self.leftIdle, (0, -abs(math.sin(self.game.now // (8*60) )) * 2))
            elif self.lastWalkStatement == 3:
                self.image.blit(self.rightIdle, (0, -abs(math.sin(self.game.now // (8*60) )) * 2))

    def wander(self):
        self.vel = vec(0, 0)

        isDone = False

        if self.targetPlayer:
            return None

        if self.currentMove[0] == 1:
            if self.pos.x < self.lastPos[0] + int(self.currentMove[1])*32:
                self.vel.x = MOB_WALK_SPEED
            else:
                self.pos.x = self.lastPos[0] + int(self.currentMove[1])*32
                isDone = True
        elif self.currentMove[0] == 2:
            if self.pos.x > self.lastPos[0] - int(self.currentMove[1])*32:
                self.vel.x = -MOB_WALK_SPEED
            else:
                self.pos.x = self.lastPos[0] - int(self.currentMove[1])*32
                isDone = True
        elif self.currentMove[0] == 3:
            if self.pos.y > self.lastPos[1] - int(self.currentMove[1])*32:
                self.vel.y = -MOB_WALK_SPEED
            else:
                self.pos.y = self.lastPos[1] - int(self.currentMove[1])*32
                isDone = True
        elif self.currentMove[0] == 4:
            if self.pos.y < self.lastPos[1] + int(self.currentMove[1])*32:
                self.vel.y = MOB_WALK_SPEED
            else:
                self.pos.y = self.lastPos[1] + int(self.currentMove[1])*32
                isDone = True
        elif self.currentMove[0] == 0:
            if self.game.now >= self.lastTemp + int(self.currentMove[1]):
                isDone = True

        if isDone or self.hasCollided:
            self.hasCollided = False
            self.lastPos = (self.pos.x, self.pos.y)

            instruction = randint(0, 4)
            if instruction == 0:
                self.currentMove = (instruction, randint(500, 3000))
            else:
                self.currentMove = (instruction, randint(1, 5))

            self.lastTemp = self.game.now

    def target(self, player):
        distance = math.hypot(self.pos.x  - player.pos.x, self.pos.y - player.pos.y)
        if distance <= PLAYER_DETECTION_RADIUS:
            self.targetPlayer = True
            self.hasTarget = True
        elif self.Attacktype != 0:
            self.path = []
            self.hasTarget = True
        else:
            self.hasTarget = False

        if self.targetPlayer and self.hasTarget and len(self.path) == 0:

            if self.game.area:
                #https://pypi.org/project/pathfinding/
                self.currentPathfind = self.game.getCurrentPathfind()

                grid = Grid(matrix=self.currentPathfind[1])

                #print(f'{int((self.pos.x // 32) - self.game.pathfind[0].x)} : {int((self.pos.y // 32) - self.game.pathfind[0].y)} -> {int((player.pos.x // 32) - self.game.pathfind[0].x)} : {int((player.pos.y // 32) - self.game.pathfind[0].y)}')

                startX = max(min(int((self.pos.x // TILESIZE) - (self.currentPathfind[0].x)), len(self.currentPathfind[1][0]) - 1), 0)
                startY = max(min(int((self.pos.y // TILESIZE) - (self.currentPathfind[0].y)), len(self.currentPathfind[1]) - 1), 0)

                start = grid.node(startX, startY)
                end = grid.node(int((player.pos.x // TILESIZE) - (self.currentPathfind[0].x)), int((player.pos.y // TILESIZE) - (self.currentPathfind[0].y)))

                finder = AStarFinder(diagonal_movement=DiagonalMovement.never)
                self.path, runs = finder.find_path(start, end, grid)
                self.i = 1

        elif len(self.path) > 0 and self.i < len(self.path) - self.stopDistance:
            self.vel = vec(0, 0)
            nx = int((self.pos.x // TILESIZE) - (self.currentPathfind[0].x))
            ny = int((self.pos.y // TILESIZE) - (self.currentPathfind[0].y))
            if self.pathdirection == '':
                if int(self.path[self.i][0]) > nx:
                    self.pathdirection = 'r'
                elif int(self.path[self.i][0]) < nx:
                    self.pathdirection = 'l'
                elif int(self.path[self.i][1]) < ny:
                    self.pathdirection = 'u'
                elif int(self.path[self.i][1]) > ny:
                    self.pathdirection = 'b'

            isDone = False
            if self.pathdirection == 'r':
                if nx * TILESIZE < int(self.path[self.i][0])*TILESIZE:
                    self.vel.x = MOB_WALK_SPEED
                else:
                    self.pos.x = int(self.currentPathfind[0].x + self.path[self.i][0])*TILESIZE
                    isDone = True
            elif self.pathdirection == 'l':
                if nx * TILESIZE > int(self.path[self.i][0])*TILESIZE:
                    self.vel.x = -MOB_WALK_SPEED
                else:
                    self.pos.x = int(self.currentPathfind[0].x + self.path[self.i][0])*TILESIZE
                    isDone = True
            elif self.pathdirection == 'u':
                if ny * TILESIZE > int(self.path[self.i][1])*TILESIZE:
                    self.vel.y = -MOB_WALK_SPEED
                else:
                    self.pos.y = int(self.currentPathfind[0].y + self.path[self.i][1])*TILESIZE
                    isDone = True
            elif self.pathdirection == 'b':
                if ny * TILESIZE < int(self.path[self.i][1])*TILESIZE:
                    self.vel.y = MOB_WALK_SPEED
                else:
                    self.pos.y = int(self.currentPathfind[0].y + self.path[self.i][1])*TILESIZE
                    isDone = True

            if isDone or self.hasCollided:
                self.i += 1
                self.pathdirection = ''
                self.lastPos = (self.pos.x, self.pos.y)

        elif self.targetPlayer and self.hasTarget and self.i > len(self.path) - self.stopDistance:
            if self.vel.x == 0 and self.vel.y == 0:
                self.attack()
        else:
            self.path = []

    def attack(self):
        if self.Attacktype == 1:
            if self.game.now - self.last_attack > FIRE_RATE:
                self.last_attack = self.game.now
                dx = self.game.player.pos.x - self.pos.x
                dy = self.game.player.pos.y - self.pos.y
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

                pg.mixer.Sound.play(self.game.audioList.get('arrow_shot')) #joue le son préchargée
                Projectile(self.game, vec(self.pos.x + 10, self.pos.y + 5) + PROJECTILE_OFFSET.rotate(-deg - 42), deg, 0, math.hypot(dx, dy), 2)
        elif self.Attacktype == 2:
            if self.game.now - self.last_attack > FIRE_RATE * 1.2:
                self.last_attack = self.game.now
                 
                distance = math.hypot(self.pos.x  - self.game.player.pos.x, self.pos.y - self.game.player.pos.y)
                if distance <= MELEEREACH:
                    if self.game.player.health > 1:
                        self.game.player.last_hit = self.game.now
                        self.game.player.health -= 3
                        lifeb = self.game.player.lifebar
                        lifeb.updateHealth(self.game.player.health)
                        lifeb.updateSurface()

                        self.game.hasPlayerStateChanged = True #autorise la sauvegarde du joueur
                    else:
                        self.game.player.die()
                    
                    pg.mixer.Sound.play(self.game.audioList.get('punch')) #joue le son préchargée

    def colorize(self, image, newColor, alpha):
        image = image.copy()
        image.fill((0, 0, 0, alpha), None, pg.BLEND_RGBA_MULT) #remise à zero des valeurs rgb
        image.fill(newColor[0:3] + (0,), None, pg.BLEND_RGBA_ADD) #ajoute la nouvelle valeur rgb
        return image

    def changeAllSpriteColor(self, newColor, alpha):
        if alpha == 255:
            self.forwardIdle = self.staticForwardIdle
            self.backwardIdle = self.staticBackwardIdle
            self.leftIdle = self.staticLeftIdle
            self.rightIdle = self.staticRightIdle

            self.walkForward = [self.staticWalkForward[0], self.staticWalkForward[1]]
            self.walkBackward = [self.staticWalkBackward[0], self.staticWalkBackward[1]]
            self.walkLeft = [self.staticWalkLeft[0], self.staticWalkLeft[1]]
            self.walkRight = [self.staticWalkRight[0], self.staticWalkRight[1]]
        else:
            self.forwardIdle = self.colorize(self.forwardIdle, newColor, alpha)
            self.backwardIdle = self.colorize(self.backwardIdle, newColor, alpha)
            self.leftIdle = self.colorize(self.leftIdle, newColor, alpha)
            self.rightIdle = self.colorize(self.rightIdle, newColor, alpha)

            for i, im in enumerate(self.walkForward):
                self.walkForward[i] = self.colorize(im, newColor, alpha)
            for i, im in enumerate(self.walkBackward):
                self.walkBackward[i] = self.colorize(im, newColor, alpha)
            for i, im in enumerate(self.walkLeft):
                self.walkLeft[i] = self.colorize(im, newColor, alpha)
            for i, im in enumerate(self.walkRight):
                self.walkRight[i] = self.colorize(im, newColor, alpha)

    def takeDamage(self, amount):
        if self.health > 1:
            self.health -= amount

            self.changeAllSpriteColor((255, 0, 0), 254)
            self.lastPlayerHit = self.game.now
            self.isHit = True
        else:
            self.die()

    def die(self):
        if self.droppedItem[0] != 0:
            FloatingItem(self.game, self.pos.x, self.pos.y, [self.droppedItem[0], randrange(1, self.droppedItem[1])])

        if self.isEnemy == 1:
            self.game.hostile_mobs_amount -= 1
        else:
            self.game.friendly_mobs_amount -= 1
        self.kill()

class Projectile(pg.sprite.Sprite):
    def __init__(self, game, pos, deg, team, distBetween, damage):
        self.groups = game.all_sprites, game.moving_sprites, game.projectiles
        pg.sprite.Sprite.__init__(self, self.groups)
        self.image = pg.Surface((16, 16), pg.SRCALPHA, 32)
        tex = pg.transform.scale(game.items_img.subsurface((1*TILESIZE, 0*TILESIZE, TILESIZE, TILESIZE)), (20, 20))
        self.image.blit(tex, (0, 0))
        self.rect = self.image.get_rect()
        self.game = game
        self.team = team
        self.damage = damage
        self.pos = pos
        self.tilepos = vec(int(self.pos.x / TILESIZE), int(self.pos.y / TILESIZE))
        self.chunkpos = self.tilepos * CHUNKSIZE

        self.rect.topleft = self.pos
        spread = uniform(-SPREAD, SPREAD)
        self.image = pg.transform.rotate(self.image, deg - 45 - spread)#+ 135
        if distBetween < 150:
            distBetween = 150
        self.vel = vec(1, 0).rotate(-deg + spread) * PROJECTILE_SPEED * (distBetween // 150)
        self.spawn_time = self.game.now

    def update(self):
        ''' auto guided
        dx = self.game.player.pos.x - self.pos.x
        dy = self.game.player.pos.y - self.pos.y
        rads = atan2(-dy,dx)
        rads %= 2*pi
        deg = degrees(rads)
        self.vel = vec(1, 0).rotate(-deg) *(PROJECTILE_SPEED / 3)
        '''

        self.pos += self.vel * self.game.dt
        self.rect.topleft = self.pos

        self.tilepos = vec(int(self.pos.x / TILESIZE), int(self.pos.y / TILESIZE))
        self.chunkpos = vec(int(self.tilepos.x / CHUNKSIZE), int(self.tilepos.y / CHUNKSIZE))

        if pg.sprite.spritecollideany(self, self.game.Layer1):
            self.kill()
        if pg.sprite.spritecollideany(self, self.game.players) and self.team == 0:
            if self.game.player.health > 1:
                self.game.player.last_hit = self.game.now
                self.game.player.health -= self.damage
                lifeb = self.game.player.lifebar
                lifeb.updateHealth(self.game.player.health)
                lifeb.updateSurface()

                self.game.hasPlayerStateChanged = True #autorise la sauvegarde du joueur
            else:
                self.game.player.die()
            self.kill()
        elif self.team == 1:
            hits = hits = pg.sprite.spritecollide(self, self.game.mobs, False)
            if len(hits) > 0:
                hits[0].takeDamage(self.damage)
                self.kill()

        if self.game.now - self.spawn_time > PROJECTILE_LIFETIME:
            self.kill()

class Menu(pg.sprite.Sprite):
    def __init__(self, game, xOffset, yOffset):
        self.groups = game.gui #game.all_sprites, game.gui
        pg.sprite.Sprite.__init__(self, self.groups)
        self.game = game
        self.gameFolder = os.path.dirname(__file__)
        self.image = pg.Surface((len(game.menuData[0]) * TILESIZE, len(game.menuData) * TILESIZE), pg.SRCALPHA, 32)

        self.Page = 0

        self.UiList = []
        self.last_Ui = 0
        self.current = []
        self.inputBoxes = []

        self.seed = str(time.time()).replace('.', '')
        self.world_name = 'World-' + str(time.time())[-5:]

        self.worlds_list = []

        wLst = os.listdir(self.gameFolder + '/saves')
        if wLst:
            for world in wLst:
                self.worlds_list.append((world, str(datetime.fromtimestamp(os.path.getmtime(self.gameFolder + '/saves/' + world))) ))

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
                txt = self.game.font_32.render('New Game', True, BLACK)
                x = (WIDTH / 2) - (txt.get_width() / 2)
                self.image.blit(txt, (x, 200))
                self.UiList.append((x, 200, txt.get_width(), txt.get_height(), 1))

                txt = self.game.font_32.render('Load Game', True, BLACK)
                x = (WIDTH / 2) - (txt.get_width() / 2)
                self.image.blit(txt, (x, 250))
                self.UiList.append((x, 250, txt.get_width(), txt.get_height(), 2))

                txt = self.game.font_32.render('Settings', True, BLACK)
                x = (WIDTH / 2) - (txt.get_width() / 2)
                self.image.blit(txt, (x, 300))
                self.UiList.append((x, 300, txt.get_width(), txt.get_height(), 3))
            elif page == 1:
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
                        pg.mixer.Sound.play(self.game.audioList.get('menu_hover')) #joue le son préchargée
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
                    x = str(randint(-9999, 9999))
                    y = str(randint(-9999, 9999))
                    playerState = x + ':' + y + ':0:20:20'
                    txtSave = playerState + '\n' + str(TOTAL_SLOTS * [[0, 0]]) + '\n' + str(abs(hash(self.seed))) + '\n' + x + ':' + y + '\n0\n255'

                    os.mkdir(self.gameFolder + '/saves/' + self.world_name)

                    with open(self.gameFolder + '/saves/' + self.world_name + '/level.save', 'w') as f: #ouverture du document pathfinding.map en écriture
                        f.write(txtSave)

                    with open(self.gameFolder + '/saves/' + self.world_name + '/signs.txt', 'w') as f:
                        f.write('{}')
                    with open(self.gameFolder + '/saves/' + self.world_name + '/mobs.txt', 'w') as f:
                        f.write('{}')
                    with open(self.gameFolder + '/saves/' + self.world_name + '/floatingItems.txt', 'w') as f:
                        f.write('[]')
                    with open(self.gameFolder + '/saves/' + self.world_name + '/chests.txt', 'w') as f:
                        f.write('{}')
                    with open(self.gameFolder + '/saves/' + self.world_name + '/furnaces.txt', 'w') as f:
                        f.write('{}')

                    self.game.worldName = self.world_name
                    self.game.playing = True
                    self.kill()

            pg.mixer.Sound.play(self.game.audioList.get('menu_click')) #joue le son préchargée

    def calculateClick(self, pos, box):
        if pos[0] > box[0] and pos[0] < box[0] + box[2] and pos[1] > box[1] and pos[1] < box[1] + box[3]:
            return True
        else:
            return False

class InputBox:
    def __init__(self, game, x, y, w, h, text='', limit=40, expandTwoWay=False):
        self.rect = pg.Rect(x, y, w, h)
        self.w = w
        self.game = game
        self.color = BLACK
        self.text = text
        self.limit = limit
        self.expandTwoWay = expandTwoWay
        self.txt_surface = self.game.font_32.render(text, True, self.color)
        self.active = False

    def handle_event(self, event):
        if event.type == pg.MOUSEBUTTONDOWN:
            # If the user clicked on the input_box rect.
            if self.rect.collidepoint(event.pos):
                # Toggle the active variable.
                self.active = not self.active
                pg.mixer.Sound.play(self.game.audioList.get('menu_hover')) #joue le son préchargée
            else:
                self.active = False
            # Change the current color of the input box.
            self.color = WHITE if self.active else BLACK
        if event.type == pg.KEYDOWN:
            self.game.isGamePaused = self.active
            if self.active:
                if event.key == pg.K_RETURN:
                    pass
                elif event.key == pg.K_BACKSPACE:
                    self.text = self.text[:-1]
                    pg.mixer.Sound.play(self.game.audioList.get('menu_click')) #joue le son préchargée
                else:
                    if len(self.text) < self.limit:
                        self.text += event.unicode
                        pg.mixer.Sound.play(self.game.audioList.get('menu_click')) #joue le son préchargée
                # Re-render the text.
                self.txt_surface = self.game.font_32.render(self.text, True, self.color)

    def update(self):
        # Resize the box if the text is too long.
        width = max(self.w, self.txt_surface.get_width()+10)
        if self.expandTwoWay:
            self.rect.x = (WIDTH / 2) - (width / 2)
        self.rect.w = width

    def draw(self, screen):
        # Blit the text.
        screen.blit(self.txt_surface, (self.rect.x+5, self.rect.y+5))
        # Blit the rect.
        pg.draw.rect(screen, self.color, self.rect, 2)
