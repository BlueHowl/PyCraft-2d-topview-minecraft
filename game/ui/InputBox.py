import pygame as pg

from game.config.settings import BLACK, WHITE, WIDTH

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
