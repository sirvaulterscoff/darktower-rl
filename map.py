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
from maputils import  xy_in_room, MultilevelRoom, find_feature, replace_feature_atxy, Room, square_search_nearest
from collections import Iterable
from items import Item
import rlfl

FOV_ALGORITHM = libtcod.FOV_PERMISSIVE_8
FOV_LIGHT_WALLS = True
logger = util.create_logger('DG')


class MainView(object):
    def __init__(self, map, map_src):
        self._map = map
        self.map_src = map_src
        self.inited = False
        self.height = len(map)
        self.width = len(map[0])
        self.fov_map = None
        self.fov_map0 = None
        self.map_critters = []
        self.critter_xy_cache = {}

    def find_feature(self, id=None, oftype=None, multiple=False, filter=None):
        return find_feature(self._map, id, oftype, multiple, filter)

    def replace_feature_atxy(self, x, y, with_what):
        return replace_feature_atxy(self._map, x, y, with_what)

    def tile_at(self, x, y):
        return self._map[y][x]

class LayerView(MainView):
    """Represent's layered view. It can be displayed above main view or below.
    Main goal of LayerView is to correct coords - i.e. when you go upstairs in a building
    you should appear at the same position on screen you were before ascending"""
    def __init__(self):
        self.main = None
        self.rooms = []
        self._map = []
        self.inited = False
        self.level = 0

    def set_base_view(self, main):
        self.main = main
        super(LayerView, self).__init__(main._map, main.map_src)
        self._map = [[None for x in xrange(main.width)] for y in xrange(main.height)]

    def add_room(self, room, level_map, xy):
        """ Adds new room to current view.
        add_room (Room, MapDef, (xy) )
        """
        x,y = xy
        nr = Room()
        nr.x, nr.y= xy
        nr.map = level_map
        nr.room_src = room
        self.rooms.append(nr)
        for line in level_map:
            for tile in line:
                if not isinstance(tile, features.NoneFeature):
                    self._map[y][x] = tile
                x+=1
            y += 1
            x = xy[0]

    def find_room(self, x, y):
        for room in self.rooms:
            if xy_in_room(room, x, y):
                return room.room_src


    def tile_at(self, x, y):
        tile = self._map[y][x]
        if tile:
            return tile
        if self.level <= 0:
            return None
        tile = self.main._map[y][x]
        return self.thumb_tile(tile)

    def thumb_tile(self, tile):
        return features.Thumb(tile.color, tile.dim_color)


def _materialize_piece(piece):
    """Checks if the given object is either callable or is a type
    and constructs it"""
    if not piece:
        return None
    if callable(piece) or isinstance(piece, type):
        return piece()
    return piece

class Map(object):
    def __init__(self, map_src):
        self.init(map_src)

    def init(self, map_src):
        """ init(MapDef) => None
        Initializez current Map
        @map_src - MapDef of current map"""
        self.map_src = map_src
        self.fov_map = None
        """ Points to already prepared bytes of map [][]"""
        self.map = map_src.map
        """ Layers of the map """
        self.layers = {}
        """ Main layer of the map """
        self.main = MainView(self.map, self.map_src)
        """ Current layer of the map. All operations are done on current layer"""
        self.current = self.main
        self.square = self.current.height * self.current.width
        self.current_level = 0

    @property
    def width(self):
        return self.current.width
    @property
    def height(self):
        return self.current.height

    @property
    def critters(self):
        return self.current.map_critters

    @property
    def critter_xy_cache(self):
        return self.current.critter_xy_cache

    def prepare_level(self):
        """ This launches preparation on new level.
        1. Checks if a level was already prepared
        2. Materializez it from MapDef object (creates all required tiles)
        """
        if self.current.inited:
            return
        mobs = self.__materialize()
        self.current.inited = True
        for mob in mobs:
            self.place_critter(mob, mob.x, mob.y)
        del mobs
        self._link_stairs()

    def _link_stairs(self):
        """ _link_stairs() => None
        Tries to link stairs for all rooms """
        #first - find base stairs
        up_level = str(self.current_level + 1)
        current = str(self.current_level)
        down_level = str(self.current_level - 1)
        logger.debug('Linking stairs for current level')
        for room in self.map_src.rooms.values():
            if not isinstance(room, MultilevelRoom):
                continue # we only link multilevel rooms
            #if this room is actualy multilevel room
            current_map = None
            if self.current_level == 0:
                current_map = room.map
            else:
                current_map = room.levels[current]
            if room.levels and room.levels.has_key(up_level):
                self._link_stairs_in_room(room.levels[up_level], 'StairsDown', current_map, room)
            if room.levels and room.levels.has_key(down_level):
                self._link_stairs_in_room(room.levels[down_level], 'StairsUp', current_map, room)

    def _link_stairs_in_room(self, next_level, stairs_type, current_level, room):
        """ _link_stairs_in_room([][], str, [][], Room) => None
        Finds stairs on next level of type stairs_type and matches with oppositite
        type of stairs on current_level """
        current_type = 'StairsUp' if stairs_type == 'StairsDown' else 'StairsDown'
        #we try to find DonwStairs on the level above
        next_level_stairs = find_feature(next_level, oftype=stairs_type, multiple = 'True', filter = lambda x: x.pair is None)
        if next_level_stairs: #if there are any downstairs
            for next_stairs, x, y in next_level_stairs:
                #first we check if this stairs are id-linked
                if next_stairs.id and isinstance(next_stairs.id, str):
                    pair = find_feature(current_level, id=next_stairs.id)
                    if not pair:
                        raise RuntimeError('Failed to find pair for staircases with id %s in room %s' % (next_stairs.id, room.id))
                    next_stairs = _materialize_piece(next_stairs)
                    replace_feature_atxy(next_level, x, y, next_stairs)
                    next_stairs.pair = pair
                    pair[0].pair = next_stairs, x, y
                    continue
                #now for each DownStair in the upper room we find
                #UpStairs in current room, sort them by relative distance from current
                #stairs and see which of them doesn't have pair
                #todo - add id matching
                candidates = square_search_nearest(x, y, current_level, oftype=current_type)
                candidates = filter(lambda x: x[0].pair is None, candidates)
                if not candidates:
                    raise RuntimeError('Failed to map stairs for room %s' % room.id)
                next_stairs = _materialize_piece(next_stairs)
                replace_feature_atxy(next_level, x, y, next_stairs)
                next_stairs.pair = candidates[0]
                candidates[0][0].pair = next_stairs, x, y
        #time to check we matched everything
        errors =  find_feature(current_level, oftype=current_type, filter=lambda x: x.pair is None)
        if errors:
            raise RuntimeError('Failed to map %d %s for room %s' %(len(errors), current_type, room.id))


    def __materialize(self):
        mobs = []
        _map = self.current._map
        logger.debug('Materializing map %dx%d' % (len(_map[0]), len(_map)))

        for y in xrange(0, len(_map)):
            for x in xrange(0, len(_map[0])):
                try:
                    tile = _materialize_piece(_map[y][x])
                    _map[y][x] = tile
                    if not tile:
                        continue
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
                    mob = _map[y][x].mob
                    if mob:
                        mob = mob()
                        mob.x, mob.y = x, y
                        mobs.append(mob)
                        del _map[y][x].mob
                except IndexError:
                    print 'The ' + str(y) + ' line of map is ' + str(x) + ' len. expected ' + str(self.current.width)
                    break
        self.current._map = _map
        return mobs

    def tile_at(self, x, y):
        return self.current.tile_at(x, y)

    def place_player(self, player):
        pos_set = False
        if self.main.map_src.entry_pos:
            player.x, player.y = self.main.map_src.entry_pos
            pos_set = True
        if not pos_set:
            player.x, player.y = self.find_passable_square()
        self.player = player
        player.map = self

    def configure(self):
        """
            configure() => None
            Invoked after place_player(player) takes place. This method should configure
            all features/critters dependant on player.
            1. It sets target monster's HD (=player.xl)
            2. Sets the levels of traps for this level

            HD-adjustment's are not made if strict_hd is specified for a critter
        """
        #first adjust creatures' HDs
        for crit in self.critters:
            if not getattr(crit, 'strict_hd', False):
                #we assume all critters has critter.hd set and we just call adjust_hd which will reset
                #critter's hd to hd + player.xl
                crit.adjust_hd(self.player.xl)
        #now configure hiddens
        hiddens = find_feature(self.current._map, oftype=features.HiddenFeature, multiple=True)
        #actualy all hiddens should have relative HD. So we add player's HD to that of hidden
        if hiddens:
            for hidden_feature, x, y in hiddens:
                if not(getattr(hidden_feature, 'strict_hd', False)):
                    hidden_feature.skill += self.player.xl


    def init_fov(self):
        if self.current.fov_map0 is None:
            self.current.fov_map0 = rlfl.create_map(self.current.width, self.current.height)
#        self.current.fov_map = libtcod.map_new(self.current.width, self.current.height)
        for y in xrange(self.current.height):
            for x in xrange(self.current.width):
                self.update_fov_for(x, y)


    def update_fov_for(self, x, y):
#        libtcod.map_set_properties(self.current.fov_map, x, y, not self.tile_at(x, y).flags & features.BLOCK_LOS,
#                                           not self.tile_at(x, y).flags & features.BLOCK_WALK)

#        if self.tile_at(x, y).flags & features.BLOCK_LOS:
#            flags = rlfl.CELL_WALK
        xy = (x, y)
        fov_map_ = self.current.fov_map0
        tile = self.tile_at(*xy)
        if not tile:
            return
        if tile.flags & features.BLOCK_WALK:
            if tile.flags & features.BLOCK_LOS == features.BLOCK_LOS:
                return

        flags = rlfl.get_flags(fov_map_, xy)
        flags |= rlfl.CELL_OPEN | rlfl.CELL_WALK
        rlfl.set_flag(fov_map_, xy, flags)

    def recompute_fov(self):
        try:
            rlfl.fov(self.current.fov_map0, (self.player.x, self.player.y), self.player.fov_range, rlfl.FOV_PERMISSIVE, True, True)
#            libtcod.map_compute_fov(self.current.fov_map, self.player.x, self.player.y, self.player.fov_range, FOV_LIGHT_WALLS,
#                                FOV_ALGORITHM)
        except Exception, e:
            print e

    def place_critter(self, crit, x, y):
        self.critters.append(crit)
        self.critter_xy_cache[(x, y)] = crit
        crit.place(x, y, self)

    def place_random_critter(self, dlvl, hd, x, y):
        crit = util.random_by_level(dlvl, critters.mobs.values())
        if crit is None: return
        crit = crit()
        crit.hd = dlvl - hd
#        crit.adjust_hd(hd)
        self.place_critter(crit, x, y)

    # basic algo: take player level (xl), and pick random number between xl - 3 and xl + 3.
    # let it be monster HD. Now take random monsters appropirate for this and prev levels (Critter.dlvl <= __dlvl__)
    # set this monster HD to a value defined earlier
    # for OOD monsters - same HD as previous case, and Critter.dlvl <= random(__dlvl__ + 2, __dlvl +3)
    def place_random_monsters(self):
        #todo - maybe we should move this to mapgenerator (check for theme, etc)
        #choose random number of monsters
        #3d(dlvl) + 3d2 + 7 monsters total - at least 11 monsters on d1 and up-to 40 on d27
        num_monsters = util.roll(1, gl.__dlvl__, util.roll(3, 2, 7))
        num_monsters -= len(self.critters)
        free_squares = -2
        for line in self.map:
            for tile in line:
                if tile.passable(): free_squares += 1

        num_monsters = util.cap(num_monsters, free_squares)
        #if it was capped - then map is too small...
        if num_monsters == free_squares:
            num_monsters = randrange(1 , free_squares / 2)

        passes = num_monsters * 5
        for i in range(num_monsters):
            if passes <= 0: break
            passes -= 1
            #choose random spot for this monster
            x, y = self.find_random_square(self.has_critter_at)
            room = self._find_room(x, y)
            if room:
                if room.src.no_mon_gen:
                    continue

            #determining critter level. it may vary from XL - 3 to XL + 1. To let is scale better multiply by 100
            #cap it to be no lower than 1
            crit_hd = max(randrange(gl.__xl__ - 3, gl.__xl__ + 1), 1)
            self.place_random_critter(gl.__dlvl__, crit_hd, x, y)

        #check for OOD monster. let's create OOD 10% of the time for now
        if libtcod.random_get_int(0, 0, 100) >= 89:
            crit_level = libtcod.random_get_int(0, gl.__dlvl__ + 2, gl.__dlvl__ + 3)
            crit_hd = max(randrange(gl.__xl__ - 3, gl.__xl__ + 3), 1)
            x, y = self.find_random_square(self.has_critter_at)

            room = self._find_room(x, y)
            if room:
                if room.src.no_mon_gen:
                    return

            self.place_random_critter(crit_level, crit_hd, x, y)

    def has_critter_at(self, coords):
        return coords in self.critter_xy_cache

    def get_critter_at(self, x, y):
        return self.critter_xy_cache[(x, y)]

    def remove_critter(self, critter):
        self.critter_xy_cache.pop((critter.x, critter.y))
        self.critters.remove(critter)

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
        for row in self.current._map:
            for item in row:
                if not item.passable(): y += 1
                else: return y, x
            y = 0
            x += 1
        return 1, 1


    def iterate_fov(self, x, y, range, action):
        xy = util.iterate_fov(x, y, range, self.current.width, self.current.height)
        for x,y in xy:
#            if libtcod.map_is_in_fov(self.current.fov_map, x, y):
            if rlfl.has_flag(self.current.fov_map0, (x, y), rlfl.CELL_SEEN):
                tile = self.current._map[y][x]
                if tile:
                    action(tile, x, y, self.current)

    def player_moved(self):
#        self.search()
        pass

    def _find_room(self,x, y):
        """
        Returns MapDef for a room at specified location. Returns None if no room found
        """
        if isinstance(self.current, LayerView):
            inroom = self.current.find_room(x, y)
            if inroom:
                return inroom
        inroom = None
        for room in self.map_src.rooms.values():
            if xy_in_room(room, x, y):
                inroom = room
                break
        return inroom

    def descend_or_ascend(self, descend):
        #todo generalize this method removing references to player (any mob can go down)
        tile = self.tile_at(self.player.x, self.player.y)
        if getattr(tile, 'type', 0) == 4 and getattr(tile, 'can_go_down', False) == descend: #descend
            #this is stairs square
            #now we need to find a room (if any)
            inroom = self._find_room(self.player.x, self.player.y)
            if inroom and isinstance(inroom, MultilevelRoom):
                #this is actualy a static room so we go down it's level
                self._handle_static_descend(inroom, descend, tile)
            else:
                #this is actualy a dungeon - fire event to generate next dungeon level
                self._handle_dungeon_descend(descend)
            #okay, lets have just the first stairs. TODO - link stairs while parsing the map
            self.player.x, self.player.y = tile.pair[1], tile.pair[2]
            self.init_fov()
            gl.__fov_recompute__ = True
            return True

    def _handle_static_descend(self, inroom, descend, current_stairs):
        """ Descends to a static room
        """
        self.current_level += -1 if descend else 1
        if self.current_level == 0:
            self.current = self.main
            return
        if descend:
            next_level = str(self.current_level)
        else:
            next_level = str(self.current_level)

        #first we check if this is standalone room (so no LayerView)
        if inroom.src.align == 'none': #this is not aligned level
            #since none-aligned rooms will have their own 'views' we use room_id+level as id here
            id = inroom.src.id + next_level
            if self.layers.has_key(id):
                self.current = self.layers[id]
            else:
                layer = MainView(inroom.levels[next_level], inroom.levels_src[next_level])
                self.layers[id] = layer
                self.current = layer
                self.prepare_level()
            return

        #Now the LayerView case
        if not self.layers.has_key(next_level):
            #We don't have such layer - time to build one
            layer = LayerView()
            self.current = layer
            self.layers[next_level] = layer
            layer.level = self.current_level
            #now we iterate over all rooms on this layer and add them to layer
            layer.set_base_view(self.main)
            for room in self.map_src.rooms.values():
                if room.levels and room.levels.has_key(next_level):
                    if room.src.align != 'base' and room.src.align != 'stairs':
                    #we handle only non-standalone rooms (align != none)
                        continue
                    #align the edges of upper levels agains base room coords
                    layer.add_room(room, room.levels[next_level], self.adjust_room_coords(room, next_level, current_stairs))
            self.prepare_level()
        else:
            self.current = self.layers[next_level]

    def _handle_dungeon_descend(self, descend):
        pass

    def adjust_room_coords(self, inroom, next_level, current_stairs):
        """
        Calculates new room coords based on current player location and map align param
        @inroom - MultilevelRoom
        @nextlevel - level number
        @current stairs = features.Stairs
        """
        if inroom.src.align == 'base':
            return inroom.x, inroom.y
        elif inroom.src.align == 'stairs':
            xy = self.find_stairs_pair(inroom, next_level, current_stairs)
            if not xy:
                logger.warn('Failed to map stairs for room %s' % inroom.id)
                return inroom.x, inroom.y
            x, y = max(self.player.x - xy[0], 0), max(self.player.y - xy[1], 0)
            if x > self.main.width:
                x = self.main.width - inroom.levels_src[next_level].width - 2
            if y > self.main.height:
                y = self.main.height - inroom.levels_src[next_level].height - 2
            return x, y

    def find_stairs_pair(self, inroom, next_level, current_stairs):
        return current_stairs.pair[1], current_stairs.pair[2]




