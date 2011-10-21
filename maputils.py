import util

NO_FLIP = 0
HORIZONTAL_FLIP = 1
VERTICAL_FLIP = 2
ROTATE = 4
FORCE_HORIZONTAL_FLIP = (1 << 4) | HORIZONTAL_FLIP
FORCE_VERTICAL_FLIP = (1 << 5) | VERTICAL_FLIP
FORCE_ROTATE = (1 << 6) | ROTATE
ANY = HORIZONTAL_FLIP | VERTICAL_FLIP | ROTATE
FORCE_ALL = 100

rotate_setting = {
    "any" : ANY,
    "RANDOM": ANY
}

def random_rotate(map, settings = 'any', params = None):
    """
    random_rotate(...) -> (map, (rev_x, rev_y, swap_x_y))
    Rotates a map.
    """
    if not rotate_setting.has_key(settings) : raise RuntimeError('Not valid orientation [%s] passed to random_rotate' % settings)
    settings = rotate_setting[settings]
    if params and not settings & FORCE_ALL:
        rev_x, rev_y, swap_x_y = params
    else:
        rev_x, rev_y = util.coinflip(), util.coinflip()
        swap_x_y = util.coinflip()
        if settings & FORCE_VERTICAL_FLIP:
            rev_x = 1
        if settings & FORCE_HORIZONTAL_FLIP:
            rev_y = 1
        if settings & FORCE_ROTATE:
            swap_x_y = 1
    map = __clone_map(map)
    if rev_x and settings & VERTICAL_FLIP:
        for line in map:
            line.reverse()
    if rev_y and settings & HORIZONTAL_FLIP:
        map.reverse()
    if swap_x_y and settings & ROTATE:
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