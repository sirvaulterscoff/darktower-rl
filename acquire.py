import util
import items
import random

TOP_COST = 1000
TOP_COST_RANGE = 100
ONE_PIECE_ENCHANTMENT = 130
FIXED_ART_UP = 100
def acquire_weapon(npc):
    cost = TOP_COST + random.randrange(-1 * TOP_COST_RANGE, TOP_COST_RANGE)
    base_type = random.choice(items.weapons)
    cost -= base_type.base_cost
    wep = base_type()
    if util.coinflip():
        cost -= make_brand(wep)
    if util.onechancein(5):
        cost += FIXED_ART_UP
        cost -= make_randart(wep)
        cost -= add_misc(wep, cost)
    add_enchants(wep, cost)
    return wep

def gen_artefact_weapon(base_type, price):
    cost = price
    wep = base_type()
    cost -= make_brand(wep)
    cost -= make_randart(wep)
    if util.coinflip():
        cost -= add_misc(wep, cost)
    else:
        cost /= 2
    add_enchants(wep, cost)
    return wep


def make_brand(wep):
    if util.coinflip():
        wep.brand = "fire"
        return 200
    else:
        return 0

def add_enchants(wep, cost):
    max_wait = 20
    while cost > 0 and wep.enchantment < wep.max_enchantment and max_wait > 0:
        max_wait -= 1
        for x in (0, 1):
            if util.onechancein(3) and wep.enchantment[x] < wep.max_enchantment[x] and cost > 0:
                wep.enchantment[x] += 1
                cost -= ONE_PIECE_ENCHANTMENT

def add_misc(wep, cost):
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

def make_randart(wep):
    wep.randart = True
    wep.unique_name = util.gen_name('artefact')
    return 100

acquire_weapon(None).debug_print()
for i in range(1, 10):
    gen_artefact_weapon(items.ShortBlade, 1200).debug_print()
