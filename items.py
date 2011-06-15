import gl
import util
from random import randrange, choice, shuffle
from acquire import acquire

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
        self.randart = False
        self.unique_name = None
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


W_BLADE = 1
W_SHORT_BLADE = 2
W_SCOURGE = 3
W_AXE = 4
W_LARGE_AXE = 5
W_POLEARM = 6
W_STAFF = 7
W_FLAIL = 8
W_KATANA = 9
W_BOW = 10
W_LONGBOW = 11
W_XBOW = 12
multilevel_features = ["rF", "rC"]
innate_features = ["rPois", "rElec"]

class Weapon(Item):
    def __init__(self):
        self.brand = None
        self.resists = []
        self.enchantment = [0, 0]

    def debug_print(self):
        br = ''
        if self.brand is not None:
            br = 'of %s' % (self.brand)

        art = ''
        if self.randart:
            art = 'artefact '
        nm = self.name
        if self.unique_name is not None:
            nm += ' ' + self.unique_name
        str = '%s%s +%d,+%d %s {%s} ' % (art, nm, self.enchantment[0], self.enchantment[1], br, ",".join(self.resists))
        print str

class Blade(Weapon):
    name = "blade"
    base_damage = 10
    base_delay = 10
    min_delay = 6
    max_enchantment = (7, 7)
    skill = "blade"
    base_cost = 200
class ShortBlade(Weapon):
    name = "short blade"
    base_damage = 4
    base_delay = 7
    min_delay = 4
    max_enchantment = (11, 11)
    skill = "blade"
    base_cost = 100
class Katana(Weapon):
    name = "katana"
    base_damage = 12
    base_delay = 9
    min_delay = 4
    max_enchantment = (11, 11)
    skill = "blade"
    base_cost = 500

weapons = [Blade, ShortBlade, Katana]

class Armor(Item):
    def __init__(self):
        super(Armor, self).__init__()
        self.resist = None
        self.resists = []
        self.enchantment = 0

class Crown(Armor):
    name = "crown"
    base_ac = 1
    base_cost = 100
    max_enchantment = 2
armor = [Crown]

artefacts = util.parseDes('art', ArtefactDes)
quest_items = util.parseDes('quest', QuestItemDes)
key_items = util.parseDes('key', KeyItemDes)

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

def generate_artefacts(artefacts_count, check=None):
    """Generates as many artefacts as specified by artefacts_count argument."""
    result = []
    arts = artefacts[:]
    shuffle(arts)
    while artefacts_count > 0:
        artefacts_count -= 1
        if util.onechancein(3) and len(arts) > 0:
            result.append(arts.pop())
        else:
            result.append(acquire(unique=check, artefact=True))
    return result
