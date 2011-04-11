import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from dungeon_generators import CaveGenerator, parse_string, StaticGenerator

from features import *
import unittest


class TestCaveGenerator(unittest.TestCase):
    def testFinish(self):
        sg = StaticGenerator()
        gen = CaveGenerator(5, 5)
        gen._map = sg.parse_string(['#####',
                                 '#   #',
                                 '# # #',
                                 '#   #',
                                 '#####'])[0]
        map = gen.finish()
        print_map(map)
        etalon_map = [[FT_ROCK_WALL() for i in range(0, 5)],
                      [FT_ROCK_WALL(), FT_ROCK_WALL(), FT_FLOOR(), FT_FLOOR(), FT_ROCK_WALL()],
                      [FT_ROCK_WALL(), FT_FLOOR(), FT_FLOOR(), FT_FLOOR(), FT_ROCK_WALL()],
                      [FT_ROCK_WALL(), FT_ROCK_WALL(), FT_FLOOR(), FT_FLOOR(), FT_ROCK_WALL()],
                      [FT_ROCK_WALL() for i in range(0, 5)]]


        y,x = 0,0
        for row in map:
            for item in row:
                assert item.char == etalon_map[y][x].char
                x +=1
            y += 1
            x = 0


def print_map(map):
    for row in map:
        str = ''
        for item in row:
            str += item.char
        print(str)
