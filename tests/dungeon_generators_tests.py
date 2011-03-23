import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from dungeon_generators import CaveGenerator, parse_string

from features import *
import unittest


class TestCaveGenerator(unittest.TestCase):
	def testFinish(self):
		gen = CaveGenerator(5, 5)
		gen._map = parse_string(['#####',
								 '#   #',
								 '# # #',
								 '#   #',
								 '#####'])
		map = gen.finish()
		print_map(map)
		etalon_map = [[FT_ROCK_WALL for i in range(0, 5)],
					  [FT_ROCK_WALL, FT_ROCK_WALL, FT_FLOOR, FT_ROCK_WALL, FT_ROCK_WALL],
					  [FT_ROCK_WALL, FT_FLOOR, FT_FLOOR, FT_FLOOR, FT_ROCK_WALL],
					  [FT_ROCK_WALL, FT_FLOOR, FT_FLOOR, FT_FLOOR, FT_ROCK_WALL],
					  [FT_ROCK_WALL for i in range(0, 5)]]

		assert map == etalon_map

def print_map(map):
	for row in map:
		str = ''
		for item in row:
			str += item.char
		print(str)
