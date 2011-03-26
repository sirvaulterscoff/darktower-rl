#! /usr/bin/env python
from critters import *
from dungeon_generators import *
import game_input
from gui import  LibtcodGui
from game_input import *
from features import *
from map import Map


def main_loop():
	while gl.__game_state__ != "quit":
		gui.render_all(map, player)
		gui.clear_all(map.map_critters)
		key = game_input.readkey()
		handle_key(key)
		for critter in map.map_critters:
			if gl.__game_state__ == "died":
				break
			critter.take_turn()

def handle_key(key):
    command = parse_key(key)
    if command is None: return
    if isinstance(command, str):
        globals()["handle_" + command]()
    else:
        name, args = command
        globals()["handle_" + name](*args)

def handle_move(dx, dy):
    if gl.__game_state__ == "playing":
        if player.move(dx, dy):
            gl.__fov_recompute__ = True
            gl.__turn_count__ += 1

def handle_quit():
    gl.__game_state__ = "quit"

def handle_wizard():
    gl.__wizard_mode__ = True

def handle_wait():
	if gl.__game_state__ == "playing":
		gl.__turn_count__ += 1
	#TODO handle wait properly


if __name__ == "__main__":
    gui = LibtcodGui()
    player = Player()
    critters = [player]

    dg = CaveGenerator(40, 25)
    dg.generate()
    #map = dg.finish()
    #map = Map(dg.finish())

#    dg = RoomsCoridorsGenerator(80, 40)
#    dg.generate()
#    map = Map(dg.finish())
#    dg = StaticGenerator()
#    dg.generate()
    map = Map(dg.finish(), player)
    map.place_monsters()
    map.init_fov()
    player.x, player.y = find_passable_square(map.map)
    main_loop()
