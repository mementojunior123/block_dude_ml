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

class GameStates:
    def __init__(self) -> None:
        self.transition = 'Transition'
        self.normal = 'Normal'
        self.paused = 'Paused'


class Game:
    font_40 = pygame.Font('assets/fonts/Pixeltype.ttf', 40)
    font_50 = pygame.Font('assets/fonts/Pixeltype.ttf', 50)
    font_60 = pygame.Font('assets/fonts/Pixeltype.ttf', 60)
    font_70 = pygame.Font('assets/fonts/Pixeltype.ttf', 70)
    
    def __init__(self) -> None:
        self.STATES : GameStates = GameStates()

        self.active : bool = False
        self.state : None|str = None
        self.prev_state : None|str = None
        self.game_timer : Timer|None = None
        self.game_data : dict|None = {}

        

    def start_game(self):
        self.active = True
        self.state = self.STATES.normal
        self.prev_state = None
        self.game_timer = Timer(-1)
        self.game_data = {}
        self.make_connections()

        player : TestPlayer = TestPlayer.spawn(pygame.Vector2(random.randint(0, 960),random.randint(0, 540)))
        #Setup varaibles

    def make_connections(self):
        core_object.event_manager.bind(pygame.KEYDOWN, self.handle_key_event)

    def remove_connections(self):
        core_object.event_manager.unbind(pygame.KEYDOWN, self.handle_key_event)

    def handle_key_event(self, event : pygame.Event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_p:
                if self.state == self.STATES.paused:
                    self.unpause()
                elif self.state == self.STATES.normal:
                    self.pause()

    def main_logic(self, delta : float):
        pass
    
    def pause(self):
        if not self.active: return
        if self.state == self.STATES.paused: return 
        self.game_timer.pause()
        window_size = core_object.main_display.get_size()
        pause_ui1 = BrightnessOverlay(-60, pygame.Rect(0,0, *window_size), 0, 'pause_overlay', zindex=999)
        pause_ui2 = TextSprite(pygame.Vector2(window_size[0] // 2, window_size[1] // 2), 'center', 0, 'Paused', 'pause_text', None, None, 1000,
                               (self.font_70, 'White', False), ('Black', 2), colorkey=(0, 255, 0))
        core_object.main_ui.add(pause_ui1)
        core_object.main_ui.add(pause_ui2)
        self.prev_state = self.state
        self.state = self.STATES.paused
    
    def unpause(self):
        if not self.active: return
        if self.state != self.STATES.paused: return
        self.game_timer.unpause()
        pause_ui1 = core_object.main_ui.get_sprite('pause_overlay')
        pause_ui2 = core_object.main_ui.get_sprite('pause_text')
        if pause_ui1: core_object.main_ui.remove(pause_ui1)
        if pause_ui2: core_object.main_ui.remove(pause_ui2)
        self.state = self.prev_state
        self.prev_state = None
    
    
    def fire_gameover_event(self, goto_result_screen : bool = True):
        new_event = pygame.event.Event(core_object.END_GAME, {})
        pygame.event.post(new_event)
    
    def end_game(self):
        self.remove_connections()
        self.cleanup()

    def cleanup(self):
        #Cleanup basic variables
        self.active = False
        self.state = None
        self.prev_state = None
        self.game_timer = None
        self.game_data.clear()

        #Cleanup ingame object
        Sprite.kill_all_sprites()

        #Clear game varaibles
         

   
    def init(self):
        global core_object
        from core.core import core_object

        #runtime imports for game classes
        global game, TestPlayer      
        import game.test_player
        from game.test_player import TestPlayer


        
    
