import pygame
import random
from utils.ui.ui_sprite import UiSprite
from utils.ui.textsprite import TextSprite
from utils.ui.base_ui_elements import BaseUiElements
import utils.tween_module as TweenModule
import utils.interpolation as interpolation
from utils.my_timer import Timer
from utils.ui.brightness_overlay import BrightnessOverlay
from math import floor
from utils.helpers import ColorType
from typing import Callable

class BaseMenu:
    font_40 = pygame.font.Font(r'assets/fonts/Pixeltype.ttf', 40)
    font_50 = pygame.font.Font(r'assets/fonts/Pixeltype.ttf', 50)
    font_60 = pygame.font.Font(r'assets/fonts/Pixeltype.ttf', 60)
    font_70 = pygame.font.Font(r'assets/fonts/Pixeltype.ttf', 70)
    font_150 = pygame.font.Font(r'assets/fonts/Pixeltype.ttf', 150)

    def __init__(self) -> None:
        self.stage : int
        self.stages : list[list[UiSprite]]
        self.bg_color : ColorType|str
        self.temp : dict[UiSprite, Timer] = {}
        
    def init(self):
        self.bg_color = (94, 129, 162)
        self.stage = 1
        self.stage_data : list[dict] = [None, {}]
        self.stages = [None, []]
    
    def add_temp(self, element : UiSprite, time : float|Timer, override = False, time_source : Callable[[], float]|None = None, time_scale : float = 1):
        if element not in self.temp or override == True:
            timer = time if type(time) == Timer else Timer(time, time_source, time_scale)
            self.temp[element] = timer
    def alert_player(self, text : str, alert_speed : float = 1):
        text_sprite = TextSprite(pygame.Vector2(core_object.main_display.get_width() // 2, 90), 'midtop', 0, text, 
                        text_settings=(core_object.menu.font_60, 'White', False), text_stroke_settings=('Black', 2), colorkey=(0,255,0))
        
        text_sprite.rect.bottom = -5
        text_sprite.position = pygame.Vector2(text_sprite.rect.center)
        temp_y = text_sprite.rect.centery
        self.add_temp(text_sprite, 5)
        TInfo = TweenModule.TweenInfo
        goal1 = {'rect.centery' : 50, 'position.y' : 50}
        info1 = TInfo(interpolation.quad_ease_out, 0.3 / alert_speed)
        goal2 = {'rect.centery' : temp_y, 'position.y' : temp_y}
        info2 = TInfo(interpolation.quad_ease_in, 0.4 / alert_speed)
        
        on_screen_time = 1 / alert_speed
        info_wait = TInfo(lambda t : t, on_screen_time)
        goal_wait = {}

        chain = TweenModule.TweenChain(text_sprite, [(info1, goal1), (info_wait, goal_wait), (info2, goal2)], True)
        chain.register()
        chain.play()

    def add_connections(self):
        core_object.event_manager.bind(pygame.MOUSEBUTTONDOWN, self.handle_mouse_event)
        core_object.event_manager.bind(UiSprite.TAG_EVENT, self.handle_tag_event)
    
    def remove_connections(self):
        core_object.event_manager.unbind(pygame.MOUSEBUTTONDOWN, self.handle_mouse_event)
        core_object.event_manager.unbind(UiSprite.TAG_EVENT, self.handle_tag_event)
    
    def __get_core_object(self):
        global core_object
        from core.core import core_object

    def render(self, display : pygame.Surface):
        sprite_list = [sprite for sprite in (self.stages[self.stage] + list(self.temp.keys())) if sprite.visible == True]
        sprite_list.sort(key = lambda sprite : sprite.zindex)
        for sprite in sprite_list:
            sprite.draw(display)
        
    
    def update(self, delta : float):
        to_del = []
        for item in self.temp:
            if self.temp[item].isover(): to_del.append(item)
        for item in to_del:
            self.temp.pop(item)

        stage_data = self.stage_data[self.stage]
        match self.stage:
            case 1:
                pass
    
    def prepare_entry(self, stage : int = 1):
        self.add_connections()
        self.stage = stage
    
    def prepare_exit(self):
        self.stage = 0
        self.remove_connections()
        self.temp.clear()
    
    def goto_stage(self, new_stage : int):
        self.stage = new_stage

    def launch_game(self):
        new_event = pygame.event.Event(core_object.START_GAME, {})
        pygame.event.post(new_event)

    def get_sprite(self, stage, tag):
        """Returns the 1st sprite with a corresponding tag.
        None is returned if it was not found in the stage."""
        if tag is None or stage is None: return None

        the_list = self.stages[stage]
        for sprite in the_list:
            if sprite.tag == tag:
                return sprite
        return None
    
    def get_sprite_by_name(self, stage, name):
        """Returns the 1st sprite with a corresponding name.
        None is returned if it was not found in the stage."""
        if name is None or stage is None: return None

        the_list = self.stages[stage]
        sprite : UiSprite
        for sprite in the_list:
            if sprite.name == name:
                return sprite
        return None

    def get_sprite_index(self, stage, name = None, tag = None):
        '''Returns the index of the 1st occurence of sprite with a corresponding name or tag.
        None is returned if the sprite is not found'''
        if name is None and tag is None: return None
        the_list = self.stages[stage]
        sprite : UiSprite
        for i, sprite in enumerate(the_list):
            if sprite.name == name and name is not None:
                return i
            if sprite.tag == tag and tag is not None:
                return i
        return None
    
    def find_and_replace(self, new_sprite : UiSprite, stage : int, name : str|None = None, tag : int|None = None, sprite : UiSprite|None = None) -> bool:
        found : bool = False
        for index, sprite in enumerate(self.stages[stage]):
            if sprite == new_sprite and sprite is not None:
                found = True
                break
            if sprite.tag == tag and tag is not None:
                found = True
                break
            if sprite.name == name and name is not None:
                found = True
                break
        
        if found:
            self.stages[stage][index] = new_sprite
        else:
            print('Find and replace failed')
        return found
    
    def handle_tag_event(self, event : pygame.Event):
        if event.type != UiSprite.TAG_EVENT:
            return
        tag : int = event.tag
        name : str = event.name
        trigger_type : str = event.trigger_type
        stage_data = self.stage_data[self.stage]
        match self.stage:
            case 1:
                pass
                   
    
    def handle_mouse_event(self, event : pygame.Event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos : tuple = event.pos
            sprite : UiSprite
            for sprite in self.stages[self.stage]:
                if type(sprite) != UiSprite: continue
                if sprite.rect.collidepoint(mouse_pos):
                    sprite.on_click()

class Menu(BaseMenu):
    font_40 = pygame.font.Font(r'assets/fonts/Pixeltype.ttf', 40)
    font_50 = pygame.font.Font(r'assets/fonts/Pixeltype.ttf', 50)
    font_60 = pygame.font.Font(r'assets/fonts/Pixeltype.ttf', 60)
    font_70 = pygame.font.Font(r'assets/fonts/Pixeltype.ttf', 70)
    font_150 = pygame.font.Font(r'assets/fonts/Pixeltype.ttf', 150)
    
    def init(self):
        window_size = core_object.main_display.get_size()
        centerx = window_size[0] // 2

        self.stage = 1
        
        self.stage_data : list[dict] = [None, {}, {}]
        self.stages = [None, 
        [BaseUiElements.new_text_sprite('Block Dude', (Menu.font_60, 'Black', False), 0, 'midtop', (centerx, 50)),
         BaseUiElements.new_button('BlueButton', 'Play', 1, 'midbottom', (centerx - 375, window_size[1] - 15), (0.5, 1.4), 
        {'name' : 'play_button'}, (Menu.font_40, 'Black', False)),
        BaseUiElements.new_button('BlueButton', 'Sim', 1, 'midbottom', (centerx - 125, window_size[1] - 15), (0.5, 1.4), 
        {'name' : 'sim_button'}, (Menu.font_40, 'Black', False)),
        BaseUiElements.new_button('BlueButton', 'Map Editor', 1, 'midbottom', (centerx + 125, window_size[1] - 15), (0.5, 1.2), 
        {'name' : 'map_edit_button'}, (Menu.font_40, 'Black', False)),
        BaseUiElements.new_button('BlueButton', 'Replay', 1, 'midbottom', (centerx + 375, window_size[1] - 15), (0.5, 1.2), 
        {'name' : 'replay_button'}, (Menu.font_40, 'Black', False))],
        [BaseUiElements.new_text_sprite('Map Select', (Menu.font_60, 'Black', False), 0, 'midtop', (centerx, 50)),
        BaseUiElements.new_textless_button("Left", 1, "midbottom", (350, window_size[1] - 15), 0.5, name='left_button'),
        BaseUiElements.new_textless_button("Right", 2, "midbottom", (window_size[0] - 350, window_size[1] - 15), 0.5, name='right_button')]
        ]
        self.bg_color = (94, 129, 162)
    
    def update(self, delta : float):
        stage_data = self.stage_data[self.stage]
        match self.stage:
            case 1:
                pass
    
    def get_maplist(self) -> list[str]:
        return sorted(core_object.storage.get_maplist())

    def enter_stage2(self):
        self.stage = 2
        stage_data = self.stage_data[self.stage]
        stage_data['maplist'] = self.get_maplist()
        stage_data['max_page_index'] = ((len(stage_data['maplist']) - 1) // 6)
        stage_data['page_index'] = 0
        self.add_stage2_sprites(stage_data['page_index'])
        self.update_stage2_button_visiblity()
    
    def add_stage2_sprites(self, page_index : int = 0):
        stage_data = self.stage_data[self.stage]
        stage_data['extra_sprites'] = self.make_stage2_sprites(page_index)
        for sprite in stage_data['extra_sprites']:
            self.stages[2].append(sprite)

    def make_stage2_sprites(self, page_index : int) -> list[UiSprite]:
        stage_data = self.stage_data[self.stage]
        start_index : int = page_index * 6
        end_index : int = page_index * 6 + 6
        maplist : list[str] = stage_data['maplist']
        map_count : int = len(maplist)
        maps_used : list[str]
        if (end_index) < map_count:
            maps_used = maplist[start_index:end_index]
        else:
            maps_used = maplist[start_index:]
        return_value : list[UiSprite] = []
        current_x : int = 200
        current_y : int = 100
        for map_name in maps_used:
            new_button = BaseUiElements.new_button('BlueButton', 'Play', 1, 'midbottom', (current_x, current_y), (0.4, 1.1), 
                                                   text_settings=(Menu.font_40, 'Black', False), name=f'play_button_{map_name}')
            new_text_sprite = BaseUiElements.new_text_sprite(f'{map_name}', (Menu.font_50, 'Black', False), 0, 'midbottom', 
                                                             (current_x, current_y-60), name=f'title_{map_name}')
            return_value.append(new_button)
            return_value.append(new_text_sprite)
            if current_x > 200:
                current_y += 150
                current_x = 200
            else:
                current_x = 760
        return return_value

    def clear_stage2_sprites(self):
        stage_data = self.stage_data[2]
        for sprite in stage_data['extra_sprites']:
            if sprite in self.stages[2]:
                self.stages[2].remove(sprite)
        del stage_data['extra_sprites']
    
    def change_page_stage2(self, new_index : int):
        stage_data = self.stage_data[2]
        stage_data['page_index'] = new_index
        self.clear_stage2_sprites()
        self.add_stage2_sprites(new_index)
        self.update_stage2_button_visiblity()
    
    def update_stage2_button_visiblity(self):
        curr_index : int = self.stage_data[2]['page_index']
        self.get_sprite_by_name(2, 'left_button').visible = False if curr_index <= 0 else True
        self.get_sprite_by_name(2, 'right_button').visible = False if curr_index >= self.stage_data[2]['max_page_index'] else True

    def exit_stage2(self):
        self.clear_stage2_sprites()
        self.stage_data[2].clear()
    
    def handle_tag_event(self, event : pygame.Event):
        if event.type != UiSprite.TAG_EVENT:
            return
        tag : int = event.tag
        name : str = event.name
        trigger_type : str = event.trigger_type
        stage_data = self.stage_data[self.stage]
        match self.stage:
            case 1:
                if name == 'play_button':
                    self.enter_stage2()
                elif name == "sim_button":
                    pygame.event.post(pygame.Event(core_object.START_GAME, {'mode' : "Sim"}))
                elif name == "map_edit_button":
                    pygame.event.post(pygame.Event(core_object.START_GAME, {'mode' : "MapEditor"}))
                elif name == "replay_button":
                    mode = "Replay_F" if pygame.key.get_pressed()[pygame.K_f] else "Replay"
                    pygame.event.post(pygame.Event(core_object.START_GAME, {'mode' : mode}))
            case 2:
                if name.startswith('play_button_'):
                    map_name = name.removeprefix('play_button_')
                    self.exit_stage2()
                    pygame.event.post(pygame.Event(core_object.START_GAME, {'mode' : 'Player', 'map_name' : map_name}))
                    import game.game_states as game_states
                elif name == 'left_button':
                    current_page : int = stage_data['page_index']
                    if current_page > 0:
                        self.change_page_stage2(current_page - 1)
                elif name == 'right_button':
                    current_page : int = stage_data['page_index']
                    if current_page < stage_data['max_page_index']:
                        self.change_page_stage2(current_page + 1)
    
