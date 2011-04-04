import logging
import os
import random
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from thirdparty.libtcod import libtcodpy as libtcod
from __init__ import logger
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
# [*][ ][   4] good NPC, which will give you quest, reward you (and will participate at least at 2 quests?)
# [ ][ ][1 3 ] bad NPC, which will hold one of quest-items (or sub-quest) and will actualy run away (or even capture you) and reappear at the end quest
# [*][+][1 34] betrayal-type NPC, which will pretend to be good and send you to certain death. Soon you find the truth and follow him to in order to kill. Will meet him once again later
# [*][ ][1234] were-NPC (^_^). Appears as human (for example), later  (end of quest) turns out to be a demon or king or your relative or whatever. that type can follow any path above (good, bad, betray)
# [*][+][1234] deity-NPC. Appears as human but after the quest turn out to be deity and give you the main quest or give you directions for next step
# [*][ ][1 34] controlled-NPC. This can be either bad or betrayal-type (prefered). After defeating him will turn out to be controlled by some other MNPC
# [ ][+][1 3 ] overpowered-NPC. This seems to be overpowered. Will beat you to death or capture or banish or whatever the first time. Will stay alive the next time,but when you manage to beat him turns out to be just a minor puppet of some other might MNPC
# [ ][+][ 2  ] adventure-NPC. Just like you, but knows a bit more. Will eventualy meet with you several times, giving you pieces of information. This is not quest-target NPC, though he can be placed inside quests (quest-info) or during main-plot (main-plot info) or both (prefered)
#![ ][+][   4] thief-NPC. Will eventualy steal the quest item, running away. Following him you can find his master or even get to another realm
#![ ][ ][ 2  ] summoned-NPC (or resurected, or cured). Should be placed inside quests and will help you out later (variant of adventure-NPC).
# [ ][ ][ 2  ] immobile-NPC (trees, stones, statues etc). Sources of subquests of information. Can be then referend by end-game NPC as a "powerfull mage" or "fallen deity" or whatever. Possibly you return to them or summon them to you
#![ ][+][ 2  ] shadows-of-the-past-NPC. will eventualy appear as ghosts or shadows either trying to kill you (some past reference), or asking you to help, or telling you about quest-item or quest-mob or main-plot. Should be place-defined in later casess. Can be shadows of quest-targets
# [ ][ ][1 3 ] band-NPC. Just a random ones. will roam around with band, offering sub-quests. can be avoided - others can refer to them
# [ ][+][123 ] unique-NPCs. Predefined ones. Can be refered, fought or will provide info. no special cases.
# [ ][+][12  ] trader-NPCs. Will eventualy pop up and offer you to buy something. it can randomly be something useless, sub-quest item or something needed to reach secret places. If the player reject bying sub-quest item he than will have to buy it for a higher price or fight NPC. In that case NPC is actualy bad or betrayal-type NPC
# help-NPCs. Will eventualy help you out with tough bosses. Nothing more at all.
# mercenary-NPCs. While carrying quest-item to quest-giver you can be assaulted by mercenary(ies) hired to kill you to get quest-item.

#some of the listed NPCs are generate inside quests. First we should define those,
# who will be encountered throughtout the game (marked as +).
# Then we define quest_givers marked as *.
# Quest targets are marked as
# 1 for killable target (quest target itself), 2 for talk-only-target, 3 for guard-type (guard quest item), 4 break-down plot (change plot)
# ! denotes NPCs which are occasionaly generated during quest generation-only!
#Actualy we don't want classic quests. instead let's use the quest as some meating point for plot-oriented-NPC. i.e. if the player is sent
#to obtain amulet from and wafull demon not neccessarily he should get it. Instead he should be given some important information and be directed to the next quest


#######FIRST_PHASE: (all the NPC inhabiting the world instead of those, generated inside quests nly)
#first let's define our world's population: this will include
# all the NPC's of all types we have, except those which can be placed inside quesuts only
#let's roll for number of NPC.  NOTE that we will also add types denoted by ! later.
mNPC_count = util.roll(*MNPC_ROLL)
#now let's roll for number of quest-givers. we do want them to exist
min_quest_fivers = util.roll(*QUEST_GIVER_ROLL)
#now let's roll for immobile NPCs. we don't want many of them. let em be 0-3 at 50% chance for now
immobile_npc = 0
if util.coinflip():
    to_roll = util.roll(*IMMOBILE_NPC_ROLL)
    for i in range(0, to_roll):
        immobile_npc += util.coinflip()
unique_npc = util.roll(*UNIQUES_ROLL)
traders_npc = util.roll(*TRADERS_ROLL)
logger.debug("Rolled for %d main NPCs (%d NPC able to issue quests), %d immobile NPCs, %d uniques, %d traders)", mNPC_count, min_quest_fivers, immobile_npc, unique_npc, traders_npc)
logger.debug("Total of %d NPCs (%d with traders)", mNPC_count + immobile_npc + unique_npc, mNPC_count + immobile_npc + unique_npc + traders_npc)
#now toss

#generate_plot()

class QuestNPC(object):
    #denotes if this NPC-type can be generate at first phase
    non_worldgen = False
    __metaclass__ = util.AutoAdd
    mNPC = []
    __meta_dict__ = { 'generated_at_1_phase' : mNPC }
    def __init__(self):
        pass

class GoodNPC(QuestNPC):
    pass

class BadNPC(QuestNPC):
    pass

class BetrayalNPC(BadNPC):
    pass

class WereNPC(BadNPC):
    pass

class DeityNPC(QuestNPC):
    pass

class ControlledNPC(BetrayalNPC):
    pass

class OverpoweredNPC(ControlledNPC):
    pass

class AdventureNPC(GoodNPC):
    pass

class ImmobileNPC(GoodNPC):
    pass

class BandNPC(BadNPC):
    pass

class UniqueNPC(BadNPC):
    pass

class TraderNPC(GoodNPC):
    pass

class ThiefNPC(BetrayalNPC):
    generated_at_1_phase = True

class SummonedNPC(GoodNPC):
    generated_at_1_phase = True

class  ShadowOfThePastNPC(QuestNPC):
    generated_at_1_phase = True

shuffled_npcs = QuestNPC.mNPC[:]
