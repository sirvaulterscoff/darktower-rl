import math
import gl
import util
from thirdparty.libtcod import libtcodpy as libtcod
from collections import Iterable
from util import build_type
from maputils import find_feature
from collections import deque

WALKING = 1
FLYING = 1
UNDEAD = 1
COLD_BLOODED = 1
PASS_THRU_WALLS = 1
PASS_THRU_DOORS = 1
INTELLIGENT = 1
DEMON = 1
SMALL_SIZE = 1
LARGE_SIZE = 1

class ActionCost(object):
    attack = 10.0
    move = 10.0
    flee = 9.0
    pickup = 20.0
    stairsdown = 15.0
    wield = 5.0
    inven_action = 10.0

    def __init__(self, **args):
        self.set_params(args)

    def set_params(self, argv):
        for k, v in argv.items():
            setattr(self, k, v)

    def modify(self, by):
        self.attack *= by
        self.move *= by
        self.flee *= by
        self.pickup *= by
        self.stairsdown *= by
        self.wield *= by
        self.inven_action *= by


class BasicAI(object):
    pass
class ActiveAI(BasicAI):

    def __init__(self):
        super(ActiveAI, self).__init__()
        self.patroling = True

    def _nexttoplayer(self, crit, player, map):
        xyz = util.iterate_fov(crit.x, crit.y, 1, map.current.width, map.current.height)
        for xy in xyz:
            if xy == (player.x, player.y):
                return True
        return False

    def decide(self, crit, player, _map):
        if not crit.is_awake:
            return
        if self._nexttoplayer(crit, player, _map):
            if crit.can_melee(player):
                gl.scheduler.schedule(crit.action_cost.attack, lambda: crit.attack(player))
#                crit.attack(player)
            else:
                crit.find_shooting_point(player, _map)
            return
        #check if player in los
        if util.has_los(crit.x, crit.y, player.x, player.y, _map.current.fov_map0):
            #this will actualy check if this creature is in player's los, not vice-versa
            #todo add pathfinding here
            if crit.can_range(player):
                crit.attack_range(player)
            else:
                gl.scheduler.schedule(crit.action_cost.move, lambda : crit.move_towards(player.x, player.y))
        elif self.patroling:
            if not crit.path:
                points = []
                #finding something of interest
                altars = _map.current.find_feature(oftype='Altar', multiple=True)
                if altars:
                    map(lambda x: util.do_if_one_chance_in(3, lambda : points.append( (x[1], x[2]) ) ), altars)
                stairs = _map.current.find_feature(oftype='StairsDown', multiple=True)
                if stairs:
                    map(lambda x: util.do_if_one_chance_in(3, lambda : points.append( (x[1], x[2]) ) ), stairs)
                path = deque()
                path.append((crit.x, crit.y))
                prev_point = path[0]
                if len(points) > 0:
                    for point in points:
                        path.extend(util.create_path(_map.current.fov_map0, prev_point[0], prev_point[1], *point))
                        prev_point = point
                    crit.path = path

                    newxy = crit.path[0]
#                    crit.move_towards(*newxy)
                    gl.scheduler.schedule(crit.action_cost.move, lambda : crit.move_towards(*newxy))
                    crit.path.rotate(-1)
            else:
                newxy = crit.path[0]
                gl.scheduler.schedule(crit.action_cost.move, lambda : crit.move_towards(*newxy))
#                crit.move_towards(*newxy)
                crit.path.rotate(-1)

class Critter(object):
    name = 'crit'
    unique_name = None
    char = '@'
    color = (255, 255, 255)
    x = 0
    y = 0
    last_seen_at = None
    regen_rate = 1
    description_past = 'Generic critter from the past'
    description_present = 'Generic critter from present time'
    description_future = 'Generic critter from distant future'
    base_hd = 1
    base_hp = 1
    base_mp = 1
    speed = 1
    base_ac = 0
    base_dmg = [(1, 1)]
    dlvl = 1
    inven = []
    common = 10
    fov_range = 5
    ai = ActiveAI()
    hp = base_hp
    mp = base_mp
    flags = {WALKING}
    xp = 1
    hd = 0 #relative HD (to that of player)
    action_cost = ActionCost()
    path = None
    is_awake = True

    def __init__(self):
        self.map = None
        pass

    def adjust_hd(self, new_hd):
        """ adjust_hd(new_hd) => None
        Called to update current critter's HD. It is set to a new value + relative HD.
        Thus base_hd is completly ignored in that case.
        """
        #TODO implement HD rebasing
        self.base_hd = new_hd + self.hd
        pass

    def place(self, x, y, map):
        self.x, self.y = x, y
        self.map = map

    def move(self, dx, dy):
        newx, newy = self.x + dx, self.y + dy
        if self.map.has_critter_at((newx, newy)):
            return False
        player = self.map.player
        if player.x == newx and player.y == newy:
            assert 'This should not happen here'
            return True

        next_tile = self.map.tile_at(newx, newy)
        if next_tile.passable():
            self.map.critter_xy_cache.pop((self.x, self.y))
            self.x, self.y = newx, newy
            self.map.critter_xy_cache[(self.x, self.y)] = self
            return True
        return False

    def attack(self, whom):
        dmgs = []
        for attack in self.base_dmg:
            dmg = util.roll(*attack)
            #let's roll 1d20 + HD for now, assuming that monster
            # can hit player no lees than 30% of the time
            # (thus checking it to be > 14)
            #TODO add player's/monsters' evade to calculations
            if util.roll(1, 20, self.base_hd) >= 14:
                dmgs.append(dmg)
            else:
                #todo parametrize verb misses - as it's incorrect for player
                gl.message(self.name.capitalize() + ' misses ' + whom.name)
            whom.take_damage(self, dmgs, attack)
        return self.action_cost.attack


    def move_towards(self, target_x, target_y):
        dx = target_x - self.x
        dy = target_y - self.y
        distance = math.sqrt(dx ** 2 + dy ** 2)
        if not distance:
            return False

        dx = int(round(dx / distance))
        dy = int(round(dy / distance))
        return self.move(dx, dy)

    def see_player(self, player):
        see_range = self.fov_range
        #if it's intelligent one - let it follow source of light
        if check_flag(self, INTELLIGENT):
            see_range += player.fov_range / 2
#        if libtcod.map_is_in_fov(self.map.fov_map, self.x, self.y):
#            d = util.distance(self.x, self.y, player.x, player.y)
#            if d <= see_range:
#                return d
        return None

    def take_turn(self, player):
        if self.ai is None:
            if self.see_player(player):
                gl.scheduler.schedule(self.action_cost.move, lambda : self.move_towards(player.x, player.y))
        else:
            self.ai.decide(self, player, self.map)

    def take_damage(self, mob, dmgs, attack):
        """
        take_damage(source, [int], attack) => None
        This method inflicts damage to a creature of amount specified as dmgs list whic was dealt by mob
        """
        for dmg in dmgs:
            for i in range(0, self.base_ac + 1):
                if util.coinflip(): dmg -= 1
                if dmg <= 0: continue
            if dmg > 0 and self.hp > 0:
                gl.message(mob.name.capitalize() + ' hits ' + self.name + ' for ' + str(dmg) + ' damage.', 5)
                self.hp -= dmg
            elif self.hp > 0:
                gl.message (mob.name.capitalize() + ' fails to harm ' + self.name)
        if self.hp <= 0:
            self.die(mob)

    def die(self, killer):
        gl.message(self.name.capitalize() + ' dies')
        if isinstance(killer, Critter):
            killer.earn_exp(self)
        self.map.remove_critter(self)

    def earn_exp(self, src):
        #method written beforehand, when we will have alies or whatever
        #we're adjusting HD, taking in acount killed mob hd and dlvl
        #basicaly we make mob.hd / self.hd, same for dlv
        # then we multiply this values by 1/self.dlvl
        #so that more advanced mob lvl-up slower (at 1/27 rate for killing mob of their lvl+hd)
        hd_delta = src.base_hd / self.base_hd
        dlvl_delta = src.dlvl / self.dlvl
        self.adjust_hd(self.base_hd + (hd_delta + dlvl_delta - 1) * 1 / self.dlvl)

    def is_demon(self):
        return self.check_flag(DEMON)

    def is_intelligent(self):
        return self.check_flag(INTELLIGENT)

    def can_range(self, player):
        """ can_range(Player) => boolean
        Returns True if this creature can range-attack player (by means of bow/xbow or magic)
        """
        return False

    def attack_range(self, player):
        """ attack_range(Player) => boolean?
        """
        return False

    def can_melee(self, player):
        """ can_melee(Player) => boolean
        Returns True if this creature can melee player
        """
        return True

def check_flag(critter, flag):
    if isinstance(flag, Iterable):
        for flg in flag:
            if not flg in critter.flags:
                return False
        return True
    else:
        return flag in critter.flags


class Rat(Critter):
    char = 'r'
    name = 'rat'
    color = (240, 240, 240)
    description_past = 'Obesity makes this plague-bearing rats realy huge. Interesting, can you even kill one that big...'
    description_present = 'Huge, fat rat somehow managed to leave sewers or households and now posess enourmous threat to unwary adventurer.'
    description_future = 'Strange mental-wave-immune creature, you have not seen ever before. According to records in central creature database (CCDB) these should be called rat'
    base_hd = 1
    base_hp = 3
    speed = 2


class Bat(Critter):
    char = 'w'
    name = 'bat'
    flags = {FLYING}
    color = (0, 255, 60)
    description_past = 'Strange green glow comes from afar... Maybe it\'s a lost sool seeking exit from endless caverns... Wait! It\'s a bat?! Ouch, stop biting me!'
    description_present = 'Tiny bat emmiting a strange green glow, fliting high above the ground. If you can only catch one alive it can become a nice lantern.'
    description_future = 'Flying creature, glowing with strange mutagenic radiation - it would be better if you don\'t touch it'
    base_hd = 1
    base_hp = 3
    base_dmg = [(1, 1, 0, 150), (1, 1)]
    move_speed = 2
    common = 3


class Orc(Critter):
    char = 'o'
    name = 'orc'
    flags = {WALKING , INTELLIGENT}
    color = (255, 0, 0)
    description_past = 'Beware! This mighty ugly-looking humanoid will eat you for dinner. Nightmare comes to live. By the way, there should be it\' friends somewhere nearby'
    description_present = 'Surely you have read about orcs (remember all this books, about hobbits, elves and others). This one looks exactly... dissimilary.'
    description_future = 'This creature looks as if it managed to escape from mad-scientist lab, where it was created. Several scars are spread along it\' torso, giving you hint that this creature is not going to chat with you.'
    base_hd = 3
    base_hp = 10
    base_ac = 1
    base_dmg = [(1, 3)]
    dlvl = 3

class Troll(Critter):
    char = 't'
    name = 'troll'
    flags = {WALKING,  INTELLIGENT}
    color = (220, 120, 120)
    description_past = 'Troll'
    description_present = 'Troll'
    description_future = 'Troll'
    base_hd = 5
    base_hp = 10
    base_ac = 1
    base_dmg = [(1, 3)]
    dlvl = 3

class Skeleton(Critter):
    name = 'skeleton'
    flags = {UNDEAD}
    description_past = 'Skeleton'
    char = 'z'

    def __init__(self, name = None, base_hd_adjust=0):
        super(Skeleton, self).__init__()
        self.action_cost.move = 20
        #if name is None:
            #self.name = creature.name + ' skeleton'
        #else:
            #self.name = name
        #for flag in creature.flags:
            #if flag != INTELLIGENT and flag != DEMON:
                #self.flags.add(flag)
        #if self.check_flag(LARGE_SIZE):
            #self.char = 'Z'


mobs = {}
skeleton = Skeleton

loc = locals()
for var, deff in loc.items():
    if isinstance(deff,type) and issubclass(deff, Critter):
        mobs[var] = deff

def filter_critters_by_flags(critter, flags=0, not_flags=0):
    result = False
    if flags == 0 and not_flags == 0: return True
    elif flags != 0:
        result = check_flag(critter, flags)
    if not_flags != 0:
        result &= not check_flag(critter, not_flags)
    return result

def random_for_player_hd(hd = 1, inverse = False, exact=True, max_hd=1000, flags=0, not_flags=0):
    """ Finds and return creature apropriate for given HD. It first tries to find
    creature with request HD. If this is not possible a random creature and adjust it's HD.
    hd - target HD
    inverse - will select items with lower 'common' value if turned on
    exact - tells function to select mobs of exact given HD. If set to False then
        mobs are filtered by hd >= hd and hd <= max_hd
    max_hd - tells to select mobs with HD no higher than max_hd. Usable only with exact=False
    flags - let's filter creatures by flags
    not_flags - lets you select creatures with exact flag set to false
    """
    ff = None
    if exact:
        ff = lambda x: x.base_hd == hd and filter_critters_by_flags(x, flags)
    else:
        ff = lambda x: x.base_hd >=hd and x.base_hd <= max_hd and filter_critters_by_flags(x, flags, not_flags)
    hd_match = filter(ff, mobs)
    if len (hd_match) < 1:#if no such NPC, take any and adjust HD
        ff2 = lambda x: filter_critters_by_flags(x , flags, not_flags)
        anymob = util.random_from_list_weighted(filter(ff2, mobs), inverse)()
        new_hd = hd
        if not exact:
            new_hd = max_hd
        anymob.adjust_hd(new_hd)
        return anymob

    return util.random_from_list_weighted(hd_match, inverse)()



