import pygame as pg
vec = pg.math.Vector2

#couleurs
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
DARKGREY = (40, 40, 40)
LIGHTGREY = (100, 100, 100)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
YELLOW = (255, 255, 0)

#parametres du jeu
WIDTH = 24*32  # 16 * 64 - 32 * 32 - 64 * 16 largeur de la fenetre prevue par rapport au format de textures
HEIGHT = 16*32 # 16 * 48 - 32 * 24 - 64 * 12 longueur de la fenetre prevue par rapport au format de textures
FPS = 60 #images par secondes
TITLE = "Pycraft" # titre du jeu
SAVE_DELAY = 20 * 1000
ITEM_DESPAWN_TIME = 4 * 60 * 1000

TILESIZE = 32 #taille en px du format de textures
GRIDWIDTH = WIDTH / TILESIZE #largeur de la grille affichée
GRIDHEIGHT = HEIGHT / TILESIZE #longeur de la grille affichée

MELTING_SPEED = 2500

MIN_NIGHT_SHADE = 40
DAY_LENGTH = 15 * 60 * 1000 #*96 --> 24h
SHADE_SPEED = 200

MAX_FRIENDLY_MOBS = 4
MAX_HOSTILE_MOBS = 6

#parametres relatifs au joueur
WALK_SPEED = 5*TILESIZE #vitesse de déplacement sur terre
WATER_SPEED_DIVIDER = 2.5 #vitesse de déplacement dans l'eau
ANIMATE_SPEED_DIVIDER = 5.5 #diviseur permettant de réguler la vitesse d'animation
PLAYER_SPRITE = "playerSprite.png" #chemin d'acces relatif à la fiche image du personnage
REGENSPEED = 500
MELEEREACH = 3*32
STACK = 64
HOTBAR_SLOTS = 9
INVENTORY_SLOTS = 25
TOTAL_SLOTS = HOTBAR_SLOTS + INVENTORY_SLOTS

#parametres relatifs au projectiles
PROJECTILE_SPEED = 7*TILESIZE
PROJECTILE_LIFETIME = 3 * 1000
FIRE_RATE = 750
PROJECTILE_OFFSET = vec(16, 16)
SPREAD = 5

#parametres relatifs au mobs
PLAYER_DETECTION_RADIUS = 10*TILESIZE #rayon de detection de joueur en pixel
MOB_WALK_SPEED = 3*TILESIZE #vitesse de déplacement des personnages non joueur

#parametres relatifs à la génération procedurale
CHUNKSIZE = 4
CHUNKTILESIZE = CHUNKSIZE * TILESIZE
CHUNKRENDERX = 4 #5
CHUNKRENDERY = 3 #4

TERRAIN_OCTAVE = 2
TERRAIN_SCALE = 60

BIOME_OCTAVE = 1
BIOME_SCALE = 120
