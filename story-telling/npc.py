import os
from random import random, randint, choice
import string
import sys
import world
from itertools import chain

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
import critters
import util
import items
import dungeon_generators

logger = util.create_logger('npc')
MAX_HD_DIFF = 4
class QuestTarget(object):
    def init(self, world):
        pass
    def finish(self, npc, world):
        """invoked when quest is finished"""
        pass
parsed_kd_des = None
parsed_vp_des = None

def current_city(world):
    if world.current_city is None:
        #create it then
        name = util.gen_name('city', world.cities_names)
        city = util.coinflip()
        if city:
            world.depart_place_rank = util.roll(1, 3, 3)
        else:
            world.depart_place_rank = util.roll(1, 3)
        world.current_city = world.depart_place = name
    return world.current_city

DEAD = 1
ESCAPED = 2
class KillDudeTarget(QuestTarget):
    def _gen_new_killdude(self, world):
        #generate new NPC here
        dude = util.random_from_list_weighted(killable_dudes)()
        dude.name = util.gen_name(check_unique=world.npc_names)
        world.mNPC.append(dude)
        logger.debug('Generated new kill-dude ' + dude.name + ' ' + str(dude.__class__))
        return dude

    def init(self, world):
        super(KillDudeTarget, self).init(world)
        #actualy we need some mobs for kill-dude-purpose-only.
        #kill-dude-npc at 1/4 rate. 3/4 is a plain kill 100 rats quest
        self.what = choice(('kill ', 'demolish ', 'free the world from ', 'assassinate '))
        self.description = ''
        if util.roll(1, 4) == 4:
            if util.coinflip():
                #lets kill one of already generated NPCs
                self.dude = choice(get_kill_dudes(world.mNPC))
                if self.dude is None:
                    self.dude = self._gen_new_killdude(world)
                logger.debug('Selected killdude ' + str(self.dude) + ' ' + str(self.dude.name))
                logger.debug('Selected quest-target-dude ' + self.dude.name +' ' + str(self.dude.__class__))
            else:
                self.dude = self._gen_new_killdude(world)
            self.what += self.dude.name
        #plain old - go kill 100500 bats quest
        else:
            self.band = []
            #todo here we should place lambda instead and calc hd later
            player_hd = 1
            target_hd = randint(player_hd, player_hd + MAX_HD_DIFF)
            logger.debug('Target HD for kill-dude is '+ str(target_hd))
            #if we rolled same HD just make a huge band
            if target_hd == player_hd:
                #max roll being 3d6 + 3
                band_count = util.roll(3, util.cap(player_hd, 6), 3)
                logger.debug('Generating ' + str(band_count) + ' killdudes of HD ' +str(target_hd) )
                self.dude = critters.random_for_player_hd(player_hd, exact=False, max_hd=player_hd + 1)
                logger.debug('We are going to ask player to kill ' + str(band_count) + ' ' + self.dude.name + 's')
                for x in xrange(0, band_count):
                    self.band.append(self.dude)
                self.what += choice(('pack of ', 'small group of ', 'band of ', 'few ', 'some ')) + self.dude.name + 's'
                self.description = self.generate_description('pack', world)
            else: #else we gen a band with a leader
                # gen dude. Note - only intelligent critters are alowed to form bands
                self.dude = critters.random_for_player_hd(target_hd, inverse=True, flags=critters.INTELLIGENT)
                self.band.append(self.dude)
                logger.debug('We\'re going to kill ' + self.dude.name + ' of HD ' + str(target_hd))
                #if target creature is intelligent we may optional give a name to it
                if util.coinflip():
                    flavour = 'name'
                    if self.dude.is_demon():
                        flavour = 'demon'
                    self.dude.unique_name = util.gen_name(flavour, check_unique = world.npc_names)
                self.description = self.generate_description('band_with_leader', world)
                #if maxed target_hd - it's one-target monster, else - it's a band
                if target_hd - MAX_HD_DIFF < player_hd:
                    #gen band
                    band_hd = target_hd - player_hd
                    #roll for 1dband_hd + 2 band
                    band_count = util.roll(2, band_hd, 2)
                    logger.debug('Dude generated with a band of ' + str(band_count))
                    for x in xrange(0, band_count):
                        critter = critters.random_for_player_hd(randint(player_hd, band_hd), exact=True, flags=critters.INTELLIGENT)
                        self.band.append(critter)

                    band_list = string.join(map(lambda x:x.name + ' HD: ' + str(x.base_hd), self.band), ',')
                    logger.debug('Band list is: ' + band_list)
                    if self.dude.unique_name is None:
                        band_members = set(map(lambda x: x.name + 's', self.band))
                        self.what += ' the band of ' + ', '.join(band_members)
                    else:
                        self.what += ' the band of ' + self.dude.unique_name + ' the ' + self.dude.name
                else: #no-band dude
                    logger.debug('Dude generated alone')
                    self.what += self.dude.name
                    self.description = self.generate_description('single_critter', world)
        print self.description
        print self.what

    def generate_description(self, which, world):
        """Generates a random description for kill-dude background"""
        global parsed_kd_des
        if parsed_kd_des is None:
            parsed_kd_des = util.parseDes('killdude_background', KillDudeBackground)[0]
        s = choice(parsed_kd_des.__dict__[which].strip().splitlines())
        substs = util.LambdaMap()
        #here we parse following options: $depart_village, $who (dude.name) and $name (dude.unique_name)
        substs['who'] = self.dude.name
        substs['name'] = self.dude.unique_name
        substs['current_city'] = lambda : current_city(world)
        substs['village_name'] = lambda : util.gen_name('city')

        res = string.Template(s).safe_substitute(substs)
        return res

    def finish(self, npc, world):
        self.outcome = ESCAPED
        #here we have npc killed (or maybe not)
        if self.outcome == DEAD:
            npc.target_is_dead(self) #we notify that target critter is dead
        elif self.outcome == ESCAPED:
            npc.target_escaped(self) #we notify that our target somehow escaped
        else:
            npc.target_is_alive(self) #PC decided not to kill target

class KillDudeBackground():
    pass

class BringItemTarget(QuestTarget):
    def init(self, world):
        #here we have following options:
        #bring general item (like potion or key)
        #bring artefact
        #bring overpowered item (actualy you wont be able to obtain it)
        #bring key item (you will give it to quest-issuer but will eventualy
        #need it later). Here we have an option of allowing a player to leave
        #this item. such items will be used in other parts of the game
        prob = util.roll(1, 75)
        if prob <= 50: #general item
            logger.debug('Using general item as quest target')
            self.target_item = items.random_quest_target(False, world.generated_quest_items)
        elif prob <= 65: #artefact
            logger.debug('Using artefact tem as quest target')
            self.target_item = items.random_quest_target(True, world.generated_quest_items)
        elif prob < 70: #dunno what here. maybe just remember that its
            logger.debug('Using artefact item as quest target')
            self.target_item = items.random_quest_target(True, world.generated_quest_items)
        else:
            logger.debug('Using key item as quest target')
            self.target_item = items.random_key_item(world.generated_quest_items)
        logger.debug('Generate item-quest-target: ' + str(self.target_item))
        self.what = choice(('obtain' , 'retrieve', 'bring', 'find')) + ' ' + self.target_item.name

    def finish(self, npc, world):
        npc.target_achieved(self)

class GetInfoTarget(QuestTarget):
    pass
class VisitPlaceTarget(QuestTarget):
    def init(self, world):
        self.what='wat'
        #here we have options:
        #1. visit predefined location (minimap in map) - ie temple, some house etc
        #2. visit another city
        #3. visit random location near starting city
        #4. some unreachable place - in that case you will get
        # teleported elsewhere or just return back with empty hands
        #5. visit a place in starting city. in that case we need something else in the end
        self.scenario = util.roll(1, 4)
        if self.scenario == 1:
            #predefined location (places of interest)
            self.place = dungeon_generators.StaticRoomGenerator(flavour='pip', type='maps').finish()
            #if you need to bring something from map
            print 'self.place.is' + str(self.place)
            if self.place.quest_type == 'obtain':
                self.what = ' bring ' + self.place.quest_item + ' from ' + self.place.name
            else:
                self.what = ' visit ' + self.place.name
        elif self.scenario == 2:
            #Visit a guild target
            self.guild = util.gen_name(flavour='guild')
            self.what = choice(('visit', 'find')) + ' guild ' + self.guild + ' and talk to it\'s leader'
            world.require_for_nextgen('guild', self.guild)
        elif self.scenario == 3:
            #Visit a place near city
            self.generate_scenario(world)
            self.visit_type = choice(('forest', 'ruins', 'cave', 'shipwreck'))
            self.description = self.generate_scenario(world)
            self.what = ' investigate strange event near ' + self.name
            print self.description
        elif self.scenario == 4:
            #visit another city (maybe we should sqaus it with previous case)
            self.name = util.gen_name('city', world.cities_names)
            world.require_for_nextgen('city', self.name)
            self.what = ' visit city ' + self.name

    def generate_scenario(self, world):
        global parsed_vp_des
        if not parsed_vp_des:
            parsed_vp_des = util.parseDes('sightseeing', util.Des)[0]

        self.category = choice(parsed_vp_des.__dict__.keys())
        s = choice(parsed_vp_des.__dict__[self.category].strip().splitlines())
        substs = util.LambdaMap()
        self.name = util.gen_name(flavour='city')
        substs['name'] = self.name
        substs['current_city'] = lambda : current_city(world)
        substs['village_name'] = lambda : util.gen_name('city', world.cities_names)
        if len(world.bad_npc_names) > 0:
            substs['bad_npc'] = choice(world.bad_npc_names)
        else:
            substs['bad_npc'] = util.gen_name()
        world.require_for_nextgen(self.category, self.name)
        res = string.Template(s).safe_substitute(substs)
        return res

    def finish(self, npc, world):
        npc.target_achieved(self)

###PART1 - quests
#the typical layout of the plot
# you get a random number of quests (say between 3 and 10). each quest consists of following part
# a) your aim in quest (obtain, kill, bring, find, steal, make, buy and so on)
# b) what (or whom) = depends on a) - amulet, ring, orb, treasure
# c) quest-giver
# d) quest-item (person) placement. It can lay somewhere alone, can be hold by powerfull mob, can be
#    guarded by band of mobs, can be hold by another NPC (sub-quest, or story-line-break)
# d.1) actual nature of quest item
#   -general item (no special abs)
#   -teleportator or whatever, which will teleport you
#   -some powerfull item which will allow you to enter some secret place late-game
#   -the soul of a demon, or statue of a powerfull mage or whatever
# e)quest-item-holder (or a person if quest is to kill someone). Anyway any quest item should
# make the possible the future advancement of plot. i.e. quest-holder can turn-out to be your
# -relative who will ask you to help him,
# -demon - who will offer his service in exchange for his life,
# -some powerfull wizard (you're not able to kill him and he'll live leaving a portal)
# -a piecefull mob which will instead ask you to kill quest-giver (which can be a demon)
# f) random NPC, which can lead you to quest item or tell something about it
# g) quest item environment - apropriate environment for an itme
# h) quest item location - apropriate room/cave or whatever for item located within g)

#anyway the first 1-2 quests should lead you to another realm (main realm)
#and the last quest should lead you to npc who can explain you the constant plot (main, not random plot)
#first quest is given you since the start of the game - so you need not to search for NPC
#an example:

#you was asked to bring to A a herbs (random item) from nearby forest (quest- item allows only forest location)
#upon entering the forest you met a man (random NPC, attached to quest) which told you
#that such herbs are actualy guarded by Minotaur (quest-item-holder) which can be found near the cave-entrance(quest_location)
#when you encountered minotaur he told you: he will give you quest item, if you help him to break the curse (kill wizrd, sub-quest)
#or this herbs are actualy - another random item guarded by random_creature, and quest giver send you to certain death (betrayal-break)
#upon completing subquest (kill wizard) you get herbs and return to quest_giver.
# quest-giver give you potion of heroism claiming it will make you invincible, but instead it make you teleport to random room with 100 teleports in it
#or (betrayal plot) you come back to quest-giver to kill him, but instead you find a portal he used to escape and step through the portal

###PART2 - key characters
#at the start of quest generation we will define key NPCs, who will follow you
#throughout the game. Main types of such main NPCs(MNPC):
# [*][+][   4] good NPC, which will give you quest, reward you (and will participate at least at 2 quests?)
# [ ][+][1 3 ] bad NPC, which will hold one of quest-items (or sub-quest) and will actualy run away (or even capture you) and reappear at the end quest
# [*][+][1 34] betrayal-type NPC, which will pretend to be good and send you to certain death. Soon you find the truth and follow him to in order to kill. Will meet him once again later
# [*][+][1234] were-NPC (^_^). Appears as human (for example), later  (end of quest) turns out to be a demon or king or your relative or whatever. that type can follow any path above (good, bad, betray)
# [*][+][1234] deity-NPC. Appears as human but after the quest turn out to be deity and give you the main quest or give you directions for next step. Can be actualy a master of some realm, where you get tepelorted occassionaly
# [*][+][1 34] controlled-NPC. This can be either bad or betrayal-type (prefered). After defeating him will turn out to be controlled by some other MNPC
# [ ][+][1 3 ] overpowered-NPC. This seems to be overpowered. Will beat you to death or capture or banish or whatever the first time. Will stay alive the next time,but when you manage to beat him turns out to be just a minor puppet of some other might MNPC
# [ ][+][ 2  ] adventure-NPC. Just like you, but knows a bit more. Will eventualy meet with you several times, giving you pieces of information. This is not quest-target NPC, though he can be placed inside quests (quest-info) or during main-plot (main-plot info) or both (prefered)
#![ ][ ][   4] thief-NPC. Will eventualy steal the quest item, running away. Following him you can find his master or even get to another realm
#![ ][ ][ 2  ] summoned-NPC (or resurected, or cured). Should be placed inside quests and will help you out later (variant of adventure-NPC).
# [ ][=][ 2  ] immobile-NPC (trees, stones, statues etc). Sources of subquests of information. Can be then referend by end-game NPC as a "powerfull mage" or "fallen deity" or whatever. Possibly you return to them or summon them to you
#![ ][ ][ 2  ] shadows-of-the-past-NPC. will eventualy appear as ghosts or shadows either trying to kill you (some past reference), or asking you to help, or telling you about quest-item or quest-mob or main-plot. Should be place-defined in later casess. Can be shadows of quest-targets
# [ ][=][1 3 ] band-NPC. Just a random ones. will roam around with band, offering sub-quests. can be avoided - others can refer to them
# [ ][=][123 ] unique-NPCs. Predefined ones. Can be refered, fought or will provide info. no special cases.
# [ ][=][12  ] trader-NPCs. Will eventualy pop up and offer you to buy something. it can randomly be something useless, sub-quest item or something needed to reach secret places. If the player reject bying sub-quest item he than will have to buy it for a higher price or fight NPC. In that case NPC is actualy bad or betrayal-type NPC
#![ ][ ][    ] help-NPCs. Will eventualy help you out with tough bosses. Nothing more at all.
#![ ][ ][    ] mercenary-NPCs. While carrying quest-item to quest-giver you can be assaulted by mercenary(ies) hired to kill you to get quest-item.

#some of the listed NPCs are generate inside quests. First we should define those,
# who will be encountered throughtout the game (marked as +).
# + - mainNPCs - i.e. persistent ones. generated once - at the start
# * Then we define quest_givers .
# = mark those that are generated despite of others (have their own roll to be generated guring mNPC generation)
# Quest targets are marked as
# 1 for killable target (quest target itself),
# 2 for talk-only-target,
# 3 for guard-type (guard quest item),
# 4 break-down plot (change plot)
# ! denotes NPCs which are occasionaly generated during quest generation-only!
#Actualy we don't want classic quests. instead let's use the quest as some meating point for plot-oriented-NPC. i.e. if the player is sent
#to obtain amulet from and wafull demon not neccessarily he should get it. Instead he should be given some important information and be directed to the next quest
#

class Inventory(object):
    """inventory for npc"""
    def __init__(self):
        self.items = []
        self.stolen_items = {}

generated_names = set()
class QuestNPC(object):
    mNPC = []
    quest_giver_NPC = []
    common = 2

    def __init__(self):
        self.name = None
        self.is_demon = False
        self.history = []
        self.friends = []
        self.enemies = []
        self.contact = []
        self.deity = None
        self.dead = False
        self.inventory = Inventory()

    def has_items(self):
        return len(self.inventory.items) > 0

    def became_owner_of(self, item):
        self.inventory.items.append(item)
        self.history.append('In year %d %s became owner of %s ' % (world.year, self.name, item.unique_name))

    def know(self, other):
        for contact in chain(self.friends, self.enemies, self.contact):
            if contact.name == other.name:
                return True
        return False
    def has_enemies(self):
        return len(self.enemies)> 0

    def friend_with(self, other):
        self.friends.append(other)
        other.friends.append(self)
        self.history.append('In year %d %s made friends with %s' % (world.year, self.name, other.name))

    def conflict_with(self, other):
        self.enemies.append(other)
        #todo add some logic here. like b stole from a some artefact etc (ie generate artefacts
        #and owners during worldgen)
        other.enemies.append(self)
        self.history.append('In year %d %s became enemy of %s' % (world.year, self.name, other.name))

    def steal_from(self, from_who, what):
        self.history.append('In year %d %s stole %s from %s' % (world.year, self.name, what.unique_name, from_who.name))
        from_who.history.append('In year %d %s was stolen by %s' % (world.year, what.unique_name, self.name))
        self.became_owner_of(what)
        from_who.inventory.stolen_items[what] = self

    def kill(self, other):
        other.dead = True
        for friend in other.friends:
            friend.conflict_with(self)
        if isinstance(other, BadNPC):
            if other.master is not None:
                other.master.minions.remove(other)
            for minion in  other.minions:
                minion.master = None
        friend = ''
        if other.friends.__contains__(self):
            friend = 'a friend '
        enemy = ''
        if self.enemies.__contains__(other):
            enemy = ' his old enemy'
        other.history.append('In year %d %s was killed by %s%s' % (world.year, other.name, friend, self.name))
        self.history.append('In year %d %s killed %s%s' % (world.year, self.name, other.name, enemy))
        if other.has_items():
            for item in other.inventory.items:
                if item.randart:
                    self.became_owner_of(item)
        other.inventory.items = []

    def __str__(self):
        return self.name

    @classmethod
    def register(cls, what, main_npc = True, quest_giver = False):
        if main_npc:
            QuestNPC.mNPC.append(what)
        if quest_giver:
            QuestNPC.quest_giver_NPC.append(what)

    quest_targets = [KillDudeTarget, BringItemTarget,BringItemTarget, VisitPlaceTarget]
    #quest_targets = [VisitPlaceTarget]
    def doit(self, world):
        logger.debug('Starting action on ' + str(self.__class__))
        #choose qu
        # est type (a - bring item, b- kill sum1, c - vistin sum1
        target = choice(self.quest_targets)()
        target.init(world)
        logger.debug('Target of quest is ' + str(target))
        print(self.name + ' asks you to ' + target.what)
        target.finish(self, world)

    def target_is_dead(self, target):
        print self.name + ' thanks you for killing ' + target.dude.name
    def target_escaped(self, target):
        print self.name + ' is upset by ' + target.dude.name + '\'s escape'
    def target_is_alive(self, target):
        print self.name + ' asks: "Why you let " + target.dude.name + " alive?"'
    def target_achieved(self, target):
        print self.name + ' thanks you for your service'


class GoodNPC(QuestNPC):
    common = 7

class BadNPC(QuestNPC):
    common = 7
    def __init__(self):
        super(BadNPC, self).__init__()
        """since this is bad npc -it may have relations with other bad guys """
        self.minions = []
        self.master = None
        pass

class BetrayalNPC(BadNPC):
    common = 2


class WereNPC(BetrayalNPC):
    common = 1
    pass

class DeityNPC(QuestNPC):
    common = 2

    def __init__(self):
        super(DeityNPC, self).__init__()
        self.folowers = []
        self.enemies = []
    pass

class ControlledNPC(BetrayalNPC):
    common = 1
    pass

class OverpoweredNPC(ControlledNPC):
    common = 1
    pass

class AdventureNPC(GoodNPC):
    common = 6
    pass

class ImmobileNPC(GoodNPC):
    pass

class BandNPC(BadNPC):
    common = 3
    pass

class UniqueNPC(BadNPC):
    id = None
    _uniques = {}

    @classmethod
    def register_self(cls, id, wat):
        UniqueNPC._uniques[id] = wat


random_artefact_here = '[place here random artefact]'
#static unique for now
class Oddyssy(UniqueNPC, AdventureNPC):
    id = 'Oddyssy'
    name = choice(('Odd Yssy', 'Oddyssy'))
    real_name = name
    description = 'A long journey in search of mythical relic ' + random_artefact_here + ' led him to a foreign land where this relic is hidden, according to rummors.'
    common = 10

UniqueNPC.register_self(Oddyssy.id, Oddyssy)


class TraderNPC(GoodNPC):
    pass

class ThiefNPC(BetrayalNPC):
    pass

class SummonedNPC(GoodNPC):
    pass

class  ShadowOfThePastNPC(QuestNPC):
    pass

QuestNPC.register(GoodNPC, True, True)
QuestNPC.register(BadNPC, True, False)
QuestNPC.register(BetrayalNPC, True, True)
QuestNPC.register(WereNPC, True, True)
QuestNPC.register(DeityNPC, True, True)
QuestNPC.register(ControlledNPC, True, True)
QuestNPC.register(OverpoweredNPC, True)
QuestNPC.register(AdventureNPC, True)


def get_npcs_of_type(type, npcs):
    return filter(lambda x: isinstance(x, type), npcs)

killable_dudes = (
    BadNPC, BetrayalNPC, WereNPC, DeityNPC, ControlledNPC, OverpoweredNPC, BandNPC, UniqueNPC, TraderNPC)
def get_kill_dudes(npcs):
    return get_npcs_of_type(killable_dudes, npcs)
