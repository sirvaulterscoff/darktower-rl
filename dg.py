from dungeon_generators import MapDef, MapRequest, get_map_name, parse_file 
from random import choice
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
            f. river/lava river generator (if apropriate lvl1 was selected)
            g. bridge generator (if lvl2.f was selected)
            h. items generator
            i. checker - checks for lvl connectivity, and number of desired features/items
            Lvl2 generators should be piped in stated order
    """
    def generate_map(width=400, height=300, player_hd=1, generator_type=None, requests=None, params={}, name='', theme=''):
        if not generators.has_key(generator_type):
            raise RuntimeError('Unknow style [%s] for dungeon generator' % generator_type)
        map_draft = generators[generator_type]() #okay we just take requested generator and invoke it. Now we have draft map
    generate_map = staticmethod(generate_map)

def null_generator():
    """Special cased generator - used when we need full sized, untransformed map from des file
    """
    return MapDef()

generators['null'] = null_generator
class PipeItem(object):
    def __init__(self, transformer):
        self.transformer = transformer
        self.ttype = transformer.__name__

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




def __assure_mapsize(map_draft, rooms):
    """
    __assure_mapsize(...) -> None
    Assures that map_draft has enought width/height to include all desired rooms
    @map_draft - MapDef with current map
    @rooms - list of rooms to include
    """

def __find_random_mergepoint(map_draft, map, position):
    if position == 'NW':
        return 0,0
    if position == ''
    maxx, maxy = map_draft.width - map.width, map_draft.height - map.height #first of all let's determine maximum id where we can place our map

def __merge_leveled(map_draft, child_map, level, parent_map):
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
        mode = map.mode
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

transformation_pipe.append(PipeItem(static_transformer))
