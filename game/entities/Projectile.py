from random import uniform
import pygame as pg
vec = pg.math.Vector2

from game.config.settings import CHUNKSIZE, PROJECTILE_LIFETIME, PROJECTILE_SPEED, SPREAD, TILESIZE

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
