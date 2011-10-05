from random import choice, randrange
import gl

BLOCK_WALK = 1
BLOCK_LOS = 2
NONE = 4
import util
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

def build_type(name, base=None, **argv):
    if not base:
        new_type = type(name, (DungeonFeature,), argv)
    else:
        new_type = type(name, (base,), argv)
    return new_type

class DungeonFeature(object):
    invisible = False
    color_back = (30, 30, 30)
    dim_color_back = (5, 5, 5)
    description = 'Generic feature'
    def __init__(self):
        self.seen = False
        self.items = []
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

class Door (DungeonFeature):
    def __init__(self, opened=False):
        super(Door, self).__init__()
        char = '+'
        if opened:
            char = '-'
        self.set_params({'char': char, 'color' : (255,255,255), 'dim_color':(128,128,128), 'type':ft_types['door'], 'flags': BLOCK_LOS | BLOCK_WALK})
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
    type = ft_types['furniture']
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
    def __init__(self, id=id):
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
                getattr(self, self.action)(*ft, map_def=map_def, player=player)
        return True, True, True

    def remove(self, feature, ft_x, ft_y, map_def, player):
        map_def.map_src.replace_feature_atxy(ft_x, ft_y, map_def.map_src.floor)


class Trap(DungeonFeature):
    invisible = True
    def __init__(self):
        super(Trap, self).__init__()

def FT_PREASURE_PLATE(affected='x', type='remove'):
    return  build_type('PreasurePlate_', PreasurePlate, affected=affected, type=type, subst=FT_FLOOR())

def FT_TRAP():
    return build_type('Trap_', Trap, char='.', invisible=True)
def FT_FIXED_WALL(id=None): return build_type('FixedWall', char='#', color=(130, 110, 50), dim_color=(0, 0, 100), flags=BLOCK_LOS | BLOCK_WALK, id=id, type=ft_types['wall'])
def FT_ROCK_WALL(id=None): return build_type('RockWall', char='#', color=(130, 110, 50), dim_color=(0, 0, 100), flags=BLOCK_LOS | BLOCK_WALK, id=id, type=ft_types['wall'])
def FT_GLASS_WALL(id=None): return build_type('GlassWall', char='#', color=(30, 30, 160), dim_color=(0, 0, 100), flags=BLOCK_WALK, id=id)
def FT_WINDOW(id=None): return build_type('Window', char='0', color=(128, 128, 160), dim_color=(0, 0, 60), flags=BLOCK_WALK, id=id)
def FT_WELL(id=None): return build_type('Well', char='o', color=(255, 255, 255), dim_color=(0, 0, 60), type=ft_types['furniture'], flags=BLOCK_WALK, id=id)
def FT_TREE(id=None): return build_type('Tree', char='T', color=(0, 90, 0), dim_color=(0, 40, 0), type=ft_types['furniture'], flags=BLOCK_WALK | BLOCK_LOS, id=id)
def FT_STATUE(id=None): return build_type('Statue', char='T', color=(100, 100, 100), dim_color=(80, 80, 80), type=ft_types['furniture'], flags=BLOCK_WALK | BLOCK_LOS, id=id)
def FT_FOUNTAIN(id=None): return build_type('Fountain', char='{', color=(20, 60, 200), dim_color=(10, 30, 100), type=ft_types['furniture'], flags=BLOCK_WALK, id=id)
def FT_POOL(id=None): return build_type('Pool', char='{', color=(20, 60, 200), dim_color=(10, 30, 100), type=ft_types['furniture'], flags=BLOCK_WALK, id=id)
def FT_BUSH(color=(0, 90, 0),id=None ): return DungeonFeature('Bush', char='*', color=color, dim_color=(0, 40, 0), type=ft_types['furniture'], flags=BLOCK_WALK, id=id)
def FT_FLOOR(id=None): return build_type('Floor', char='.', color=(255, 255, 255), dim_color=(0, 0, 100), type=ft_types['floor'], id=id)
def FT_ROAD(back=None, char=' ', id=None):
    if  back == None:
        color_bk = (128,128,128)
        dcolor_bk = (50,50,50)
    else:
        color_bk = back
        dcolor_bk = (50, 50, 50) #todo auto-dim-color-adjust
    return build_type('Road', char=char, color=(0, 0, 0), dim_color=(0, 0, 0), type=ft_types['road'], color_back=color_bk, dim_color_back=dcolor_bk)

def FT_CARPET(back=None, char='.', id=None):
    if  back == None:
        color_bk = (128,128,128)
        dcolor_bk = (50,50,50)
    else:
        color_bk = back
        dcolor_bk =(50,50,50)
    return build_type('Carpet', char=char, color=(0,0,0), dim_color=(0,0,0), type=ft_types['floor'], color_back=color_bk, dim_color_back=dcolor_bk)

def FT_GRASS(id=None):
    return build_type('Grass_', base=Grass, dim_color =(0, 30, 10), type=ft_types['floor'])

def FT_DOOR(id=None): return build_type('ClosedDoor', base=Door, opened=False)
def FT_CHAIR(id=None): return build_type('Chair', base=Furniture, char='h', color=(120, 120, 0), dim_color=(40, 40, 0))
def FT_TABLE(id=None): return build_type('Table', base=Furniture, char='T', color=(120, 120, 0), dim_color=(40, 40, 0))
def FT_BED(id=None): return build_type('Bed', Furniture, char='8',color=(120, 120, 0), dim_color=(40, 40, 0))

def FT_RANDOM_FURNITURE(id=None): return choice ((FT_CHAIR, FT_TABLE, FT_BED))()

class Stairs(DungeonFeature):
    def __init__(self, id=None, down=True):
        char = '>'
        if not down:
            char = '<'
        super(Stairs, self).__init__()
        self.set_params({'char':char, 'color':(255,255,255), 'dim_color':(80,80,80), 'type':ft_types["stairs"], 'id':id})
        self.can_go_down = down

def FT_STAIRCASES_UP(id=None): return Stairs(id, False)
def FT_STAIRCASES_DOWN(id=None): return Stairs(id)
def FT_TREASURE_CHEST(id=None): return TreasureChest()

def FT_HIDDEN_DOOR(skill=5, id=None):
    return build_type('HiddenDoor', base=HiddenDoor, skill=skill, feature=FT_ROCK_WALL())


def FT_ALTAR(id=None):
    return Altar(id)

class PH(DungeonFeature):
    invisible = True
    def __init__(self, id):
        self.id = id
        super(PH, self).__init__()
        self.set_params({'char':' ', 'type':1, 'flags':NONE, 'id':id})

