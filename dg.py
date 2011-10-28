from dungeon_generators import MapDef, MapRequest, get_map_name, parse_file 
from random import choice, randrange
from util import random_from_list_weighted, roll
from maputils import *
from map import *

generators = {}
transformation_pipe = []
class DungeonGenerator(object):
    """Generates new map of given width/heigh and style taking in account player's HD
    It works as follows:
        1. it chooses apropriate generator. If we request forest - use forest generator etc
        2. using selected generator it creates terrain
        3. if there is a request fro some feature - it searches for specific 2nd level generator
        4. then it morph result from 2 and 3 producing the result adjusting size of the map as needed
        Any level (is generated using 1 level generator). There should be following types of lvl1 generators:
            a. forest
            b. desert ?
            c. seashore
            d. cave-like
            e. maze-like
            f. canyon
            f1. mines
            g. city
            h. village ?
            i. null - used for static levels from des-files
        lvl2 generators can be following:
            0. static big_map generator - used only with null lvl1 generator
            a. pool/lava pool generator
            b. random feature generator (like placing some chests or another apropriate stuff)
            c. trap generator
            d. small features generator (those are from des files)
            e. house generator* (actualy will be only used by lvl1 generators)
            e1. tower generator
            f. river/lava river generator (if apropriate lvl1 was selected)
            g. bridge generator (if lvl2.f was selected)
            h. items generator
            i. checker - checks for lvl connectivity, and number of desired features/items
            Lvl2 generators should be piped in stated order
    """
    def generate_map(generator_type, width=400, height=300, player_hd=1, requests=None, params={}, name='', theme=''):
        if not generators.has_key(generator_type):
            raise RuntimeError('Unknow style [%s] for dungeon generator' % generator_type)
        map_draft = generators[generator_type](width, height, player_hd, generator_type, requests, params, theme) #okay we just take requested generator and invoke it. Now we have draft map
        for transformer in transformation_pipe:
            if transformer.decide(player_hd, generator_type, requests, theme, params):
                transformer.transformer(map_draft, player_hd, generator_type, requests, theme, params)
    generate_map = staticmethod(generate_map)

def null_generator(width, height, player_hd, generator_type, requests, params, theme):
    """Special cased generator - used when we need full sized, untransformed map from des file
    """
    map_draft = MapDef()
    map_draft.width, map_draft.height = width, height
    mapsrc= [ ['.' for y in xrange(width)] for x in xrange(height)]
    map_draft.map = mapsrc
    map_draft.prepare()
    return MapDef()

generators['null'] = null_generator
class PipeItem(object):
    def __init__(self, transformer, name=None):
        self.transformer = transformer
        if not name:
            self.ttype = transformer.__name__
        else:
            self.ttype = name

    def decide(self, player_hd, generator_type, requests, theme,  params={}):
        if self.ttype == 'static_transformer':
            if generator_type == 'null': #if it's null generator - then definetly static_transformer is what we need
                return True
            #now check if we have MapRequests
            map_requests = filter(lambda x: isinstance(x, MapRequest), requests)
            return len(map_requests) > 0
        if self.ttype == 'pool_transformer':
            return False #stub for now

unique_maps_already_generated = {}
def __check_static_params(generator_type, hd, x, params):
    """ Check params for MapDef loaded from des file. Check that map theme matches that of generator.
        Player HD is higher or equals that defined in des file etc... """
    if generator_type != 'null':
        if generator_type != x.terrain:
            return False
    if x.HD >  hd:
        return False
    if x.unique and unique_maps_already_generated.has_key(x.id):
        return False
    #we can have exact id specified
    if params.has_key('map_id'):
        return params['map_id'] == x.id
    return True


def __choose_map(generator_type, params, player_hd, type):
    av_maps = parse_file(get_map_name(type))
    total_maps_of_theme = len(av_maps)
    if total_maps_of_theme < 1: raise RuntimeError('No maps for MapRequest with type [%s]' % type)
    #now let's filter them leaving maps suitable for current generator/player HD and other params
    av_maps = filter(lambda x: __check_static_params(generator_type, player_hd, x, params), av_maps)
    tmap = None
    while True:
        if total_maps_of_theme < 1:
            #if we iterated over enough maps and can't decide on them - break unless none is selected
            if tmap: break
            raise RuntimeError('Cannot select map of type %s - too few maps available' % type)
        total_maps_of_theme -= 1
        # choose a random map from a weighed list
        tmap = random_from_list_weighted(av_maps)
        if tmap.chance > 0:
            if roll(1, tmap.chance) == 1:
                break
        else:
            break
    unique_maps_already_generated[tmap.id] = 1
    #prepare a map
    tmap.prepare()
    return tmap


def static_transformer(map_draft, player_hd, generator_type, requests, theme, params={}):
    """
    static_transformer(..) - > [MapDef, ...]
    This transformer loads static resources from .des files by theme.
    @map_draft - draft of the map generated by some 1lvl generator
    @player_hd - current level of the player. Used to select apropriate maps
    @generator_type - type of lvl1 generator use to generate map_draft
    @requests - requests to dungeon generator
    @theme - theme of this generator
    @params - optional params to this generator:
        -map_id - tells map generator to use only certain map_id
    """
    result = []
    #first we need to know what type of map we need
    if theme:
        tmap = __choose_map(generator_type, params, player_hd, theme)
        result.append(tmap)

    if not requests:
        if not len(result): raise RuntimeError('Neither theme nor maprequests specified')
        return result
    #now check requests if we have any
    map_requests = filter(lambda x: isinstance(x, MapRequest), requests)
    if len(map_requests < 1):
        raise RuntimeError('Neither theme nor MapRequests specified for static_transfomer')

    #let's go through all MapRequests and see which we can fullfill
    for request in map_requests:
        #now we load a file with requested theme
        tparams = {}
        tparams.update(params)
        tparams.update(request.params)
        tmap = __choose_map(generator_type, tparams, player_hd, request.type)
        result.append(tmap)
    return result



rooms_rows = 3 #todo this is param.
map_free_coeff = 1.5 #todo move to params
def __assure_mapsize(map_draft, rooms):
    """
    __assure_mapsize(...) -> None
    Assures that map_draft has enought width/height to include all desired rooms
    @map_draft - MapDef with current map
    @rooms - list of rooms to include
    """
    if len(rooms) < rooms_rows:
        width = reduce(lambda x,y : x.width + y.width, rooms)
        height = reduce(lambda x,y: max(x.height, y.height), rooms)
        map_draft.width, map.height = width * map_free_coeff, height * map_free_coeff
    hrooms = rooms[:]
    hrooms.sort(lambda x, y: (x.height) - (y.height), reverse=True) #now we sort all rooms by side
    wrooms = rooms[:]
    wrooms.sort(lambda x, y: (x.width) - (y.width), reverse=True) #now we sort all rooms by side
    height, width = 0,0
    for x in xrange(0, rooms_rows):#total height should be sum of all larges elements
        height += hrooms[x].height
        width += wrooms[x].width
    map_draft.width, map.height = width * map_free_coeff, height * map_free_coeff

def __find_random_mergepoint(map_draft, room, position):
    """__find_random_mergepoint(MapDef, MapDef, MapDef.position) - > (x, y)
    Finds a random pair of x,y suitable for merging this room into map_draft
    """
    if position == 'NW':
        return 0,0 #todo check if it's already occupied
    if position == 'NE':
        return map_draft.width - room.width, 0
    if position == 'SE':
        return map_draft.width -room.width, map_draft.height - room.height
    if position == 'SW':
        return 0, map_draft.height - room.height
    if position == 'CENTER':
        return (map_draft.width / 2) - (room.width / 2), (map_draft.height / 2) - (room.height / 2)
    itercnt = 1000 #time to find solution
    while True:
        if itercnt <= 0: raise RuntimeError('Failed to place a room')
        itercnt -= 1
        x, y = randrange(0, map_draft.width), randrange(0, map_draft.heigth)
        if x + room.width > map_draft.width or y + room.height > map_draft.height:
            #if we are beyond the map edge - try again
            continue
        for room in map_draft.rooms:
            if xy_in_room(room, x, y):
                continue
        return x, y


def __merge_leveled(map_draft, child_map, level, parent_map):
    """Adds non-base level map to a room which will hold base level map"""
    #check if rooms already exists
    if map_draft.rooms.has_key(parent_map.id):
        room = map_draft.rooms[parent_map.id]
    else:
        room = MultilevelRoom()
        map_draft.rooms[parent_map.id] = room
    room[level] = child_map
    room.src = parent_map

def __create_room(map_draft, newmap, map_src):
        #check if rooms already exists
    if map_draft.rooms.has_key(map_src.id):
        room = map_draft.rooms[map_src.id]
    else:
        room = Room()
        map_draft.rooms[map_src.id] = room
    room.src = map_src
    room.map = newmap
    room.width = map_src.width
    room.height = map_src.height
    return room

nomerge_chance = 50
def __merge(map_draft, room, params):
    """ __merge(MapDef, MapDef, {}) -> None
    Merges room in map_draft, choosing random location
    """
    mode = room.src.mode
    x, y = __find_random_mergepoint(map_draft, room, room.src.position)
    room.x, room.y = x.y
    for line in map.src.map:
        for tile in line:
            dest_tile = map_draft.map[y][x]
            if mode == 'overflow':
                if dest_tile.is_fixed(): continue #in overflow mode we don't rewrite underlying pixels
                if tile.is_fixed(): #we should rewrite if room's fixel is fixed
                    map_draft.map[y][x] = tile
                elif util.roll(1, nomerge_chance) == 1: #or we may not rewrite 1/nomerge_chance
                    continue
            elif mode == 'include' or mode == 'asis':
                map_draft.map[y][x] = tile
            else:
                raise RuntimeError('Invalid merge mode [%s] specified for map [%s]' % (mode, room.src.id)) 


def merger(producer, map_draft, player_hd, generator_type, requests, theme, params={}):
    """
    merger(...) -> map_draft:MapDraft
    Merges the result of transformer(producer) into map_draft.
    The basic idea behind this is to adjust map_draft size (if needed), transform result from producer (rotate)
    and merge it cell by cell into map_draft.
    @producer -> function() wich will produce data to merge into map_draft
    @map_draft - MapDef we are currently working on
    @player_hd - player's XL (not used in merger)
    @generator_type - type of lvl1 generator being used
    @requests - requests to dungeon generator (not used in merger)
    @theme - theme of the lvl1 generator (not used)
    @params - optional params
    """
    maps_to_merge = producer(map_draft, player_hd, generator_type, requests, theme, params)
    rooms = []
    for map in maps_to_merge:
        if map.orient:
            newmap, rotate_params = random_rotate(map.map, map.orient)
        else:
            newmap, rotate_params = map.map, None
        for level, child in map.levels.items(): # now we transform all submaps
            child_map = None
            if child.orient: #if child redefines orient - let's use it
                child_map = random_rotate(child.map, child.orient)
            elif rotate_params: #keep the same orient as parent
                child_map = random_rotate(child.map, map.orient, params=rotate_params)
            __merge_leveled(map_draft, child_map, level, map)

#            __merge(map_draft, newmap, map, mode)
        rooms.append(__create_room(map_draft, newmap, map))
    __assure_mapsize(map_draft, rooms)
    for room in rooms:
        __merge_room(map_draft, room, params)


transformation_pipe.append(PipeItem(lambda map_draft, player_hd, generator_type, requests, theme, params: \
    merger(static_transfomer, map_draft, player_hd, generator_type, requests, theme, params), 'static_transformer'))
