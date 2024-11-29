from sys import platform as PLATFORM
from typing import Any
if PLATFORM == 'emscripten':
    from platform import window

class GameStorage:
    '''Most of these functions are incomplete and need implementing.\nThis module is made to handle file I/O and saving on multiple platforms.'''
    def __init__(self) -> None:
        self.high_score : int = 0
        pass

    def load_from_file(self, file_path : str = 'assets/data/game_info.json'):
        pass

    def save_to_file(self, file_path : str = 'assets/data/game_info.json'):
        pass

    def load_from_web(self):
        self.high_score = int(self.get_web('high_score') or 0)

    def save_to_web(self):
        self.set_web('high_score', self.high_score)

    def get_web(self, key : str) -> str:
        window.localStorage.getItem(key)

    def set_web(self, key : str, value : Any):
        window.localStorage.setItem(key, str(value) )