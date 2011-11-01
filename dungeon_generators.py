import os
from random import randrange, random, choice, shuffle
from features import features
import thirdparty.libtcod.libtcodpy as libtcod
import util
import des
from copy import deepcopy
from items import Item, items
from types import FunctionType
from critters import mobs

logger = util.create_logger('DG')
ft = util.NamedMap(features)

default_map_chars = {'#': ft.rock_wall,
	' ': ft.floor,
	'.': ft.floor,
	',': ft.grass,
	'+': ft.door,
	'0': ft.window,
	'{' : ft.fountain,
	'<' : ft.stairs_up,
	'>' : ft.stairs_down,
	'h' : ft.chair,
	'T' : ft.table,
	'8' : ft.bed,
    }

def parse_string(mapBytes, map_chars, mapDef=None, items=None, mobs=None):
    new_map = []
    x, y = 0, 0
    if isinstance(mapBytes, list):
        iterable = mapBytes
    elif isinstance(mapBytes, str):
        iterable = mapBytes.splitlines()

    for line in iterable:
        if len(line) < 1 :continue
        new_map.append([])
        for char in line:
            ft = map_chars.get(char)
            #it can me mob definition
            if ft is None and mapDef:
                    if char == '@':
                        mapDef.entry_pos = (x, y)
                        ft = mapDef.floor(id='entry_pos')
                    else:
                        ft = mapDef.floor()
                    if mobs and mobs.has_key(char):
                        newMob = mobs[char]
                        newMob.x, newMob.y = x, y
                        if not mapDef.mobs:
                            mapDef.mobs = []
                        mapDef.mobs.append(newMob)
                    elif items and items.has_key(char):
                        if not mapDef.items:
                            mapDef.items = []
                        newItem = mapDef.items[char]
                        mapDef.items.append(newItem)
                        newItem.x, newItem.y = x, y
            #todo remove this check once all dungeon features are parametrized classes
            if getattr(ft, 'invisible', False) and mapDef:
                ft_delegate = mapDef.floor()
                if callable(ft):
                    ft = ft()
                ft.set_target(ft_delegate)

            if ft is None:
                raise RuntimeError('failed to parse char ' + char)
            new_map[y].append(ft)
            x += 1
        y += 1
        x = 0
    return new_map

class FeatureRequest(object):
    """ Holds info for dungeon generator about specific feature that should be placed
    on the map during mapgen """
    def __init__(self, mapdef, params={}):
        self.mapdef = mapdef
        self.params = params
        self.mapdef.tune(params)


class MapRequest(object):
    """Holds info for dungeon generator about specific map to load from des """
    def __init__(self, type, params={}):
        self.type = type
        #available sizes are large, mini?, None
        self.size = None
        self.params = {}

    def __repr__(self):
        return "MapRequest type=%s size=%s params=%s" % (self.type, self.size, self.params)


class RegionRequest(object):
    """Holds info about specific region request (i.e. forest, city etc)"""
    pass

#todo move entire class to des.py
class MapDef(object):
    parent = None
    current_level = 0
    def __init__(self, parent=None):
        self.parent = parent
        self.id = ''
        self.max_levels = 0
        """ Used in multi-layered maps. Holds references to another """
        self.levels = {}
        self.floor = ft.floor
        self.mobs = {}
        self.items = {}
        self.map = None
        self.entry_pos = None
        """ There is several available modes
        include = places a map over already generated map (i.e. place a house in forest)
        overflow = place a map over generated map, possibly morphing it into original map 
        (i.e. can remove some walls or features)
        asis = this map is already a fully functional map - similar to include but will not generate
        neither monsters nor traps/items on that map
        """
        self.mode = 'overflow'
        """Terrain defines what type of dungeon generator is suitabe for this map.
        Map placement/generator selection can use two separate algorithms:
            1. we have specific generator defined and when we place our submaps we
            check terrain type for each, making sure it's the same as current generator
            2. we have a request for specific map type (i.e. crypt) - we choose a map
            and see what generator would be apropriate for that map (checking attr terrain)
        """
        self.terrain = None
        """Require only one map with such id"""
        self.unique = False
        """ Sets the minimum hd which is allowed for this map """
        self.HD = 0
        """ How common is this map """
        self.common = 10
        """ Whats the chance of selecting this map """
        self.chance = 0
        """ Rooms already on that map """
        self.rooms = {}
        self.width = 0
        self.height = 0
        self.orient = 'RANDOM'
        self.prepared = False
        """ Speicifes where dungeon generator should place this room, valid option are:
            -SW, SE, NW, NE, CENTER, NONE
        """
        self.position = None
        self.subst = {}
        self.map_chars = default_map_chars.copy()

    def _prepare_subst(self):
        calc = {}
        for k,v in self.subst.iteritems():
            calc[k] = self._parse_value(v)
        self.map_chars.update(calc)
        self.mons_chars = {}
        if hasattr(self, 'mons'):
            for k,v in self.mobs.iteritems():
                self.mons_chars[k] = self._parse_value(v)
        print 'substs:'
        for k,v in self.map_chars.items():
            print '%s => %s ' %(k, v)

    def _parse_value(self, v):
        #todo delete this
        """Parses value from SUBST or MONS tags. if it starts as $ - it's a script"""
        if isinstance(v, str):
            res = globals()[v.strip()]
        else:
            res = v
        #now check if it's type
        if isinstance(res, FunctionType):
            return res()
        return res

    def prepare(self):
        if self.prepared:
            return
        if not self.parent:
            self.level = 0 #disable autoleveling for des parsing
            self.max_levels = len(self.levels)
        self._prepare_subst()
        self.map = parse_string(self.map, self.map_chars, self, items, mobs)
        for level in self.levels.values():
            level.map = parse_string(level.map, level.map_chars, level, items, mobs)
        for lvl in self.levels.values():
            lvl.prepare() #todo check that multilevels actualy prepare
        self.height = len(self.map)
        self.width = len(self.map[0])
        self.prepared = True

    def tune(params = {}):
        """ Tunes the map - i.e. adjust some of it parameters, or place items, or monsters """
        #todo map script callback

    def find_feature(self, id=None, oftype=None, multiple=False, filter=None):
        """ Finds feature from map by id (if specified) or by certain type name (if specified
        if multiple => True - all matching items will be returned list of tuples. Otherwise
        only single tuple is returned
        filter is a lambda expression invoked on each found item
        returns tuple tile, x, y
        """
        res = []
        x, y = 0,0
        for line in self.map[self.base_level]:
            for char in line:
                if id:
                    if hasattr(char, 'id') and char.id == id:
                        if filter and not filter(char): continue
                        if multiple:
                            res.append((char, x, y))
                        else:
                            return char, x, y
                elif oftype:
                    if char.__class__.__name__ == oftype:
                        if filter and not filter(char): continue
                        if multiple:
                            res.append((char, x, y))
                        else:
                            return char, x, y
                x+=1
            y+=1
            x=0
        if multiple and len(res):
            return res
        return None

    def replace_feature_atxy(self, x, y, with_what):
        ft = with_what
        if callable(with_what):
            ft = with_what()
        if isinstance(ft, type):
            ft = ft()

        self.map[self.base_level][y][x] = ft

    def __setattr__(self, name, value):
        if name == 'map_chars' or name=='levels' or name=='prepared':
            object.__setattr__(self, name, value)
            return
        if name == 'level': #here we switch level
            if value > 0:
                self.current_level = value
                self.levels[value] = MapDef(self)
                self.levels[value].current_level = value
            else:
                object.__setattr__(self, 'current_level', value)
            return
        if self.parent: #already at child record
            object.__setattr__(self, name, value)
            return
        if self.current_level > 0: #set on child record
            object.__setattr__(self.levels[self.current_level], name, value)
        else:
            object.__setattr__(self, name, value)

#    def __getattribute__(self, name):
#        if name == 'levels' or name == 'current_level':
#            return object.__getattribute__(self, name)
#        if self.current_level > 0:
#            next = object.__getattribute__(self, 'levels')[self.current_level]
#            try:
#                return object.__getattribute__(next, name)
#            except AttributeError: #inner level has no such attr
#                return object.__getattribute__(self, name)
#        else:
#            return object.__getattribute__(self, name)

class Rect:
    def __init__(self, x, y, width, heigh):
        self.x1 = x
        self.y1 = y
        self.x2 = x + width
        self.y2 = y + heigh

    def center(self):
        center_x = (self.x1 + self.x2) / 2
        center_y = (self.y1 + self.y2) / 2
        return center_x, center_y

    def intersect(self, other):
        return (self.x1 <= other.x2 and self.x2 >= other.x1 and
                self.y1 <= other.y2 and self.y2 >= other.y1)


class AbstractGenerator(object):
    def __init__(self, length, width):
        self._map = [[ft.rock_wall()
                      for i in range(0, length)]
                     for j in range(0, width)]

    def generate(self):
        pass
    def generate_border(self):
        for j in range(0, self.length):
            self._map[0][j] = ft.fixed_wall()
            self._map[self.width - 1][j] = ft.fixed_wall()

        for j in range(0, self.width):
            self._map[j][0] = ft.fixed_wall()
            self._map[j][self.length - 1] = ft.fixed_wall()


class CaveGenerator(AbstractGenerator):
    def __init__(self, length, width, open_area=0.60):
        self.length = length
        self.width = width
        self.open_area = open_area
        self._map = [[ft.rock_wall()
                      for i in range(0, length)]
                     for j in range(0, width)]


    def generate(self):
        self.generate_border()
        walls_left = int(self.length * self.width * self.open_area)
        #we don't want this process to hang
        ticks = self.length * self.width
        while walls_left > 0:
            if not ticks:
                print("Map generation tackes too long - returning as is")
                break
            rand_x = randrange(1, self.length - 1)
            rand_y = randrange(1, self.width - 1)

            if self._map[rand_y][rand_x].is_wall:
                self._map[rand_y][rand_x] = ft.floor()
                walls_left -= 1
                ticks -= 1

    def finish(self):
        count_walls = self.count_neigh_walls
        wall, floor = ft.rock_wall, ft.floor
        for x in range(1, self.length - 1):
            for y in range(1, self.width - 1):
                wall_count = count_walls(y, x)

                if self._map[y][x].is_floor():
                    if wall_count > 5:
                        self._map[y][x] = wall()
                elif wall_count < 4:
                    self._map[y][x] = floor()

        return self._map


    def count_neigh_walls(self, x, y):
        count = 0
        for row in (-1, 0, 1):
            for col in (-1, 0, 1):
                if not self._map[(x + row)][y + col].is_floor() and not(row == 0 and col == 0):
                    count += 1
        return count


class RoomsCoridorsGenerator(AbstractGenerator):
    def __init__(self, length, width, room_max_size=15, room_min_size=3, max_rooms=30):
        self._map = [[ft.fixed_wall()
                      for i in range(0, length)]
                     for j in range(0, width)]
        self.length = length
        self.width = width
        self.max_rooms = max_rooms
        self.room_min_size = room_min_size
        self.room_max_size = room_max_size

    def generate(self):
        rooms = []
        num_rooms = 0
        ticks = self.max_rooms * 5

        for r in range(self.max_rooms):
            if ticks <= 0: break
            ticks -= 1
            if num_rooms > self.max_rooms: break

            width = libtcod.random_get_int(0, self.room_min_size, self.room_max_size)
            height = libtcod.random_get_int(0, self.room_min_size, self.room_max_size)
            #random position without going out of the boundaries of the map
            x = libtcod.random_get_int(0, 0, self.length - width - 1)
            y = libtcod.random_get_int(0, 0, self.width - height - 1)
            new_room = Rect(x, y, width, height)
            if not self.check_room_overlap(rooms, new_room):
                rooms.append(new_room)
                new_x, new_y = new_room.center()
                if num_rooms > 0:
                    prev_x, prev_y = rooms[num_rooms - 1].center()
                    if libtcod.random_get_int(0, 0, 1) == 1:
                        self.create_h_tunnel(prev_x, new_x, prev_y)
                        self.create_v_tunnel(prev_y, new_y, new_x)
                    else:
                        self.create_v_tunnel(prev_y, new_y, prev_x)
                        self.create_h_tunnel(prev_x, new_x, new_y)
                num_rooms += 1

        for room in rooms:
            self.create_room(room)

    def create_h_tunnel(self, x1, x2, y):
        for x in range(min(x1, x2), max(x1, x2)):
            self._map[y][x] = ft.floor()

    def create_v_tunnel(self, y1, y2, x):
        for y in range(min(y1, y2), max(y1, y2)):
            self._map[y][x] = ft.floor()


    def check_room_overlap(self, rooms, new_room):
        for room in rooms:
            if room.intersect(new_room): return True
        return False

    def create_room(self, room):
        for x in range(room.x1 + 1, room.x2):
            for y in range(room.y1 + 1, room.y2):
                self._map[y][x] = ft.floor()

    def finish(self):
        self.generate_border()
        return self._map

file_parsed = False
_parsed_files = {}
_available_maps = {}

def get_map_file(flavour, subfolder='', size=None):
    """ get_map_file (...) => string (or None if nothing found)
    Generates filename for requested map.
    @flavour is the name of the map (e.g. flavour='crypt' will return 'crypt.des')
    @subfolder (optional) allows to reach subdirs in data folder
    @size is the prefix for the name (e.g. flavour='crypt' and prefix='mini' will produce mini_crypt.des
    """
    prefix = '..'
    for file in os.listdir('.'):
        if file == 'data':
            prefix = '.'
            break
    for file in os.listdir(prefix + '/data/maps/' + subfolder):
        name = flavour + '.des'
        if size:
            name = size + '_' + name
        if file.find(name) > -1:
            if not file.endswith('.des'): continue
            logger.debug('Parsing mapfile ' + file)
            return os.path.join(prefix, 'data/maps/' + subfolder, file)
    return None

def parse_file(map_file):
    maps = des.parseFile(map_file, MapDef, [items, features, mobs])
    _parsed_files[map_file] = maps
    for map in maps:
        _available_maps[map.id] = map
    return maps


class StaticRoomGenerator(AbstractGenerator):
    def __init__(self, flavour='', type='rooms'):
        prefix = '..'
        for file in os.listdir('.'):
            if file == 'data':
                prefix = '.'
                break
        for file in os.listdir(prefix + '/data/maps/' + type):
            if file.find(flavour + '.des') > -1:
                if not file.endswith('.des'): continue
                logger.debug('Parsing mapfile ' + file)
                _map_files.append(os.path.join(prefix, 'data/maps/', type, file))

    def parse_file(self, map_file):
        maps = des.parseFile(map_file, MapDef, [features, items])
        _parsed_files[map_file] = maps
        for map in maps:
            _available_maps[map.id] = map
        return maps

    def finish(self):
        map_file = choice(_map_files)
        if _parsed_files.get(map_file):
            maps = _parsed_files.get(map_file)
        else:
            maps = self.parse_file(map_file)
        map = choice(maps).prepare()
	return map.materialize()

    def random(self):
        map_file = choice(_map_files)
        if _parsed_files.get(map_file):
            maps = _parsed_files.get(map_file)
        else:
            maps = self.parse_file(map_file)
        map = choice(maps).prepare()
	return map.materialize()


    def map_by_name(self, name):
        global file_parsed
        if _available_maps.get(name):
            return _available_maps[name].materialize()
        elif not file_parsed:
            for file in _map_files:
                print 'parsing file ' + str(file)
                self.parse_file(file)
            file_parsed = True
        if not name in _available_maps:
            return None
        map = _available_maps.get(name).prepare()
        return map.materialize()

class CityGenerator(StaticRoomGenerator):
    RANK_CITY = 3
    def __init__(self, flavour, width, height, rank, filler=ft.grass, road=ft.road, break_road=10,
                 room_placer=None):
        ms_start = libtcod.sys_elapsed_milli()
        self.flavour = flavour
        self.width = width
        self.height = height
        #city rank - larger cities have laarger ranks
        self.rank = rank
        self.filler=filler
        self.road=road
        #at what step road should begin to deform
        self.break_road = break_road
        self._map = [[filler()
                      for x in xrange(0, width)]
                        for y in xrange(0,height)]
        ms_end = libtcod.sys_elapsed_milli()
        print 'Filled in '+ str(ms_end - ms_start) + ' ms'
        self.roadminy, self.roadmaxy=height,0
        #method for placing generated rooms
        self.room_placer = room_placer

    def generate(self):
        shops = 0
        hotel = 0
        taverns = util.roll(1, self.rank, -1)
        if self.rank >=3:
            if util.coinflip():
                shops = util.roll(1, self.rank, -2)
            hotel = util.coinflip()
        #roll for number of houses. it'lee be 4-8 houses for small village
        #and 6-12 for town. and much for for large city. but that's it for now
        house_count = util.roll(self.rank,3, self.rank)
        noble_house_count = util.roll(1, self.rank, -3)
        gl.logger.debug('Generating buildings: %d rooms, %d noble, %d tavern, %d shops, %d hotel' % (house_count, noble_house_count, taverns, shops, hotel))
        gen = self.create_room_generator(house_count, noble_house_count, taverns, shops, hotel)
        self.generate_road()

        for x in (noble_house_count, taverns, shops, hotel):
            house_count += util.cap_lower(x, 0, 0)
        gl.logger.debug('Total number of houses: %d' % house_count)
        if self.room_placer is None:
            self.generate_rooms_random_place(house_count, gen)
        else:
            self.room_placer(self, house_count, gen)

    def create_room_generator(self, house_count, noble_house_count, taverns, shops, hotel):
        prefix = ''
        if self.rank <= 3: prefix = 'small_'
        elif self.rank >=7: prefix = 'large_'
        else: prefix = 'med_'
        all_houses = []
        rooms_gen = StaticRoomGenerator(prefix + 'rooms')
        #place general houses
        for i in xrange(0, house_count):
            all_houses.append(lambda : rooms_gen.random())
        #place noble houses
        if noble_house_count > 0:
            noble_room_gen = StaticRoomGenerator(prefix + 'noble')
            for i in xrange(0, noble_house_count):
                all_houses.append(lambda: noble_room_gen.random())
        #place 1 residence
        if self.rank >= 7 and util.coinflip():
            gl.logger.debug('Generating residence')
            residence_room_gen = StaticRoomGenerator('residence')
            all_houses.append(lambda: residence_room_gen.random())
        if taverns > 0:
            tavern_room_gen = StaticRoomGenerator(prefix+'tavern')
            for x in xrange(0, taverns):
                all_houses.append(lambda: tavern_room_gen.random())
        if shops > 0:
            shop_room_gen = StaticRoomGenerator(prefix + 'shop')
            for x in xrange (0, shops):
                all_houses.append(lambda: shop_room_gen.random())
        if hotel > 0:
            hotel_gen = StaticRoomGenerator(prefix + 'hotels')
            all_houses.append(lambda: hotel_gen.random())
        shuffle(all_houses)
        for house in all_houses:
            yield house()

    def generate_rooms_along_road(self, house_count, room_gen, allow_crop = True):
        x = util.roll(2, 3)
        x2 = int(x)
        house_top = house_count / 2 + house_count % 2
        house_bot = house_count / 2
        for z in xrange(0, house_top):
            room = room_gen.next().materialize()
            if house_bot > 0:
                room2 = room_gen.next().materialize()
            y = self.roadminy - len(room) + (self.roadmaxy - self.roadminy)
            y2 = self.roadminy
            xw = x + len(room[0]); xh = y + len(room)
            if xw < self.width and xh < self.height:
                newxy = self.adjust_x_y_anywhere(x, y, xw, xh, -1, allow_crop)
                if newxy is None:
                    continue
                x, y = newxy
                self.copy_room(room, x, y)
                x = xw
                x += util.roll(2,2)
            if house_bot > 0:
                x2w = x2 + len(room2[0])
                y2w = y2 + len(room2)
                if x2w > self.width or y2w > self.height:
                    continue
                newxy2 = self.adjust_x_y_anywhere(x2, y2, x2w, y2w, 1, allow_crop)
                if newxy2 is not None:
                    x2, y2 = newxy2
                    self.copy_room(room2, x2, y2)
                    x2 += len(room2[0])
                    x2 += util.roll(2,2)
                    house_bot -= 1


    def generate_rooms_random_place(self, house_count, room_gen, allow_crop = True):
        occupied = []
        room = None
        iter_cnt = house_count
        while True:
            if iter_cnt < 0: break
            if room is None:
                try:
                    room = room_gen.next().materialize()
                except StopIteration:
                    break
            itercnt = 10
            while True:
                itercnt -= 1
                if itercnt <= 0:
                    room = None
                    break
                w = len(room[0])
                h = len(room)
                x, y = randrange(1, self.width - w), randrange(1, self.height - h)
                pair = self.adjust_x_y_anywhere(x, y, x + w, y + h, allow_crop)
                if pair is None:
                    continue
                x, y = pair
                no_rooms = True
                for placed_room in occupied:
                    new_rect = Rect(x, y, len(room[0]), len(room))
                    if placed_room.intersect(new_rect):
                        no_rooms = False
                        break
                if no_rooms:
                    break

            if room is None: continue
            occupied.append(Rect(x, y, len(room[0]), len(room)))
            self.copy_room(room, x, y)
            iter_cnt -= 1
            room = None

    def copy_room(self, room, x, y):
        x1, y1 = x, y
        for row in room:
            for tile in row:
                self._map[y1][x1] = tile
                x1 += 1
            x1 = x
            y1 += 1

    def adjust_x_y_anywhere(self, x, y, x2, y2, delta = None, allow_crop= True):
        w,h = x2 - x, y2 - y
        #will move up or down
        if delta is None:
            delta = util.coinflip()
            if delta == 0 : delta = -1
        itercnt = 100
        while True:
            itercnt -= 1
            #dont want it to hang foreva
            if itercnt <= 0: return None
            okay = True
            for i in range (x, x2):
                for j in range (y, y2):
                    #if it's a road - then adjust our coords
                    if self._map[j][i].is_road():
                        y += delta; y2 += delta
                        okay = False
                        if min(y, y2) <= 0 or max(y, y2) >= self.height:
                            return None
                        #were not okay, breaking
                        break
                #coords were adjusted break for main While loop
                if not okay:
                    break

            #no road crossed, were safe
            if okay:
                break
            if not allow_crop:
                if x < 0 or y < 0 or x+w >= len(self._map[0]) or y+h >= len(self._map):
                    return None

        return x, y

    def generate_road(self):
        ms_start = libtcod.sys_elapsed_milli()
        _h = self.height / 3
        road_y = randrange(_h - util.roll(1, 10), _h + util.roll(1, 10))
        len_no_break = randrange(self.break_road / 2, self.break_road)
        old_road_y = road_y
        delta = 0
        if self.rank > self.RANK_CITY:
            delta = 1
        for x in xrange(0, self.width):
            len_no_break -= 1
            if len_no_break <= 0:
                len_no_break = randrange(self.break_road / 2, self.break_road)
                y_delta = util.roll(1, 3)
                #nope, try another turn
                if y_delta == 1:
                    len_no_break = 1
                elif y_delta == 2:
                    old_road_y, road_y = road_y, util.cap_lower(road_y - 1, 0, 0)
                    delta = -1
                else:
                    old_road_y, road_y = road_y, util.cap(road_y + 1, self.height)
                    delta = 1

            self.roadminy = min(self.roadminy, road_y)
            self.roadmaxy = max(self.roadmaxy, road_y)
            if old_road_y != road_y:
                self._map[old_road_y][x] = self.road()
                self._map[road_y][x] = self.road()
                old_road_y = road_y
            else:
                self._map[road_y][x] = self.road()
                if self.rank >= self.RANK_CITY:
                    self._map[road_y + delta][x] = self.road()
        ms_end = libtcod.sys_elapsed_milli()
        print 'generated in ' + str(ms_end - ms_start) + ' ms'

    def finish(self):
        return self._map
