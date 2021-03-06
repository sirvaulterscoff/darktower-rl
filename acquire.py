import util
import items
import random

TOP_COST_WEP = 1000
TOP_COST_WEP_RANGE = 100
ONE_PIECE_ENCHANTMENT = 130
FIXED_ART_UP = 100
TOP_COST_ARMOR = 1000
TOP_COST_ARMOR_RANGE = 100

def acquire(cost=1000, unique=None, artefact=False):
    """Acquires anything """
    if artefact:
        return gen_artefact_weapon(price=1000, unique=unique)
    return acquire_weapon(cost, unique)

def acquire_weapon(npc, unique=None):
    cost = TOP_COST_WEP + random.randrange(-1 * TOP_COST_WEP_RANGE, TOP_COST_WEP_RANGE)
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

def acquire_armor(npc, unique=None, base_type=None, artefact=False):
    cost = TOP_COST_ARMOR + random.randrange(-1 * TOP_COST_ARMOR_RANGE, TOP_COST_ARMOR_RANGE)
    if base_type is None:
        base_type = random.choice(items.weapon)
    cost -= base_type.base_cost
    arm = base_type()
    if util.onechancein(6):
        cost -= _make_resist(arm)
    elif util.onechancein(7) or artefact:
        cost += FIXED_ART_UP
        cost -= _make_randart(arm, unique)
        cost -= _add_misc(arm, cost)
    _add_enchants(arm, cost, True)
    return arm

def _make_resist(arm):
    """ This is used for items with single resistance alowed - like armor """
    if util.onechancein(5):
        arm.resist = "fire"
    return 400

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

def _add_enchants(wep, cost, single_digit=False):
    max_wait = 20
    while cost > 0 and wep.enchantment < wep.max_enchantment and max_wait > 0:
        max_wait -= 1
        if single_digit:
            if util.onechancein(3) and wep.enchantment < wep.max_enchantment and cost > 0:
                wep.enchantment += 1
                cost -= ONE_PIECE_ENCHANTMENT
        else:
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

