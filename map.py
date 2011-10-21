""" This module represents critters-map-player interaction.
Map in that case if the game's field where actual actions
take place """
import critters
import features
import gl
from thirdparty.libtcod import libtcodpy as libtcod
from random import randrange
import util
from dungeon_generators import MapDef
from features import DungeonFeature
from collections import Iterable

FOV_ALGORITHM = libtcod.FOV_PERMISSIVE(2)
FOV_LIGHT_WALLS = True
logger = util.create_logger('DG')

class Map(object):
    def __init__(self, map_src):
        self.init(map_src)

    def init(self, map_src):
        self.map_critters = []
        self.critter_xy_cache = {}
        self.current_level = 0
        self.max_levels = 1
        if isinstance(map_src, Iterable):
            if not isinstance(map_src[0], MapDef):
                raise RuntimeError('MapDef should be passed to map object')
            self.map_src = map_src
        elif isinstance(map_src, MapDef):
            self.map_src = [map_src]
        else:
            raise RuntimeError('MapDef should be passed to map object')
        self.map_height = len(self.map)
        self.map_width = len(self.map[0])
        self.square = self.map_height * self.map_width
        self.fov_map = None
        self.map = [None for x in len(self.map_src)]
        #shortcut for self.map[self.current_level]
        self.shortcut = None

    def __getitem__(self, item):
        return self.shortcut[item]

    def prepare_level(self):
        """ This launches preparation on new level.
        1. Checks if a level was already prepared
        2. Materializez it from MapDef object (creates all required tiles)
        """
        if self.map[self.current_level]:
            return
        self.map[self.current_level] = self.__materialize()
        self.shortcut = self.map[self.current_level]
        #todo - now materialize mobs defined for that level

    def __materialize(self):
        _map = self.map_src[self.current_level]
        newmap = []
        logger.debug('Materializing map %dx%d' % (len(_map[0]), len(_map)))
        for y in xrange(0, len(_map)):
            newmap.append([])
            for x in xrange(0, len(_map[0])):
                try:
                    if callable(_map[y][x]):
                        newmap.append(_map[y][x]())
                    elif isinstance(_map[y][x], type):
                        newmap.append(_map[y][x]())
                    if not isinstance(newmap[y][x], DungeonFeature):
                        raise RuntimeError('Not a tile at %d:%d (got %s)' % (y, x, _map[y][x]))
                except IndexError:
                    print 'The ' + str(y) + ' line of map is ' + str(x) + ' len. expected ' + str(self.width)
                    break
        return newmap

    def place_player(self, player):
        pos_set = False
        if isinstance(self.map_src, MapDef):
            if self.map_src.entry_pos.has_key(self.map_src.current_level):
                player.x, player.y = self.map_src.entry_pos[self.map_src.current_level]
                pos_set = True
        if not pos_set:
            player.x, player.y = self.find_passable_square()
        self.player = player
        player.map = self

    def init_fov(self):
        self.fov_map = libtcod.map_new(self.map_width, self.map_height)
        for y in range(self.map_height):
            for x in range(self.map_width):
                self.update_fov_for(x, y)


    def update_fov_for(self, x, y):
        libtcod.map_set_properties(self.fov_map, x, y, not self[y][x].flags & features.BLOCK_LOS,
                                           not self[y][x].flags & features.BLOCK_WALK)
    def recompute_fov(self):
        try:
            libtcod.map_compute_fov(self.fov_map, self.player.x, self.player.y, self.player.fov_range, FOV_LIGHT_WALLS,
                                FOV_ALGORITHM)
        except Exception, e:
            print e

    def place_critter(self, crit_level, crit_hd, x, y):
        crit = util.random_by_level(crit_level, critters.Critter.ALL)
        if crit is None: return
        crit = crit()
        crit.adjust_hd(crit_hd)
        self.map_critters.append(crit)
        self.critter_xy_cache[(x, y)] = crit
        crit.place(x, y, self)

    # basic algo: take player level (xl), and pick random number between xl - 3 and xl + 3.
    # let it be monster HD. Now take random monsters appropirate for this and prev levels (Critter.dlvl <= __dlvl__)
    # set this monster HD to a value defined earlier
    # for OOD monsters - same HD as previous case, and Critter.dlvl <= random(__dlvl__ + 2, __dlvl +3)
    def place_monsters(self):
        #choose random number of monsters
        #3d(dlvl) + 3d2 + 7 monsters total - at least 11 monsters on d1 and up-to 40 on d27
        num_monsters = util.roll(1, gl.__dlvl__, util.roll(3, 2, 7))
        free_squares = -2
        for line in self.map:
            for tile in line:
                if tile.passable(): free_squares += 1

        num_monsters = util.cap(num_monsters, free_squares)
        #was capped ?!
        if num_monsters == free_squares:
            num_monsters = randrange(free_squares /2 , free_squares)

        for i in range(num_monsters):
            #choose random spot for this monster
            x, y = self.find_random_square(self.has_critter_at)
            #determining critter level. it may vary from XL - 3 to XL + 3. To let is scale better multiply by 100
            #cap it to be no lower than 1
            crit_hd = util.cap_lower(randrange(gl.__xl__ - 3, gl.__xl__ + 3), 1, 1)
            self.place_critter(gl.__dlvl__, crit_hd, x, y)

        #check for OOD monster. let's create OOD 10% of the time for now
        if libtcod.random_get_int(0, 0, 100) >= 89:
            crit_level = libtcod.random_get_int(0, gl.__dlvl__ + 2, gl.__dlvl__ + 3)
            crit_hd = util.cap_lower(randrange(gl.__xl__ - 3, gl.__xl__ + 3), 1, 1)
            x, y = self.find_random_square(self.has_critter_at)
            self.place_critter(crit_level, crit_hd, x, y)

    def has_critter_at(self, coords):
        return coords in self.critter_xy_cache

    def get_critter_at(self, x, y):
        return self.critter_xy_cache[(x, y)]

    def remove_critter(self, critter):
        self.critter_xy_cache.pop((critter.x, critter.y))
        self.map_critters.remove(critter)

    def find_random_square(self, occupied):
        startx = libtcod.random_get_int(0, 0, self.map_width)
        starty = libtcod.random_get_int(0, 0, self.map_height)

        for y in range(starty, self.map_height):
            for x in range(startx, self.map_width):
                if self.map[y][x].passable() and not occupied((x, y)):
                    return x, y
            #if nothing found - let's try once again
        return self.find_random_square(occupied)

    def can_walk(self, x, y):
        return self.map[y][x].passable() and not self.has_critter_at((x, y))

    def passable(self, x, y):
        return self.map[y][x].passable()

    def coords_okay(self, x, y):
        return not (x < 0 or y< 0 or x >= self.map_width or y >= self.map_height)

    def find_passable_square(self):
        x, y = 0, 0
        for row in self.map:
            for item in row:
                if not item.passable(): y += 1
                else: return y, x
            y = 0
            x += 1
        return 1, 1

    def descend(self):
        tile = self.map[self.player.y][self.player.x]
        if getattr(tile, 'type', 0) == 4 and getattr(tile, 'can_go_down', False): #ft_types.stairs
            #this is stairs square
            if self.map_src.max_levels < self.map_src.current_level + 1:
                return False
            self.map_src.current_level += 1
            stairs_up = self.map_src.find_feature(oftype='Stairs', multiple=True,
                                                  filter=lambda ft: ft.can_go_down==False)
            #okay, lets have just the first stairs. TODO - link stairs while parsing the map
            self.player.x, self.player.y = stairs_up[0][1], stairs_up[0][2]
            self.init(self.map_src)
            self.init_fov()
            return True

class Room(object):
    def __init__(self):
        pass

class MultilevelRoom(Room):
    pass

