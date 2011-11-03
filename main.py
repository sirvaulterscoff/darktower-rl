#! /usr/bin/env python
from critters import *
from dungeon_generators import MapRequest
import game_input
from gui import  *
from game_input import *
from features import *
from map import Map
from dg import DungeonGenerator
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
        if handle_key(key):
            for critter in map.map_critters:
                if gl.__game_state__ == "died":
                    game_input.readkey()
                    break
                critter.take_turn()
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
    if gl.__game_state__ == "playing":
        take_turn, fov_recompute = player.move(dx, dy)
        if fov_recompute:
            gl.__fov_recompute__ = True
        if take_turn:
            gl.__turn_count__ += 1
        return take_turn


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
    map.place_monsters()
    map.init_fov()
    gui.viewport = None
    gui.render_map(map,player)

def handle_kill_all_humans():
    global map
    if not gl.__wizard_mode__:
        return
    map.map_critters = []
    map.critter_xy_cache = {}

def handle_wait():
    if gl.__game_state__ == "playing":
        gl.__turn_count__ += 1
    return True

def handle_descend():
    if not map:
        return False
    if map.descend():
        gl.__fov_recompute__ = True
        gui.reset()
        return True


if __name__ == "__main__":
    global map
    gui = LibtcodGui()
    player = Player()
    player.camx2 = VIEWPORT_WIDTH -1
    player.camy2 = VIEWPORT_HEIGHT - 1

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
    map = DungeonGenerator.generate_map('null', theme='crypt', width=10, height=10, requests=[MapRequest('crypt')])

    map = Map(map)
    map.prepare_level()
    map.place_player(player)
    map.init_fov()
    main_loop()
