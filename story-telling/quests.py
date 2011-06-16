import sys
import os
import world
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
import util

class ResqueQuest(object):
    """Quest to resque someone"""
    def __init__(self, who, issuer):
        super(ResqueQuest, self).__init__()
        self.who, self.issuer = who, issuer

    def fulfil(self, hero, chance=15):
        if util.onechancein(chance): #yeah, rescuing princesses is that simple
            world.global_quests.remove(self)
            hero.history.append('In year %d %s rescued_by %s' %
                    (world.year, hero.name, self.who.name))
            self.who.rescued_by(hero)
            self.issuer.award_for_quest(hero, self)


def filter_by_target(collection, type, who):
    filtered = filter(lambda x: isinstance(x, type), collection)
    return filter(lambda x: x.who == who, filtered)
