from dungeon_generators import *
from gui import  LibtcodGui
from game_input import *
from features import *
from map import Map

FOV_ALGORITHM = libtcod.FOV_PERMISSIVE(2)
FOV_LIGHT_WALLS = True
TORCH_RADIUS = 10

class Player(object):
	cur_pos_x, cur_pos_y = 0, 0
	char = '@'
	color = [255, 255, 255]

class Critter(Player):
	def __init__(self, char, color, x=0, y=0):
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

recompute_fov = False
def can_pass(x, y):
	global recompute_fov
	recompute_fov = passable(map.map[x][y])
	return recompute_fov

def main_loop():
	global recompute_fov
	while gui.window_is_active():
		gui.main_loop(critters, map)
		exit = input.handle_keys(can_pass)
		if exit:
			break
		if recompute_fov:
			recompute_fov = False
			libtcod.map_compute_fov(gui.fov_map, player.cur_pos_x, player.cur_pos_y, TORCH_RADIUS, FOV_LIGHT_WALLS, FOV_ALGORITHM)

gui = LibtcodGui()
player = Player()
testCritter = Critter('D', [255, 255, 0], 20, 20)

critters = [player, testCritter]
input = Input(player)
#dg = CaveGenerator(40, 25)
#dg.generate()
#map = dg.finish()
#map = dg.finish()

dg = RoomsCoridorsGenerator(40, 25)
dg.generate()
map = Map(dg.finish())

gui.init_fov(map)
#for i in  range(0, dg.length):
#	for j in range(0, dg.width):
#		gui.print_critter(i, j, map[i][j].char)
gui.main_loop(critters, map)

player.cur_pos_x, player.cur_pos_y = find_passable_square(map.map)


main_loop()

