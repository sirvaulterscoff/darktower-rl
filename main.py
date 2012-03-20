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
from rlfl import delete_all_maps
import inventory

try:
    import psyco ; psyco.full()
except ImportError:
    psyco = None
    print 'Sadly no psyco'

def main_loop():
    global map
    while gl.is_playing() and not gui.window_closed():
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
                critter.take_turn(player, cost)
        gui.render_messages(map, player)

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
    if gl.is_playing():
        if gl.__lookmode__:
            gui.handle_lookaround(dx, dy, map)
            return
        take_turn, fov_recompute, cost = player.move(dx, dy)
        map.player_moved()
        if fov_recompute:
            gl.__fov_recompute__ = True
        if take_turn:
            gl.__turn_count__ += 1
        return cost

def handle_inventory():
    #displayes inventory
    if not gl.is_playing():
        return
    gl.set_inventory()
    if not gui.render_inventory(player, "examine", handle_examine_invitem):
        #user pressed exit key
        gl.set_playing()
        return None

def handle_examine_invitem(player, item):
    gui.render_tile_description(item)

def handle_lookaround():
    #handles look-around
    if not gl.is_playing():
        return
    gl.__lookmode__ = not gl.__lookmode__
    gui.toggle_lookmode()

def handle_quit():
    gl.__game_state__ = "quit"

def handle_cancel():
    if gl.is_inventory():
        gl.set_playing()
        return
    if gl.__lookmode__:
        gl.__lookmode__ = False
        gui.toggle_lookmode()
    return False

def handle_e_action():
    global map
    #handles actions bound to e key - eat, examine
    if gl.__lookmode__:
        gui.render_examine(player, map)
        key = game_input.readkey()


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
    if gl.is_playing():
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
    return cost

def handle_ascend():
    if not map:
        return False
    global map
    cost = player.ascend(map)
    if cost:
        gl.__fov_recompute__ = True
        gui.reset()
    return cost

def handle_pickup():
    if gl.is_playing():
        global map
        cost = player.pickup(map, lambda x: gui._render_inventory(x, 'pick up', multiple=True))
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
from items import HealingPotion
player.inventory.items.append(HealingPotion)
gl.player = player

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
from storytelling.npc import KingNPC, DeityNPC

king_npc = KingNPC()
king_npc.name = 'The Great King'
king_npc.deity = DeityNPC()
king_npc.deity.name = 'OMG'
king_npc.deity.altar_name = 'Bone altar of Kikubaaquadgha'
#requests.append(MapRequest('crypt', {'corpse': king_npc}))
requests.append(MapRequest('tower' , {'map_id' : 'tower_1', 'xy': (0, 0)}))
requests.append(MapRequest('tower' , {'map_id' : 'tower_1', 'xy': (11, 2)}))
requests.append(MapRequest('tower' , {'map_id' : 'tower_2', 'xy': (2, 15)}))
#map = DungeonGenerator.generate_map('rooms_corridor', theme='crypt', width=10, height=10, requests=requests )
#map = DungeonGenerator.generate_map('tesselate', theme='crypt', width=10, height=10, requests=requests )
#map = DungeonGenerator.generate_map('compound_tesselate_corridor', theme='crypt', width=10, height=10, requests=requests )
map = DungeonGenerator.generate_map('cave', theme='crypt', width=10, height=10, requests=requests )


map = Map(map)
map.prepare_level()
map.place_player(player)
map.configure()
map.place_random_monsters()
map.init_fov()

def main():
    main_loop()


#import cProfile
#cProfile.run('main()')
if __name__ == "__main__":
    main()

