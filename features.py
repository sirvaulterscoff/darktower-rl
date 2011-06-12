from random import choice
import gl
from gui import dim_color
BLOCK_WALK = 1
BLOCK_LOS = 2
NONE = 4
import util
ft_types = {
    "road" : 5,
    "stairs" : 4,
    "furniture" : 3,
    "door": 2,
    "wall": 1,
    "floor": 0,
    "container": 6,
}

class DungeonFeature(object):
    def __init__(self, char, color, dim_color, type=1, flags=NONE):
        self.char = char
        self.color = color
        self.flags = flags
        self.dim_color = dim_color
        self.type = type
        self.seen = False
        self.color_back = (30, 30, 30)
        self.dim_color_back = (5, 5, 5)

    def is_wall(self):
        return self.type == 1

    def is_floor(self):
        return self.type == 0

    def is_road(self):
        return self.type == 5

    def passable(self):
        return not self.flags & BLOCK_WALK

    def player_move_into(self, player, x, y):
        #returns tupple. 1value for if this sqaure can be occupied,
        # second value if it takes turn
        # third value - denotes if fov should be recalculated
        return self.passable(), self.passable(), self.passable()

    def player_over(self, player):
        pass

    def parse_color(self, parser):
        self.color = parser(self.color)
        self.dim_color = parser(self.dim_color)
        self.color_back = parser(self.color_back)
        self.dim_color_back = parser(self.dim_color_back)

class Door (DungeonFeature):
    def __init__(self, opened=False):
        char = '+'
        if opened:
            char = '-'
        super(Door,self).__init__(char, (255,255,255),(128,128,128), ft_types["door"], BLOCK_LOS | BLOCK_WALK)
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

class HiddenDoor (Door):
    def __init__(self, skill=5,feature=None, opened=False):
        self.char = feature.char
        if opened:self.char = '-'
        self.hidden = True
        self.opened = opened
        self.skill = skill
        self.feature = feature

    def player_move_by(self, player, x, y):
        #todo check for traps and doors skill. now just a coinflip
        if self.hidden and util.coinflip():
            self.hidden = False
            self.char = '+'

    def player_move_into(self, player, x, y):
        if self.hidden: return
        super(HiddenDoor, self).player_move_into(player, x, y)

class Furniture(DungeonFeature):
    pass
class TreasureChest(Furniture):
    """A chest, contatining treasures"""
    def __init__(self):
        super(TreasureChest, self).__init__('8', (203,203,203), (203,203,203), type=6, flags=None)
        self.char  = '8'
        self.color = (203, 203, 203)

    def player_move_into(self, player, x, y):
        super(TreasureChest, self).player_move_into(player, x, y)
        print 'You found treasure chest'

def FT_FIXED_WALL(): return DungeonFeature('#', (130, 110, 50), (0, 0, 100), flags=BLOCK_LOS | BLOCK_WALK)
def FT_ROCK_WALL(): return DungeonFeature("#", (130, 110, 50), (0, 0, 100), flags=BLOCK_LOS | BLOCK_WALK)
def FT_GLASS_WALL(): return DungeonFeature("#", (30, 30, 160), (0, 0, 100), flags=BLOCK_WALK)
def FT_WINDOW(): return DungeonFeature("0", (128, 128, 160), (0, 0, 60), flags=BLOCK_WALK)
def FT_WELL(): return DungeonFeature("o", (255, 255, 255), (0, 0, 60), ft_types['furniture'], flags=BLOCK_WALK)
def FT_TREE(): return DungeonFeature("T", (0, 90, 0), (0, 40, 0), ft_types['furniture'], flags=BLOCK_WALK | BLOCK_LOS)
def FT_STATUE(): return DungeonFeature("T", (100, 100, 100), (80, 80, 80), ft_types['furniture'], flags=BLOCK_WALK | BLOCK_LOS)
def FT_FOUNTAIN(): return DungeonFeature("{", (20, 60, 200), (10, 30, 100), ft_types['furniture'], flags=BLOCK_WALK)
def FT_BUSH(color=(0, 90, 0)): return DungeonFeature("*", color, (0, 40, 0), ft_types['furniture'], flags=BLOCK_WALK)
def FT_FLOOR(): return DungeonFeature(".", (255, 255, 255), (0, 0, 100), ft_types["floor"])
def FT_ROAD(back=None, char=' '):
    df= DungeonFeature(char, (0, 0, 0), (0, 0, 0), ft_types["road"])
    if  back == None:
        df.color_back = (128,128,128)
        df.dim_color_back = (50,50,50)
    else:
        df.color_back = back
    return df

def FT_CARPET(back=None, char='.'):
    df = DungeonFeature(char, (0, 0, 0), (0, 0, 0), ft_types["floor"])
    if  back == None:
        df.color_back = (128,128,128)
        df.dim_color_back = (50,50,50)
    else:
        df.color_back = back
        #df.dim_color_back = dim_color(back)
    return df
def FT_GRASS():
    df = DungeonFeature(choice(['`', ',', '.']),
    choice( [ (0, 80, 0),(20, 80, 0), (0,80,20), (20,80,20)]), (0, 30, 10), ft_types["floor"])
    return df
def FT_DOOR(): return Door(False)
def FT_CHAIR(): return Furniture('h',(120, 120, 0), (40, 40, 0), ft_types["furniture"], flags=BLOCK_WALK)
def FT_TABLE(): return Furniture('T',(120, 120, 0), (40, 40, 0), ft_types["furniture"], flags=BLOCK_WALK)
def FT_BED(): return Furniture('8',(120, 120, 0), (40, 40, 0), ft_types["furniture"], flags=BLOCK_WALK)
def FT_RANDOM_FURNITURE(): return choice ((FT_CHAIR, FT_TABLE, FT_BED))()
def FT_STAIRCASES_UP(): return DungeonFeature("<", (255,255,255), (80,80,80), ft_types["stairs"])
def FT_STAIRCASES_DOWN(): return DungeonFeature(">", (255,255,255), (80,80,80), ft_types["stairs"])
def FT_HIDDEN_DOOR(skill=5):
    return HiddenDoor(skill, feature=FT_ROCK_WALL())
def FT_TREASURE_CHEST(): return TreasureChest()
