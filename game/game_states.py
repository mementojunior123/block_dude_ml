import pygame
from time import perf_counter
from typing import Any
from math import floor
from random import shuffle, choice
import random
import json
from enum import Enum, IntEnum
from collections import deque
from non_pygame.block_dude_core import CellType, save_map, load_map
import non_pygame.block_dude_core as bd_core
from non_pygame.ml_core import PopulationInterface
import non_pygame.ml_core as ml_core
import neat
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
    MAP_SCALE : int = 60
    def __init__(self, game_object : 'Game'):
        self.game = game_object
        empty_canvas : SavedMap = {
            'map' : [[0 for _ in range(22)] for _ in range(8)],
            'start_direction' : 1,
            'start_x' : 1,
            'start_y' : 5
            }
        empty_canvas['map'][6][0] = 1
        empty_canvas['map'][7][1] = CellType.BLOCK.value
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

class SimulationGameState(NormalGameState):
    def __init__(self, game_object : 'Game', sim_runner : PopulationInterface, config : neat.Config, map_used : 'SavedMap'):
        super().__init__(game_object)
        self.text_sprite_cycle_timer : Timer = Timer(0.5, self.game.game_timer.get_time)
        self.current_amount_of_dots : int = 2
        self.simulating_sprite  : TextSprite = TextSprite(pygame.Vector2(480, 270), 'center', 0, f'Simulating{self.current_amount_of_dots * '.'}', 
                                       text_settings=(self.game.font_60, 'White', False), 
                                 text_stroke_settings=('Black', 2), colorkey=(0, 255, 0))
        self.escape_sprite : TextSprite = TextSprite(pygame.Vector2(955, 5), 'topright', 0, 'Press ESC to exit', 
                                   text_settings=(self.game.font_60, 'White', False), text_stroke_settings=('Black', 2), colorkey=(0, 255, 0))
        
        self.progress_sprite : TextSprite = TextSprite(pygame.Vector2(25, 515), 'bottomleft', 0, f'0/{sim_runner.max_generations}', 
                                   text_settings=(self.game.font_60, 'White', False), text_stroke_settings=('Black', 2), colorkey=(0, 255, 0))
        self.fitness_sprite : TextSprite = TextSprite(pygame.Vector2(935, 515), 'bottomright', 0, f'Best Fitness : None', 
                                   text_settings=(self.game.font_60, 'White', False), text_stroke_settings=('Black', 2), colorkey=(0, 255, 0))
        self.current_amount_of_dots : int = 2
        core_object.main_ui.add(self.simulating_sprite)
        core_object.main_ui.add(self.escape_sprite)
        core_object.main_ui.add(self.progress_sprite)
        core_object.main_ui.add(self.fitness_sprite)
        self.sim_runner : PopulationInterface = sim_runner
        self.sim_runner.start_running()
        self.sim_runner.start_generation()
        self.config : neat.Config = config
        self.map_used : SavedMap = map_used
        self.update_phase : int = 0
        self.genome_evaluator : ml_core.GenomeEvaluator = ml_core.GenomeEvaluator(self.sim_runner.get_genome_list(), self.config, self.map_used)
     
        

    def main_logic(self, delta : float):
        super().main_logic(delta)
        self.update_wait_text()
        time_elapsed_since_frame_start : float = perf_counter() - core_object.last_dt_measurment #per counter is in seconds
        target_FPS = 10
        target_frame_time : float = 1 / target_FPS # in seconds
        current_budget : float = target_frame_time - time_elapsed_since_frame_start
        total_budget : float = max(current_budget - 0.05, 0.015)
        #print(total_budget)
        self.continue_sim(total_budget)
        if self.sim_runner.isover():
            winner = self.sim_runner.end_run()
            replay : ml_core.GenomeReplay = {'config' : self.config, 'genome' : winner, 'map_used' : self.map_used, 'net_used' : winner.net_used}
            Sprite.kill_all_sprites()
            core_object.main_ui.clear_all()
            self.game.alert_player(f'{winner.fitness}')
            core_object.game.state = ShowcaseGameState(self.game, replay)
    
    def handle_key_event(self, event : pygame.Event):
        super().handle_key_event(event)
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_s:
                genome = self.sim_runner.current_best_genome
                ml_core.save_replay('non_pygame/winners/failure', 
                                    {'config' : self.config, 'genome' : genome, 'map_used' : self.map_used, 'net_used' : genome.net_used})

    def continue_sim(self, frame_budget : float):
        timer : Timer = Timer(frame_budget, time_source=perf_counter)
        while not timer.isover():
            if self.genome_evaluator.isover():
                self.sim_runner.end_generation()
                self.update_progress_sprite()
                if self.sim_runner.isover(): return
                self.genome_evaluator = ml_core.GenomeEvaluator(self.sim_runner.get_genome_list(), self.config, self.map_used)
                self.sim_runner.start_generation()
            self.genome_evaluator.do_genome()
            if self.genome_evaluator.isover():
                pass
                #break

    def update_wait_text(self):
        if self.text_sprite_cycle_timer.isover():
            self.text_sprite_cycle_timer.restart()
            if self.current_amount_of_dots == 2:
                self.current_amount_of_dots = 3
            else:
                self.current_amount_of_dots = 2
            self.simulating_sprite.text = f'Simulating{self.current_amount_of_dots * '.'}'
            self.simulating_sprite.rect = self.simulating_sprite.surf.get_rect(center=(480, 270))
    
    def update_progress_sprite(self):
        the_text : str = f'{self.sim_runner.current_generation}/{self.sim_runner.max_generations}'
        self.progress_sprite.text = the_text
        self.progress_sprite.rect = self.progress_sprite.surf.get_rect(bottomleft=(25, 515))

        the_text2 : str = f'Best Fitness : {self.sim_runner.current_best_genome.fitness}'
        self.fitness_sprite.text = the_text2
        self.fitness_sprite.rect = self.fitness_sprite.surf.get_rect(bottomright = (935, 515))

class ShowcaseGameState(NormalGameState):
    MAX_TURNS : int = 100
    def __init__(self, game_object : 'Game', replay : ml_core.GenomeReplay):
        super().__init__(game_object)
        self.genome = replay['genome']
        self.map_used = replay['map_used']
        self.config = replay['config']
        self.current_turn : int = 0
        self.player : bd_core.Game = bd_core.Game.from_saved_map(self.map_used, copy_map=True)
        self.net = replay.get('net_used', None) or neat.nn.FeedForwardNetwork.create(self.genome, self.config)
        self.visual_map : TileMap = TileMap.spawn((480, 270), self.map_used, 75)
        self.visual_map.synchronise_with_player(self.player)
        self.action_timer : Timer = Timer(0.25, time_source=core_object.game.game_timer.get_time)
        self.first_frame : bool = True
        self.state_stream : deque[bd_core.GameState] = deque([self.player.to_game_state()], maxlen=15)
        self.action_stream : deque[int] = deque([], maxlen=14)
    
    def main_logic(self, delta : float):
        super().main_logic(delta)
        if self.first_frame:
            self.action_timer.restart()
            self.first_frame = False
        if self.action_timer.isover():
            self.action_timer.restart()
            self.take_player_action()
            self.visual_map.synchronise_with_player(self.player)
        

    
    def take_player_action(self):
        verifications, actions = self.player.get_binds()
        output : list[float] = self.net.activate([*ml_core.flatten_map_gen(self.player.map), self.player.player_x, self.player.player_y, 
                                                    self.player.player_direction, self.player.player_holding_block])
        output_dict : dict[int, float] = {i : output[i] for i in range(len(output))}
        sorted_output = ml_core.sort_dict_by_values(output_dict, reverse=True)
        duped_actions : list[int] = []
        for action, game_state in zip(self.action_stream, self.state_stream):
            if self.player == game_state:
                print('dupe', bd_core.ActionType(action).name)
                duped_actions.append(action)
                break
        took_action : bool = False
        for action_type in sorted_output:
            if action_type in duped_actions: continue
            if not verifications[action_type](): continue
            actions[action_type]()
            print('going', bd_core.ActionType(action_type).name)
            took_action = True
            break
        if not took_action:
            for action_type in sorted_output:
                if not verifications[action_type](): continue
                actions[action_type]()
                print('going', bd_core.ActionType(action_type).name)
                took_action = True
                break
        if len(self.state_stream) >= self.state_stream.maxlen: self.state_stream.popleft()
        self.state_stream.append(self.player.to_game_state())
        if len(self.action_stream) >= self.action_stream.maxlen: self.action_stream.popleft()
        self.action_stream.append(action_type)
        self.current_turn += 1
        if self.player.game_won():
            self.game.alert_player("GG!")
            self.game.state = ShowcaseOverGameState(self.game)
            replay : ml_core.GenomeReplay = {'config' : self.config, 'genome' : self.genome, 'map_used' : self.map_used, 'net_used' : self.net}
            ml_core.save_replay('non_pygame/winners/winner1', replay)
        elif self.current_turn >= self.MAX_TURNS:
            self.game.alert_player("It ran out of time...")
            self.game.state = ShowcaseOverGameState(self.game)
            #ml_core.show_genome_playing(self.genome, self.config, 5, 40, 'It ran out of time...', self.map_used)

class ShowcaseOverGameState(NormalGameState):
    def __init__(self, game_object):
        super().__init__(game_object)
        self.wait_timer : Timer = Timer(3, time_source=core_object.game.game_timer.get_time)
    
    def main_logic(self, delta : float):
        super().main_logic(delta)
        if self.wait_timer.isover():
            self.game.fire_gameover_event()

class PlayingGameState(NormalGameState):
    CAMERA_CENTER : pygame.Vector2 = pygame.Vector2(480, 400)
    def __init__(self, game_object : "Game", map_used : 'SavedMap'):
        super().__init__(game_object)
        self.player = bd_core.Game.from_saved_map(map_used, copy_map=True)
        self.visual_map : TileMap = TileMap.spawn((480, 270), map_used, 75)
        self.visual_map.synchronise_with_player(self.player)
        self.center_player(self.CAMERA_CENTER)
        self.DAS_timer : Timer = Timer(0.15, self.game.game_timer.get_time)
    
    def main_logic(self, delta : float):
        super().main_logic(delta)
        self.do_input()
        if not self.cam_moving(): self.follow_cam(self.CAMERA_CENTER, delta)
        for row in self.visual_map.tiles:
            for tile in row:
                tile.align_with_map()
    
    def handle_key_event(self, event : pygame.Event):
        super().handle_key_event(event)
        if event.type == pygame.KEYDOWN:
            self.on_key_press(event.key)
    
    def cam_moving(self) -> bool:
        pressed = pygame.key.get_pressed()
        KEYS = [pygame.K_w, pygame.K_s, pygame.K_a, pygame.K_d]
        for key in KEYS:
            if pressed[key]:
                return True
        return False
    
    def follow_cam(self, target : pygame.Vector2, delta : float):
        cam_speed : float = 10 * delta
        visual_player_loaction : pygame.Vector2 = self.visual_map.tiles[self.player.player_y][self.player.player_x].position
        offset : pygame.Vector2 = target - visual_player_loaction
        if offset.magnitude() <= 0: return
        if offset.magnitude() < cam_speed:
            self.center_player(target)
            return
        offset.scale_to_length(cam_speed)
        self.visual_map.move_by(-(offset))
    
    def center_player(self, target : pygame.Vector2):
        visual_player_loaction : pygame.Vector2 = self.visual_map.tiles[self.player.player_y][self.player.player_x].position
        offset : pygame.Vector2 = target - visual_player_loaction
        self.visual_map.move_by(-offset)
    
    def do_input(self):
        if not self.DAS_timer.isover(): return
        pressed = pygame.key.get_pressed()
        if pressed[pygame.K_LEFT] and pressed[pygame.K_RIGHT]: return
        if pressed[pygame.K_LEFT]:
            self.on_key_press(pygame.K_LEFT)
        elif pressed[pygame.K_RIGHT]:
            self.on_key_press(pygame.K_RIGHT)
        elif pressed[pygame.K_UP]:
            self.on_key_press(pygame.K_UP)

    def on_key_press(self, key : int):
        match key:
            case pygame.K_UP:
                self.try_action(bd_core.ActionType.UP)
            case pygame.K_DOWN|pygame.K_SPACE:
                self.try_action(bd_core.ActionType.DOWN)
            case pygame.K_LEFT:
                result = self.try_action(bd_core.ActionType.LEFT)
                if not result:
                    self.try_action(bd_core.ActionType.UP)
            case pygame.K_RIGHT:
                result = self.try_action(bd_core.ActionType.RIGHT)
                if not result:
                    self.try_action(bd_core.ActionType.UP)
    
    def try_action(self, action : bd_core.ActionType) -> bool:
        verifications, actions = self.player.get_binds()
        if not verifications[action.value](): return False
        actions[action.value]()
        #self.center_player(self.CAMERA_CENTER)
        if action != bd_core.ActionType.DOWN:
            self.DAS_timer.restart()
        self.visual_map.synchronise_with_player(self.player)
        if self.player.game_won():
            self.game.alert_player("You win!")
            self.game.state = PlayingVictoryGameState(self.game)
        return True

class PlayingVictoryGameState(NormalGameState):
    def __init__(self, game_object : 'Game'):
        super().__init__(game_object)
        self.wait_timer : Timer = Timer(3, time_source=core_object.game.game_timer.get_time)
    
    def main_logic(self, delta : float):
        super().main_logic(delta)
        if self.wait_timer.isover():
            self.game.fire_gameover_event()

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
    SimulationGameState = SimulationGameState
    ShowcaseGameState = ShowcaseGameState
    ShowcaseOverGameState = ShowcaseOverGameState
    PlayingGameState = PlayingGameState
    PlayingVictoryGameState = PlayingVictoryGameState