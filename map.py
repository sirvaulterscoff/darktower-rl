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
from maputils import  xy_in_room, MultilevelRoom, find_feature, replace_feature_atxy
from collections import Iterable
from items import Item

FOV_ALGORITHM = libtcod.FOV_PERMISSIVE_8
FOV_LIGHT_WALLS = True
logger = util.create_logger('DG')


class MainView(object):
    def __init__(self, map, map_src):
        self.map = map
        self.map_src = map_src
        self.inited = False
        self.height = len(map)
        self.width = len(map[0])

    def find_feature(self, id=None, oftype=None, multiple=False, filter=None):
        return find_feature(self.map, id, oftype, multiple, filter)

    def replace_feature_atxy(self, x, y, with_what):
        return replace_feature_atxy(self.map, x, y, with_what)

class LayerView(MainView):
    def __init__(self, map, map_src):
        super(LayerView, self).__init__(map, map_src)

def _materialize_piece(piece):
    """Checks if the given object is either callable or is a type
    and constructs it"""
    if callable(piece) or isinstance(piece, type):
        return piece()
    return piece

class Map(object):
    def __init__(self, map_src):
        self.init(map_src)

    def init(self, map_src):
        self.map_critters = []
        self.critter_xy_cache = {}
        self.map_src = map_src
        self.fov_map = None
        self.map = map_src.map
        """ Layers of the map """
        self.layers = {}
        """ Main layer of the map """
        self.main = MainView(self.map, self.map_src)
        """ Current layer of the map. All operations are done on current layer"""
        self.current = self.main
        self.square = self.current.height * self.current.width

    @property
    def width(self):
        return self.current.width
    @property
    def height(self):
        return self.current.height

    def prepare_level(self):
        """ This launches preparation on new level.
        1. Checks if a level was already prepared
        2. Materializez it from MapDef object (creates all required tiles)
        """
        if self.current.inited:
            return
        self.__materialize()
        self.current.inited = True
        #todo - now materialize mobs defined for that level


    def __materialize(self):
        _map = self.current.map
        logger.debug('Materializing map %dx%d' % (len(_map[0]), len(_map)))
        hd, hdx, hdy = find_feature(_map, oftype=features.HiddenDoor)

        for y in xrange(0, len(_map)):
            for x in xrange(0, len(_map[0])):
                try:
                    _map[y][x] = _materialize_piece(_map[y][x])
                    if isinstance(_map[y][x], Iterable): #we get this case when we have multiple items on one tile
                        #we need to find a tile first
                        tile =  filter(lambda x: issubclass(x, DungeonFeature) , _map[y][x])
                        if not len(tile):
                            raise RuntimeError('No tile at %d:%d (got only %s)' % (x, y, _map[y][x]))
                        elif len(tile) > 1:
                            raise RuntimeError('Got several tiles at %d:%d (%s)' % (x, y, _map[y][x]))
                        _map[y][x].remove(tile[0])
                        tile = _materialize_piece(tile[0])
                        if not isinstance(tile, DungeonFeature):
                            raise RuntimeError('Failed to initialze tile %s' %tile)
                        items = filter(lambda t: issubclass(t, Item), _map[y][x])
                        tile.items = []
                        for item in items:
                            tile.items.append(item)
                        _map[y][x] = tile

                    if not isinstance(_map[y][x], DungeonFeature):
                        raise RuntimeError('Not a tile at %d:%d (got %s)' % (x, y, _map[y][x]))
                    _map[y][x].init()
                except IndexError:
                    print 'The ' + str(y) + ' line of map is ' + str(x) + ' len. expected ' + str(self.current.width)
                    break
        self.current.map = _map

    def tile_at(self, x, y):
        return self.current.map[y][x]

    def place_player(self, player):
        pos_set = False
        if self.main.map_src.entry_pos:
            player.x, player.y = self.main.map_src.entry_pos
            pos_set = True
        if not pos_set:
            player.x, player.y = self.find_passable_square()
        self.player = player
        player.map = self

    def init_fov(self):
        self.fov_map = libtcod.map_new(self.current.width, self.current.height)
        for y in range(self.current.height):
            for x in range(self.current.width):
                self.update_fov_for(x, y)


    def update_fov_for(self, x, y):
        libtcod.map_set_properties(self.fov_map, x, y, not self.tile_at(x, y).flags & features.BLOCK_LOS,
                                           not self.tile_at(x, y).flags & features.BLOCK_WALK)
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
        startx = libtcod.random_get_int(0, 0, self.current.width)
        starty = libtcod.random_get_int(0, 0, self.current.height)

        for y in range(starty, self.current.height):
            for x in range(startx, self.current.width):
                if self.map[y][x].passable() and not occupied((x, y)):
                    return x, y
            #if nothing found - let's try once again
        return self.find_random_square(occupied)

    def can_walk(self, x, y):
        return self.tile_at(x, y).passable() and not self.has_critter_at((x, y))

    def passable(self, x, y):
        return self.tile_at(x, y).passable()

    def coords_okay(self, x, y):
        return not (x < 0 or y< 0 or x >= self.current.width or y >= self.current.height)

    def find_passable_square(self):
        x, y = 0, 0
        for row in self.current.map:
            for item in row:
                if not item.passable(): y += 1
                else: return y, x
            y = 0
            x += 1
        return 1, 1

    def descend(self):
        tile = self.tile_at(self.player.x, self.player.y)
        if getattr(tile, 'type', 0) == 4 and getattr(tile, 'can_go_down', False): #ft_types.stairs
            #this is stairs square
            #now we need to find a room (if any)
            inroom = None
            for room in self.map_src.rooms.values():
                if xy_in_room(room, self.player.x, self.player.y):
                    inroom = room
                    break
            if inroom and isinstance(inroom, MultilevelRoom):
                #this is actualy a static room so we go down it's level
                self._handle_static_descend(inroom)
            else:
                #this is actualy a dungeon - fire event to generate next dungeon level
                self._handle_dungeon_descend()
            stairs_up = find_feature(self.current.map, oftype='StairsUp', multiple=True)
            if not stairs_up:
                raise RuntimeError('No upstairs found on the level below')
            #okay, lets have just the first stairs. TODO - link stairs while parsing the map
            self.player.x, self.player.y = stairs_up[0][1], stairs_up[0][2]
            self.init_fov()
            return True

    def _handle_static_descend(self, inroom):
        """ Descends to a static room
        """
        next_level = str(-1)
        level = inroom.levels[next_level]
        if not level:
            raise RuntimeError('No level %s in room %s' % (next_level, inroom))
        if not self.layers.has_key(next_level):
            layer = LayerView(level, inroom.src)
            self.current = layer
            self.layers[next_level] = layer
            self.prepare_level()
        else:
            self.current = self.layers[next_level]

    def _handle_dungeon_descend(self):
        pass


