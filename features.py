from random import choice, randrange
import gl

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
    "altar" : 7,
}

#todo make FT_FLOOR etc return parametrized classes instead of objects
#i.e. if we request FT_FLOOR(some_params) - return a class, upon creation of which we get proper fields filled
class DungeonFeature(object):
    invisible = False
    def __init__(self, char, color, dim_color, type=1, flags=NONE, id=None):
        self.char = char
        self.color = color
        self.flags = flags
        self.dim_color = dim_color
        self.type = type
        self.seen = False
        self.color_back = (30, 30, 30)
        self.dim_color_back = (5, 5, 5)
        self.items = []
        self.description = 'Generic feature'
        self.id=id

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

    def set_target(self, delegate):
        self.delegate = delegate
        self.char = delegate.char
        self.color = delegate.color
        self.dim_color = delegate.dim_color
        self.color_back = delegate.color_back
        self.dim_color_back = delegate.dim_color_back

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
        super(HiddenDoor, self).__init__(opened)
        self.char = feature.char
        if opened:
            self.char = '-'
        self.hidden = not opened
        self.opened = opened
        self.skill = skill
        self.feature = feature

    def player_move_by(self, player, x, y):
        #todo check for traps and doors skill. now just a coinflip
        if self.hidden and util.coinflip():
            self.hidden = False
            self.char = '+'

    def player_move_into(self, player, x, y):
        #todo check for traps and doors skill. now just a coinflip
        if self.hidden and util.coinflip():
            self.hidden = False
            self.char = '+'
        if self.hidden:
            return False, False, False
        return super(HiddenDoor, self).player_move_into(player, x, y)

class Furniture(DungeonFeature):
    pass
class TreasureChest(Furniture):
    """A chest, contatining treasures"""
    def __init__(self):
        super(TreasureChest, self).__init__('8', (203,203,203), (203,203,203), type=6, flags=NONE)
        self.char  = '8'
        self.color = (203, 203, 203)

    def player_move_into(self, player, x, y):
        super(TreasureChest, self).player_move_into(player, x, y)
        print 'You found treasure chest'

class Altar(DungeonFeature):
    def __init__(self, id=id):
        super(Altar, self).__init__('_', (255,255,255), (128,128,128), type=7, flags=NONE, id=id)

def FT_FIXED_WALL(id=None): return DungeonFeature('#', (130, 110, 50), (0, 0, 100), flags=BLOCK_LOS | BLOCK_WALK, id=id)
def FT_ROCK_WALL(id=None): return DungeonFeature("#", (130, 110, 50), (0, 0, 100), flags=BLOCK_LOS | BLOCK_WALK, id=id)
def FT_GLASS_WALL(id=None): return DungeonFeature("#", (30, 30, 160), (0, 0, 100), flags=BLOCK_WALK, id=id)
def FT_WINDOW(id=None): return DungeonFeature("0", (128, 128, 160), (0, 0, 60), flags=BLOCK_WALK, id=id)
def FT_WELL(id=None): return DungeonFeature("o", (255, 255, 255), (0, 0, 60), ft_types['furniture'], flags=BLOCK_WALK, id=id)
def FT_TREE(id=None): return DungeonFeature("T", (0, 90, 0), (0, 40, 0), ft_types['furniture'], flags=BLOCK_WALK | BLOCK_LOS, id=id)
def FT_STATUE(id=None): return DungeonFeature("T", (100, 100, 100), (80, 80, 80), ft_types['furniture'], flags=BLOCK_WALK | BLOCK_LOS, id=id)
def FT_FOUNTAIN(id=None): return DungeonFeature("{", (20, 60, 200), (10, 30, 100), ft_types['furniture'], flags=BLOCK_WALK, id=id)
def FT_POOL(id=None): return DungeonFeature("{", (20, 60, 200), (10, 30, 100), ft_types['furniture'], flags=BLOCK_WALK, id=id)
def FT_BUSH(color=(0, 90, 0),id=None ): return DungeonFeature("*", color, (0, 40, 0), ft_types['furniture'], flags=BLOCK_WALK, id=id)
def FT_FLOOR(id=None): return DungeonFeature(".", (255, 255, 255), (0, 0, 100), ft_types["floor"], id=id)
def FT_ROAD(back=None, char=' ', id=None):
    df= DungeonFeature(char, (0, 0, 0), (0, 0, 0), ft_types["road"])
    if  back == None:
        df.color_back = (128,128,128)
        df.dim_color_back = (50,50,50)
    else:
        df.color_back = back
    return df

def FT_CARPET(back=None, char='.', id=None):
    df = DungeonFeature(char, (0, 0, 0), (0, 0, 0), ft_types["floor"])
    if  back == None:
        df.color_back = (128,128,128)
        df.dim_color_back = (50,50,50)
    else:
        df.color_back = back
        #df.dim_color_back = dim_color(back)
    return df
def FT_GRASS(id=None):
    df = DungeonFeature(choice(['`', ',', '.']),
    choice( [ (0, 80, 0),(20, 80, 0), (0,80,20), (20,80,20)]), (0, 30, 10), ft_types["floor"])
    return df
def FT_DOOR(id=None): return Door(False)
def FT_CHAIR(id=None): return Furniture('h',(120, 120, 0), (40, 40, 0), ft_types["furniture"], flags=BLOCK_WALK)
def FT_TABLE(id=None): return Furniture('T',(120, 120, 0), (40, 40, 0), ft_types["furniture"], flags=BLOCK_WALK)
def FT_BED(id=None): return Furniture('8',(120, 120, 0), (40, 40, 0), ft_types["furniture"], flags=BLOCK_WALK)
def FT_RANDOM_FURNITURE(id=None): return choice ((FT_CHAIR, FT_TABLE, FT_BED))()
def FT_STAIRCASES_UP(id=None): return DungeonFeature("<", (255,255,255), (80,80,80), ft_types["stairs"])
def FT_STAIRCASES_DOWN(id=None): return DungeonFeature(">", (255,255,255), (80,80,80), ft_types["stairs"])
def FT_HIDDEN_DOOR(skill=5, id=None):
    return HiddenDoor(skill, feature=FT_ROCK_WALL())
def FT_TREASURE_CHEST(id=None): return TreasureChest()

class FT_PREASURE_PLATE(DungeonFeature):
    invisible = True
    def __init__(self, affected='x', type='remove'):
        super(FT_PREASURE_PLATE, self).__init__('.', None, None, type=1, flags=NONE)
        self.affected=affected
        self.type=type

class FT_TRAP(DungeonFeature):
    invisible = True
    def __init__(self):
        super(FT_TRAP, self).__init__(' ', None, None, type=1, flags=NONE, id=id)


def FT_ALTAR(id=None):
    return Altar(id)

class PH(DungeonFeature):
    invisible = True
    def __init__(self, id):
        self.id = id
        super(PH, self).__init__(' ', None, None, type=1, flags=NONE, id=id)
