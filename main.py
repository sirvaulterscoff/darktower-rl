from critters import *
from dungeon_generators import *
from gui import  LibtcodGui
from game_input import *
from features import *
from map import Map

FOV_ALGORITHM = libtcod.FOV_PERMISSIVE(2)
FOV_LIGHT_WALLS = True
TORCH_RADIUS = 10


recompute_fov = True
def can_pass(x, y):
	global recompute_fov
	recompute_fov = map.can_walk(x, y)
	return recompute_fov

def main_loop():
	global recompute_fov
	while gui.window_is_active():
		if recompute_fov:
			recompute_fov = False
			libtcod.map_compute_fov(gui.fov_map, player.x, player.y, TORCH_RADIUS, FOV_LIGHT_WALLS, FOV_ALGORITHM)
		gui.main_loop(map, player)
		exit = input.handle_keys(can_pass)
		if exit:
			break

gui = LibtcodGui()
player = Player()

critters = [player]
input = Input(player)

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

