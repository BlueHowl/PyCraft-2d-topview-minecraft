import pygame as pg
from game.config.settings import BLACK, WHITE, WIDTH

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