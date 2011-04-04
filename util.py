from thirdparty.libtcod import libtcodpy as libtcod
from random import randrange, choice

# return aDb + c
def roll(a, b, c=0, *ignore):
    return sum(libtcod.random_get_int(0, 1, b) for i in range(a)) + c

#caps value at max, if value < 0 return 0
def cap(what, to=100000):
    if what < 0 and to > 0: return 0
    return min(what, to)


def cap_lower(what, min, to):
    if what < min: return to
    return min


def random_by_level(level, items):
    items = filter(lambda a: a.dlvl == level, items)
    start = sum(item.common for item in items)
    if not start: return None
    n = randrange(start)
    for item in items:
        if n < item.common:
            return item
        else:
            n -= item.common
    return choice(items)


class AutoAdd(type):
    def __new__(mcs, name, bases, dict):
        cls = type.__new__(mcs, name, bases, dict)
        holder = None
        if dict.get('__meta_field__'):
            holder = cls.__meta_field__
        else:
            holder = cls.ALL
        if dict.get('__meta_skip__'):
          if not dict.get(dict.get('__meta_skip__')):
              holder.append(cls)
        elif not dict.get('skip_register'):
            holder.append(cls)
        return cls


def distance(x1, y1, x2, y2):
    dx = abs(x2 - x1)
    dy = abs(y2 - y1)
    return (dx + dy + max(dx, dy)) / 2


def coinflip():
    return libtcod.random_get_int(0, 0, 1)

def put_cloud(startx, starty, tile_check_callback, tile_create_callback,
               pattern = [ (0,0), (1, 0), (2, 0),
                            (0,1), (1,1), (2,1),
                            (0,2), (1, 2), (2, 2)]):
    failed = False
    for coord in pattern:
        newx = startx + coord[0]
        newy = starty + coord[1]
        if tile_check_callback(newx, newy):
            if tile_create_callback is not None:
                tile_create_callback (newx, newy)
        else:
            failed = True
    return failed

#this method will try to place cloud of default size 3x3, if it's not possible
#it will use flood fill
def flood_fill(startx, starty, tile_check_callback, tile_create_callback,
               pattern = [ (0,0), (1, 0), (2, 0),
                            (0,1), (1,1), (2,1),
                            (0,2), (1, 2), (2, 2)],
               passed = None):
    #means it's topmost run
    if passed == None:
        passed = []
        #let's check if we can place cloud and place it if we can ^_^
        if put_cloud(startx, starty, tile_check_callback, None, pattern) :
            put_cloud(startx, starty, tile_check_callback, tile_create_callback, pattern)

    if len(passed) == len(pattern):
        return
    for coord in pattern:
        prevx, prevy = None, None
        newx = startx + coord[0]
        newy = starty + coord[1]
        if not passed.__contains__( (newx, newy) ):
            if tile_check_callback(newx, newy):
                tile_create_callback(newx, newy)
                passed.append( (newx, newy))
                prevx, prevy = newx, newy
            else:
                #let's continue from previous "good" tile
                if prevx != None:
                    flood_fill(prevx, prevy, tile_check_callback, tile_create_callback, pattern, passed)


EXP_MAP = (0, 10, 30, 70, 140, 270, 520, 1010, 1980, 3910, 7760, 15450, 29000, 48500, 74000, 105500, 143000, 186500,
236000, 291500, 353000, 420500, 494000, 573500, 659000, 750500, 848000)
def xp_for_lvl(next_lvl):
    return EXP_MAP[next_lvl]


