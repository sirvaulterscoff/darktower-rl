from critters import Critter
import gl
import util

class Player(Critter):
    x, y = 0, 0
    char = '@'
    color = (255, 255, 255)
    skip_register = True
    fov_range = 10
    base_hp = 10
    base_mp = 10
    mp = 10
    hp = base_hp
    name = 'you'
    xl = 1
    xp = 0

    def __init__(self):
        self.map = None
        self.gold = 0

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

  