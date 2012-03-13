from critters import Critter, ActionCost
import gl
import util
from inventory import Inventory

search_skill_scale = [x for x in xrange(5, 1000, 17)]
search_skill_scale.insert(0, 0)
search_skill_base_chance = 10
class PassiveSkill(object):
    pass

class SearchSkill(PassiveSkill):
    def __init__(self, player):
        self.skill = 1
        self.player = player

    def observe(self, tile):
        if self.skill >= tile.skill:
            total_chance = min(search_skill_base_chance + (self.skill - tile.skill), 25) #cap at 25%
            #if player search level is higher than feature's then we have tile_skill/skill chance of feature veing revealed
            if util.chance_in(total_chance, 100):
                tile.found(self.player)
        else: #player skill is lover
            total_chance = int(max(1, search_skill_base_chance - ((tile.skill - self.skill) * 1.5)))
            if util.chance_in(total_chance, 100):
                tile.found(self.player)


class PlayerActionCost(ActionCost):
    search = ActionCost.move
    def __init__(self, **args):
        super(PlayerActionCost, self).__init__(**args)
        self.move = 5.0

class Player(Critter):
    pronoun = 'you'
    x, y = 0, 0
    char = '@'
    color = (255, 255, 255)
    skip_register = True
    fov_range = 10
    base_hp = 155
    base_mp = 10
    mp = 10
    hitpoints = base_hp
    name = 'you'
    xl = 1
    xp = 0
    energy = 10.0
    current_energy = energy
    action_cost = PlayerActionCost()
    time = 'past' #present or future

    def __init__(self):
        self.map = None
        self.gold = 0
        self.search_skill = SearchSkill(self)
        self.inventory = Inventory(self)

    def move(self, dx, dy):
        newx, newy = self.x + dx, self.y + dy
        if not self.map.coords_okay(newx, newy):
            return False, False, None
        if self.map.has_critter_at((newx, newy)):
            cost = self.attack(self.map.get_critter_at(newx, newy))
            return True, False, cost
        next_tile = self.map.tile_at(newx, newy)
        move_to, take_turn, fov_recalc = next_tile.player_move_into(self, newx, newy, self.map)
        if move_to:
            #todo move cost should be changed by the type of tile we're entering
            self.x, self.y = newx, newy
            self.search(self.map, 4)
            return take_turn, fov_recalc, self.action_cost.move
        elif next_tile.is_wall():
            gl.message("You bump into wall")
        return take_turn, fov_recalc, None

    def search(self, map, range=None):
        if not range:
            range = self.fov_range
        map.iterate_fov(self.x, self.y, range, self.see)
        return self.action_cost.search

    def descend(self, map):
        if map.descend_or_ascend(True):
            return self.action_cost.stairsdown / 2
        return None

    def ascend(self, map):
        if map.descend_or_ascend(False):
            return self.action_cost.stairsdown / 2
        return None

    def die(self, killer):
        gl.message( 'You die...', 'CRITICAL')
        gl.__game_state__ = "died"

    def earn_exp(self, src):
        self.xp += src.xp
        if self.xp > util.xp_for_lvl(self.xl):
            self.lvl_up()

    def lvl_up(self):
        self.xl += 1
        gl.message ("Congratulations! Level up", 'INFO')

    def see(self, tile, tilex, tiley, map):
        if tile.items and len(tile.items):
            item = tile.items[0]
            if not getattr(item, 'seen', False):
                gl.message('You see %s' % item)
                item.seen = True
        if getattr(tile, 'has_hidden', False):
            self.search_skill.observe(tile)

    def take_damage(self, mob, dmgs, attack):
        #take evasion into account
        super(Player, self).take_damage(mob, dmgs, attack)
        if self.hitpoints <= self.base_hp * gl.__hp_warning__:
            gl.message('Low HP!!!', 'WARN')


    def gethp(self):
        return self.hitpoints

    def sethp(self, value):
        self.hitpoints = value
        gl.require_hud_update()

    hp = property(gethp, sethp)

    def get_inventory_categorized(self):
        """ get_inventory_categorized() => {category :[items]}
        Returns list of items divided by category
        """
        return self.inventory.categorized_view()
