#! /usr/bin/env python
from critters import *
from dungeon_generators import *
import game_input
from gui import  *
from game_input import *
from features import *
from map import Map


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
                    break
                critter.take_turn()
    game_input.readkey()


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
        return True


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
    dg = RandomRoomGenerator()
    map = Map(dg.map_by_name(map_name), player)
    map.place_monsters()
    map.init_fov()
    player.x, player.y = find_passable_square(map.map)

    gui.render_map(map,player)

def handle_wait():
    if gl.__game_state__ == "playing":
        gl.__turn_count__ += 1
    return True


if __name__ == "__main__":
    global map
    gui = LibtcodGui()
    player = Player()
    player.camx2 = VIEWPORT_WIDTH -1
    player.camy2 = VIEWPORT_HEIGHT - 1

    dg = CaveGenerator(100, 100)
    dg.generate()
    #map = dg.finish()
    #map = Map(dg.finish())

    #    dg = RoomsCoridorsGenerator(80, 40)
    #    dg.generate()
    #    map = Map(dg.finish())
    #dg = StaticGenerator()
    #dg = RandomRoomGenerator()
    #dg.generate()

    map = Map(dg.finish(), player)
    map.place_monsters()
    map.init_fov()
    player.x, player.y = find_passable_square(map.map)
    main_loop()
