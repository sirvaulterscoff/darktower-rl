from critters import *
from dungeon_generators import *
import game_input
from gui import  LibtcodGui
from game_input import *
from features import *
from map import Map

FOV_ALGORITHM = libtcod.FOV_PERMISSIVE(2)
FOV_LIGHT_WALLS = True
TORCH_RADIUS = 10


recompute_fov = True
def can_pass(x, y):
	return map.can_walk(x, y)

def main_loop():
	global recompute_fov
	while gl.__game_state__ != "quit":
		if recompute_fov:
			recompute_fov = False
			libtcod.map_compute_fov(gui.fov_map, player.x, player.y, TORCH_RADIUS, FOV_LIGHT_WALLS, FOV_ALGORITHM)
		gui.main_loop(map, player)
		key = game_input.readkey()
		handle_key(key)

def handle_key(key):
	command = parse_key(key)
	if command is None: return
	if isinstance(command, str):
		globals()["handle_" + command]()
	else:
		name, args = command
		globals()["handle_" + name](*args)

def handle_move(dx, dy):
	global  recompute_fov
	if player.move(dx, dy, can_pass):
		recompute_fov = True

def handle_quit():
	gl.__game_state__ = "quit"

def handle_wizard():
	gl.__wizard_mode__ = True

gui = LibtcodGui()
player = Player()

critters = [player]

#dg = CaveGenerator(40, 25)
#dg.generate()
#map = dg.finish()
#map = Map(dg.finish())

#dg = RoomsCoridorsGenerator(80, 40)
#dg.generate()
#map = Map(dg.finish())
dg = StaticGenerator()
dg.generate()
map = Map(dg.finish())

map.place_monsters()

gui.init_fov(map)
player.x, player.y = find_passable_square(map.map)
main_loop()
