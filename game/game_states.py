import pygame
from typing import Any
from math import floor
from random import shuffle, choice
import random
import json
from enum import Enum, IntEnum
from non_pygame.block_dude_core import CellType, save_map, load_map
import utils.tween_module as TweenModule
from utils.ui.ui_sprite import UiSprite
from utils.ui.textbox import TextBox
from utils.ui.textsprite import TextSprite
from utils.ui.base_ui_elements import BaseUiElements
import utils.interpolation as interpolation
from utils.my_timer import Timer
from game.sprite import Sprite
from utils.helpers import average, random_float
from utils.ui.brightness_overlay import BrightnessOverlay

class GameState:
    def __init__(self, game_object : 'Game'):
        self.game = game_object

    def main_logic(self, delta : float):
        pass

    def pause(self):
        pass

    def unpause(self):
        pass

    def handle_key_event(self, event : pygame.Event):
        pass

    def handle_mouse_event(self, event : pygame.Event):
        pass

class NormalGameState(GameState):
    def main_logic(self, delta : float):
        Sprite.update_all_sprites(delta)
        Sprite.update_all_registered_classes(delta)

    def pause(self):
        if not self.game.active: return
        self.game.game_timer.pause()
        window_size = core_object.main_display.get_size()
        pause_ui1 = BrightnessOverlay(-60, pygame.Rect(0,0, *window_size), 0, 'pause_overlay', zindex=999)
        pause_ui2 = TextSprite(pygame.Vector2(window_size[0] // 2, window_size[1] // 2), 'center', 0, 'Paused', 'pause_text', None, None, 1000,
                               (self.game.font_70, 'White', False), ('Black', 2), colorkey=(0, 255, 0))
        core_object.main_ui.add(pause_ui1)
        core_object.main_ui.add(pause_ui2)
        self.game.state = PausedGameState(self.game, self)
    
    def handle_key_event(self, event : pygame.Event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_p:
                self.pause()

class TestGameState(NormalGameState):
    def __init__(self, game_object : 'Game'):
        super().__init__(game_object)
        player : TestPlayer = TestPlayer.spawn(pygame.Vector2(random.randint(0, 960),random.randint(0, 540)))

    def main_logic(self, delta : float):
        super().main_logic(delta)

    def pause(self):
        if not self.game.active: return
        self.game.game_timer.pause()
        window_size = core_object.main_display.get_size()
        pause_ui1 = BrightnessOverlay(-60, pygame.Rect(0,0, *window_size), 0, 'pause_overlay', zindex=999)
        pause_ui2 = TextSprite(pygame.Vector2(window_size[0] // 2, window_size[1] // 2), 'center', 0, 'Paused', 'pause_text', None, None, 1000,
                               (self.game.font_70, 'White', False), ('Black', 2), colorkey=(0, 255, 0))
        core_object.main_ui.add(pause_ui1)
        core_object.main_ui.add(pause_ui2)
        self.game.state = PausedGameState(self.game, self)
    
    def handle_key_event(self, event : pygame.Event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_p:
                self.pause()

class MapEditorMode(IntEnum):
    SELECT = 0
    BRICK = 1
    BLOCK = 2
    DOOR = 3
    PLAYER = 4
    
class MapEditorGameState(NormalGameState):
    MAP_SIZE : tuple[int, int] = (10,10)
    MAP_SCALE : int = 50
    def __init__(self, game_object : 'Game'):
        self.game = game_object
        empty_canvas : SavedMap = {
            'map' : [[0 for _ in range(12)] for _ in range(12)],
            'start_direction' : 1,
            'start_x' : 1,
            'start_y' : 8
            }
        empty_canvas['map'][9][0] = 1
        empty_canvas['map'][9][1] = CellType.BLOCK.value
        self.map = TileMap.spawn((480, 270), empty_canvas, self.MAP_SCALE)
        self.current_action_mode : MapEditorMode = MapEditorMode.SELECT
        self.cursor = UiSprite(pygame.transform.scale(Tile.BLOCK_TEXTURE, (50,50)), pygame.rect.Rect(0,0,50,50), 0, zindex=1)
        self.cursor.visible = False
        core_object.main_ui.add(self.cursor)

    def main_logic(self, delta : float):
        super().main_logic(delta)
        self.cursor.rect.topleft = pygame.mouse.get_pos()
    
    def handle_key_event(self, event):
        super().handle_key_event(event)
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_o:
                if (pygame.key.get_pressed()[pygame.K_LSHIFT]):
                    print(self.map.to_saved_map()['map'])
                else:
                    save_map('non_pygame/other_maps/map_editor_result.json', self.map.to_saved_map())
            
            elif event.key == pygame.K_0:
                self.change_action_mode(MapEditorMode(0))
            elif event.key == pygame.K_1:
                self.change_action_mode(MapEditorMode(1))
            elif event.key == pygame.K_2:
                self.change_action_mode(MapEditorMode(2))
            elif event.key == pygame.K_3:
                self.change_action_mode(MapEditorMode(3))
            elif event.key == pygame.K_4:
                self.change_action_mode(MapEditorMode(4))
    
    def handle_mouse_event(self, event):
        if event.type == Sprite.SPRITE_CLICKED:
            clicked_sprite : Sprite|Tile = event.main_hit
            if not isinstance(clicked_sprite, Tile):
                return
            if event.button == 1:
                if self.current_action_mode == MapEditorMode.SELECT:
                    if clicked_sprite.tile_type == CellType.PLAYER:
                        self.map.player_direction *= -1
                        clicked_sprite.change_type(CellType.PLAYER)
                else:
                    clicked_sprite.change_type(CellType(self.current_action_mode.value))
            
            elif event.button == 2:
                self.change_action_mode(MapEditorMode(clicked_sprite.tile_type.value))
            
            elif event.button == 3:
                clicked_sprite.change_type(CellType.EMPTY)

    def change_action_mode(self, new_mode : MapEditorMode):
        self.current_action_mode = new_mode
        self.cursor.visible = False if self.current_action_mode == MapEditorMode.SELECT else True
        if self.current_action_mode == MapEditorMode.PLAYER and self.map.player_direction == 1:
            self.cursor.surf = pygame.transform.scale(Tile.PLAYER_TEXTURE_MIRRORED, (50, 50))
            return
        self.cursor.surf = pygame.transform.scale(Tile.TEXTURES[CellType(new_mode.value)], (50, 50))

                    

class PausedGameState(GameState):
    def __init__(self, game_object : 'Game', previous : GameState):
        super().__init__(game_object)
        self.previous_state = previous
    
    def unpause(self):
        if not self.game.active: return
        self.game.game_timer.unpause()
        pause_ui1 = core_object.main_ui.get_sprite('pause_overlay')
        pause_ui2 = core_object.main_ui.get_sprite('pause_text')
        if pause_ui1: core_object.main_ui.remove(pause_ui1)
        if pause_ui2: core_object.main_ui.remove(pause_ui2)
        self.game.state = self.previous_state

    def handle_key_event(self, event : pygame.Event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_p:
                self.unpause()

def runtime_imports():
    global Game
    from game.game_module import Game
    global core_object
    from core.core import core_object

    #runtime imports for game classes
    global game, TestPlayer      
    import game.test_player
    from game.test_player import TestPlayer

    global Tile, TileMap, SavedMap
    import game.map_sprites
    from game.map_sprites import TileMap, Tile, SavedMap

class GameStates:
    NormalGameState = NormalGameState
    MapEditorGameState = MapEditorGameState
    PausedGameState = PausedGameState
    TestGameState = TestGameState
