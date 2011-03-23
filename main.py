from dungeon_generators import CaveGenerator
from gui import AbstractGui, LibtcodGui
from game_input import *

class Player(object):
	cur_pos_x, cur_pos_y = 0, 0
	char = '@'
	color = [255, 255, 255]

class Critter(Player):
	def __init__(self, char, color, x = 0, y = 0):
		self.char = char
		self.color = color
		self.cur_pos_x = x
		self.cur_pos_y = y

class Tile:
	def __init__(self, blocked, block_sight=None):
		self.blocked = blocked

		if block_sight is None: block_sight = blocked
		self.block_sight = block_sight

critters = []

def main_loop():
	while gui.window_is_active():
		gui.main_loop(critters)
		exit = input.handle_keys()
		if exit:
			break

gui = LibtcodGui()
player = Player()
testCritter = Critter('D', [255,255,0], 20, 20)

critters = [player, testCritter]
input = Input(player)
dg = CaveGenerator(80, 25)
dg.generate()
for i in  range(0, dg.length):
  for j in range(0,dg.width):
      gui.print_critter(i, j, dg._map[i][j].char)
main_loop()

