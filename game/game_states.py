import pygame
from typing import Any
from math import floor
from random import shuffle, choice
import random
from enum import Enum
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
        pass

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

class TestGameState(GameState):
    def __init__(self, game_object : 'Game'):
        super().__init__(game_object)
        player : TestPlayer = TestPlayer.spawn(pygame.Vector2(random.randint(0, 960),random.randint(0, 540)))

    def main_logic(self, delta : float):
        pass

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


class MapEditorGameState(NormalGameState):
    MAP_SIZE : tuple[int, int] = (10,10)
    MAP_SCALE : int = 50
    def __init__(self, game_object : 'Game'):
        self.game = game_object
        empty_canvas : SavedMap = {
            'map' : [[0 for _ in range(10)] for _ in range(10)],
            'start_direction' : 1,
            'start_x' : 1,
            'start_y' : 8
            }
        empty_canvas['map'][9][0] = 1
        self.map = TileMap.spawn((480, 270), empty_canvas, self.MAP_SCALE)

    def main_logic(self, delta : float):
        pass
    
    def handle_key_event(self, event):
        super().handle_key_event(event)
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_o:
                pass

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
