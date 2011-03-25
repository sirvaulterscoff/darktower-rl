from critters import *
from dungeon_generators import *
import game_input
from gui import  LibtcodGui
from game_input import *
from features import *
from map import Map

recompute_fov = True

def main_loop():
	global recompute_fov
	while gl.__game_state__ != "quit":
		if recompute_fov:
			recompute_fov = False
			map.recompute_fov()
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
	if gl.__game_state__ == "playing":
		if player.move(dx, dy):
			recompute_fov = True
			gl.__turn_count__ += 1

def handle_quit():
	gl.__game_state__ = "quit"

def handle_wizard():
	gl.__wizard_mode__ = True

def handle_wait():
	gl.__turn_count__ += 1
	#TODO handle wait properly

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
map = Map(dg.finish(), player)

map.place_monsters()

map.init_fov()
player.x, player.y = find_passable_square(map.map)
main_loop()
