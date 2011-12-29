import util

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

def random_rotate(map, settings = 'any', params = None):
    """
    random_rotate(...) -> (map, (rev_x, rev_y, swap_x_y))
    Rotates a map.
    """
    if not rotate_setting.has_key(settings) : raise RuntimeError('Not valid orientation [%s] passed to random_rotate' % settings)
    settings = rotate_setting[settings]
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
    map = __clone_map(map)
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

class Room(object):
    def __init__(self):
        self.x, self.y = None, None
        self.width, self.height = 0, 0
        """ point to source description of this map => MapDef"""
        self.src = None
        """ points to map bytes => [][]"""
        self._map = None

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
            return self.x + self.width
        else:
            return None
    @property
    def y2(self):
        if self.y is not None and self.height:
            return self.y + self.height
        else:
            return None


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

def xy_in_room(room , x, y):
    if x>=room.x and x<=room.x2:
        if y>=room.y and y<=room.y2:
            return True
    return False


def find_feature(_map, id=None, oftype=None, multiple=False, filter=None):
    """ Finds feature from map by id (if specified) or by certain type name (if specified
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
