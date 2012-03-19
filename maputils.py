import util
from collections import namedtuple

NO_FLIP = 0
HORIZONTAL_FLIP = 1
VERTICAL_FLIP = 2
ROTATE = 4
FORCE_HORIZONTAL_FLIP = (1 << 4)
FORCE_VERTICAL_FLIP = (1 << 5)
FORCE_ROTATE = (1 << 6)
ANY = HORIZONTAL_FLIP | VERTICAL_FLIP | ROTATE
FORCE_ALL = 100

rotate_setting = {
    'any' : ANY,
    'RANDOM': ANY,
    'NONE' : NO_FLIP,
    'FORCE_ALL' : FORCE_ALL
}

def random_rotate_and_clone_map(map, settings = 'any', params = None):
    """
    random_rotate(...) -> (map, (rev_x, rev_y, swap_x_y))
    Rotates a map.
    """
    if not rotate_setting.has_key(settings) : raise RuntimeError('Not valid orientation [%s] passed to random_rotate' % settings)
    settings = rotate_setting[settings]
    map = __clone_map(map)
    if settings == NO_FLIP:
        return map, (0, 0, 0)
    if params and settings & FORCE_ALL != FORCE_ALL:
        rev_x, rev_y, swap_x_y = params
    else:
        rev_x, rev_y = util.coinflip(), util.coinflip()
        swap_x_y = util.coinflip()
        if settings & FORCE_VERTICAL_FLIP == FORCE_VERTICAL_FLIP:
            rev_x = 1
            settings |= VERTICAL_FLIP
        if settings & FORCE_HORIZONTAL_FLIP == FORCE_HORIZONTAL_FLIP:
            rev_y = 1
            settings |= HORIZONTAL_FLIP
        if settings & FORCE_ROTATE == FORCE_ROTATE:
            swap_x_y = 1
            settings |= ROTATE
    if rev_x and (settings & VERTICAL_FLIP == VERTICAL_FLIP):
        for line in map:
            line.reverse()
    if rev_y and (settings & HORIZONTAL_FLIP == HORIZONTAL_FLIP):
        map.reverse()
    if swap_x_y and (settings & ROTATE == ROTATE):
        new_map = []
        for x in xrange(0, len(map[0])):
            new_line = []
            for y in xrange(0, len(map)):
                new_line.append(map[y][x])
            new_map.append(new_line)
        return new_map, (swap_x_y, rev_x, rev_y)
    return map, (swap_x_y, rev_x, rev_y)

def __clone_map(original):
    return [[y for y in x] for x in original]

class SubList(list):
    def __init__(self, src, start, to):
        super(SubList, self).__init__()
        self.src = src
        self.start = start
        self.to = to

    def __getitem__(self, index):
        return self.src[self.start + index]
    def __setitem__(self, index, value):
        self.src[self.start + index] = value

    def __len__(self):
        return self.to - self.start

    def __iter__(self):
        return self.src[self.start: self.to + 1].__iter__()

class Room(object):
    def __init__(self):
        self.x, self.y = None, None
        self.width, self.height = 0, 0
        """ point to source description of this map => MapDef"""
        self.src = None
        """ points to map bytes => [][]"""
        self._map = None
        """ points to MapRequest which generated this room """
        self.request = None
        self.id = None

    def get_map(self):
        return self._map

    def set_map(self, map):
        self._map = map
        self.width = len(map[0])
        self.height = len(map)
    map = property(fget=get_map, fset=set_map)

    @property
    def x2(self):
        if self.x is not None and self.width:
            return self.x + self.width - 1 #we start from 0
        else:
            return None
    @property
    def y2(self):
        if self.y is not None and self.height:
            return self.y + self.height - 1 #we start from 0
        else:
            return None

    @property
    def center(self):
        center_x = (self.x + self.x2) / 2
        center_y = (self.y + self.y2) / 2
        return center_x, center_y


    @property
    def is_fixed(self):
        if not self.src:
            return False
        else:
            return self.src.fixed

    def xy_in_room(self, x, y):
        return self.x <= x <= self.x2 and self.y <= y <= self.y2

    def xy_is_border(self, x, y):
        _x, _y = self.x - 1, self.y - 1
        _x2, _y2 = self.x2 + 1, self.y2 + 1
        border = _x == x or _x2 == x and (self.y <= y <= self.y2)
        border |= _y == y or _y2 == y and (self.x <= x <= self.x2)
        return border

    def overlap(self, x, y, x2, y2):
        return self.x < x2 and self.x2 > x and self.y < y2 and self.y2 > y

class MultilevelRoom(Room):
    """
    Describes multilevel room
    """
    def __init__(self):
        super(MultilevelRoom, self).__init__()
        """ point to levels in this room => [][]"""
        self.levels = {}
        """ points to MapDef of each level """
        self.levels_src = {}

    def get_map(self):
        return self._map

    def set_map(self, map):
        self._map = map
        self.width = len(map[0])
        self.height = len(map)
        self.levels['0'] = self._map
    map = property(fget=get_map, fset=set_map)


def find_feature(_map, id=None, oftype=None, multiple=False, filter=None):
    """ find_feature => (tile, x, y)
    or find_feature(multiple=True) => [(tile,x,y)...]
    Finds feature from map by id (if specified) or by certain type name (if specified
    if multiple => True - all matching items will be returned list of tuples. Otherwise
    only single tuple is returned
    filter is a lambda expression invoked on each found item
    returns tuple tile, x, y
    """
    res = []
    x, y = 0,0
    for line in _map:
        for char in line:
            if id:
                if hasattr(char, 'id') and char.id == id:
                    if filter and not filter(char): continue
                    if multiple:
                        res.append((char, x, y))
                    else:
                        return char, x, y
            elif oftype:
                if isinstance(oftype, str):
                    if isinstance(char, type):
                        if char.__name__ == oftype:
                            if filter and not filter(char): continue
                            if multiple:
                                res.append((char, x, y))
                            else:
                                return char, x, y
                    if char.__class__.__name__ == oftype:
                        if filter and not filter(char): continue
                        if multiple:
                            res.append((char, x, y))
                        else:
                            return char, x, y
                elif isinstance(oftype, type):
                    char_type = char
                    if not isinstance(char_type, type):
                        char_type = type(char)
                    if issubclass(char_type, oftype):
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

def replace_feature_atxy(map, x, y, with_what):
    ft = with_what
    if callable(with_what):
        ft = with_what()
    if isinstance(ft, type):
        ft = ft()

    map[y][x] = ft

def replace_feature(map, type, id, with_what):
    features = find_feature(map, id=id, oftype=type, multiple=True)
    if features:
        for nouse, x, y in features:
            replace_feature_atxy(map, x, y, with_what)


def _manhattan_distance(x, y, x2, y2):
    return abs(x - x2) + abs(y - y2)

def _cmp_tiles_by_distance(x, y, t1, t2):
    return 1 if _manhattan_distance(x, y, t1[1], t1[2]) > \
            _manhattan_distance(x, y, t2[1], t2[2]) else -1

def square_search_nearest(base_x, base_y, map, oftype):
    """ square_search_nearest(int, int, [][], str or type) => [(tile,x,y)...]
    Returns tiles sorted by their relative distance from point (base_x, base_y)
    """
    feats = find_feature(map, oftype=oftype, multiple=True)
    if not feats:
        return None
    feats.sort(lambda a, b: _cmp_tiles_by_distance(base_x, base_y, a, b))
    return feats

