from typing import TypeAlias, TypedDict, Callable
from enum import Enum, IntEnum
import json
import os
from sys import exit
import sys
sys.path.append(".")
from copy import deepcopy



class InvalidMapError(BaseException):
    pass

class CellType(IntEnum):
    EMPTY = 0
    BRICK = 1
    BLOCK = 2
    DOOR = 3

class ActionType(IntEnum):
    UP = 0
    LEFT = 1
    RIGHT = 2
    DOWN = 3

GameMap : TypeAlias = list[list[int]]
class SavedMap(TypedDict):
    map : GameMap
    start_x : int
    start_y : int
    start_direction : int

class GameState(TypedDict):
    map : GameMap
    player_x : int
    player_y : int
    player_holding_block : False
    player_direction : int

def clear_console(method : int = 1):
    if method == 1:
        print("\033c", end="")
    elif method == 2:
        x = 3
        print(f"\033[H\033[{x}J", end="")
    elif method == 3:
        print("\n" * 50)
    else:
        os.system('cls' if os.name == 'nt' else 'clear')


def is_solid(cell : CellType) -> bool:
    if cell == CellType.BRICK: return True
    if cell == CellType.BLOCK: return True
    return False

def is_solid_in_map(map : list[list[int]], x : int, y : int) -> bool:
    return is_solid(map[y][x])

def validate_map(map : GameMap, raise_errors : bool = False) -> bool:
    door_count : int = 0
    for y, row in enumerate(map):
        for x, cell in enumerate(row):
            if cell == CellType.DOOR:
                door_count += 1
    if door_count != 1: 
        if raise_errors: raise InvalidMapError(f'Map has {door_count} doors instead of 1!')
        return False
    return True

def load_map(map_name : str, strict = False) -> SavedMap|None:
    try:
        with open(f'non_pygame/maps/{map_name}.json', 'r') as file:
            map_data : SavedMap = json.load(file)
    except FileNotFoundError:
        print('Map does not exist!')
    validate_map(map_data['map'], raise_errors=True)
    return map_data
    

class Game:
    def __init__(self, starting_map : list[list[int]], start_player_pos : list[int, int], start_orientation : int = 1):
        if not validate_map(starting_map): raise InvalidMapError('Map isnt valid!')
        self.map : list[list[int]] = starting_map
        self.player_x : int = start_player_pos[0]
        self.player_y : int = start_player_pos[1]
        self.player_holding_block : bool = False
        self.player_direction : int = start_orientation
        self.door_coords : list[int, int]
        for y, row in enumerate(self.map):
            for x, cell in enumerate(row):
                if cell == CellType.DOOR:
                    self.door_coords = [x, y]
                    return
    
    @staticmethod
    def from_game_state(game_state : GameState, copy_map : bool = False) -> 'Game':
        new_game = Game(game_state['map'], [game_state['player_x'], game_state['player_y']], game_state['player_direction'])
        new_game.player_holding_block = game_state['player_holding_block']
        if copy_map: new_game.map = deepcopy(new_game.map)
        return new_game
    
    @staticmethod
    def from_saved_map(saved_map : SavedMap, copy_map : bool = False) -> 'Game':
        new_game = Game(saved_map['map'], [saved_map['start_x'], saved_map['start_y']], saved_map['start_direction'])
        if copy_map: new_game.map = deepcopy(new_game.map)
        return new_game
    
    def to_game_state(self) -> GameState:
        game_state : GameState = {
            'map' : self.map,
            'player_x' : self.player_x,
            'player_y' : self.player_y,
            'player_direction' : self.player_direction,
            'player_holding_block' : self.player_holding_block
        }
        return game_state
    
    def get_at(self, x : int, y : int):
        return self.map[y][x]
    
    def get_above_player(self) -> CellType:
        return self.map[self.player_y - 1][self.player_x]
    
    def get_below_player(self) -> CellType:
        return self.map[self.player_y + 1][self.player_x]

    def get_facing_player(self) -> CellType:
        return self.map[self.player_y][self.player_x + self.player_direction]
    
    def get_above_and_facing_player(self) -> CellType:
        return self.map[self.player_y - 1][self.player_x + self.player_direction]

    def up_legal(self) -> bool:
        facing_cell : CellType = self.get_facing_player()
        if is_solid(facing_cell):
            target_cell : CellType = self.get_above_and_facing_player()
            if not is_solid(target_cell):
                return True
        return False

    def up(self) -> bool:
        if self.up_legal():
            self.player_x += self.player_direction
            self.player_y -= 1
            return True
        return False
    
    def left_legal(self) -> bool:
        return True
    
    def left(self) -> bool:
        self.player_direction = -1
        target_cell : CellType = self.get_facing_player()
        if not is_solid(target_cell):
            self.player_x += self.player_direction
            if self.player_holding_block:
                if self.get_above_player() != CellType.EMPTY:
                    self.player_holding_block = False
                    self.drop_block(self.player_x - self.player_direction, self.player_y)
            while not is_solid(self.get_below_player()):
                self.player_y += 1
                if self.player_y > 9999: raise InvalidMapError('No floor detected!')
        return True
    
    def right_legal(self) -> bool:
        return True
    
    def right(self) -> bool:
        self.player_direction = 1
        target_cell : CellType = self.get_facing_player()
        if not is_solid(target_cell):
            self.player_x += self.player_direction
            if self.player_holding_block:
                if self.get_above_player() != CellType.EMPTY:
                    self.player_holding_block = False
                    self.drop_block(self.player_x - self.player_direction, self.player_y)
            while not is_solid(self.get_below_player()):
                self.player_y += 1
                if self.player_y > 9999: raise InvalidMapError('No floor detected!')
        return True
    
    def down_legal(self) -> bool:
        if self.player_holding_block:
            above_facing_cell : CellType = self.get_above_and_facing_player()
            if above_facing_cell != CellType.EMPTY:
                return False
            return True
        else:
            facing_cell : CellType = self.get_facing_player()
            above_facing_cell : CellType = self.get_above_and_facing_player()
            above_cell : CellType = self.get_above_player()
            if facing_cell == CellType.BLOCK and above_facing_cell == CellType.EMPTY and above_cell == CellType.EMPTY:
                return True
            return False
    
    def down(self) -> bool:
        if not self.down_legal(): return False
        if self.player_holding_block:
            self.player_holding_block = False
            self.drop_block(self.player_x + self.player_direction, self.player_y - 1)
        else:
            self.player_holding_block = True
            self.map[self.player_y][self.player_x + self.player_direction] = CellType.EMPTY
        return True

    
    def drop_block(self, x : int, y : int):
        while self.map[y + 1][x] == CellType.EMPTY:
            y += 1
            if y > 9999: raise InvalidMapError('No floor detected!')
        self.map[y][x] = CellType.BLOCK
    
    def render_terminal(self, scale : int = 1):
        ressources : str = ' -OD'
        player_ressource : str = '>' if self.player_direction == 1 else '<'
        lines : list[str] = []
        for y, y_level in enumerate(self.map):
            line = ''.join(item for item in map(lambda cell: ressources[cell] * scale, y_level))
            if self.player_y - 1 == y:
                if self.player_holding_block: line = line[:self.player_x * scale] + ressources[CellType.BLOCK] * scale + line[(self.player_x + 1) * scale:]
            if self.player_y == y:
                line = line[:self.player_x * scale] + player_ressource * scale + line[(self.player_x + 1) * scale:]
            for _ in range(scale): lines.append(line)
        for line in lines:
            print(line)
    
    def game_won(self) -> bool:
        if self.player_x == self.door_coords[0] and self.player_y == self.door_coords[1]:
            return True
        return False
    
    def get_binds(self) -> tuple[dict[int, Callable[[], bool]], dict[int, Callable[[], bool]]]:
        verifications : dict[int, Callable[[], bool]] = {
            ActionType.DOWN.value : self.down_legal,
            ActionType.UP.value : self.up_legal,
            ActionType.LEFT.value : self.left_legal,
            ActionType.RIGHT.value : self.right_legal,
        }
        actions : dict[int, Callable[[], bool]] = {
            ActionType.DOWN.value : self.down,
            ActionType.UP.value : self.up,
            ActionType.LEFT.value : self.left,
            ActionType.RIGHT.value : self.right,
        }
        return verifications, actions


def render_terminal_gamestate(game_state : GameState):
    ressources : str = ' XOD'
    lines : list[str] = []
    for y, y_level in enumerate(game_state['map']):
        line = ''.join(item for item in map(lambda cell: ressources[cell], y_level))
        if game_state['player_y'] == y:
            line[game_state['player_x']] = 'Y'
        lines.append(line)
    for line in lines:
        print(line)

def test1():
    clear_console()
    with open('maps/map_test.json', 'r') as file:
        test_map_data : SavedMap = json.load(file)
    game = Game.from_saved_map(test_map_data)
    game.render_terminal()

def get_action() -> ActionType|str:
    while True:
        response : str = input("What now?\n").upper()
        allowedset1 = ['0', '1', '2', '3']
        allowedset2 = ['UP', 'DOWN', 'LEFT', 'RIGHT']
        allowedset3 = ['HELP', 'QUIT']
        if response in allowedset1:
            return ActionType(int(response))
        elif response in allowedset2:
            return ActionType[response]
        elif response in allowedset3:
            return response
        else:
            print("Illegal input! Try again.")

def interactive_test():
    with open('maps/map_test.json', 'r') as file:
        test_map_data : SavedMap = json.load(file)
    game = Game.from_saved_map(test_map_data)
    verifications : dict[ActionType, Callable[[], bool]] = {
        ActionType.DOWN : game.down_legal,
        ActionType.UP : game.up_legal,
        ActionType.LEFT : game.left_legal,
        ActionType.RIGHT : game.right_legal,
    }
    actions : dict[ActionType, Callable[[], bool]] = {
        ActionType.DOWN : game.down,
        ActionType.UP : game.up,
        ActionType.LEFT : game.left,
        ActionType.RIGHT : game.right,
    }
    clear_console()
    while True:
        game.render_terminal()
        decision = get_action()
        if decision == 'QUIT':
            print('Goodbye!')
            exit()
        elif decision == 'HELP':
            print('Cant help ya right now!')
        else:
            if verifications[decision]():
                actions[decision]()
                if game.game_won():
                    clear_console()
                    game.render_terminal()
                    print("You won!")
                    exit()
                clear_console()
            else:
                clear_console()
                print("Illegal Move!")

TEST_MAP : SavedMap = load_map('map_test')
TEST_MAP2 : SavedMap = load_map('map_test2')

if __name__ == '__main__':
    interactive_test()

