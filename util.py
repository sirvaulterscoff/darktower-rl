import inspect
import itertools
import os
import random
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
    return what


def random_by_level(level, items):
    items = filter(lambda a: a.dlvl == level, items)
    return random_from_list(items)

def random_from_list(items):
    start = sum(item.common for item in items)
    if not start: return None
    n = randrange(start)
    for item in items:
        if n < item.common:
            return item
        else:
            n -= item.common
    return choice(items)

def random_from_list_weighted(items, inverse = False):
    result = []
    _max = 0
    if inverse:
        _max = reduce(lambda x,y: max(x, y.common), items).common
    for item in items:
        #if inverse - reverse monster common. we still giva a chance to monsters with highest common
        if inverse:
            result.extend(itertools.repeat(item, _max - item.common + 1))
        else:
            result.extend(itertools.repeat(item, item.common))
    return result[random.randrange(0, len(result))]

class AutoAdd(type):

    def __new__(mcs, name, bases, dict):
        cls = type.__new__(mcs, name, bases, dict)
        if dict.has_key('__meta_dict__'):
            skip_dict = dict.get('__meta_dict__')
        else:
            skip_dict = find_base(cls)
        if not skip_dict:
            skip_dict = { 'skip_register' : cls.ALL }
        for key, value in skip_dict.items():
            if not dict.get(key):
                value.append(cls)
        return cls

def find_base(cls):
    for bcls in cls.__bases__:
        if bcls.__dict__.has_key('__meta_dict__'):
            return bcls.__meta_dict__
        else:
            return find_base(bcls)
    return None


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

def init_name_gen(postfix):
    for file in os.listdir('../data/namegen') :
        if file.find(postfix + '.cfg') > 0 :
            libtcod.namegen_parse(os.path.join('..','data','namegen',file))
    return libtcod.namegen_get_sets()

static_names = """Void Vic Mark Pablo Moose_Tachio Taco See_Shall Omen_Ra Betsi
"""
static_cities = """SilverCove
"""

def create_name_gen(prefix, statics):
    ng_names = init_name_gen(prefix)
    if statics is not None:
        names_list = map(lambda x: x.strip().replace('_', ' '), statics.strip().split(' '))
        random.shuffle(names_list)
        static_names_gen = itertools.cycle(names_list)
    while True:
        if roll(1, 3) == 1 and statics is not None:
            name = static_names_gen.next()
            yield name
        name = libtcod.namegen_generate(ng_names[random.randrange(0, len(ng_names))])
        yield name


ng_names = {
    'name' : create_name_gen('names', static_names),
    'demon' : create_name_gen('names', None),
    'city' : create_name_gen('town', static_cities)
}

def gen_name(flavour='name', check_unique=None):
    if check_unique is not None:
        while True:
            name = ng_names[flavour].next()
            if check_unique.isdisjoint(name):
                check_unique.add(name)
                return name
            
    return ng_names[flavour].next()
