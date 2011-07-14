from npc import *
import world
from random import choice, shuffle, randrange
from itertools import combinations, chain
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
import util
import items
import acquire
logger = util.create_logger('plot')
#3d10 + 20 roll for mNPC
MNPC_ROLL = (3, 10, 20)
DEITY_ROLL = (2, 3, 2)
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
CITIES_COUNT = 6
#the chance of ceratain NPC to become holder of some artefact
ARTEFACT_OWNER_CHANCE = 4

debug_names = True
def assign_random_name_from_list(instances, names, demon = False):
    for npc in world.mNPC:
        if npc.name is not None:
            continue
        if isinstance(npc, instances) and len(names) > 0:
            if util.coinflip():
                name = choice(names)
                names.remove(name)
                if debug_names:
                    npc.name = name + str(npc.__class__)
                npc.is_demon = demon
                logger.debug('Creating reference NPC ' +str(npc.__class__) +' for ' + name + ' from background')
    for npc in world.mNPC:
        if isinstance(npc, instances) and npc.name is not None:
            names.append(npc.name)

while True:
    world.reset()
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
            if not npc in QuestNPC.quest_giver_NPC:
                actual_quest_givers += 1
    world.mNPC.extend(result)
    #now let's generate deities
    deity_coun= util.roll(*DEITY_ROLL)
    deities = []
    for x in xrange(0, deity_coun):
        deity = DeityNPC()
        deities.append(deity)
    world.mNPC.extend(deities)

    world.quest_givers = filter(lambda x: x.__class__ in QuestNPC.quest_giver_NPC, result)
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
    #now let's generate a king - why not?
    king = KingNPC()
    world.king = king
    king.name = util.gen_name(check_unique=world.npc_names)
    logger.debug('Generated king %s' % (king.name))
    for x in range(2, util.roll(2, 3, 1)):
        guard = GoodNPC()
        guard.name = util.gen_name(check_unique=world.npc_names)
        king.guards.append(guard)
    crown = acquire.acquire_armor(king, world.artefact_names, items.Crown, True)
    king.became_owner_of(crown)
    queen = RoyaltyNPC("queen")
    queen.name = util.gen_name('female', check_unique=world.npc_names)
    world.royalties.append(queen)
    heir_count = randrange(0, 3)
    logger.debug('King will have %d heir/s'% (heir_count))
    for x in range(0, heir_count):
        heir = RoyaltyNPC("princess")
        heir.name = util.gen_name('female', check_unique=world.npc_names)
        world.royalties.append(heir)

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
    if world.antagonist is not None and isinstance(world.antagonist, str):
        #antagonists = filter(lambda x: isinstance(x, BadNPC) or isinstance(x, OverpoweredNPC) or isinstance(x, WereNPC) or isinstance(x, ControlledNPC), world.mNPC)
        #_antagonist = choice(antagonists)
        #if _antagonist is None:
        _antagonist = choice((BadNPC, OverpoweredNPC, ControlledNPC, WereNPC))()
        _antagonist.name = world.antagonist
        world.antagonist = _antagonist
        logger.debug('Generated antagonist ' + world.antagonist.name)

    #now let's take names from background gen and set them randomly to apropirate NPCS
    assign_random_name_from_list(GoodNPC, world.good_npc_names)
    assign_random_name_from_list((BadNPC, ControlledNPC, OverpoweredNPC, WereNPC), world.bad_npc_names)
    assign_random_name_from_list((WereNPC, BadNPC), world.demon_npc_names, demon=True)
    assign_random_name_from_list(DeityNPC, world.deity_npc_names)
    #all that left without names gets brand new name
    for npc in world.mNPC:
        if npc.name is None:
            name = util.gen_name(check_unique=world.npc_names)
            if debug_names:
                name += ' ' + str(npc.__class__)
            npc.name = name
    #now we handle WereNPC, so that each get his own proxy and target
    weres = filter(lambda x: isinstance(x, WereNPC), world.mNPC)
    wered_npc = {}
    for were in weres:
        while True:
            #first find target
            if util.onechancein(20): #mimic royalty
                if util.coinflip():
                    if wered_npc.has_key(world.king): continue
                    were.target = world.king
                    wered_npc[world.king] = were
                    logger.debug('King will be WereNPC  '+ were.name)
                else:
                    royalty = choice(world.royalties)
                    if wered_npc.has_key(royalty): continue
                    were.target = royalty
                    wered_npc[royalty] = were
                    logger.debug('%s %s will be WereNPC %s' % (royalty.type, royalty.name, were.name))
                break
            else:
                target = choice(world.mNPC)
                if isinstance(target, WereNPC): continue
                if wered_npc.has_key(target): continue
                were.target = target
                wered_npc[target] = were
                break
        #now we define proxy type
        if is_good_npc(were.target):
            proxy = choice((BadNPC, BadWizardNPC, OverpoweredNPC))
            were.proxy = proxy
        else:
            were.proxy = BetrayalNPC
    controlled_npcs = filter(lambda x: x.__class__== ControlledNPC, world.mNPC)
    bad_npc = filter(lambda x: x.__class__==BadNPC, world.mNPC)
    for controlled in controlled_npcs:
        #we need to define master of ControlledNPC
        controlled.master = choice(bad_npc)
        controlled.history.append('%s is controlled by %s' % (controlled.name, controlled.master.name))
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
    world.city_map = city_map
    need_to_place = world.mNPC[:]
    for j in range (1, CITIES_COUNT):
        city = world.City(util.gen_name('city', world.cities_names))
        city_map.append(city)
        city.city_map = city_map
    capital = choice(city_map)
    capital.set_king(world.king)
    world.capital = capital

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
                denizen.city = city_map[y]

    logger.debug('Done settling down')
    logger.debug('Distributing  %d artefacts amongst NPCs'% (len(world.artefacts)))
    aarts = world.artefacts[:]
    for npc in  world.mNPC: #generating artefacts
        if len(aarts) <= 0 : break
        if isinstance(npc, (ImmobileNPC, TraderNPC, DeityNPC)):continue
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
        suspicion_of_connection = combinations(filter(lambda x: not x.dead, city.denizens), 2)
        for pair in suspicion_of_connection:
            #if they're still not acquainted - make them friends or enemies
            a, b = pair
            if a.dead or b.dead: continue

            if not a.know(b) and util.onechancein(3):
                a.ack(b, city)
            elif a.know(b):
                a.meet(b, city)
        for denizen in city.denizens:
            denizen.free_action(city)
        for deity in city.deities:
            deity.free_action(city)
        if isinstance(world.king, KingNPC):
            world.king.free_action(city)
        if city.plague_src : #if there is a plague in the city
            if util.onechancein(15) and city==world.capital and len(world.royalties): 
                #infect royalty
                victim = choice(world.royalties)
                victim.plague = True
            elif util.onechancein(7) and len(city.denizens):
                victim = choice(city.denizens)
                victim.plague = True


    def move_to_city(city):
       random_denizen = choice(city.denizens)
       if random_denizen.dead: return
       city.denizens.remove(random_denizen)
       new_city = choice(city_map)
       new_city.denizens.append(random_denizen)
       if city != new_city:
           random_denizen.history.append('In year %d %s moved from city of %s to a %s' % (world.year, random_denizen,city.name,new_city.name))
           random_denizen.city = new_city

    while stopyear > 1:
        for city in city_map:
            make_relations(city)
            if util.onechancein(6) and stopyear > 3 and len(city.denizens) > 0: #we need to move one denizen to another city
                move_to_city(city)
        stopyear -= 1
        world.year += 1


    for npc in world.mNPC:
        print 'History for %s ============ %s' % (npc.name, str(npc.__class__))
        for message in npc.history:
            print '\t' + message

    print 'History for king %s and family' % (king.name)
    for message in king.history:
        print '\t' + message
    for royalty in chain(world.royalties, world.royalties_kidnapped) :
        print 'History for %s %s' % (royalty.type, royalty.name)
        for message in royalty.history:
            print '\t' + message

    if king != world.king and world.king:
        print 'History for last living king ' + world.king.name
        for message in world.king.history:
            print '\t' + message
    print 'DEITY INFO======'
    for npc in world.mNPC:
        if  not isinstance(npc, DeityNPC): continue
        print '%s has %d followers and %d enemies' % (npc.name, len(npc.folowers), len(npc.enemies))

    bands = filter(lambda x: isinstance(x, BadNPC) and x.master is None and len(x.minions) > 0, world.mNPC)
    print 'BANDS INFO======='
    for band in bands:
        print 'The band of %s consist of %d members ' % (band.name, count_band(band))
    #we do want a nice starting scenario
    ##starting_place = choice(('room', 'forest', 'city', 'cave', 'desert', 'pip'))
    #world.require_for_nextgen(starting_place, 'start')
    #now we are ready to set off.
    #shuffle(world.quest_givers)
    #first_quest_giver = world.quest_givers[0]
    #first_quest_giver.doit(world)
    #first_quest_giver = world.quest_givers[1]
    #first_quest_giver.doit(world)

    #let's see what quests we have: they're prioretized 0 - minor, 2 major
    available_quests = { 0 : [], 1: [], 2: [] }
    for npc in world.mNPC:
        for item in npc.inventory.stolen_items.keys():
            available_quests[1].append('%s want\'s you to find item %s' % (npc.name, item.unique_name))
        #for enemy in npc.enemies:
        #    available_quests[0].append('%s want\'s you to kill %s' %(npc.name, enemy.name))
    if isinstance(king, KingNPC):
        for item in npc.inventory.stolen_items.keys():
            available_quests[2].append('King %s want\'s you to find item %s' % (npc.name, item.unique_name))
        for enemy in npc.enemies:
            available_quests[1].append('King %s want\'s you to kill %s' %(npc.name, enemy.name))
    for quest in world.global_quests:
        available_quests[2].append('%s want\'s you to %s %s' % (quest.issuer.name, quest.verb, quest.what.name))
    print 'Available quests============='
    for quest_group in available_quests.items():
        print str(quest_group[0]) + ':'
        for quest in quest_group[1]:
            print quest
    print 'Potential quests==========='
    quest_cnt = len(available_quests[2]) / 2 ##2 quests count as 0.5 quest xD
    bad_wiz = filter(lambda x: isinstance(x, BadWizardNPC), world.capital.denizens)
    for wiz in bad_wiz:
        print 'Bad wizard %s lives in capital' % (wiz.name)
        if len(wiz.minions) >= 3:
            print 'Bad %s wizard raised a group of zombies' %(wiz.name)
        quest_cnt += 1
        if getattr(wiz, 'lich', False):
            print 'There is a lich %s' % wiz.name
    if world.king is None or not isinstance(world.king, KingNPC):
        print 'King was killed by someone'
        quest_cnt += 1
    dead_kings = filter(lambda x: isinstance(x, RoyaltyNPC), world.deaders)
    for dead_king in dead_kings:
        if dead_king.tomb :
            print 'The %s is burried in a tomb with all his treasures' % dead_king.type
            quest_cnt +=1
    if isinstance(world.king, KingNPC):
        if isinstance(world.king.councilor, BadNPC):
            print 'King\'s councilor %s is betrayer' % (world.king.councilor.name)
            quest_cnt +=1
        for knight in world.king.knights:
            if isinstance(knight, BadNPC):
                print 'King\'s knight %s is betrayer' % (knight.name)
                quest_cnt +=1
        if isinstance(world.king.court_magician, BadWizardNPC):
            print 'Court magician %s is bad wizard' %(world.king.court_magician.name)
            quest_cnt +=1

    for royalty in world.royalties:
        if royalty.plague:
            print 'Someone infected %s %s ' % (royalty.type, royalty.name)
            quest_cnt +=1
    crime_armies = filter(lambda x: count_band(x) > 6, bands)
    for armie in crime_armies:
        print 'There is criminal army of %d members' % (count_band(armie))
        quest_cnt +=1

    infected_cities = filter(lambda x: city.plague_src, city_map)
    quest_cnt += len(infected_cities) / 2
    for city in infected_cities:
        print 'There is a plague in city %s' % (city.name)

    def find_city(denizen):
        citis = filter(lambda x: denizen in x.denizens, city_map)
        if not len(citis):
            return None
        return citis[0]

    false_kings = filter(lambda x: isinstance(x, BadNPC) and x.false_king, world.mNPC)
    for false_king in false_kings:
        if false_king.dead: continue
        print 'There is a false king %s in city %s' % (false_king.name, find_city(false_king).name)
        quest_cnt +=1

    if quest_cnt >= 3:
        break
