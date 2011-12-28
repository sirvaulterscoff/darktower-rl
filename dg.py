from dungeon_generators import MapDef, MapRequest, get_map_file, parse_file
from random import choice, randrange, randint
from features import FIXED, none
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
    def generate_map(generator_type, width=1, height=1, player_hd=1, requests=None, params=None, name='', theme=''):
        """generate_map(generator_type, ...) => MapDef
        """
        if not generators.has_key(generator_type):
            raise RuntimeError('Unknow style [%s] for dungeon generator' % generator_type)
        map_draft = MapDef()
        map_draft.name = name
        map_draft.width, map_draft.height = width, height
        _static_request_preprocessor(generator_type, player_hd, requests, params, theme)
        _assure_mapsize(map_draft, generator_type, requests)
        map_draft = generators[generator_type](map_draft, player_hd, generator_type, requests, params, theme) #okay we just take requested generator and invoke it. Now we have draft map
        for transformer in transformation_pipe:
            if transformer.decide(player_hd, generator_type, requests, theme, params):
                transformer.transformer(map_draft, player_hd, generator_type, requests, theme, params)
        return map_draft
    generate_map = staticmethod(generate_map)

#Cache of unique maps names
unique_maps_already_generated = {}
def _check_static_params(generator_type, hd, x, params):
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
    if params and params.has_key('map_id'):
        return params['map_id'] == x.id
    return True


def _choose_map(generator_type, params, player_hd, theme, size):
    """ _choose_map(...) = > MapDef (or None if theme file does not exist)
    Loads the list of available maps and chooses a random one.
    Maps gets filtered first by number of parameters. Selection is based on weight/chance of a map.
    Also map is checked against unique maps list already generated.
    """
    file = get_map_file(theme, size=size)
    if not file:
        return None
    av_maps = parse_file(file)
    total_maps_of_theme = len(av_maps)
    if total_maps_of_theme < 1: raise RuntimeError('No maps for MapRequest with theme [%s]' % theme)
    #now let's filter them leaving maps suitable for current generator/player HD and other params
    av_maps = filter(lambda x: _check_static_params(generator_type, player_hd, x, params), av_maps)
    tmap = None
    while True:
        if total_maps_of_theme < 1:
            #if we iterated over enough maps and can't decide on them - break unless none is selected
            if tmap: break
            raise RuntimeError('Cannot select map of theme %s - too few maps available' % theme)
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
    tmap.prepare(params)
    return tmap


rooms_rows = 3 #todo this is param.
map_free_coeff = 1.3 #todo move to params

def _assure_mapsize(map_draft, generator_type, requests):
    """
    __assure_mapsize(...) -> map_draft
    Assures that map_draft has enought width/height to include all desired rooms.

    @map_draft - MapDef with current map
    @rooms - list of rooms to include
    @requests - mapgen requests
    """
    _rooms = []
    if requests:
        map_requests = filter(lambda x: isinstance(x, MapRequest), requests)
        for request in map_requests:
            _rooms.append(request.map)


    if len(_rooms) < rooms_rows: #if we can lay all the rooms in one row
        maxed = reduce(lambda x,y : x + max(y.height, y.width), _rooms, max(_rooms[0].width,_rooms[0].height))
        width, height = int(round(maxed * map_free_coeff)), int(round(maxed* map_free_coeff))
        map_draft.width = max(width, map_draft.width)
        map_draft.height = max(height, map_draft.height)
        return
    hrooms = _rooms[:]
    hrooms.sort(lambda x, y: x.height - y.height, reverse=True) #now we sort all rooms by side
    wrooms = _rooms[:]
    wrooms.sort(lambda x, y: x.width - y.width, reverse=True) #now we sort all rooms by side
    maxed = 0
    for x in xrange(0, rooms_rows):#total height should be sum of all larges elements
        maxed += max (hrooms[x].height , wrooms[x].width)
    width, height = int(round(maxed * map_free_coeff)), int(round(maxed * map_free_coeff))
    map_draft.width = max(width, map_draft.width)
    map_draft.height = max(height, map_draft.height)


#todo parametrize this variable
large_theme_map_chance=(1, 5)  #chance of large map to be included in current level (1/5 chance for now)
def _static_request_preprocessor(generator_type, player_hd, requests, params, theme):
    """ _staic_request_processor(...) => None
    The goal of static request processor is to take large MapRequests, choose apropriate map for them and assure map-size.
    @params - no_large can be passed to disable random large-map selection
    """
    #now process requests
    if requests:
        map_requests = filter(lambda x: isinstance(x, MapRequest), requests)
        for request in map_requests:
            #now we load a file with requested theme
            tparams = {}
            if params:
                tparams.update(params)
            if request.params:
                tparams.update(request.params)
            tmap = _choose_map(generator_type, tparams, player_hd, request.type, request.size)
            if not tmap:
                raise RuntimeError('Requested map cannot be found %s ' % request)
            request.map = tmap
        #check if we have request for large map we're done for now
        if filter(lambda x: isinstance(x, MapRequest) and x.size=='large', requests) > 0:
            return


    if params and params.has_key('no_large'):
        return
    #if no large maps were requested we can create a random one
    if theme and util.roll(*large_theme_map_chance) == 1:
        try:
            large = _choose_map(generator_type, params, player_hd, theme, 'large')
            if large:
                request = MapRequest(theme)
                requests.append(request)
        except Exception, e:
            print 'Exception during static preprocessor ' + e



def null_generator(map_draft, player_hd, generator_type, requests, params, theme):
    """Special cased generator - used when we need full sized, untransformed map from des file
    """
    mapsrc= [ ['.' for y in xrange(map_draft.width)] for x in xrange(map_draft.height)]
    map_draft.map = mapsrc
    map_draft.prepare(None)
    return map_draft

generators['null'] = null_generator
class PipeItem(object):
    def __init__(self, transformer, name=None):
        self.transformer = transformer
        if not name:
            self.ttype = transformer.__name__
        else:
            self.ttype = name

    def decide(self, player_hd, generator_type, requests, theme,  params):
        if self.ttype == 'static_transformer':
            if generator_type == 'null': #if it's null generator - then definetly static_transformer is what we need
                return True
            #now check if we have MapRequests
            map_requests = filter(lambda x: isinstance(x, MapRequest), requests)
            return len(map_requests) > 0
        if self.ttype == 'pool_transformer':
            return False #stub for now


small_theme_maps_count=(1, 8) #number of themed minimaps per level
def static_transformer(map_draft, player_hd, generator_type, requests, theme, params):
    """
    static_transformer(..) - > [MapDef, ...]
    This transformer loads static resources from .des files for theme or requests.
    In contrast to _static_request_processor this one loads only small features.
    It then agregates all static content in one collection and return
    @map_draft - draft of the map generated by some 1lvl generator
    @player_hd - current level of the player. Used to select apropriate maps
    @generator_type - type of lvl1 generator use to generate map_draft
    @requests - requests to dungeon generator
    @theme - theme of this generator
    @params - optional params to this generator:
        -map_id - tells map generator to use only certain map_id
    """
    result = []
    #first let's see what requests we skipped in _static_request_processor
    for request in filter(lambda x: isinstance(x, MapRequest), requests):
        if request.map: #that was already generated - just add to collection
            request.map.prepare(request.params)
            result.append(request.map)
            continue
        tparams = {}
        if params:
            tparams.update(params)
        if request.params:
            tparams.update(request.params)
        tmap =  _choose_map(generator_type, tparams, player_hd, request.type, request.size)
        result.append(tmap)
        tmap.prepare(tparams)

    mini_map_count = randrange(*small_theme_maps_count)
    logger.debug('Generating %d mini-maps for current map' % mini_map_count)
    #now generate plenty of small features
    if theme:
        for x in xrange(mini_map_count):
            tmap = _choose_map(generator_type, params, player_hd, theme, 'mini')
            if tmap:
                result.append(tmap)
                tmap.prepare(params)

    logger.debug('Total of %d static maps selected for current map generation' % len(result))
    return result

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
        x, y = randrange(1, map_draft.width), randrange(1, map_draft.height)
        if x + room.width + 1 > map_draft.width or y + room.height + 1 > map_draft.height:
            #if we are beyond the map edge - try again
            continue
        for room in map_draft.rooms.values():
            if xy_in_room(room, x, y):
                continue
        return x, y


def __merge_leveled(map_draft, child_map_bytes, child, level):
    """Adds non-base level map to a room which will hold base level map
    @map_draft - map being generated
    @child_map_bytes - map bytes [][] after applying orientation
    @child - MapDef of child level
    @level - level number
    """
    #check if rooms already exists
    map_id = child.parent_map.id
    if map_draft.rooms.has_key(map_id):
        room = map_draft.rooms[map_id]
    else:
        room = MultilevelRoom()
        map_draft.rooms[map_id] = room
    room.levels[level] = child_map_bytes
    room.levels_src[level] = child
    room.src = child.parent

def __create_room(map_draft, newmap, map_src):
        #check if rooms already exists
    if map_draft.rooms.has_key(map_src.id):
        room = map_draft.rooms[map_src.id]
    else:
        room = Room()
        map_draft.rooms[map_src.id] = room
    room.src = map_src
    room.map = newmap
    room.width = len(newmap[0])
    room.height = len(newmap)
    return room

nomerge_chance = 50
def __merge_room(map_draft, room, params):
    """ __merge_room(MapDef, MapDef, {}) -> None
    Merges room in map_draft, choosing random location
    """
    mode = room.src.mode
    x, y = __find_random_mergepoint(map_draft, room, room.src.position)
    room.x, room.y = x, y
    try:
        for line in room.map:
            for tile in line:
                if type(tile) == none: #special tile type - don't merge onto map
                    x+=1
                    continue
                dest_tile = map_draft.map[y][x]
                if mode == 'overflow':
                    if dest_tile.flags & FIXED: continue #in overflow mode we don't rewrite underlying pixels
                    if tile.flags & FIXED: #we should rewrite if room's fixel is fixed
                        map_draft.map[y][x] = tile
                    elif util.roll(1, nomerge_chance) == 1: #or we may not rewrite 1/nomerge_chance
                        x+=1
                        continue
                    else:
                        map_draft.map[y][x] = tile
                elif mode == 'include' or mode == 'asis': #in both modes we just
                    map_draft.map[y][x] = tile
                else:
                    raise RuntimeError('Invalid merge mode [%s] specified for map [%s]' % (mode, room.src.id))
                x+=1
            x = room.x
            y += 1
    except IndexError, ie:
        print 'Failed to merge static feature into map. Map params w:[%d] h:[%d] \n Room params: w:[%d] h:[%d] x:[%d] y:[%d]\n current %d,%d' % \
              (map_draft.width, map_draft.height, room.width, room.height, room.x, room.y, x, y)
        raise ie


def merger(producer, map_draft, player_hd, generator_type, requests, theme, params):
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
            child_map_bytes = None
            if child.orient: #if child redefines orient - let's use it
                child_map_bytes, ignored = random_rotate(child.map, child.orient)
            elif rotate_params: #keep the same orient as parent
                child_map_bytes, ignored = random_rotate(child.map, map.orient, params=rotate_params)
            __merge_leveled(map_draft, child_map_bytes, child, level)

        rooms.append(__create_room(map_draft, newmap, map))
    for room in rooms:
        __merge_room(map_draft, room, params)


transformation_pipe.append(PipeItem(lambda map_draft, player_hd, generator_type, requests, theme, params: \
    merger(static_transformer, map_draft, player_hd, generator_type, requests, theme, params), 'static_transformer'))

#DungeonGenerator.generate_map('null', requests=[MapRequest('crypt')])
