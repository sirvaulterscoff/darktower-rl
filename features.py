from random import choice, randrange
import gl
from util import build_type as build_type_

BLOCK_WALK = 1
BLOCK_LOS = 2
NONE = 4
FIXED=8
import util
class TypeEnum(object):
    ft_types = {
        'road' : 5,
        'stairs' : 4,
        'furniture' : 3,
        'door': 2,
        'wall': 1,
        'floor': 0,
        'container': 6,
        'altar' : 7,
        'trap' : 8,
    }

    def __getattr__(self, name):
        return self.ft_types[name]

ftype = TypeEnum()

class DungeonFeature(object):
    invisible = False
    color_back = (30, 30, 30)
    dim_color_back = (5, 5, 5)
    color = (255, 255, 255)
    dim_color = (128, 128, 128)
    description = 'Generic feature'
    flags = NONE
    def __init__(self, id=None):
        self.seen = False
        self.items = []
        self.id = id
        if not hasattr(self, 'flags'):
            self.flags = NONE

    def set_params(self, argv):
        for k, v in argv.items():
            setattr(self, k, v)

    def is_wall(self):
        return self.type == 1

    def is_floor(self):
        return self.type == 0

    def is_road(self):
        return self.type == 5
    def is_fixed(self):
        return self.flags & FIXED

    def passable(self):
        return not self.flags & BLOCK_WALK

    def player_move_into(self, player, x, y, map_def):
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
        if hasattr(delegate, 'color_back'):
            self.color_back = delegate.color_back
        if hasattr(delegate, 'dim_color_back'):
            self.dim_color_back = delegate.dim_color_back

def build_type(name, base=DungeonFeature, **args):
    return build_type_(name, base, **args)

class Door (DungeonFeature):
    def __init__(self, opened=False):
        super(Door, self).__init__()
        char = '+'
        if opened:
            char = '-'
        self.set_params({'char': char, 'color' : (255,255,255), 'dim_color':(128,128,128), 'type':ftype.door, 'flags': BLOCK_LOS | BLOCK_WALK | FIXED})
        self.opened = opened

    def player_move_into(self, player, x, y, mapdef):
        super(Door, self).player_move_into(player, x, y, mapdef)
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
        if feature is None:
            self.char = '#'
        else:
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

    def player_move_into(self, player, x, y, mapdef):
        #todo check for traps and doors skill. now just a coinflip
        if self.hidden and util.coinflip():
            self.hidden = False
            self.char = '+'
        if self.hidden:
            return False, False, False
        return super(HiddenDoor, self).player_move_into(player, x, y, mapdef)

class Furniture(DungeonFeature):
    type = ftype.furniture
    flags = BLOCK_WALK

class TreasureChest(Furniture):
    '''A chest, contatining treasures'''
    def __init__(self):
        super(TreasureChest, self).__init__()
        self.set_params({'char':'8', 'color': (203,203,203), 'dim_color':(203,203,203), 'type':6, 'flags':NONE})

    def player_move_into(self, player, x, y, mapdef):
        super(TreasureChest, self).player_move_into(player, x, y, mapdef)
        print 'You found treasure chest'

class Altar(DungeonFeature):
    def __init__(self):
        super(Altar, self).__init__()
        self.set_params({'char':'_', 'color':(255,255,255), 'dim_color':(128,128,128), 'type':7, 'flags':NONE, 'id':id})

class Grass(DungeonFeature):
    def __init__(self):
        super(Grass, self).__init__()
        self.char = choice(['`', ',', '.'])
        self.color = choice( [ (0, 80, 0),(20, 80, 0), (0,80,20), (20,80,20)])

class PreasurePlate(DungeonFeature):
    invisible = True
    def __init__(self, affected='x', action='remove'):
        super(PreasurePlate, self).__init__()
        self.affected=affected
        self.action=action
        self.reacted = False

    def player_move_into(self, player, x, y, map_def):
        #todo check player is flying (maybe)
        if self.reacted: return True, True, True #already pressed
        self.reacted = True #todo - take skills in account
        gl.message('You step on the pressure plate')
        fts = map_def.map_src.find_feature(self.affected, multiple=True)
        if fts:
            for ft in fts:
                if self.action == 'remove':
                    map_def.map_src.replace_feature_atxy(*ft, with_what=map_def.map_src.floor)
            if self.action == 'remove':
                if util.coinflip():
                    gl.message('You hear grinding noise')
                else:
                    gl.message('You hear some strange shrieking noise')
        return True, True, True


class Trap(DungeonFeature):
    invisible = True
    def __init__(self):
        super(Trap, self).__init__()

class Stairs(DungeonFeature):
    def __init__(self, id=None, down=True):
        char = '>'
        if not down:
            char = '<'
        super(Stairs, self).__init__()
        self.set_params({'char':char, 'color':(255,255,255), 'dim_color':(80,80,80), 'type':ftype.stairs, 'id':id, 'flags': FIXED})
        self.can_go_down = down


floor = build_type('Floor', char='.', color=(255, 255, 255), dim_color=(0, 0, 100), type=ftype.floor)
preasure_plate = build_type('PreasurePlate_', PreasurePlate, affected='x', type='remove', subst=floor)
trap = build_type('Trap_', Trap, char='.', invisible=True)
fixed_wall = build_type('FixedWall', char='#', color=(130, 110, 50), dim_color=(0, 0, 100), flags=FIXED | BLOCK_LOS | BLOCK_WALK, type=ftype.wall)
rock_wall  = build_type('RockWall', char='#', color=(130, 110, 50), dim_color=(0, 0, 100), flags=BLOCK_LOS | BLOCK_WALK, type=ftype.wall)
glass_wall = build_type('GlassWall', char='#', color=(30, 30, 160), dim_color=(0, 0, 100), flags=BLOCK_WALK)
window = build_type('Window', char='0', color=(128, 128, 160), dim_color=(0, 0, 60), flags=BLOCK_WALK)
well = build_type('Well', char='o', color=(255, 255, 255), dim_color=(0, 0, 60), type=ftype.furniture, flags=BLOCK_WALK)
tree = build_type('Tree', char='T', color=(0, 90, 0), dim_color=(0, 40, 0), type=ftype.furniture, flags=BLOCK_WALK | BLOCK_LOS)
statue = build_type('Statue', char='T', color=(100, 100, 100), dim_color=(80, 80, 80), type=ftype.furniture, flags=BLOCK_WALK | BLOCK_LOS)
fountain = build_type('Fountain', char='{', color=(20, 60, 200), dim_color=(10, 30, 100), type=ftype.furniture, flags=BLOCK_WALK)
pool = build_type('Pool', char='{', color=(20, 60, 200), dim_color=(10, 30, 100), type=ftype.furniture, flags=BLOCK_WALK)
bush = build_type('Bush', char='*', color=(0, 90, 0), dim_color=(0, 40, 0), type=ftype.furniture, flags=BLOCK_WALK)
road = build_type('Road', char=' ', color=(0, 0, 0), dim_color=(0, 0, 0), type=ftype.road, color_back=(128,128,128), dim_color_back=(50,50,50))
carpet = build_type('Carpet', char='.', color=(0,0,0), dim_color=(0,0,0), type=ftype.floor, color_back=(128,128,128), dim_color_back=(50,50,50))
grass = build_type('Grass_', base=Grass, dim_color =(0, 30, 10), type=ftype.floor)

door = build_type('ClosedDoor', base=Door, opened=False)
chair = build_type('Chair', base=Furniture, char='h', color=(120, 120, 0), dim_color=(40, 40, 0))
table = build_type('Table', base=Furniture, char='T', color=(120, 120, 0), dim_color=(40, 40, 0))
bed = build_type('Bed', Furniture, char='8',color=(120, 120, 0), dim_color=(40, 40, 0))

stairs_up = build_type('StairsUp', base=Stairs, down=False)
stairs_down = build_type('StairsDown', base=Stairs, down=True)
treasure_chest = build_type('TreasureChest_', TreasureChest)
hidden_door = build_type('HiddenDoor', base=HiddenDoor, skill=50, feature=rock_wall)

altar = build_type('Altar_', base=Altar)
ph = build_type('PH', DungeonFeature)


features = {}
loc = locals()
for var, deff in loc.items():
    if isinstance(deff,type) and issubclass(deff, DungeonFeature):
        features[var] = deff

