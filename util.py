from thirdparty.libtcod import libtcodpy as libtcod
from random import randrange, choice

# return aDb + c
def roll(a, b, c=0, *ignore):
	return sum(libtcod.random_get_int(0, 1, b) for i in range(a)) + c

#caps value at max, if value < 0 return 0
def cap(what, to = 100000):
    if what < 0 and to > 0: return 0
    return min(what, to)

def cap_lower(what, min, to):
    if what < min : return to
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
        if not dict.get('skip_register'):
            cls.ALL.append(cls)
        return cls

def distance(x1, y1, x2, y2):
    dx = abs(x2-x1)
    dy = abs(y2-y1)
    return (dx+dy+max(dx,dy))/2

def coinflip():
	return libtcod.random_get_int(0, 0, 1)
