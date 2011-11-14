from critters import Critter
import gl
import util
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
            total_skill = min(search_skill_base_chance + (self.skill - tile.skill), 25) #cap at 25%
            #if player search level is higher than feature's then we have tile_skill/skill chance of feature veing revealed
            if util.chance_in(total_skill, 100):
                tile.found(self.player)
        else: #player skill is lover
            total_skill = int(max(1, search_skill_base_chance - ((tile.skill - self.skill) * 1.5)))
            if util.chance_in(total_skill, 100):
                tile.found(self.player)
            
                

class Player(Critter):
    pronoun = 'you'
    x, y = 0, 0
    char = '@'
    color = (255, 255, 255)
    skip_register = True
    fov_range = 10
    base_hp = 25
    base_mp = 10
    mp = 10
    hitpoints = base_hp
    name = 'you'
    xl = 1
    xp = 0

    def __init__(self):
        self.map = None
        self.gold = 0
        self.search_skill = SearchSkill(self)

    def move(self, dx, dy):
        newx, newy = self.x + dx, self.y + dy
        if not self.map.coords_okay(newx, newy):
            return False, False
        if self.map.has_critter_at((newx, newy)):
            self.attack(self.map.get_critter_at(newx, newy))
            return True, False
        next_tile = self.map.tile_at(newx, newy)
        move_to, take_turn, fov_recalc = next_tile.player_move_into(self, newx, newy, self.map)
        if move_to:
            self.x, self.y = newx, newy
            return take_turn, fov_recalc
        elif next_tile.is_wall():
            gl.message("You bump into wall")
        return take_turn, fov_recalc

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

    @property
    def fov_xy0(self):
        """Returns the upper-left corner of player fov"""
        return max(self.x - self.fov_range, 0), max(self.y - self.fov_range, 0)
    @property
    def fov_xy2(self):
        """Returns the lower-right corner of player fov"""
        return self.x + self.fov_range, self.y + self.fov_range

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



