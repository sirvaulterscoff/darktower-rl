#! /usr/bin/env python
from critters import *
from dungeon_generators import MapRequest
import game_input
from gui import  *
from game_input import *
from features import *
from map import Map
from dg import DungeonGenerator
from player import Player
from scheduler import Scheduler
from rlfl import delete_all_maps

try:
    import psyco ; psyco.full()
except ImportError:
    print 'Sadly no psyco'

def main_loop():
    global map
    while gl.__game_state__ == "playing" and not gui.window_closed():
        gui.render_map(map, player)
        if gl.__show_chapter__:
            gui.render_intro(gl.__chapter_text__)
            gl.__show_chapter__ = None
        #gui.clear_all(map.map_critters)
        gui.render_ui(player)
        key = game_input.readkey()
        cost = handle_key(key)
        if cost:
            for critter in map.critters: #we only move critters from current level
                if gl.__game_state__ == "died":
                    game_input.readkey()
                    break
                critter.take_turn(player)
            gl.scheduler.waterline = cost
            events = gl.scheduler.get_scheduled()
            for event in events:
                event()
                #todo render moving creatures here
            gl.scheduler.next_turn()
        gui.render_messages()

def handle_key(key):
    command = parse_key(key)
    if command is None: return
    if isinstance(command, str):
        return globals()["handle_" + command]()
    else:
        name, args = command
        return globals()["handle_" + name](*args)


def handle_move(dx, dy):
    global map
    if gl.__game_state__ == "playing":
        take_turn, fov_recompute, cost = player.move(dx, dy)
        map.player_moved()
        if fov_recompute:
            gl.__fov_recompute__ = True
        if take_turn:
            gl.__turn_count__ += 1
        return cost


def handle_quit():
    gl.__game_state__ = "quit"


def handle_wizard():
    gl.__wizard_mode__ = True

def handle_toggle_map():
    global map
    if not gl.__wizard_mode__:
        return
    map_name = gui.render_dialog('Enter map name')
    gui.clear_screen()
    dg = StaticRoomGenerator()
    _map = dg.map_by_name(map_name)
    if not _map:
        gl.message('No such map', 'CRITICAL')
        gui.render_messages()
        return
    map = Map(_map)
    map.place_player(player)
    map.place_random_monsters()
    map.init_fov()
    gui.viewport = None
    gui.render_map(map,player)

def handle_kill_all_humans():
    global map
    if not gl.__wizard_mode__:
        return
    map.map_critters = []
    map.critter_xy_cache.clear()


def handle_search():
    if gl.__game_state__ == "playing":
        global map
        gl.message('You check your surroundings')
        cost = player.search(map)
        return cost

def handle_descend():
    if not map:
        return False
    global map
    cost = player.descend(map)
    if cost:
        gl.__fov_recompute__ = True
        gui.reset()
        gl.scheduler.schedule_player_action(player.action_cost.stairsdown / 2, lambda: player.search(map))
    return cost

def handle_ascend():
    if not map:
        return False
    global map
    cost = player.ascend(map)
    if cost:
        gl.__fov_recompute__ = True
        gui.reset()
        gl.scheduler.schedule_player_action(player.action_cost.stairsdown / 2, lambda: player.search(map))
    return cost


def exit():
    print 'Exiting...'
    delete_all_maps()

from atexit import register
register(exit)
global map
gui = LibtcodGui()
gl.gui_listener = gui
player = Player()
player.camx2 = VIEWPORT_WIDTH -1
player.camy2 = VIEWPORT_HEIGHT - 1
gl.player = player
gl.scheduler = Scheduler()

#dg = CaveGenerator(60, 60)
#dg = CityGenerator('',80, 40, 3, break_road=1000, room_placer=CityGenerator.generate_rooms_along_road)
#dg = CityGenerator('',80, 40, 5, break_road=5, room_placer=CityGenerator.generate_rooms_along_road)
#dg = CityGenerator('',80, 40, 2, break_road=5)
#map = dg.finish()
#map = Map(dg.finish())

#    dg = RoomsCoridorsGenerator(80, 40)
#    dg.generate()
#    map = Map(dg.finish())
#dg = StaticRoomGenerator(type='')
#dg.generate()

#map = Map(dg.finish())
#map.place_monsters()
requests=[]
#requests.append(MapRequest('crypt', None))
requests.append(MapRequest('tower' , {'map_id' : 'tower_2'}))
map = DungeonGenerator.generate_map('null', theme='crypt', width=10, height=10, requests=requests )


map = Map(map)
map.prepare_level()
map.place_player(player)
map.configure()
#map.place_random_monsters()
map.init_fov()

def main():
    main_loop()


#import cProfile
#cProfile.run('main()')
if __name__ == "__main__":
    main()

