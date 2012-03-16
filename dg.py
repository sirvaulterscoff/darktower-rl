from dungeon_generators import MapDef, MapRequest, get_map_file, parse_file, ft
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
        params : no_large => bool (disable generation of large maps [map file with prefix large_])
                map_id => str (place map with certain id ontop of current map)
                room_maxwidth, room_minwidth, room_maxheight, room_minheight => int (parameters of rooms if applicable)
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
def _check_static_params(generator_type, hd, MapDef, params):
    """ Check params for MapDef loaded from des file. Check that map theme matches that of generator.
        Player HD is higher or equals that defined in des file etc... """
    if generator_type != 'null':
        if not MapDef.has_terrain(generator_type):
            return False
    if MapDef.HD >  hd:
        return False
    if MapDef.unique and unique_maps_already_generated.has_key(MapDef.id):
        return False
    #we can have exact id specified
    if params and params.has_key('map_id'):
        return params['map_id'] == MapDef.id
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
    if not av_maps:
        return None
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
    return tmap.prepare(params)


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
                request = MapRequest(theme, {})
                requests.append(request)
        except Exception, e:
            print 'Exception during static preprocessor ' + e



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
    static_transformer(..) - > [ (MapDef, MapRequest) ...]
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
            _map = request.map.prepare(request.params)
            result.append( (_map, request) )
            continue
        tparams = {}
        if params:
            tparams.update(params)
        if request.params:
            tparams.update(request.params)
        tmap =  _choose_map(generator_type, tparams, player_hd, request.type, request.size)
        if tmap:
            result.append( (tmap, request) )
            tmap.prepare(tparams)

    mini_map_count = randrange(*small_theme_maps_count)
    logger.debug('Generating %d mini-maps for current map' % mini_map_count)
    #now generate plenty of small features
    if theme:
        for x in xrange(mini_map_count):
            tmap = _choose_map(generator_type, params, player_hd, theme, 'mini')
            if tmap:
                result.append((tmap, None))
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
        valid_position = True
        #check rooms overlapping
        for room in map_draft.rooms.values():
            if room.xy_in_room(x, y):
                valid_position = False
                break
        #if rooms do not overlap
        if valid_position:
            return x, y


def __merge_leveled(map_draft, child_map_bytes, child, level, roomid):
    """Adds non-base level map to a room which will hold base level map
    @map_draft - map being generated
    @child_map_bytes - map bytes [][] after applying orientation
    @child - MapDef of child level
    @level - level number
    @roomid - id of the room (we use it to stack levels)
    """
    #check if rooms already exists
    map_id = roomid
    if map_draft.rooms.has_key(map_id):
        room = map_draft.rooms[map_id]
    else:
        room = MultilevelRoom()
        map_draft.rooms[map_id] = room
    room.levels[level] = child_map_bytes
    room.levels_src[level] = child
    room.src = child.parent

def __create_room(map_draft, newmap, map_src, id, request):
    #check if rooms already exists
    if map_draft.rooms.has_key(id):
        room = map_draft.rooms[id]
        room.request = request
        room.id = id
    else:
        room = Room()
        map_draft.rooms[id] = room
        room.request = request
        room.id = id
    room.src = map_src
    room.map = newmap
    room.width = len(newmap[0])
    room.height = len(newmap)
    return room

nomerge_chance = 50 #todo move to params
def __merge_room(map_draft, room, params):
    """ __merge_room(MapDef, MapDef, {}) -> None
    Merges room in map_draft, choosing random location
    @map_draft -> MapDef
    @room -> Room or MultilevelRoom to merge
    @params - params of dungeon generator itself
    """
    placement = room.src.placement
    _rparams = None
    if room.request:
        _rparams = room.request.params

    if _rparams and _rparams.has_key('xy'):
        x, y = _rparams['xy']
    else:
        x, y = __find_random_mergepoint(map_draft, room, room.src.position)
    room.x, room.y = x, y
    try:
        for line in room.map:
            for tile in line:
                if type(tile) == none: #special tile type - don't merge onto map
                    x+=1
                    continue
                dest_tile = map_draft.map[y][x]
                if placement == 'overflow':
                    if dest_tile.flags & FIXED: continue #in overflow placement we don't rewrite underlying pixels
                    if tile.flags & FIXED: #we should rewrite if room's fixel is fixed
                        map_draft.map[y][x] = tile
                    elif util.roll(1, nomerge_chance) == 1: #or we may not rewrite 1/nomerge_chance
                        #todo let's actualy make clustered ruins - i.e. skip merge for a 3x3 or large square
                        x+=1
                        continue
                    else:
                        map_draft.map[y][x] = tile
                elif placement == 'include' or placement == 'asis': #in both modes we just
                    map_draft.map[y][x] = tile
                else:
                    raise RuntimeError('Invalid merge placement [%s] specified for map [%s]' % (placement, room.src.id))
                x+=1
            x = room.x
            y += 1
    except IndexError, ie:
        print 'Failed to merge static feature into map. Map params w:[%d] h:[%d] \n Room params: w:[%d] h:[%d] x:[%d] y:[%d]\n current %d,%d' % \
              (map_draft.width, map_draft.height, room.width, room.height, room.x, room.y, x, y)
        raise ie
    map_view = []
    for y in xrange(room.y, room.y2):
        map_view.append(SubList(map_draft.map[y], room.x, room.x2))
    room.map = map_view


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
    ids = {}
    #iterate over list of MapDefs
    for map, request in maps_to_merge:
        #now assure map id uniqueness. Static map uniqueness handling is the task of static preprocessor
        #here we just need to assure that we have unique id space for each room
        id = map.id
        cnt = 1
        while ids.has_key(id):
            id = map.id + '$' + str(cnt)
            cnt += 1
        ids[id] = True
        if map.orient:
            newmap, rotate_params = random_rotate_and_clone_map(map.map, map.orient)
        else:
            newmap, rotate_params = map.map, None
        for level, child in map.levels.items(): # now we transform all submaps
            child_map_bytes = None
            if child.orient and child.orient != 'NONE': #if child redefines orient - let's use it
                child_map_bytes, ignored = random_rotate_and_clone_map(child.map, child.orient)
            elif rotate_params: #keep the same orient as parent
                child_map_bytes, ignored = random_rotate_and_clone_map(child.map, map.orient, params=rotate_params)
            __merge_leveled(map_draft, child_map_bytes, child, level, id)

        rooms.append(__create_room(map_draft, newmap, map, id, request))
    for room in rooms:
        __merge_room(map_draft, room, params)
    del ids


def __gen_floor_square(MapDef, x, y, w, h):
    mapsrc = [['.' for y in xrange(x+w)] for x in xrange(y+h)]
    MapDef.map = mapsrc
    return MapDef.prepare(None)

def __gen_wall_square(MapDef, x, y, w, h):
    mapsrc = [['#' for y in xrange(x+w)] for x in xrange(y+h)]
    MapDef.map = mapsrc
    return MapDef.prepare(None)


def null_generator(map_draft, player_hd, generator_type, requests, params, theme):
    """Special cased generator - used when we need full sized, untransformed map from des file
    """
    return __gen_floor_square(map_draft, 0, 0, map_draft.width, map_draft.height)


MIN_ROOM_WIDTH = 5
MIN_ROOM_HEIGHT = 2
MIN_ROOM_SIZE = MIN_ROOM_WIDTH * MIN_ROOM_HEIGHT
CORRIDOR_FACTOR = 0.5

def __get_room_size_params(params, map_w, map_h):
    minw, maxw, minh, maxh = 5, 20, 2, 20
    if not params:
        return minw, maxw, minh, maxh
    if params.has_key('room_maxwidth'):
        maxw = min(map_w - 2, params['room_maxwidth']) #waxwidth < mapwidth
    if params.has_key('room_minwidth'):
        minw = min(max(2, params['room_minwidth']), maxw) # 2<minwidht<maxwidth
    if params.has_key('room_maxheight'):
        maxh = min(map_h - 2, params['room_maxheight']) #maxheight < mapheight
    if params.has_key('room_minheight'):
        minh = min(max(2, params['room_minheight']), maxh)# 2<minheight<maxheight
    return minw, maxw, minh, maxh

ROOM_DOOR_CHANCE = 7
ROOM_HIDDEN_DOOR_CHANCE = 60
def __create_h_tunnel(MapDef, x1, x2, y, room):
    for x in range(min(x1, x2), max(x1, x2)):
        tile = MapDef.map[y][x]
        if not tile.passable():
            if room.xy_is_border(y, x):
                if util.one_chance_in(ROOM_DOOR_CHANCE):
                    MapDef.map[y][x] = ft.door
                    continue
                elif util.one_chance_in(ROOM_HIDDEN_DOOR_CHANCE):
                    MapDef.map[y][x] = ft.hidden_door
                    continue
            MapDef.map[y][x] = ft.floor

def __create_v_tunnel(MapDef, y1, y2, x, room):
    for y in range(min(y1, y2), max(y1, y2)):
        tile = MapDef.map[y][x]
        if not tile.passable():
            if room.xy_is_border(y, x):
                if util.one_chance_in(ROOM_DOOR_CHANCE):
                    MapDef.map[y][x] = ft.door
                    continue
                elif util.one_chance_in(ROOM_HIDDEN_DOOR_CHANCE):
                    MapDef.map[y][x] = ft.hidden_door
                    continue
            MapDef.map[y][x] = ft.floor

def rooms_corridors_generator(map_draft, player_hd, generator_type, requests, params, theme):
    map_draft = __gen_wall_square(map_draft, 0, 0, map_draft.width, map_draft.height)
    rooms = []
    num_rooms = 0
    square = map_draft.width * map_draft.height
    max_rooms = int((square / MIN_ROOM_SIZE) * CORRIDOR_FACTOR) #determine maximum number of rooms

    for roomid in xrange(max_rooms):
        if num_rooms > max_rooms: break

        minw, maxw, minh, maxh = __get_room_size_params(params, map_draft.width, map_draft.height)

        ticks = max_rooms * 5 #retries to generate all rooms
        new_rooms = []
        while True:
            if ticks <= 0: break
            ticks -= 1

            width = randrange(minw, maxw)
            height = randrange(minh, maxh)
            #random position without going out of the boundaries of the map
            x = randrange(1, map_draft.width - 1 - width)
            y = randrange(1, map_draft.height - 1 - height)

            if filter(lambda room: room.overlap(x-1, y-1, x+width+1, y+height+1), map_draft.rooms.values()):
                continue #room overlap
            room = Room()
            room.x, room.y = x, y
            room.width, room.height = width, height
#            room.src = __gen_floor_square(MapDef(), 0, 0, width, height)
#            __gen_floor_square(map_draft, x, y, width, height)
            for _x in xrange(width):
                for _y in xrange(height):
                    map_draft.replace_feature_atxy(x+_x, y+_y, ft.floor())
            new_rooms.append(room)
            map_draft.rooms['roomc' + str(roomid)] = room

            new_x, new_y = room.center
            if num_rooms > 0:
                prev_x, prev_y = new_rooms[-1].center
#                if util.coinflip():
#                    __create_h_tunnel(map_draft, prev_x, new_x, prev_y, room)
#                    __create_v_tunnel(map_draft, prev_y, new_y, new_x, room)
#                else:
#                    __create_v_tunnel(map_draft, prev_y, new_y, prev_x, room)
#                    __create_h_tunnel(map_draft, prev_x, new_x, new_y, room)
            num_rooms += 1
            break
    map_draft.debug_print()
    return map_draft

generators['null'] = null_generator
generators['rooms_corridor'] = rooms_corridors_generator

transformation_pipe.append(PipeItem(lambda map_draft, player_hd, generator_type, requests, theme, params: \
    merger(static_transformer, map_draft, player_hd, generator_type, requests, theme, params), 'static_transformer'))


#todo - overlapping generator: place a room - make walls around room FIXED. place another room withour checking for overalap - remove walls except FIXED. rinse and repeat