import pygame
from typing import Any
from math import floor
from random import shuffle, choice
import random
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

    def update(self, delta : float):
        pass

    def pause(self):
        pass

    def unpause(self):
        pass

class NormalGameState(GameState):
    def update(self, delta : float):
        pass

    def pause(self):
        if not self.active: return
        self.game.state = PausedGameState(self.game)

class PausedGameState(GameState):
    pass


def runtime_imports():
    global Game
    from game.game_module import Game