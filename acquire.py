import util
import items
import random

TOP_COST = 1000
TOP_COST_RANGE = 100
ONE_PIECE_ENCHANTMENT = 130
FIXED_ART_UP = 100
def acquire_weapon(npc, unique=None):
    cost = TOP_COST + random.randrange(-1 * TOP_COST_RANGE, TOP_COST_RANGE)
    base_type = random.choice(items.weapons)
    cost -= base_type.base_cost
    wep = base_type()
    if util.coinflip():
        cost -= _make_brand(wep)
    if util.onechancein(5):
        cost += FIXED_ART_UP
        cost -= _make_randart(wep, unique)
        cost -= _add_misc(wep, cost)
    _add_enchants(wep, cost)
    return wep

def gen_artefact_weapon(base_type=None, price=1000, unique=None):
    cost = price
    if base_type is None:
        base_type = random.choice(items.weapons)
    wep = base_type()
    cost -= _make_brand(wep)
    cost -= _make_randart(wep, unique)
    if util.coinflip():
        cost -= _add_misc(wep, cost)
    else:
        cost /= 2
    _add_enchants(wep, cost)
    return wep


def _make_brand(wep):
    if util.coinflip():
        wep.brand = "fire"
        return 200
    else:
        return 0

def _add_enchants(wep, cost):
    max_wait = 20
    while cost > 0 and wep.enchantment < wep.max_enchantment and max_wait > 0:
        max_wait -= 1
        for x in (0, 1):
            if util.onechancein(3) and wep.enchantment[x] < wep.max_enchantment[x] and cost > 0:
                wep.enchantment[x] += 1
                cost -= ONE_PIECE_ENCHANTMENT

def _add_misc(wep, cost):
    old_cost = cost
    accumulated_chance = 2
    accumulated_cost = 100
    feats = items.multilevel_features[:]*3 + items.innate_features[:]
    random.shuffle(feats)
    for feat in feats:
        if cost <= 0 : break
        if util.onechancein(accumulated_chance):
            wep.resists.append(feat)
            cost -= accumulated_cost
            accumulated_cost *= 3
            accumulated_chance *= 2
    return old_cost - cost

def _make_randart(wep, unique=None):
    wep.randart = True
    wep.unique_name = util.gen_name('artefact', unique)
    return 100

def acquire(cost=1000, unique=None, artefact=False):
    """Acquires anything """
    if artefact:
        return gen_artefact_weapon(price=1000, unique=unique)
    return acquire_weapon(cost, unique)
