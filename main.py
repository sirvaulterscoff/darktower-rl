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

recompute_fov = True
def can_pass(x, y):
	global recompute_fov
	recompute_fov = passable(map.map[y][x])
	return recompute_fov

def main_loop():
	global recompute_fov
	while gui.window_is_active():
		if recompute_fov:
			recompute_fov = False
			libtcod.map_compute_fov(gui.fov_map, player.cur_pos_x, player.cur_pos_y, TORCH_RADIUS, FOV_LIGHT_WALLS, FOV_ALGORITHM)
		gui.main_loop(critters, map)
		exit = input.handle_keys(can_pass)
		if exit:
			break

gui = LibtcodGui()
player = Player()
testCritter = Critter('D', [255, 255, 0], 20, 20)

critters = [player, testCritter]
input = Input(player)

dg = CaveGenerator(40, 25)
dg.generate()
map = dg.finish()
map = Map(dg.finish())

#dg = RoomsCoridorsGenerator(80, 40)
#dg.generate()
#map = Map(dg.finish())

#dg = StaticGenerator()
#dg.generate()
#map = Map(dg.finish())

gui.init_fov(map)
#for i in  range(0, dg.length):
#	for j in range(0, dg.width):
#		gui.print_critter(i, j, map[i][j].char)
#gui.main_loop(critters, map)

player.cur_pos_x, player.cur_pos_y = find_passable_square(map.map)
testCritter.cur_pos_x, testCritter.cur_pos_y = find_passable_square(map.map)

main_loop()

#libtcod.console_set_custom_font('fonts/arial10x10.png', libtcod.FONT_TYPE_GREYSCALE | libtcod.FONT_LAYOUT_TCOD)
#libtcod.console_init_root(40, 20, 'darktower-rl', False)
#con = libtcod.console_new(40, 20)
#libtcod.console_print_left(con, 1, 1, libtcod.BKGND_NONE, '1')
#libtcod.console_print_left(con, 0, 5, libtcod.BKGND_NONE, 'y')
#libtcod.console_print_left(con, 5, 0, libtcod.BKGND_NONE, 'x')
#libtcod.console_blit(con, 0, 0, 40, 20, 0, 0, 0)
#libtcod.console_flush()
#input.handle_keys(can_pass)
#



