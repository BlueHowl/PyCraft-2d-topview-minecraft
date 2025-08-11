"""
Input Manager - Handles all input events and commands.
"""
import pygame as pg
import math
from random import uniform
from game.config.settings import *

vec = pg.math.Vector2


class InputManager:
    """Manages all input events and user interactions."""
    
    def __init__(self, game):
        self.game = game
        
    def handle_events(self):
        """Handle all pygame events."""
        for event in pg.event.get():
            if event.type == pg.QUIT:
                self.game.quit()

            if event.type == pg.KEYDOWN:
                self._handle_keydown(event)
            elif event.type == pg.KEYUP:
                self._handle_keyup(event)
            elif event.type == pg.MOUSEBUTTONDOWN:
                self._handle_mousedown(event)

            if self.game.input_commands:
                self.game.input_commands_txt.handle_event(event)
    
    def _handle_keydown(self, event):
        """Handle key press events."""
        if event.key == pg.K_ESCAPE:
            self._handle_escape()
        elif event.key >= pg.K_1 and event.key <= pg.K_9 and not self.game.isGamePaused:
            slot = event.key - pg.K_1
            self.game.player.hotbar.updateSelector(slot)
        elif event.key == pg.K_a and not self.game.isGamePaused:
            self._handle_drop_item(event)
        elif event.key == pg.K_e and self.game.player.vel.x == 0 and self.game.player.vel.y == 0 and not self.game.isGamePaused and not self.game.isEPressed:
            self._handle_interact()
        elif event.key == pg.K_TAB and not self.game.isTabPressed:
            self._handle_inventory_toggle()
        elif event.key == 178 and not self.game.isPowerPressed:  # Squared key
            self._handle_debug_console()
        elif self.game.input_commands and event.key == pg.K_RETURN:
            self._handle_command_execute()
    
    def _handle_keyup(self, event):
        """Handle key release events."""
        if event.key == pg.K_TAB:
            self.game.isTabPressed = False
        elif event.key == pg.K_e:
            self.game.isEPressed = False
        elif event.key == 178:
            self.game.isPowerPressed = False
    
    def _handle_mousedown(self, event):
        """Handle mouse button press events."""
        if event.button == 1:  # Left click
            if not self.game.isGamePaused:
                self.game.player.action(vec(self.game.camera.getCamClickTopLeft()[0] + self.game.mousePos[0], 
                                           self.game.camera.getCamClickTopLeft()[1] + self.game.mousePos[1]))
            elif self.game.isInventoryOpened:
                self.game.player.inventory.click(self.game.mousePos, 0)
            elif self.game.player.dead:
                self._handle_respawn_click()
        elif event.button == 3:  # Right click
            if self.game.isInventoryOpened:
                self.game.player.inventory.click(self.game.mousePos, 1)
        elif event.button == 4 and not self.game.isGamePaused:  # Scroll up
            self.game.player.hotbar.updateSelector(self.game.player.hotbar.index - 1)
        elif event.button == 5 and not self.game.isGamePaused:  # Scroll down
            self.game.player.hotbar.updateSelector(self.game.player.hotbar.index + 1)
    
    def _handle_escape(self):
        """Handle escape key press."""
        if self.game.input_commands:
            self.game.input_commands = False
            self.game.isGamePaused = False
            self.game.input_commands_txt.active = False
            self.game.input_commands_txt.color = BLACK
            pg.mouse.set_visible(False)
        elif self.game.isInventoryOpened:
            if self.game.player.inventory.craftPage == 9:
                self.game.map.furnacesData.get(self.game.lastFurnaceId)[3] = self.game.now
                self.game.player.inventory.openedFurnace = False
            self.game.isInventoryOpened = False
            self.game.player.inventory.toggleGui(False, 0)
            pg.mouse.set_visible(False)
        else:
            self.game.quit()
    
    def _handle_drop_item(self, event):
        """Handle item dropping."""
        from game.entities.FloatingItem import FloatingItem
        
        currentItem = self.game.player.hotbar.itemList[self.game.player.hotbar.index]
        itemInfos = self.game.itemTextureCoordinate.get(currentItem[0])
        keys = pg.key.get_pressed()

        dropOffset = vec(self.game.player.pos.x + uniform(-4, 4), self.game.player.pos.y + uniform(-4, 4))

        # Offset based on player direction
        if self.game.player.lastWalkStatement == 0:
            dropOffset.y -= 32
        elif self.game.player.lastWalkStatement == 1:
            dropOffset.y += 32
        elif self.game.player.lastWalkStatement == 2:
            dropOffset.x -= 32
        elif self.game.player.lastWalkStatement == 3:
            dropOffset.x += 32

        if currentItem[0] != 0:
            if keys[pg.K_LCTRL]:
                # Drop entire stack
                FloatingItem(self.game, dropOffset.x, dropOffset.y, [currentItem[0], currentItem[1]])
                currentItem[0] = 0
                currentItem[1] = 0
                self.game.player.hotbar.updateSelector(self.game.player.hotbar.index)
                self.game.play_sound('drop_item')
                self.game.hasPlayerStateChanged = True
            else:
                # Drop single item
                hasStacked = False
                if itemInfos[2] == 1:  # If item is stackable
                    for floatItem in self.game.floatingItems:
                        distance = math.hypot(floatItem.pos.x - self.game.player.pos.x, 
                                            floatItem.pos.y - self.game.player.pos.y)
                        if distance <= MELEEREACH and currentItem[0] == floatItem.item[0]:
                            if floatItem.item[1] < STACK:
                                floatItem.item[1] += 1
                                self.game.player.hotbar.substractItem(currentItem)
                                self.game.play_sound('drop_item')
                                hasStacked = True
                                self.game.hasPlayerStateChanged = True
                                break

                if not hasStacked:
                    FloatingItem(self.game, dropOffset.x, dropOffset.y, [currentItem[0], 1])
                    self.game.player.hotbar.substractItem(currentItem)
                    self.game.play_sound('drop_item')
    
    def _handle_interact(self):
        """Handle interaction (E key)."""
        self.game.isEPressed = True
        x = int((self.game.player.pos.x + 16) // TILESIZE)
        y = int((self.game.player.pos.y + 16) // TILESIZE)
        currentItem = self.game.player.hotbar.itemList[self.game.player.hotbar.index]

        # Handle consumables
        if currentItem[0] == 5 and self.game.player.health < self.game.player.lifebar.maxHealth:
            self._use_health_item(currentItem, self.game.player.lifebar.maxHealth, 'heal_bonus')
        elif currentItem[0] == 9 and self.game.player.health < self.game.player.lifebar.maxHealth:
            self._use_health_item(currentItem, min(self.game.player.health + 4, self.game.player.lifebar.maxHealth), 'heal_bonus')
        elif currentItem[0] == 6:
            self.game.player.hotbar.substractItem(currentItem)
            self.game.player.lifebar.maxHealth += 2
            self.game.player.lifebar.updateHealth(self.game.player.health)
            self.game.player.lifebar.updateSurface()
            self.game.play_sound('max_health_bonus')
        else:
            # Handle tile interactions
            self._handle_tile_interactions(x, y)
    
    def _use_health_item(self, item, new_health, sound):
        """Use a health item."""
        self.game.player.hotbar.substractItem(item)
        self.game.player.health = new_health
        self.game.player.lifebar.updateHealth(self.game.player.health)
        self.game.player.lifebar.updateSurface()
        self.game.play_sound(sound)
    
    def _handle_tile_interactions(self, x, y):
        """Handle interactions with tiles around the player."""
        directions = [
            (1, 0, 3),   # Right
            (-1, 0, 2),  # Left  
            (0, 1, 1),   # Down
            (0, -1, 0)   # Up
        ]
        
        for dx, dy, direction in directions:
            if self.game.player.lastWalkStatement == direction:
                tile = self.game.getTile(vec((x + dx) * 32, (y + dy) * 32), False)
                if tile != '.':
                    if tile == '10':  # Sign
                        self._interact_with_sign(x + dx, y + dy)
                    elif tile == '117':  # Furnace
                        self._open_furnace(x + dx, y + dy)
                    elif tile == '120':  # Chest
                        self._open_chest(x + dx, y + dy)
                    elif tile == '026':  # Bed
                        # Set spawn point to the sleeping bag location before sleeping
                        sleeping_bag_pos = vec((x + dx) * TILESIZE, (y + dy) * TILESIZE)
                        self.game.spawnPoint = sleeping_bag_pos
                        self.game.sleep()
                        # Mark that player state has changed so it gets saved
                        self.game.hasPlayerStateChanged = True
                break
    
    def _interact_with_sign(self, x, y):
        """Interact with a sign."""
        from game.ui.TextObject import TextObject
        
        for l in self.game.map.levelSignData:
            if int(l[0]) == x and int(l[1]) == y:
                txt = l[2].split('-|-')
                self.game.play_sound('menu_click')
                
                if not self.game.player.isDialog:
                    self.game.currentDialog = TextObject(
                        self.game, 
                        self.game.camera.getCamTopLeft()[0], 
                        self.game.camera.getCamTopLeft()[1] + HEIGHT - (HEIGHT / 6), 
                        WIDTH, HEIGHT, txt, False
                    )
                    self.game.player.isDialog = True
                    self.game.player.canMove = False
                else:
                    if self.game.currentDialog.i < len(txt):
                        self.game.currentDialog.nextLine()
                    else:
                        self.game.currentDialog.delete()
                        self.game.player.isDialog = False
                        self.game.player.canMove = True
                break
    
    def _open_furnace(self, x, y):
        """Open furnace interface."""
        self.game.isInventoryOpened = True
        pg.mouse.set_visible(self.game.isInventoryOpened)
        self.game.lastFurnaceId = f"{x}:{y}"
        self.game.player.inventory.toggleGui(True, 9)
    
    def _open_chest(self, x, y):
        """Open chest interface."""
        self.game.isInventoryOpened = True
        pg.mouse.set_visible(self.game.isInventoryOpened)
        self.game.lastChestId = f"{x}:{y}"
        self.game.player.inventory.toggleGui(True, 10)
    
    def _handle_inventory_toggle(self):
        """Toggle inventory."""
        self.game.isTabPressed = True
        self.game.isInventoryOpened = not self.game.isInventoryOpened
        pg.mouse.set_visible(self.game.isInventoryOpened)
        self.game.player.inventory.toggleGui(self.game.isInventoryOpened, 0)
    
    def _handle_debug_console(self):
        """Toggle debug console."""
        if not self.game.input_commands_txt.active and self.game.input_commands:
            self.game.input_commands = False
            self.game.isGamePaused = False
            self.game.input_commands_txt.active = False
            self.game.input_commands_txt.color = BLACK
        else:
            self.game.isPowerPressed = True
            self.game.input_commands = True
            self.game.input_commands_txt.txt = ''
        pg.mouse.set_visible(self.game.input_commands)
    
    def _handle_respawn_click(self):
        """Handle respawn button click."""
        if (self.game.mousePos[0] > self.game.respawn_rect[0] and 
            self.game.mousePos[0] < self.game.respawn_rect[0] + self.game.respawn_rect[2] and 
            self.game.mousePos[1] > self.game.respawn_rect[1] and 
            self.game.mousePos[1] < self.game.respawn_rect[1] + self.game.respawn_rect[3]):
            self.game.player.respawn()
    
    def _handle_command_execute(self):
        """Execute console command."""
        if self.game.input_commands_txt.active:
            command = self.game.input_commands_txt.text.lower().split(' ')
            if len(command) > 0:
                self._execute_command(command)
            self.game.input_commands_txt.text = ''
    
    def _execute_command(self, command):
        """Execute a specific command."""
        if command[0] == '/give' and len(command) > 2:
            self._cmd_give(command)
        elif command[0] == '/tp' and len(command) > 2:
            self._cmd_teleport(command)
        elif command[0] == '/speed' and len(command) > 1:
            self._cmd_speed(command)
        elif command[0] == '/regen':
            self._cmd_regen()
        elif command[0] == '/maxhealth' and len(command) > 1:
            self._cmd_maxhealth(command)
        elif command[0] == '/save':
            self.game.save()
        elif command[0] == '/hitbox':
            self._cmd_hitbox(command)
        elif command[0] == '/spawnpoint' and len(command) > 2:
            self._cmd_spawnpoint(command)
        elif command[0] == '/time' and len(command) > 2:
            self._cmd_time(command)
        elif command[0] == '/spawn' and len(command) > 3:
            self._cmd_spawn(command)
        elif command[0] == '/clear' and len(command) > 1:
            self._cmd_clear(command)
        elif command[0] == '/kill':
            self.game.player.die()
    
    def _cmd_give(self, command):
        """Give item command."""
        if command[2].isdigit():
            if command[1].isdigit():
                if int(command[1]) in self.game.itemTextureCoordinate:
                    self.game.giveItem(int(command[1]), int(command[2]))
            else:
                for itemId, name in self.game.itemTextureCoordinate.items():
                    if command[1] in name:
                        self.game.giveItem(itemId, int(command[2]))
                        break
    
    def _cmd_teleport(self, command):
        """Teleport command."""
        if command[1].isdigit() and command[2].isdigit():
            self.game.player.pos = vec(int(command[1]) * TILESIZE, int(command[2]) * TILESIZE)
            self._close_console()
    
    def _cmd_speed(self, command):
        """Speed command."""
        if command[1].isdigit():
            self.game.player.speed = int(command[1]) * TILESIZE
    
    def _cmd_regen(self):
        """Regenerate health command."""
        self.game.player.health = self.game.player.lifebar.maxHealth
        self.game.player.lifebar.updateHealth(self.game.player.health)
        self.game.player.lifebar.updateSurface()
    
    def _cmd_maxhealth(self, command):
        """Set max health command."""
        self.game.player.lifebar.maxHealth = int(command[1])
        self.game.player.health = self.game.player.lifebar.maxHealth
        self.game.player.lifebar.updateHealth(self.game.player.health)
        self.game.player.lifebar.updateSurface()
    
    def _cmd_hitbox(self, command):
        """Toggle hitbox debug command."""
        if len(command) > 1:
            if command[1].isdigit():
                self.game.hitboxDebug = int(command[1]) == 1
        else:
            self.game.hitboxDebug = True
    
    def _cmd_spawnpoint(self, command):
        """Set spawn point command."""
        if command[1].isdigit() and command[2].isdigit():
            # Convert tile coordinates to pixel coordinates
            self.game.spawnPoint = vec(int(command[1]) * TILESIZE, int(command[2]) * TILESIZE)
    
    def _cmd_time(self, command):
        """Time manipulation command."""
        if command[1] == 'add' and command[2].isdigit():
            self.game.global_time += int(command[2])
        elif command[1] == 'set':
            if command[2].isdigit():
                self.game.global_time -= self.game.day_time
                self.game.global_time += int(command[2]) % DAY_LENGTH
            elif command[2] == 'day':
                self.game.skipNight()
            elif command[2] == 'night':
                self.game.global_time -= self.game.day_time
                self.game.global_time += DAY_LENGTH - (DAY_LENGTH // 3)
        self._close_console()
    
    def _cmd_spawn(self, command):
        """Spawn mob command."""
        from game.entities.mobs.Mob import Mob
        
        if command[1].isdigit() and command[2].isdigit() and command[3].isdigit():
            mobId = max(min(int(command[1]), len(self.game.mobList) - 1), 0)
            Mob(self.game, int(command[2]), int(command[3]), mobId)
        elif command[2].isdigit() and command[3].isdigit():
            mobId = -1
            for mob in self.game.mobList:
                mobId += 1
                if mob[5] == command[1]:
                    break
            if mobId != -1:
                Mob(self.game, int(command[2]), int(command[3]), mobId)
    
    def _cmd_clear(self, command):
        """Clear command."""
        if command[1] == 'inventory':
            for i in range(len(self.game.player.hotbar.itemList)):
                self.game.player.hotbar.itemList[i] = [0, 0]
            self.game.player.hotbar.updateSelector(0)
        elif command[1] == 'items':
            for floatItem in self.game.floatingItems:
                floatItem.kill()
        elif command[1] == 'entities':
            for mob in self.game.mobs:
                mob.kill()
            self.game.friendly_mobs_amount = 0
            self.game.hostile_mobs_amount = 0
            for projectile in self.game.projectiles:
                projectile.kill()
            for floatItem in self.game.floatingItems:
                floatItem.kill()
    
    def _close_console(self):
        """Close the debug console."""
        self.game.input_commands = False
        pg.mouse.set_visible(self.game.input_commands)
        self.game.isGamePaused = False
        self.game.input_commands_txt.active = False
        self.game.input_commands_txt.color = BLACK
