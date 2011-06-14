from npc import *
import world
from random import choice, shuffle, randrange
from itertools import combinations
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
import util
import items
logger = util.create_logger('plot')
#5d10 + 20 roll for mNPC
MNPC_ROLL = (5, 10, 20)
#1d4 + 4 (from 6-10 quests)
QUEST_GIVER_ROLL =  (2, 3, 4)
#1d4 - 1 roll for immobile NPCs (means 0-3).
IMMOBILE_NPC_ROLL = (1, 4, -1)
#uniques roll 5d2 + 3  (from 8 to 13)
UNIQUES_ROLL = (5, 2, 3)
#traders roll. we want at leat 10 of them, 20 at max.
TRADERS_ROLL = (2, 6,  8)
#min artefacts count
ARTEFACTS_COUNT = (4, 3, 4)
CITIES_COUNT = 15
#the chance of ceratain NPC to become holder of some artefact
ARTEFACT_OWNER_CHANCE = 4


def assign_random_name_from_list(instances, names, demon = False):
    for npc in world.mNPC:
        if npc.name is not None:
            continue
        if isinstance(npc, instances) and len(names) > 0:
            if util.coinflip():
                name = choice(names)
                names.remove(name)
                npc.name = name
                npc.is_demon = demon
                logger.debug('Creating reference NPC ' +str(npc.__class__) +' for ' + name + ' from background')
    for npc in world.mNPC:
        if isinstance(npc, instances) and npc.name is not None:
            names.append(npc.name)

artefacts_count = util.roll(*ARTEFACTS_COUNT)
logger.debug('Rolled for %d artefacts ' % (artefacts_count))
world.artefacts = items.generate_artefacts(artefacts_count, check=world.artefact_names)

from background import make_story
story = make_story()
print story
#######FIRST_PHASE: (all the NPC inhabiting the world except those, generated inside quests nly)
#first let's define our world's population: this will include
# all the NPC's of all types we have, except those which can be placed inside quesuts only

#now let's roll for number of quest-givers. we do want them to exist
min_quest_givers = util.roll(*QUEST_GIVER_ROLL)
actual_quest_givers = 0
while actual_quest_givers < min_quest_givers:
    if actual_quest_givers > 0:
        logger.debug("Rerroling mNPCs as too low number %d of quest-givers was generated (expecting %d)", actual_quest_givers, min_quest_givers)
    #let's roll for number of NPC.  NOTE that we will also add types denoted by ! later.
    mNPC_count = util.roll(*MNPC_ROLL)
    #now toss
    result = []
    actual_quest_givers = 0
    for x in xrange(0, mNPC_count):
        rnd = util.random_from_list_weighted(QuestNPC.mNPC)
        result.append(rnd())
        if not QuestNPC.quest_giver_NPC.__contains__(rnd):
            actual_quest_givers += 1
world.mNPC.extend(result)
world.quest_givers = filter(lambda x: QuestNPC.quest_giver_NPC.__contains__(x.__class__), result)
#now let's roll for immobile NPCs. we don't want many of them. let em be 0-3 at 50% chance for now
immobile_npc = 0
if util.coinflip():
    to_roll = util.roll(*IMMOBILE_NPC_ROLL)
    for i in range(0, to_roll):
        immobile_npc += util.coinflip()
#for now let's place immobile NPCs together with main NPCs
for i in xrange(0, immobile_npc):
    world.mNPC.append(ImmobileNPC())
unique_npc = util.roll(*UNIQUES_ROLL)

uniques = {}
for i in xrange(0, unique_npc):
    unique = util.random_from_list_weighted(UniqueNPC._uniques.values())
    uniques[unique.id] = unique()
world.uniques = uniques.values()
world.mNPC.extend(uniques.values())

traders_npc = util.roll(*TRADERS_ROLL)
for i in xrange(0, traders_npc):
    world.traders.append(TraderNPC())
logger.debug("Rolled for %d main NPCs (Min %d actual %d NPCs are able to issue quests), %d immobile NPCs, %d uniques, %d traders)", mNPC_count, min_quest_givers, actual_quest_givers, immobile_npc, unique_npc, traders_npc)
logger.debug("Total of %d NPCs (%d with traders)", mNPC_count + immobile_npc + unique_npc, mNPC_count + immobile_npc + unique_npc + traders_npc)

#now let's fill names. if we mentioned antagonist - generate apropriate  npc for it
if world.antagonist is not None:
    #antagonists = filter(lambda x: isinstance(x, BadNPC) or isinstance(x, OverpoweredNPC) or isinstance(x, WereNPC) or isinstance(x, ControlledNPC), world.mNPC)
    #_antagonist = choice(antagonists)
    #if _antagonist is None:
    _antagonist = choice((BadNPC, OverpoweredNPC, ControlledNPC, WereNPC))()
    _antagonist.name = world.antagonist
    world.antagonist = _antagonist
    logger.debug('Generated antagonist ' + str(world.antagonist))

#now let's take names from background gen and set them randomly to apropirate NPCS
assign_random_name_from_list(GoodNPC, world.good_npc_names)
assign_random_name_from_list((BadNPC, ControlledNPC, OverpoweredNPC, WereNPC), world.bad_npc_names)
assign_random_name_from_list((WereNPC, BadNPC), world.demon_npc_names, demon=True)
assign_random_name_from_list(DeityNPC, world.deity_npc_names)
#all that left without names gets brand new name
for npc in world.mNPC:
    if npc.name is None:
        npc.name = util.gen_name(check_unique=world.npc_names)
debug_map = {}
for item in world.mNPC:
    cnt = debug_map.get(item.__class__, 0)
    debug_map[item.__class__] = cnt + 1

logger.debug("Generated following mNPC's types")
for k,v in debug_map.items():
    logger.debug(str(k) + '\t\t' + str(v))

#Now we generate NPC circles and their backgrounds
#each NPC has 2 circles. first - is his friends/enemies. second - is the people he know about (friends' enemies)
#lets start from some dwarf-fortress like world-gen. 
#First we gen the world and place mnpc there
city_map = []
need_to_place = world.mNPC[:]
for j in range (1, CITIES_COUNT):
    city = world.City(util.gen_name('city', world.cities_names))
    city_map.append(city)

while len(need_to_place) > 0:
    for y in range(1, len(city_map)):
        if len(need_to_place) == 0: break
        if util.coinflip():
            denizen = need_to_place.pop()
            if isinstance(denizen, ImmobileNPC):
                continue
            if isinstance(denizen, DeityNPC):
                logger.debug('Adding deity %s to city %s deities' % (denizen.name, city_map[y].name))
                city_map[y].add_deity(denizen)
                continue
            logger.debug('Adding %s %s to citizens of %s' % (denizen.name, denizen.__class__, city_map[y].name))
            city_map[y].add_denizen(denizen)

logger.debug('Done settling down')
logger.debug('Distributing  %d artefacts amongst NPCs'% (len(world.artefacts)))
aarts = world.artefacts[:]
for npc in  world.mNPC: #generating artefacts
    if len(aarts) <= 0 : break
    if isinstance(npc, (ImmobileNPC, TraderNPC)):continue 
    if util.onechancein(ARTEFACT_OWNER_CHANCE):
        art = aarts.pop()
        npc.became_owner_of(art)
logger.debug('Done distributing artefacts. We have %d artefacts left' % (len(aarts)))
logger.debug('Launching aquaintance')
world.free_artefacts = aarts
stopyear = randrange(10,20)

def make_relations(city):
    """ Try to make relations between citizens of current city """
    #we get all possible variants here, to see if we can make connection
    suspicion_of_connection = combinations(city.denizens, 2)
    for pair in suspicion_of_connection:
        #if they're still not acquainted - make them friends or enemies
        a, b = pair
        if a.dead or b.dead: continue
        if util.roll(1, 3) == 1:
            if len(city.deities) > 0:
                if a.deity is None:
                    a.deity = choice(city.deities)
                    a.history.append('In year %d %s became worshipper of %s' % (world.year, a.name, a.deity.name))
                    a.deity.folowers.append(a)
                elif util.roll(1, 3) == 3: #in 1/3 cases giveup deity
                    old_deity = a.deity
                    new_deity = choice(city.deities)
                    if old_deity != new_deity:
                        old_deity.enemies.append(a)
                        old_deity.folowers.remove(a)
                        a.deity = new_deity
                        new_deity.folowers.append(a)
                        try:
                            new_deity.enemies.remove(a)
                        except ValueError:
                            pass
                        a.history.append('In year %d %s traded deity %s for %s' % (world.year, a.name, old_deity.name, new_deity.name))

        if not a.know(b) and util.onechancein(5):
            good = isinstance(a, GoodNPC)
            if good: #if a is good 
                if isinstance(b, (BetrayalNPC, GoodNPC)): #and b is either Betrayer or good - friend them
                    a.friend_with(b)
                elif isinstance(b, BadNPC): #else - conflict
                    b.conflict_with(a)
            else: #if a is bad
                if isinstance(b, GoodNPC): #and b is good - conflict
                    if util.onechancein(6): #kill NPC
                        a.kill(b)
                        try:
                            city.denizens.remove(b)
                        except ValueError: pass
                        world.deaders.append(b)
                    elif util.onechancein(5):
                        if b.has_items(): #steal items instead
                            stolen = b.inventory.items.pop()
                            a.became_owner_of(stolen)
                            b.history.append('In year %d %s stole %s from %s' % (world.year, a.name, stolen.unique_name, b.name))
                            b.conflict_with(a)
                    else:
                        a.conflict_with(b)
                elif isinstance(b, BadNPC): #if b is bad as well - try to make relations between them
                    if util.roll(1,5) == 2: #kill NPC
                        if a.master != b:
                            a.kill(b)
                            city.denizens.remove(b)
                            world.deaders.append(b)
                    if util.coinflip(): #make a master of b
                        if b.master is not None and b.master != a and a.master != b: #if b already had master, make a enemy of b.master
                            a.history.append('In year %d %s tried to overtake the control over %s, but failed' % (world.year, a.name, b.name))
                            b.master.conflict_with(a)
                        else: # replace master of b with a
                            b.master = a
                            a.minions.append(b)
                            a.history.append('In year %d %s became boss over %s' %(world.year, a.name, b.name))
                    else: #make a minion of b
                        if a.master is not None :#if a had master, make b enemy of a.master
                            if a.master == b or b.master == a: continue #a.master already is b
                            prev_master = a.master
                            a.conflict_with(prev_master)
                            a.master.minions.remove(a)
                            a.history.append('In year %d %s betrayed his master %s for %s' %(world.year, a.name, prev_master.name, b.name))
                        a.master = b
                        b.minions.append(a)
                        a.history.append('In year %d %s became minnion of %s' %(world.year, a.name, b.name))
        elif a.know(b):
            #a.kill(b)
            pass
while stopyear > 1:
    for city in city_map:
        make_relations(city)
        if util.onechancein(6) and stopyear > 3 and len(city.denizens) > 0: #we need to move one denizen to another city
           random_denizen = choice(city.denizens)
           if random_denizen.dead: continue
           city.denizens.remove(random_denizen)
           new_city = choice(city_map)
           new_city.denizens.append(random_denizen)
           if city != new_city:
               random_denizen.history.append('In year %d %s moved from city of %s to a %s' % (world.year, random_denizen,city.name,new_city.name))
    stopyear -= 1
    world.year += 1


for npc in world.mNPC:
    print 'History for %s ============' % (npc.name)
    for message in npc.history:
        print '\t' + message

print 'DEITY INFO======'
for npc in world.mNPC:
    if not isinstance(npc, DeityNPC): continue
    print '%s has %d followers and %d enemies' % (npc.name, len(npc.folowers), len(npc.enemies))

def count_band(npc, visited=None):
    cnt = 0
    if visited is not None and visited.__contains__(npc): return 0
    if visited is None:
        visited = [npc]
    cnt += len(npc.minions)
    for minion in npc.minions:
        if len(minion.minions) > 0:
            cnt += count_band(minion, visited)
    return cnt
bands = filter(lambda x: isinstance(x, BadNPC) and x.master is None and len(x.minions) > 0, world.mNPC)
for band in bands:
    print 'The band of %s consist of %d members ' % (band.name, count_band(band))
#we do want a nice starting scenario
##starting_place = choice(('room', 'forest', 'city', 'cave', 'desert', 'pip'))
#world.require_for_nextgen(starting_place, 'start')
#now we are ready to set off.
shuffle(world.quest_givers)
first_quest_giver = world.quest_givers[0]
first_quest_giver.doit(world)
first_quest_giver = world.quest_givers[1]
first_quest_giver.doit(world)
