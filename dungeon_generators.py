from random import randrange
from features import *
import thirdparty.libtcod.libtcodpy as libtcod

def parse_string(map):
    new_map = []
    x, y = 0, 0
    map_chars = {'#': FT_ROCK_WALL,
                 ' ' : FT_FLOOR,
                 '.' : FT_FLOOR,
                 '+' : FT_DOOR}
    orient = None
    for line in map:
        if is_orient(line):
            orient = pasrse_orient(line)
            continue
        if is_subst(line):
            parse_subst(line, map_chars)
            continue
        new_map.append([])
        for char in line:
            ft = map_chars.get(char)
            if ft is None:
                raise RuntimeError('failed to parse char ' + char)
            new_map[y].append(ft())
            x += 1
        y += 1
        x = 0
    if orient is not None:
        orient.transform(new_map)
    return new_map


def parse_subst(line, map_chars):
    subst_line = line.replace('SUBST=', '', 1)
    substs = subst_line.split(',')
    for subst_item in substs:
        subst_def = subst_item.split('=>', 1)
        map_chars [subst_def[0]] = globals()[subst_def[1]]


def is_subst(line):
    return line.startswith('SUBST=')


def pasrse_orient(line):
    return None

def is_orient(line):
    return line.startswith('ORIENT=')


def find_passable_square(map):
    x, y = 0, 0
    for row in map:
        for item in row:
            if not item.passable(): y += 1
            else: return y, x
        y = 0
        x += 1
    return 1, 1


class Rect:
    def __init__(self, x, y, width, heigh):
        self.x1 = x
        self.y1 = y
        self.x2 = x + width
        self.y2 = y + heigh

    def center(self):
        center_x = (self.x1 + self.x2) / 2
        center_y = (self.y1 + self.y2) / 2
        return center_x, center_y

    def intersect(self, other):
        return (self.x1 <= other.x2 and self.x2 >= other.x1 and
                self.y1 <= other.y2 and self.y2 >= other.y1)


class AbstractGenerator(object):
    def __init__(self, length, width):
        self._map = [[FT_ROCK_WALL()
                      for i in range(0, length)]
                     for j in range(0, width)]

    def generate_border(self):
        for j in range(0, self.length):
            self._map[0][j] = FT_FIXED_WALL()
            self._map[self.width - 1][j] = FT_FIXED_WALL()

        for j in range(0, self.width):
            self._map[j][0] = FT_FIXED_WALL()
            self._map[j][self.length - 1] = FT_FIXED_WALL()


class CaveGenerator(AbstractGenerator):
    def __init__(self, length, width, open_area=0.60):
        self.length = length
        self.width = width
        self.open_area = open_area
        self._map = [[FT_ROCK_WALL()
                      for i in range(0, length)]
                     for j in range(0, width)]


    def generate(self):
        self.generate_border()
        walls_left = int(self.length * self.width * self.open_area)
        #we don't want this process to hang
        ticks = self.length * self.width
        while walls_left > 0:
            if not ticks:
                print("Map generation tackes too long - returning as is")
                break
            rand_x = randrange(1, self.length - 1)
            rand_y = randrange(1, self.width - 1)

            if self._map[rand_y][rand_x].is_wall:
                self._map[rand_y][rand_x] = FT_FLOOR()
                walls_left -= 1
                ticks -= 1

    def finish(self):
        for x in range(1, self.length - 1):
            for y in range(1, self.width - 1):
                wall_count = self.count_neigh_walls(y, x)

                if self._map[y][x].is_floor():
                    if wall_count > 5:
                        self._map[y][x] = FT_ROCK_WALL()
                elif wall_count < 4:
                    self._map[y][x] = FT_FLOOR()

        return self._map


    def count_neigh_walls(self, x, y):
        count = 0
        for row in (-1, 0, 1):
            for col in (-1, 0, 1):
                if not self._map[(x + row)][y + col].is_floor() and not(row == 0 and col == 0):
                    count += 1
        return count


class RoomsCoridorsGenerator(AbstractGenerator):
    def __init__(self, length, width, room_max_size=15, room_min_size=3, max_rooms=30):
        self._map = [[FT_FIXED_WALL()
                      for i in range(0, length)]
                     for j in range(0, width)]
        self.length = length
        self.width = width
        self.max_rooms = max_rooms
        self.room_min_size = room_min_size
        self.room_max_size = room_max_size

    def generate(self):
        rooms = []
        num_rooms = 0
        ticks = self.max_rooms * 5

        for r in range(self.max_rooms):
            if ticks <= 0: break
            ticks -= 1
            if num_rooms > self.max_rooms: break

            width = libtcod.random_get_int(0, self.room_min_size, self.room_max_size)
            height = libtcod.random_get_int(0, self.room_min_size, self.room_max_size)
            #random position without going out of the boundaries of the map
            x = libtcod.random_get_int(0, 0, self.length - width - 1)
            y = libtcod.random_get_int(0, 0, self.width - height - 1)
            new_room = Rect(x, y, width, height)
            if not self.check_room_overlap(rooms, new_room):
                rooms.append(new_room)
                new_x, new_y = new_room.center()
                if num_rooms > 0:
                    prev_x, prev_y = rooms[num_rooms - 1].center()
                    if libtcod.random_get_int(0, 0, 1) == 1:
                        self.create_h_tunnel(prev_x, new_x, prev_y)
                        self.create_v_tunnel(prev_y, new_y, new_x)
                    else:
                        self.create_v_tunnel(prev_y, new_y, prev_x)
                        self.create_h_tunnel(prev_x, new_x, new_y)
                num_rooms += 1

        for room in rooms:
            self.create_room(room)

    def create_h_tunnel(self, x1, x2, y):
        for x in range(min(x1, x2), max(x1, x2)):
            self._map[y][x] = FT_FLOOR()

    def create_v_tunnel(self, y1, y2, x):
        for y in range(min(y1, y2), max(y1, y2)):
            self._map[y][x] = FT_FLOOR()


    def check_room_overlap(self, rooms, new_room):
        for room in rooms:
            if room.intersect(new_room): return True
        return False

    def create_room(self, room):
        for x in range(room.x1 + 1, room.x2):
            for y in range(room.y1 + 1, room.y2):
                self._map[y][x] = FT_FLOOR()

    def finish(self):
        self.generate_border()
        return self._map


class StaticGenerator(AbstractGenerator):
    def __init__(self):
        pass

    def generate(self):
        pass

    def finish(self):
        return parse_string([
                'SUBST=:=>FT_GLASS_WALL',
                'ORIENT=RANDOM',
                '#######################',
                '## ## ## ## ## ## ## ##',
                '#                     #',
                '####+####     ####+####',
                '###   :::     ###   ###',
                '###   ###     :::   ###',
                '###:#####     ####:####',
                '##:######## ######:####',
                '#                     #',
                '#  #   #       #   #  #',
                '#    #   #   #   #    #',
                '#                     #',
                '#######################'
        ])

