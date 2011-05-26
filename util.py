import inspect
import itertools
import os
import random
from thirdparty.libtcod import libtcodpy as libtcod
from random import randrange, choice
import des

import logging

# return aDb + c
def roll(a, b, c=0, *ignore):
    return sum(libtcod.random_get_int(0, 1, b) for i in range(a)) + c

#caps value at max, if value < 0 return 0
def cap(what, to=0):
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

def create_logger(name=__name__):
    logger = logging.getLogger("module_logger")
    logger.setLevel(logging.DEBUG)
    #create console handler and set level to debug
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    #create formatter
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    #add formatter to ch
    ch.setFormatter(formatter)
    #add ch to logger
    logger.addHandler(ch)
    return logger
logger = create_logger('util')
name_gens = []

def init_name_gen():
    global name_gens
    path = os.path.dirname(__file__)
    for file in os.listdir(os.path.join(path, 'data/namegen')) :
        if file.find('.cfg') > 0 :
            libtcod.namegen_parse(os.path.join(path, 'data','namegen',file))
    name_gens = libtcod.namegen_get_sets()

init_name_gen()
static_names = """Void Vic Mark Pablo Moose_Tachio Taco See_Shall Omen_Ra Betsi
"""
static_cities = """SilverCove
"""

def __create_name_gen(prefix, statics):
    static_names_gen = []
    ng_sets = []
    global name_gens
    for name_gen  in name_gens:
	if name_gen.startswith(prefix.strip()):
	    ng_sets.append(name_gen)
    if statics is not None:
        names_list = map(lambda x: x.strip().replace('_', ' '), statics.strip().split(' '))
        random.shuffle(names_list)
        static_names_gen = itertools.cycle(names_list)
    while True:
        if roll(1, 8) == 8 and statics is not None:
	    name = static_names_gen.next()
	    yield name
        name = libtcod.namegen_generate(choice(ng_sets))
        yield name


ng_names = {
    'name' : __create_name_gen('name', static_names),
    'demon' : __create_name_gen('demon', None),
    'city' : __create_name_gen('city', static_cities),
    'potion' : __create_name_gen('potion', None)
}
def gen_name(flavour='name', check_unique=None):
    ''' generates a name of selected flower. Optionaly checks
    if such name already exists.
	flavour - is the key in ng_names dict
	check_unique is optional dict for checking name's uniqueness
    returns generated name'''
    name = None
    if check_unique is not None:
        while True:
            name = ng_names[flavour].next()
            if not check_unique.has_key(name):
                check_unique[name] = 1
                break
    else: name = ng_names[flavour].next()
    logger.debug('Generated name %s for flavour %s' % (name, flavour))
    return name

def parseDes(file_name, type):
    """parses des file"""
    file_name = os.path.join(os.path.dirname(__file__), 'data', 'des', file_name + '.des')
    return des.parseFile(file_name, type)

def parseFile(file_name, type):
    """parses file"""
    return des.parseFile(file_name, type)

static_colors = [
(0,0,0),  (31,31,31), (63,63,63), (128,128,128), (191,191,191),
(31,31,31),(63,63,63), (128,128,128), (191,191,191),
(255,255,255), (255,0,0), (255,127,0), (255,255,0), (127,255,0),
(0,255,0), (0,255,127), (0,255,255), (0,127,255), (0,0,255),
(127,0,255), (255,0,255), (255,0,127), (127,0,0), (127,63,0),
(127,127,0), (63,127,0), (0,127,0), (0,127,63), (0,127,127),
(0,63,127), (0,0,127), (63,0,127), (127,0,127), (127,0,63),
(63,0,0), (63,31,0), (63,63,0), (31,63,0), (0,63,0),
(0,63,31), (0,63,63), (0,31,63), (0,0,63), (31,0,63),
(63,0,63), (63,0,31), (255,127,127),(255,191,127),(255,255,127),
(191,255,127), (127,255,127), (127,255,191), (127,255,255),
(127,191,255), (127,127,255), (191,127,255), (255,127,255),
(255,127,191), (127,63,63), (127,95,63), (127,127,63),
(95,127,63), (63,127,63), (63,127,95), (63,127,127),(63,95,127),
(63,63,127), (95,63,127), (127,63,127), (127,63,95),
(203,203,203), (255,255,102)]

def random_color(check_unique=None):
    return random_from_list_unique(static_colors, check_unique)

def random_from_list_unique(col, check_unique=None):
    while True:
        clr = choice(col)
        if check_unique is not None:
            if not check_unique.has_key(clr):
                check_unique[clr] = 1
                return clr
        else: return clr

