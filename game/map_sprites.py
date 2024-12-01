import pygame
from game.sprite import Sprite
from core.core import core_object

from utils.animation import Animation
from utils.pivot_2d import Pivot2D
from utils.helpers import load_alpha_to_colorkey
from non_pygame.block_dude_core import CellType, SavedMap, get_map_size


class Tile(Sprite):
    active_elements : list['Tile'] = []
    inactive_elements : list['Tile'] = []
    BRICK_TEXTURE : pygame.Surface = pygame.image.load('assets/graphics/tilemap/brick.jpg').convert()
    DOOR_TEXTURE : pygame.Surface = load_alpha_to_colorkey('assets/graphics/tilemap/door_green_colorkey.png', (0, 255, 0))
    PLAYER_TEXTURE : pygame.Surface = load_alpha_to_colorkey('assets/graphics/tilemap/player1_thick.png', (0, 255, 0))
    PLAYER_TEXTURE_MIRRORED : pygame.Surface = load_alpha_to_colorkey('assets/graphics/tilemap/player1_thick_mirrored.png', (0, 255, 0))
    EMPTY_TEXTURE : pygame.Surface = pygame.surface.Surface((300, 300))
    EMPTY_TEXTURE.fill((125, 125, 125))
    BLOCK_TEXTURE : pygame.Surface = pygame.surface.Surface((300, 300))
    BLOCK_TEXTURE.fill((205, 205, 205))
    TEXTURES : dict[CellType, pygame.Surface] = {
        CellType.EMPTY : EMPTY_TEXTURE,
        CellType.BLOCK : BLOCK_TEXTURE,
        CellType.DOOR : DOOR_TEXTURE,
        CellType.BRICK : BRICK_TEXTURE,
        CellType.PLAYER : PLAYER_TEXTURE
    }
    def __init__(self) -> None:
        super().__init__()
        self.tile_type : CellType
        self.current_map : TileMap
        self.grid_pos : list[int, int]
        Tile.inactive_elements.append(self)

    @classmethod
    def spawn(cls, grid_pos : list[int, int], current_map : 'TileMap', cell_type : CellType) -> 'Tile':
        element = cls.inactive_elements[0]

        element.image = cls.EMPTY_TEXTURE
        element.rect = element.image.get_rect()
        element.grid_pos = grid_pos
        element.tile_type = cell_type


        element.position = pygame.Vector2(0,0)
        element.align_rect()
        element.zindex = 0
        element.current_map = current_map
        element.change_type(cell_type)
        element.align_with_map()

        cls.unpool(element)
        return element
    
    def change_type(self, new_cell_type : CellType):
        self.tile_type = new_cell_type
        if new_cell_type == CellType.PLAYER:
            self.image = pygame.transform.scale(self.EMPTY_TEXTURE, (self.current_map.scale, self.current_map.scale))
            if self.current_map.player_direction == 1:
                self.image.blit(pygame.transform.scale(self.PLAYER_TEXTURE_MIRRORED, (self.current_map.scale, self.current_map.scale)), (0,0))
            else:
                self.image.blit(pygame.transform.scale(self.TEXTURES[new_cell_type], (self.current_map.scale, self.current_map.scale)), (0,0))
        else:
            self.image = pygame.transform.scale(self.TEXTURES[new_cell_type], (self.current_map.scale, self.current_map.scale))


    def update(self, delta: float):
        self.align_with_map()

    def align_with_map(self):
        scale = self.current_map.scale
        OW = self.current_map.OUTLINE_WIDTH
        offset = scale + self.current_map.OUTLINE_WIDTH
        topleft = (offset * self.grid_pos[0] + self.current_map.map_rect.left - OW * 4 - OW // 2, offset * self.grid_pos[1] + self.current_map.map_rect.top - OW * 4 - OW // 2)
        self.move_rect('topleft', pygame.Vector2(topleft))
    
    def clean_instance(self):
        self.image = None
        self.color_images = None
        self.color_image_list = None
        self.rect = None
        self._position = pygame.Vector2(0,0)
        self.zindex = None

Sprite.register_class(Tile)
for _ in range(100):
    Tile()

class TileMap(Sprite):
    active_elements : list['TileMap'] = []
    inactive_elements : list['TileMap'] = []
    NOTHING_SURF = pygame.surface.Surface((0,0))
    OUTLINE_WIDTH : int = 1
    def __init__(self) -> None:
        super().__init__()
        self.tiles : list[list['Tile']]
        self.scale : int
        self.player_direction : int
        self.map_rect : pygame.FRect
        self.map_size : tuple[int, int]
        TileMap.inactive_elements.append(self)

    @classmethod
    def spawn(cls, center : tuple[float, float], starting_map : SavedMap, map_scale : int) -> 'Tile':
        element = cls.inactive_elements[0]

        element.image = cls.NOTHING_SURF
        element.rect = element.image.get_rect()

        element.position = pygame.Vector2(0,0)
        element.align_rect()
        element.zindex = -90
        element.scale = map_scale
        element.player_direction = starting_map['start_direction']
        element.map_size = get_map_size(starting_map)
        element.map_rect = pygame.rect.FRect(0, 0, map_scale * element.map_size[0], map_scale * element.map_size[1])
        element.map_rect.center = center
        element.tiles = []
        for y_level, row in enumerate(starting_map['map']):
            new_row = [Tile.spawn([x, y_level], element, cell) for x, cell in enumerate(row)]
            element.tiles.append(new_row)
        element.tiles[starting_map['start_y']][starting_map['start_x']].change_type(CellType.PLAYER)

        element.image = element.make_grid()
        element.rect = element.image.get_rect()
        element.move_rect('center', (round(element.map_rect.center[0]), round(element.map_rect.center[1])))

        cls.unpool(element)
        return element
    
    def make_grid(self) -> pygame.Surface:
        new_surf : pygame.Surface = pygame.surface.Surface(((self.map_size[0]) * (self.scale + self.OUTLINE_WIDTH) + self.OUTLINE_WIDTH,
                                                            (self.map_size[1]) * (self.scale + self.OUTLINE_WIDTH) + self.OUTLINE_WIDTH))
        new_surf.fill('Grey')
        x_size, y_size = new_surf.get_size()
        
        for x in range(0, (self.map_size[0] + 1) * (self.scale + self.OUTLINE_WIDTH) + self.OUTLINE_WIDTH + 1, (self.scale + self.OUTLINE_WIDTH)):
            pygame.draw.rect(new_surf, 'Black', (x, 0, self.OUTLINE_WIDTH, y_size + 1))
        
        for y in range(0, (self.map_size[1] + 1) * (self.scale + self.OUTLINE_WIDTH) + self.OUTLINE_WIDTH + 1, (self.scale + self.OUTLINE_WIDTH)):
            pygame.draw.rect(new_surf, 'Black', (0, y, x_size + 1, self.OUTLINE_WIDTH))
        
        return new_surf
    
    def update(self, delta: float):
        keyboard_map = pygame.key.get_pressed()
        move_vector : pygame.Vector2 = pygame.Vector2(0,0)
        speed : int = 5
        if keyboard_map[pygame.K_a]:
            move_vector += pygame.Vector2(-1, 0)
        if keyboard_map[pygame.K_d]:
            move_vector += pygame.Vector2(1, 0)
        if keyboard_map[pygame.K_s]:
            move_vector += pygame.Vector2(0, 1)
        if keyboard_map[pygame.K_w]:
            move_vector += pygame.Vector2(0, -1)
        if move_vector.magnitude(): move_vector.normalize()
        self.position -= move_vector * speed * delta
        self.map_rect.center = round(self.position)
        self.align_rect()
    
    def clean_instance(self):
        self.image = None
        self.rect = None
        self._position = pygame.Vector2(0,0)
        self.zindex = None

for _ in range(1):
    TileMap()