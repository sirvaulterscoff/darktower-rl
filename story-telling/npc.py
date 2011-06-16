import os
from random import random, randint, choice
import string
import sys
import world
from itertools import chain
from quests import *

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
import critters
import util
import items
import dungeon_generators

logger = util.create_logger('npc')
MAX_HD_DIFF = 4
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
class QuestTarget(object):
    def init(self, world, issuer):
        pass
    def finish(self, npc, world):
        """invoked when quest is finished"""
        pass

class KillDudeTarget(QuestTarget):
    def _gen_new_killdude(self, world):
        #generate new NPC here
        dude = util.random_from_list_weighted(killable_dudes)()
        dude.name = util.gen_name(check_unique=world.npc_names)
        world.mNPC.append(dude)
        logger.debug('Generated new kill-dude ' + dude.name + ' ' + str(dude.__class__))
        return dude

    def init(self, world, issuer):
        super(KillDudeTarget, self).init(world, issuer)
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
        #item can lay down
        if self.target_item.standalone:
            #if it's just lay somewhere around - it can be a house, a dungeo, forest etc.
            #we tell the world that we need exact feature for next map_gen
            self.where = world.require_for_next_mapgen(self.target_item.where_type)
            self.what += ' from ' + self.where.name
        #if self.target_item.owned:

    def finish(self, npc, world):
        npc.target_achieved(self)

class GetInfoTarget(QuestTarget):
    def init(self, world):
        #here we ask PC to get some info from:
        # 1. some static source (book in library, talking statue, )
        pass
class VisitPlaceTarget(QuestTarget):
    def init(self, world, issuer):
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
        self.invincible = False
        self.inventory = Inventory()

    def has_items(self):
        return len(self.inventory.items) > 0

    def became_owner_of(self, item):
        self.inventory.items.append(item)
        self.history.append('In year %d %s became owner of %s ' % (world.year, self.name, item.unique_name))
        try:
            del self.inventory.stolen_items[item]
        except KeyError:
            pass

    def know(self, other):
        for contact in chain(self.friends, self.enemies, self.contact):
            if contact.name == other.name:
                return True
        return False
    def has_enemies(self):
        return len(self.enemies)> 0

    def friend_with(self, other):
        self.friends.append(other)
        self.history.append('In year %d %s made friends with %s' % (world.year, self.name, other.name))

    def conflict_with(self, other):
        self.enemies.append(other)
        #todo add some logic here. like b stole from a some artefact etc (ie generate artefacts
        #and owners during worldgen)
        self.history.append('In year %d %s became enemy of %s' % (world.year, self.name, other.name))

    def steal_from(self, from_who, random=True, what=None):
        if random and from_who.has_items():
            what = from_who.inventory.items.pop()
        self.history.append('In year %d %s stole %s from %s' % (world.year, self.name, what.unique_name, from_who.name))
        self.became_owner_of(what)
        from_who.item_was_stolen(what, self)

    def item_was_stolen(self, what, who):
        """ Called when item was stolen from self """
        self.history.append('In year %d %s was stolen by %s' % (world.year, what.unique_name, self.name))
        self.inventory.stolen_items[what] = who


    def ack(self, other, city):
        """ This is invoked when people meet each other for the first time.
        There are couple of options there. Then can make friends, or enemies
        Concrete realization is up-to sibling class"""
        pass

    def meet(self, other, city):
        """ Invoked when to acquainted persons meet each other
        returns True if the action was taken"""
    def free_action(self, city):
        if self.dead:
            return
        if len(self.inventory.stolen_items) > 0: #if we have stolen items
            item = choice(self.inventory.stolen_items.items())
            res =  self.hire_killer(item[1], city)
            return res[0]

    def hire_killer(self, other, city):
        killer = choice(city.denizens)
        if not isinstance(killer, BadNPC): return False, None
        wat = self.inventory.stolen_items.items()[0]
        if killer == wat[1]: return False, None
        if killer != self:
            self.history.append('In year %d %s hired %s to get %s back from %s ' %
                    (world.year, self.name, killer.name, wat[0].unique_name, wat[1].name))
        if util.coinflip(): #if managed to get stolen back
            killer.retrieved_stolen_from(wat[1], wat[0], self)
            return True, killer
        return False, None

    def retrieved_stolen_from(self, whom, wat, issuer, stolen=True):
        """ retrieves stolen item from other person. Called from inside of
        hire_killer."""
        try:
            if whom:
                whom.inventory.items.remove(wat)
                if stolen:
                    whom.history.append('In year %d %s was stolen from %s' %
                            (world.year, wat.unique_name, whom.name))
        except ValueError: pass
        issuer.became_owner_of(wat)

    def kill(self, other, custom_message_killer = None, cutom_message_vistim = None):
        if other.invincible:
            self.history.append('In year %d %s tried to assassinate %s but failed' % (world.year, self.name, other.name))
            other.conflict_with(self)
            return False
        if not other.die(self):
            return False
        for friend in other.friends:
            friend.conflict_with(self)
        if isinstance(other, BadNPC):
            if other.master is not None:
                try:
                    other.master.minions.remove(other)
                except ValueError: pass
            for minion in  other.minions:
                minion.master = None
        friend = ''
        if other.friends.__contains__(self):
            friend = 'a friend '
            other.history.append('In year %d %s was betrayed by his friend %s' % (world.year, other.name, self.name))
        enemy = ''
        if other == world.king:
            self.history.append('In year %d %s killed %s and became ruler of the realm' %
                    (world.year, self.name, other.name))
            world.king = self
        if self.enemies.__contains__(other):
            enemy = ' his old enemy'
        if cutom_message_vistim:
            other.history.append(cutom_message_vistim)
        else:
            other.history.append('In year %d %s was killed by %s%s' % (world.year, other.name, friend, self.name))
        if custom_message_killer:
            self.history.append(custom_message_killer)
        else:
            self.history.append('In year %d %s killed %s%s' % (world.year, self.name, other.name, enemy))
        if other.has_items():
            for item in other.inventory.items:
                if item.randart:
                    self.became_owner_of(item)
        other.inventory.items = []
        if isinstance(other, BadNPC) and len(other.hostages):
            for hostage in other.hostages:
                quests = filter_by_target(world.global_quests, ResqueQuest, hostage)
                if quests:
                    for quest in quests:
                        quest.fulfil(self, chance=1)
        return True

    def die(self, killer):
        """invoked whenever NPC is killed"""
        self.dead = True
        self.killer = killer
        return True

    def take_quest(self, qfilter=None):
        if len(world.global_quests) > 0:
            #let's part on a quest. maybe we got upgraded to knights 8)
            quests = world.global_quests
            if qfilter:
                quests = filter(lambda x: isinstance(x, qfilter), quests)
            quest = choice(quests)
            quest.fulfil(self)


    def __str__(self):
        return self.name

    @classmethod
    def register(cls, what, main_npc = True, quest_giver = False):
        if main_npc:
            QuestNPC.mNPC.append(what)
        if quest_giver:
            QuestNPC.quest_giver_NPC.append(what)

    quest_targets = [KillDudeTarget, BringItemTarget, VisitPlaceTarget]
    #quest_targets = [VisitPlaceTarget]
    def doit(self, world):
        logger.debug('Starting action on ' + str(self.__class__))
        #choose qu
        # est type (a - bring item, b- kill sum1, c - vistin sum1
        target = choice(self.quest_targets)()
        target.init(world, self)
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
    def ack(self, other, city):
        super(GoodNPC, self).ack(other, city)
        #good NPC will always try to make friends if he can
        if is_good_npc(other):
            self.friend_with(other)
            other.friend_with(self)
        elif isinstance(other, BadNPC):
            self.conflict_with(other)
            other.conflict_with(self)

    def meet(self, other, city):
        super(GoodNPC, self).meet(other, city)

    def item_was_stolen(self, what, who):
        super(GoodNPC, self).item_was_stolen(what, who)
        if util.onechancein(3):
            world.global_quests.append(RetrieveQuest(self, what, None))
            self.history.append('In year %d %s setted up bounty for anyone who can find %s' %
                    (world.year, self.name, what.unique_name))

    def free_action(self, city):
        if self.dead: return
        for what in self.inventory.stolen_items.items():
            wat = what[0]
            who = what[1]
            if len(filter_by_target(world.global_quests, RetrieveQuest, wat)) == 0:
                world.global_quests.append(RetrieveQuest(self, wat, who))
                self.history.append('In year %d %s setted up bounty for anyone who can find %s' %
                        (world.year, self.name, wat.unique_name))



#Here follows GoodNPC branches - that just bring some flavour
class RoyaltyNPC(GoodNPC):
    common = 1
    def __init__(self, type):
        super(RoyaltyNPC, self).__init__()
        self.invincible = False
        self.kidnapped = False
        self.type = type

    def rescued_by(self, who):
        world.royalties_kidnapped[self].hostage_rescued(self, who)
        world.royalties_kidnapped.pop(self)
        world.royalties.append(self)
        self.history.append('In year %d %s %s was rescued by by %s' %
                (world.year, self.type, self.name, who.name))

class KingNPC(RoyaltyNPC):
    common = 1
    def __init__(self):
        super(KingNPC, self).__init__("king")
        self.guards = []
        self.invincible = True
        self.councilor = None
        self.court_magician = None
        self.knights = {}

    def free_action(self, city):
        #react on kidpan, or councilor kills
        if util.onechancein(6):
            self._promote_denizens(city)
        self._hire_killers(city)

    def _promote_denizens(self, city=None, councilor=None, magician=None):
        if city and len(city.denizens) < 1: return
        if self.councilor is None:
            if councilor is None:
                councilor = choice(city.denizens)
            if is_good_npc(councilor):
                if not isinstance(councilor, AdventureNPC) and not self.enemies.__contains__(councilor):
                   self.councilor = councilor
                   councilor.history.append('In year %d %s became a councilor at the court of %s' %
                           (world.year, councilor.name, self.name))
                   self.history.append('In year %d %s promoted %s to the court councilor' %
                           (world.year, self.name, councilor.name))
                   return
        if self.court_magician is None:
            if city is None and magician is None: return
            cand = choice(city.denizens)
            if self.enemies.__contains__(cand): return
            if isinstance(cand, (WizardNPC, BadWizardNPC)):
                self.court_magician = cand
                cand.history.append('In year %d %s became magician at the court of %s' %
                        (world.year, cand.name, self.name))
                self.history.append('In year %d %s promoted %s to the court magician' %
                       (world.year, self.name, cand.name))

    def _hire_killers(self, city):
        if len(world.royalties_kidnapped) > 0:
            for royalty in world.royalties_kidnapped:
                if len(filter_by_target(world.global_quests, ResqueQuest, royalty)) == 0:
                    world.global_quests.append(ResqueQuest(royalty, self))
                    self.history.append('In year %d king %s placed bounty for rescuing %s %s' %
                            (world.year, self.name, royalty.type, royalty.name))


    def award_for_quest(self, hero, quest):
        if isinstance(world.king, KingNPC): #if we're still ruled by true king
            if isinstance(quest, ResqueQuest):
                self.history.append('In year %d %s fulfiled the quest to rescue %s %s' %
                        (world.year, hero.name, quest.who.type, quest.who.name))
            if util.coinflip():
                if not self.knights.has_key(hero):
                    hero.history.append('In year %d %s was promoted to knights by king %s' %
                            (world.year, hero.name, self.name))
                    self.history.append('In year %d king %s promoted %s to knights' %
                            (world.year, self.name, hero.name))
                    self.knights[hero] = True
            else:
                self._promote_denizens(city=None, councilor=hero) #try to promote hero to councilor


class WizardNPC(GoodNPC):
    """A wandering wizard that will open a school in town at some point"""
    common = 1
    def __init__(self):
        super(WizardNPC, self).__init__()
        self.invincible = True

    def meet(self, whom, city):
        if self.enemies.__contains__(whom) and util.onechancein(4):
            msg = 'In year %d %s was burnt by %s' % (world.year, whom.name, self.name)
            self.kill(whom, cutom_message_vistim=msg)

class BadNPC(QuestNPC):
    common = 7
    def __init__(self):
        super(BadNPC, self).__init__()
        """since this is bad npc -it may have relations with other bad guys """
        self.minions = []
        self.master = None
        self.hostages = []

    def ack(self, other, city):
        #super(BadNPC, self).ack(other, city)
        self.contact.append(other)

    def meet(self, other, city):
        if other == self: return
        #super(BadNPC, self).meet(other, city)
        if not self.know(other):
            self.contact.append(other)
            return False
        if util.onechancein(5) and other.has_items():
            result = self.steal_from(other, True)
            other.conflict_with(self)
            return result
        if isinstance(other, GoodNPC) :
            if util.onechancein(8):
                if self.kill(other):
                    city.was_killed(other)
        else:
            a = self
            if a == other: return
            if util.onechancein(6): #make a master of b
                if other.master is not None:
                    if other.master != a and a.master != other: #if b already had master, make a enemy of b.master
                        a.history.append('In year %d %s tried to overtake the control over %s, but failed' % (world.year, a.name, other.name))
                        other.master.conflict_with(a)
                else:
                    if a.master == other: #if we overtook controll
                        a.master = None
                        try:
                            other.minions.remove(a)
                        except ValueError: pass
                    try:
                        other.master.minions.remove(other)
                    except Exception : pass
                    a.minions.append(other)
                    other.master = a
                    a.history.append('In year %d %s became boss over %s' %(world.year, a.name, other.name))

    def free_action(self, city):
        super(BadNPC, self).free_action(city)
        band_size = count_band(self)
        if band_size >= 4 and band_leader(self) == self: #band is big enough to capture the king
            if world.king is not None and world.king != self:
                if util.onechancein(5):
                    world.king.dead = True
                    world.king.history.append('In year %d king %s was killed by %s' %
                            (world.year, world.king.name, self.name))
                    king_items = filter(lambda x: x.randart, world.king.inventory.items)
                    map(lambda x: self.became_owner_of(x), king_items)
                    if len(world.royalties):
                        map(lambda x: x.conflict_with(self), world.royalties)
                    if util.coinflip():#not neccessarily we take after the king
                        self.history.append('In year %d %s killed the king %s and became the ruler of realm' %
                                (world.year, self.name, world.king.name))
                        world.king = self
                    else:
                        self.history.append('In year %d %s killed the king %s' %
                                (world.year, self.name, world.king.name))
                        world.king = None
            if world.king and isinstance(world.king, KingNPC) and util.onechancein(10): #do not kidnap, if the king was already assasinated
                self.kidnap_royalty()

    def kidnap_royalty(self, type=None):
        victims = world.royalties
        if type:
            victims = filter(lambda x: x.type == type, victims)
        if len(victims) <= 0: return
        kidnap = choice(victims)
        self.history.append('In year %d %s kidnapped %s %s' %
                (world.year, self.name, kidnap.type, kidnap.name))
        kidnap.history.append('In year %d %s %s was kidnapped by %s' %
                (world.year, kidnap.type, kidnap.name, self.name))
        self.hostages.append(kidnap)
        world.royalties.remove(kidnap)
        world.royalties_kidnapped[kidnap] = self

    def hostage_rescued(self, hostage, rescuer):
        self.hostages.remove(hostage)
        if util.onechancein(4) and not self.dead: #let's be gentelmans and die once we have hostages freed
            rescuer.kill(self)
            for hostage in self.hostages:
                quest = filter_by_target(world.global_quests, ResqueQuest, hostage)
                if quest:
                    quest.fulfil(rescuer,chance=1)


    def hire_killer(self, other, city):
        result, killer = super(BadNPC, self).hire_killer(other, city)
        if result and util.coinflip():
            if killer.kill(other):
                city.was_killed(other)
        return result, killer


class BadWizardNPC(BadNPC):
    common = 1
    def __init__(self):
        super(BadWizardNPC, self).__init__()
        self.visited_cities = {}
        self.stop_moving = False

    def free_action(self, city):
        if self.dead: return
        if city == world.capital and util.onechancein(3) and len(world.royalties) > 0:
            self.kidnap_royalty("princess")
            self.stop_moving = True
        elif city != world.capital and not self.stop_moving:
            self.visited_cities[city] = True
            next_city = city
            if len(self.visited_cities) == len(city.city_map): #nowhere to move
                return
            while self.visited_cities.has_key(next_city):
                next_city = choice(city.city_map)
            city.denizens.remove(self)
            next_city.denizens.append(self)
            self.history.append('In year %d %s moved from city of %s to a %s' %
                    (world.year, self.name,city.name,next_city.name))

    def hostage_rescued(self, hostage, hero):
        #super(BadWizardNPC, self).hostage_rescued(hostage, hero)
        if util.onechancein(3):
            hero.kill(self)

    def meet(self, who, city):
        pass #do nothing
    def ack(self, other, city):
        pass

class BetrayalNPC(BadNPC):
    common = 2
    def meet(self, other, city):
        if self.dead: return
        if self.friends.__contains__(other):
            if isinstance(other, GoodNPC): #time to betray friends
                if self.kill(other):
                    city.was_killed(other)


    def retrieved_stolen_from(self, whom, wat, issuer):
        if util.coinflip():#will leave stolen item for itself
            try:
                whom.inventory.items.remove(wat)
                whom.history.append('In year %d %s was stolen from %s' %
                        (world.year, wat.unique_name, whom.name))
            except ValueError: pass
            issuer.history.append('In year %d %s was arrogated by %s' %
                    (world.year, wat.unique_name, self.name))
            self.became_owner_of(wat)
            self.history.append('In year %d betrayed %s and took %s for himself' %
                    (world.year, issuer.name, wat.unique_name))
            issuer.conflict_with(self)
        else:
            super(BadNPC, self).retrieved_stolen_from(whom, wat, issuer)

    def free_action(self, city):
        if self.dead: return
        if isinstance(world.king, KingNPC):
                #if there are some quests from king - we can take them on
                #complete and become councilor to do our filthy deeds
            quests_from_king = filter_by_issuer(world.global_quests, world.king)
            if len(quests_from_king):
                choice(quests_from_king).fulfil(self,chance=6)
        if len(self.hostages) and util.onechancein(4):
            quests = filter_by_target(world.global_quests, ResqueQuest, self.hostages[0])
            if len(quests):
                choice(quests).fulfil(self, 5)
        if isinstance(world.king, KingNPC): #if we live under good-old king
            king = world.king
            if self == king.councilor or king.knights.has_key(self):
                if util.onechancein(15):
                    self.history.append('In year %d %s betrayed his king' %
                            (world.year, self.name))
                    self.kidnap_royalty()
                    king.conflict_with(self)
                    king.councilor = None
                    king.knights.pop(self, None)
                    return
                if util.onechancein(22):
                    self.history.append('In year %d %s betrayed his king and killed him' %
                            (world.year, self.name))
                    self.kill(king)


class WereNPC(BetrayalNPC):
    common = 1
    def __init__(self):
        super(WereNPC,self).__init__()
        #werenpc mimics behaviour of proxy-type
        self.proxy = None
        #but actualy target is behind hist actions.
        #for exmple if target is king and proxy is BadNPC, WereNPC
        #will behave like bad NPC until he's revealed
        self.target = None
        self.revealed = False
        self.iproxy = None

    def ack(self, whom, city):
        self._init()
        if not self.revealed:
            self.iproxy.ack(whom, city)
        else:
            self.target.ack(whom, city)

    def meet(self, whom, city):
        self._init()
        if not self.revealed:
            self.iproxy.ack(whom, city)
        else:
            self.target.ack(whom, city)

    def die(self, killer):
        self.revealed = True
        self.history.append('In year %d %s was assaulted by %s and turned out to be %s' %
                (world.year, self.name, killer.name, self.target.name))

    def retrieved_stolen_from(self, whom, wat, issuer):
        self.revealed = True
        self.history.append('In year %d %s revealed that %s is %s' %
                (world.year, whom.name, self.name, self.target.name))
        super(WereNPC, self).retrieved_stolen_from(whom, wat, issuer)

    def free_action(self, city):
        if self.dead: return
        if world.king is None: #take his place
            self.proxy = KingNPC
            self.iproxy = None
            self.history.append('In year %d %s came to king\'s palace claiming to be a king' %
                    (world.year, self.name))

    def _init(self):
        if self.iproxy is None:
            self.iproxy = self.proxy()
            self.iproxy.name = self.name
            self.iproxy.friends = self.friends
            self.iproxy.enemies = self.enemies
            self.iproxy.history = self.history
            self.iproxy.hostages = self.hostages

class DeityNPC(QuestNPC):
    common = 2

    def __init__(self):
        super(DeityNPC, self).__init__()
        self.folowers = []
        self.enemies = []
    pass

class ControlledNPC(BadNPC):
    common = 1
    pass

class OverpoweredNPC(ControlledNPC):
    common = 1
    def __init__(self):
        super(OverpoweredNPC, self).__init__()
        self.killer = None

    def die(self, killer):
        if not util.onechancein(3): #not die at all
            self.killer = killer
            self.history.append('In year %d %s managed to cheat death' % (world.year, self.name))
            self.dead = False
            return False
        else:
            return super(OverpoweredNPC, self).die(killer)

    def meet(self, who, city):
        if self.killer == who:
            msg = 'In year %d %s got his revenge on %s' % (world.year, self.name, who.name)
            self.kill(who, custom_message_killer=msg)

    def free_action(self, city):
        if self.dead: return
        if city == world.capital and world.king is None:
            if util.onechancein(3):
                world.king = self
                self.history.append('In year %d %s proclaimed himself a king ' %
                        (world.year, self.name))
                #todo hire adventurer to kill impersonator

class AdventureNPC(GoodNPC):
    common = 6

    def free_action(self, city):
        self.take_quest()

class ImmobileNPC(QuestNPC):
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
class Oddyssy(UniqueNPC):
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
QuestNPC.register(WizardNPC, True, True)
QuestNPC.register(KingNPC, False, True)
QuestNPC.register(BadWizardNPC, True, True)


def is_good_npc(npc):
    if isinstance(npc, WereNPC):
        return isinstance(npc.proxy, (GoodNPC, BetrayalNPC))
    return isinstance(npc, (GoodNPC, BetrayalNPC))
def get_npcs_of_type(type, npcs):
    return filter(lambda x: isinstance(x, type), npcs)

killable_dudes = (
    BadNPC, BetrayalNPC, WereNPC, DeityNPC, ControlledNPC, OverpoweredNPC, BandNPC, UniqueNPC, TraderNPC)
def get_kill_dudes(npcs):
    return get_npcs_of_type(killable_dudes, npcs)

def count_band(npc, visited=None):
    """ Count's number of memebers in a band """
    cnt = 0
    if visited is not None and visited.__contains__(npc): return 0
    if visited is None:
        visited = []
    visited.append(npc)
    cnt += len(npc.minions)
    for minion in npc.minions:
        if len(minion.minions) > 0:
            cnt += count_band(minion, visited)
    return cnt

def band_leader(npc):
    iter_cnt = 10
    print 'npc ' + str(npc)
    print 'npc.master is' + str(npc.master)
    master = npc
    while master.master is not None:
        print 'master.master ' + str(master.master)
        master = master.master
        iter_cnt -= 1
        if iter_cnt <= 0 :
            print 'master history ' + master.name
            for message in master.history:
                print '\t' + message
            print 'master.master history ' + master.master.name
            for message in master.master.history:
                print '\t' + message
    return master

def is_in_band(npc, band, visited = None):
    if visited is not None and visited.__contains__(npc): return False
    if visited is None:
        visited = []
    visited.append(npc)
    if band.master == npc or band == npc:
        return True
    for member in band.minions:
        if member == npc:
            return True
        if is_in_band(npc, member, visited):
            return True
    if band.master:
        return is_in_band(npc, band.master, visited)
