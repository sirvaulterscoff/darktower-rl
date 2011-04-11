import gl

BLOCK_WALK = 1
BLOCK_LOS = 2
NONE = 4

ft_types = {
    "door": 2,
    "wall": 1,
    "floor": 0
}

class DungeonFeature(object):
    def __init__(self, char, color, dim_color, type=ft_types["wall"], flags=NONE):
        self.char = char
        self.color = color
        self.flags = flags
        self.dim_color = dim_color
        self.type = type
        self.seen = False
        self.color_back = [30, 30, 30]
        self.dim_color_back = [5, 5, 5]

    def is_wall(self):
        return self.type == ft_types["wall"]

    def is_floor(self):
        return self.type == ft_types["floor"]

    def passable(self):
        return not self.flags & BLOCK_WALK

    def player_move_into(self, player, x, y):
        #returns tupple. 1value for if this sqaure can be occupied,
        # second value if it takes turn
        # third value - denotes if fov should be recalculated
        return self.passable(), True, True

    def player_over(self, player):
        pass

class Door (DungeonFeature):
    def __init__(self, opened=False):
        char = '+'
        if opened:
            char = '-'
        super(Door,self).__init__(char, [255,255,255],[128,128,128], ft_types["door"], BLOCK_LOS | BLOCK_WALK)
        self.opened = opened

    def player_move_into(self, player, x, y):
        super(Door, self).player_move_into(player, x, y)
        if not self.opened:
            self.opened = True
            self.char = '-'
            self.flags = NONE
            gl.message('You open the door.')
            player.map.update_fov_for(x, y)
            return False, True, True
        return True, True, True


def FT_FIXED_WALL(): return DungeonFeature('#', [130, 110, 50], [0, 0, 100], flags=BLOCK_LOS | BLOCK_WALK)
def FT_ROCK_WALL(): return DungeonFeature("#", [130, 110, 50], [0, 0, 100], flags=BLOCK_LOS | BLOCK_WALK)
def FT_GLASS_WALL(): return DungeonFeature("#", [30, 30, 160], [0, 0, 100], flags=BLOCK_WALK)
def FT_WINDOW(): return DungeonFeature("0", [128, 128, 160], [0, 0, 60], flags=BLOCK_WALK)
def FT_FLOOR(): return DungeonFeature(".", [255, 255, 255], [60, 60, 60], ft_types["floor"])
def FT_DOOR(): return Door(False)
