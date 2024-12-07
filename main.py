import pygame
import asyncio

pygame.init()

#GAME_ICON = pygame.image.load('template_icon.png')
GAME_TITLE : str = "Test game title"
#pygame.display.set_icon(GAME_ICON)

window_size = (960, 540)
window = pygame.display.set_mode(window_size)

pygame.mixer.set_num_channels(32)

from core.core import Core, core_object

core = core_object
core.init(window)
core.FPS = 120
if core.is_web(): core.setup_web(1)


pygame.display.set_caption(GAME_TITLE)

from game.sprite import Sprite
Sprite._core_hint()

from utils.animation import Animation, AnimationTrack, _sprite_hint
_sprite_hint()

from utils.ui.base_ui_elements import BaseUiElements, UiSprite
from utils.ui.textsprite import TextSprite
from utils.helpers import rotate_around_pivot_accurate, copysign
from utils.particle_effects import ParticleEffect, Particle
from utils.my_timer import Timer
import utils.interpolation as interpolation
import utils.tween_module as TweenModule

from game.test_player import TestPlayer

TestPlayer()

core.settings.set_defualt({'Brightness' : 0})
core.settings.load()

core.set_brightness(core.settings.info['Brightness'])
if core.is_web():
    core.storage.load_from_web()
else:
    core.storage.load_from_file()
core.menu.init()
core.game.init()
import game.game_states as game_state_module
game_state_module.runtime_imports()

clock = pygame.Clock()
font_40 = pygame.font.Font('assets/fonts/Pixeltype.ttf', 40)



def start_game(event : pygame.Event):
    if event.type != core.START_GAME: return
    core.menu.prepare_exit()
    core.game.start_game(event)

    core_object.event_manager.bind(pygame.MOUSEBUTTONDOWN, Sprite.handle_mouse_event)
    core_object.event_manager.bind(pygame.FINGERDOWN, Sprite.handle_touch_event)
    core_object.event_manager.bind(pygame.KEYDOWN, detect_game_over)

    
    core.main_ui.add(fps_sprite)
    core.main_ui.add(debug_sprite)
   
    
def detect_game_over(event : pygame.Event):
    if event.type == pygame.KEYDOWN: 
        if event.key == pygame.K_ESCAPE: 
            end_game(None)
    

def end_game(event : pygame.Event = None):
    core.game.end_game()
    core.menu.prepare_entry(1)
    core_object.event_manager.unbind(pygame.MOUSEBUTTONDOWN, Sprite.handle_mouse_event)
    core_object.event_manager.unbind(pygame.FINGERDOWN, Sprite.handle_touch_event)
    core_object.event_manager.unbind(pygame.KEYDOWN, detect_game_over)

core.game.active = False
core.menu.add_connections()
core.event_manager.bind(core.START_GAME, start_game)
core.event_manager.bind(core.END_GAME, end_game)

def setup_debug_sprites():
    global fps_sprite
    global debug_sprite

    fps_sprite = TextSprite(pygame.Vector2(15 + 63 - 63, 10), 'topleft', 0, 'FPS : 0', 'fps_sprite', 
                            text_settings=(font_40, 'White', False), text_stroke_settings=('Black', 2),
                            text_alingment=(9999, 5), colorkey=(255, 0,0))

    debug_sprite = TextSprite(pygame.Vector2(15, 200), 'midright', 0, '', 'debug_sprite', 
                            text_settings=(font_40, 'White', False), text_stroke_settings=('Black', 2),
                            text_alingment=(9999, 5), colorkey=(255, 0,0), zindex=999)

core.frame_counter = 0
cycle_timer = Timer(0.1, core_object.global_timer.get_time)

setup_debug_sprites()

async def main():
    while 1:
        core.update_dt(60)
        for event in pygame.event.get():
            core.event_manager.process_event(event)

        if core.game.active == False:
            window.fill(core.menu.bg_color)
            core.menu.update(core.dt)
            core.menu.render(window)
        else:
            core.game.update(core.dt)

            window.fill((94,129,162))    
            Sprite.draw_all_sprites(window)
            core.main_ui.update()
            core.main_ui.render(window)

        core.update()
        if cycle_timer.isover(): 
            fps_sprite.text = f'FPS : {core.get_fps():0.0f}'
            cycle_timer.restart()
        if core.settings.info['Brightness'] != 0:
            window.blit(core.brightness_map, (0,0), special_flags=core.brightness_map_blend_mode)
            
        pygame.display.update()
        core.frame_counter += 1
        clock.tick(core.FPS)
        await asyncio.sleep(0)

asyncio.run(main())


