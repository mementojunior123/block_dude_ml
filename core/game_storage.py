from sys import platform as PLATFORM
import json
import os
from typing import Any, TypedDict
from utils.helpers import AnyJson


if PLATFORM == 'emscripten':
    from platform import window

class GameData(TypedDict):
    pass

class GameStorage:
    @staticmethod
    def get_maplist() -> list[str]:
        for root, dirs, files in os.walk('non_pygame/maps'):
            return [file_name.removesuffix('.json') for file_name in files if file_name.endswith('.json')]
    
    '''Most of these functions are incomplete and need implementing.\nThis module is made to handle file I/O and saving on multiple platforms.'''
    def __init__(self) -> None:
        pass

    def reset(self):
        pass

    def _get_data(self) -> GameData:
        pass

    def _load_data(self, data : GameData):
        pass

    def load_from_file(self, file_path : str = 'assets/data/game_info.json'):
        with open(file_path, 'r') as file:
            data = json.load(file)
        if data:
            self._load_data(data)

    def save_to_file(self, file_path : str = 'assets/data/game_info.json'):
        data = self._get_data()
        with open(file_path, 'w') as file:
            json.dump(data, file)

    def load_from_web(self):
        web_data = self.get_web('GameData')
        if web_data is not None:
            data = json.loads(web_data)
            if data is not None:
                self._load_data(data)

    def save_to_web(self):
        data = self._get_data()
        self.set_web('GameData', json.dumps(data))

    def get_web(self, key : str) -> str:
        window.localStorage.getItem(key)

    def set_web(self, key : str, value : Any):
        window.localStorage.setItem(key, str(value) )