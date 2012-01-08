from random import choice, randrange, randint
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
    items = None
    id = None
    mob = None
    def __init__(self, id=None):
        if not hasattr(self, 'flags'):
            self.flags = NONE
        if id and not self.id:
            self.id = id

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
        """ player_move_into(Player, int, int, map.Map) => (bool, bool, bool)
        Invoked before player steps onto next tile. Must return tuple of 3 values:
        first - if player can occupy square, second if it takes turn,
        third value - denotes if fov should be recalculated
        @player - player or monster stepping on that tile
        @x, @y - coords of tile
        @map_def - link to the map itself
        """
        if self.items:
            for item in self.items[:]:
                item.player_move_into(player, x, y, map_def)
        return self.passable(), self.passable(), self.passable()

    def player_over(self, player):
        pass

    def set_target(self, delegate):
        self.delegate = delegate
        self.char = delegate.char
        self.color = delegate.color
        self.dim_color = delegate.dim_color
        if hasattr(delegate, 'color_back'):
            self.color_back = delegate.color_back
        if hasattr(delegate, 'dim_color_back'):
            self.dim_color_back = delegate.dim_color_back

    def init(self):
        if self.items:
            for x in xrange(len(self.items)):
                self.items[x] = self.items[x]()
                self.items[x].place(self)


def build_type(name, base=DungeonFeature, **args):
    return build_type_(name, base, **args)

class Thumb(DungeonFeature):
    char = '.'

    def __init__(self, color, dim_color):
        super(Thumb, self).__init__()
        self.color = color
        self.dim_color = dim_color


class NoneFeature(DungeonFeature):
    invisible = True
    def __init__(self):
        super(NoneFeature, self).__init__()


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

class HiddenFeature(object):
    invisible = True
    has_hidden = True
    skill = 1

    def found(self, player):
        gl.message('You have found %s' % self)
        self.has_hidden = False

class HiddenDoor (Door, HiddenFeature):
    def __init__(self):
        self.set_params({'color' : (255,255,255), 'dim_color':(128,128,128), 'type':ftype.door, 'flags': BLOCK_LOS | BLOCK_WALK | FIXED})
        self.opened = False

    def found(self, player):
        super(HiddenDoor, self).found(player)
        self.has_hidden = False
        self.char = '+'

    def player_move_into(self, player, x, y, mapdef):
        if not self.has_hidden:
            return Door.player_move_into(self, player, x, y, mapdef)
        player.search_skill.observe(self)
        if self.has_hidden:
            gl.message("You bump into wall")
            return False, False, False
        return super(HiddenDoor, self).player_move_into(player, x, y, mapdef)

    def __getattribute__(self, name):
        return super(HiddenDoor, self).__getattribute__(name)

    def __repr__(self):
        return 'hidden door'

class Furniture(DungeonFeature):
    type = ftype.furniture
    flags = BLOCK_WALK

class _TreasureChest(Furniture):
    '''A chest, contatining treasures'''
    def __init__(self):
        super(_TreasureChest, self).__init__()
        self.set_params({'char':'8', 'color': (203,203,203), 'dim_color':(203,203,203), 'type':6, 'flags':NONE})

    def player_move_into(self, player, x, y, mapdef):
        super(_TreasureChest, self).player_move_into(player, x, y, mapdef)
        print 'You found treasure chest'

class _Altar(DungeonFeature):
    def __init__(self):
        super(_Altar, self).__init__()
        self.set_params({'char':'_', 'color':(255,255,255), 'dim_color':(128,128,128), 'type':7, 'flags':NONE, 'id':id})

class _Grass(DungeonFeature):
    def __init__(self):
        super(_Grass, self).__init__()
        self.char = choice(['`', ',', '.'])
        self.color = choice( [ (0, 80, 0),(20, 80, 0), (0,80,20), (20,80,20)])

class _PressurePlate(HiddenFeature, DungeonFeature):
    affected='x'
    action='remove'
    type = ftype.trap
    invisible = True
    def __init__(self):
        super(_PressurePlate, self).__init__()
        self.reacted = False

    def player_move_into(self, player, x, y, map):
        #todo check player is flying (maybe)
        if self.reacted: return True, True, True #already pressed
        self.reacted = True #todo - take skills in account
        gl.message('%s step on the pressure plate' % player.pronoun.capitalize())
        self.found(player)
        fts = map.current.find_feature(self.affected, multiple=True)
        if fts:
            for ft, x, y in fts:
                if self.action == 'remove':
                    map.current.replace_feature_atxy(x, y, with_what=map.map_src.floor)
            if self.action == 'remove':
                if util.coinflip():
                    gl.message('You hear grinding noise')
                else:
                    gl.message('You hear some strange shrieking noise')
                map.init_fov()
        else:
            gl.message('Nothing seems to happen')
        return True, True, True

    def found(self, player):
        super(_PressurePlate, self).found(player)
        self.char = '^'

    def __repr__(self):
        return 'pressure plate'


class _Trap(DungeonFeature, HiddenFeature):
    name ='trap'
    disarmed = False
    type = ftype.trap
    invisible = True
    def __init__(self):
        super(_Trap, self).__init__()

    def found(self, player):
        self.has_hidden = False
        self.char = '^'
        gl.message('You found a trap')

    def dmg(self):
        #todo cap?
        return [(util.roll(self.skill, 4)) - randint(self.skill / randint(1, 2), self.skill)]

    def max_dmg(self):
        return (self.skill * 4) - (self.skill / 2)

    def player_move_into(self, player, x, y, map_def):
        if self.has_hidden:
            player.search_skill.observe(self)
        if self.has_hidden and not self.disarmed:
            gl.message('%s step on a trap' % player.pronoun.capitalize())
            self.found(player)
            player.take_damage(self, self.dmg(), None)
        elif not self.disarmed:
            max_dm = self.max_dmg()
            if max_dm > (min(player.hp, player.base_hp * gl.__trap_low_hp_warning__)): #if this trap can be dangerous
                if gl.render_warn_yn_dialog('Step on the trap (yY/nN)?'): # we ask player
                    player.take_damage(self, self.dmg(), None)
                else:
                    return False, False, False
            else: #if this is wimpy trap - just pass over
                player.take_damage(self, self.dmg(), None)

        return super(_Trap, self).player_move_into(player, x, y, map_def)

class Stairs(DungeonFeature):
    pair = None
    def __init__(self):
        char = '>'
        if not getattr(self, 'down', True):
            char = '<'
        super(Stairs, self).__init__()
        self.set_params({'char':char, 'color':(255,255,255), 'dim_color':(80,80,80), 'type':ftype.stairs, 'id':id, 'flags': FIXED})
        self.can_go_down = getattr(self, 'down', True)
        self.pair = None

    def set_down(self, value):
        self.char = '<' if value else '>'
        self.can_go_down = True

    def get_down(self):
        return self.can_go_down

    down = property(fget=get_down, fset=set_down)


floor = build_type('Floor', char='.', color=(255, 255, 255), dim_color=(0, 0, 100), type=ftype.floor)
none = NoneFeature
fixed_wall = build_type('FixedWall', char='#', color=(130, 110, 50), dim_color=(0, 0, 100), flags=FIXED | BLOCK_LOS | BLOCK_WALK, type=ftype.wall)
rock_wall  = build_type('RockWall', char='#', color=(130, 110, 50), dim_color=(0, 0, 100), flags=BLOCK_LOS | BLOCK_WALK, type=ftype.wall)
glass_wall = build_type('GlassWall', char='#', color=(30, 30, 160), dim_color=(0, 0, 100), flags=BLOCK_WALK, type=ftype.wall)
window = build_type('Window', char='0', color=(128, 128, 160), dim_color=(0, 0, 60), flags=BLOCK_WALK, type=ftype.wall)
well = build_type('Well', char='o', color=(255, 255, 255), dim_color=(0, 0, 60), type=ftype.furniture, flags=BLOCK_WALK)
tree = build_type('Tree', char='T', color=(0, 90, 0), dim_color=(0, 40, 0), type=ftype.furniture, flags=BLOCK_WALK | BLOCK_LOS)
statue = build_type('Statue', char='T', color=(100, 100, 100), dim_color=(80, 80, 80), type=ftype.furniture, flags=BLOCK_WALK | BLOCK_LOS)
tomb = build_type('Tomb', char='_', color=(100, 100, 100), dim_color=(80, 80, 80), type=ftype.furniture, flags=BLOCK_WALK | BLOCK_LOS)
fountain = build_type('Fountain', char='{', color=(20, 60, 200), dim_color=(10, 30, 100), type=ftype.furniture, flags=BLOCK_WALK)
pool = build_type('Pool', char='{', color=(20, 60, 200), dim_color=(10, 30, 100), type=ftype.furniture, flags=BLOCK_WALK)
bush = build_type('Bush', char='*', color=(0, 90, 0), dim_color=(0, 40, 0), type=ftype.furniture, flags=BLOCK_WALK)
road = build_type('Road', char=' ', color=(0, 0, 0), dim_color=(0, 0, 0), type=ftype.road, color_back=(128,128,128), dim_color_back=(50,50,50))
carpet = build_type('Carpet', char='.', color=(0,0,0), dim_color=(0,0,0), type=ftype.floor, color_back=(128,128,128), dim_color_back=(50,50,50))
grass = build_type('Grass', base=_Grass, dim_color =(0, 30, 10), type=ftype.floor)

door = build_type('ClosedDoor', base=Door, opened=False)
chair = build_type('Chair', base=Furniture, char='h', color=(120, 120, 0), dim_color=(40, 40, 0))
table = build_type('Table', base=Furniture, char='T', color=(120, 120, 0), dim_color=(40, 40, 0))
bed = build_type('Bed', Furniture, char='8',color=(120, 120, 0), dim_color=(40, 40, 0))

stairs_up = build_type('StairsUp', base=Stairs, down=False, flags=FIXED)
stairs_down = build_type('StairsDown', base=Stairs, down=True, flags=FIXED)
dungeon_stairs_up1 = build_type('DungeonStairsUp1', base=Stairs, down=False, flags=FIXED)
dungeon_stairs_down1 = build_type('DungeonStairsDown1', base=Stairs, down=True, flags=FIXED)
dungeon_stairs_up2 = build_type('DungeonStairsUp2', base=Stairs, down=False, flags=FIXED)
dungeon_stairs_down2 = build_type('DungeonStairsDown2', base=Stairs, down=True, flags=FIXED)
dungeon_stairs_up3 = build_type('DungeonStairsUp3', base=Stairs, down=False, flags=FIXED)
dungeon_stairs_down3 = build_type('DungeonStairsDown3', base=Stairs, down=True, flags=FIXED)
treasure_chest = build_type('TreasureChest', _TreasureChest, flags=FIXED)

pressure_plate = build_type('PressurePlate', _PressurePlate, affected='x', type='remove', subst=floor, flags=FIXED)
trap = build_type('Trap', _Trap, char='.', dim_color=(0, 0, 100))
hidden_door = build_type('HiddenDoor', base=HiddenDoor, feature=rock_wall, char=fixed_wall.char)

altar = build_type('Altar', base=_Altar, flags=FIXED)
ph = build_type('PH', char=' ', invisible=True, flags=FIXED)


features = {}
loc = locals()
for var, deff in loc.items():
    if isinstance(deff,type) and issubclass(deff, DungeonFeature):
        features[var] = deff

