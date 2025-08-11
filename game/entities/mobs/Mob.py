import math
from math import atan2, degrees, pi
from random import randint, randrange
import pygame as pg

from game.entities.FloatingItem import FloatingItem
from game.entities.Projectile import Projectile
vec = pg.math.Vector2
from game.config.settings import ANIMATE_SPEED_DIVIDER, CHUNKSIZE, FIRE_RATE, MELEEREACH, MOB_WALK_SPEED, PLAYER_DETECTION_RADIUS, PROJECTILE_OFFSET, TILESIZE

from pathfinding.core.diagonal_movement import DiagonalMovement
from pathfinding.core.grid import Grid
from pathfinding.finder.a_star import AStarFinder

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
                if int(self.path[self.i].x) > nx:
                    self.pathdirection = 'r'
                elif int(self.path[self.i].x) < nx:
                    self.pathdirection = 'l'
                elif int(self.path[self.i].y) < ny:
                    self.pathdirection = 'u'
                elif int(self.path[self.i].y) > ny:
                    self.pathdirection = 'b'

            isDone = False
            if self.pathdirection == 'r':
                if nx * TILESIZE < int(self.path[self.i].x)*TILESIZE:
                    self.vel.x = MOB_WALK_SPEED
                else:
                    self.pos.x = int(self.currentPathfind[0].x + self.path[self.i].x)*TILESIZE
                    isDone = True
            elif self.pathdirection == 'l':
                if nx * TILESIZE > int(self.path[self.i].x)*TILESIZE:
                    self.vel.x = -MOB_WALK_SPEED
                else:
                    self.pos.x = int(self.currentPathfind[0].x + self.path[self.i].x)*TILESIZE
                    isDone = True
            elif self.pathdirection == 'u':
                if ny * TILESIZE > int(self.path[self.i].y)*TILESIZE:
                    self.vel.y = -MOB_WALK_SPEED
                else:
                    self.pos.y = int(self.currentPathfind[0].y + self.path[self.i].y)*TILESIZE
                    isDone = True
            elif self.pathdirection == 'b':
                if ny * TILESIZE < int(self.path[self.i].y)*TILESIZE:
                    self.vel.y = MOB_WALK_SPEED
                else:
                    self.pos.y = int(self.currentPathfind[0].y + self.path[self.i].y)*TILESIZE
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