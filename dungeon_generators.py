from random import randrange
from features import *

class AbstractGenerator(object):
    pass


class CaveGenerator(AbstractGenerator):
    def __init__(self, length, width, open_area=0.4):
        self.length = length
        self.width = width
        self.open_area = open_area
        self._map = [[FT_ROCK_WALL
                     ]]
        self.generate()

    def generate_border(self):
        for j in range(0, self.length):
            self._map[j][0] = FT_FIXED_WALL
            self._map[j][self.width - 1] = FT_FIXED_WALL

        for j in range(0, self.width):
            self._map[0][j] = FT_FIXED_WALL
            self._map[self.length - 1][j] = FT_FIXED_WALL


    def generate(self):
        for r in range(0, self.length):
            row = []
            for c in range(0, self.width):
                row.append(FT_ROCK_WALL)
            self._map.append(row)

        self.generate_border()
        walls_left = int(self.length * self.width * (1 - self.open_area))
        while walls_left > 0:
            rand_x = randrange(1, self.length - 1)
            rand_y = randrange(1, self.width - 1)

            if self._map[rand_x][rand_y] == FT_ROCK_WALL:
                self._map[rand_x][rand_y] = FT_FLOOR
                walls_left -= 1


class StaticGenerator(AbstractGenerator):
    def __init__(self):
        pass

    def generate(self):
        return [
                '#######################',
                '## ## ## ## ## ## ## ##',
                '#                     #',
                '#########     #########',
                '###   ###     ###   ###',
                '###   ###     ###   ###',
                '#########     #########',
                '########### ###########',
                '#                     #',
                '#  #   #       #   #  #',
                '#    #   #   #   #    #',
                '#                     #',
                '###########@###########'
        ]
  