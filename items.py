import gl
import util
from random import randrange, choice

class Item(object):
    char = ' '
    unided_name = color = (255,255,255)
    name = 'Generic item'
    unided_name = 'Unidentified item'
    description_past = 'description for a hero from past days'
    description_present = 'modern description'
    description_future = 'futuristic description'
    #name for unidentified item
    base_price = 100
    common = 10
    #sets quest level for that item. If quest level is none, then item can't be used for quest-targets. otherwise it can be selected fro a quest-target
    quest_level = None
    def __init__(self):
        pass

class ArtefactDes(Item):
    pass
class QuestItemDes(Item):
    pass
class KeyItemDes(Item):
    pass


potion_names = {}
potion_colors = {}
class Potion(Item):
    quaff = True
    char = '!'
    unided_color = util.random_color(check_unique=potion_colors)

    def __init__(self):
        super(Potion, self).__init__()
        self.name = 'Potion'


    def quaff(self, player):
        pass

class HealingPotion(Potion):
    base_price = 100
    common = 5
    unided_name = util.gen_name('potion', check_unique=potion_names).capitalize() + ' potion'
    name = 'Healing potion'
    description_past = 'Brewed by some artful alchemist this potion heal minor wound of those who drink it.'
    description_present = 'Strange potion that seems to heal your wounds as soon as you quaff it'
    description_future = 'Unknow chemical substance that has regenerative effect when quaffed'

    def quaff(self, player):
        super(HealingPotion, self).quaff(player)
        player.hp = util.cap(player.hp + util.roll(2, 10, 1), player.base_hp)
        gl.message('You feel somewhat better')

class ManaPotion(Potion):
    base_price = 130
    common = 5
    unided_name = util.gen_name('potion', check_unique=potion_names).capitalize() + ' potion'
    name = 'Healing potion'
    description_past = 'Potion will restore depleted mana when quaffed'
    description_present = 'This potion grants temporaly boost to mental activity, which results in quick MP restoration'
    description_future = 'You have no idea about the effect of this liquid.'

    def quaff(self, player):
        super(HealingPotion, self).quaff(player)
        player.hp = util.cap(player.hp + util.roll(2, 10, 1), player.base_hp)
        gl.message('You feel somewhat better')


class Weapon(Item):
    pass

artefacts = util.parse_des('art', ArtefactDes)
quest_items = util.parse_des('quest', QuestItemDes)
key_items = util.parse_des('key', KeyItemDes)
#print artefacts
#print artefacts[0].__dict__
#print artefacts[1].unided_name

def random_key_item(check_unique=None):
    """ Finds random key item. Key items are those items,
    that are required to fullfill certain goals ingame"""
    return util.random_from_list_unique(key_items)

def random_quest_target(artefact=False, check_unique=None) :
    result = None
    if artefact:
	result = util.random_from_list_unique(artefacts, check_unique)
    else:
	result = util.random_from_list_unique(quest_items, check_unique)
    print 'generated ' + str(artefact) + ' ' + str(result) + str(result.name)
    return result

