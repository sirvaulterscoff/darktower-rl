import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import dungeon_generators
import util
from map import Map
from dungeon_generators_tests import print_map

__author__ = 'svs'

class cloud_test(unittest.TestCase):
    def test_cloud_placement(self):
        map = dungeon_generators.parse_string([
                                        '.....',
                                        '..#..',
                                        '.....'])[0]
        def check(x, y):
            if y >= len(map) or x >= len(map[0]):
                return False
            return map[y][x].passable()
        def create(x, y):
            map[y][x].char = "%"
        util.put_cloud(1, 0, check, create)

        assert to_string(map) == '.%%%.n.%#%.n.%%%.n'

    def test_flood_fill(self):
        map = dungeon_generators.parse_string([
                                    '#########',
                                    '#........',
                                    '#########'])[0]
        def check(x, y):
            if y >= len(map) or x >= len(map[0]):
                return False
            return map[y][x].passable()
        def create(x, y):
            map[y][x].char = "%"
        util.flood_fill(1, 1, check, create)
        print_map(map)

def to_string(map):
    str = ''
    for row in map:
        for item in row:
            str += item.char
        str += 'n'
    return str