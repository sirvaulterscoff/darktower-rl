import sys
import os
import world
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
import util

class ResqueQuest(object):
    verb = "rescue"
    """Quest to resque someone"""
    def __init__(self, who, issuer):
        super(ResqueQuest, self).__init__()
        self.who, self.issuer = who, issuer
        self.what = self.who

    def fulfil(self, hero, chance=15):
        if util.onechancein(chance): #yeah, rescuing princesses is that simple
            world.global_quests.remove(self)
            hero.history.append('In year %d %s rescued %s' %
                    (world.year, hero.name, self.who.name))
            self.who.rescued_by(hero)
            self.issuer.award_for_quest(hero, self)

class RetrieveQuest(object):
    verb = "retrieve"
    """Quest to retrieve certain item"""
    def __init__(self, who, what, thief):
        super(RetrieveQuest, self).__init__()
        self.issuer, self.what, self.thief = who, what, thief

    def fulfil(self, hero, chance=15):
        if util.onechancein(chance):
            thief = 'unknown man'
            if self.thief:
                thief = self.thief.name
            world.global_quests.remove(self)
            hero.history.append('In year %d %s retrieved %s from %s' %
                    (world.year, hero.name, self.what.unique_name, thief))
            hero.retrieved_stolen_from(self.thief, self.what, self.issuer, stolen=False)

class FindItemQuest(object):
    """ Quest to find lost item """
    verb = "find"
    def __init__(self, issuer, what):
        super(FindItemQuest, self).__init__()
        self.issuer, self.what = issuer, what

    def fulfil(self, hero, chance=15):
        if util.onechancein(chance):
            hero.retrieve_lost(self.issuer, self.what)
            world.global_quests.remove(self)

def filter_by_target(collection, type, what):
    filtered = filter(lambda x: isinstance(x, type), collection)
    return filter(lambda x: x.what == what, filtered)

def filter_by_issuer(collection, issuer):
    return filter(lambda x: x.issuer == issuer, collection)
