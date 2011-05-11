from npc import *
import world

from __init__ import logger
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
import util
#1d10 + 12 roll for mNPC
MNPC_ROLL = (1, 10, 12)
#1d4 + 4 (from 6-10 quests)
QUEST_GIVER_ROLL =  (2, 3, 4)
#1d4 - 1 roll for immobile NPCs (means 0-3).
IMMOBILE_NPC_ROLL = (1, 4, -1)
#uniques roll 5d2 + 3  (from 8 to 13)
UNIQUES_ROLL = (5, 2, 3)
#traders roll. we want at leat 10 of them, 20 at max.
TRADERS_ROLL = (2, 6,  8)


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

#now let's fill names
if world.antagonist is not None:
    antagonists = filter(lambda x: isinstance(x, BadNPC) or isinstance(x, OverpoweredNPC) or isinstance(x, WereNPC) or isinstance(x, ControlledNPC), world.mNPC)
    _antagonist = choice(antagonists)
    if _antagonist is None:
        _antagonist = random.choice((BadNPC, OverpoweredNPC, ControlledNPC, WereNPC))()
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

#now we are ready to set off.
first_quest_giver = choice(world.quest_givers)
first_quest_giver.doit(world)
