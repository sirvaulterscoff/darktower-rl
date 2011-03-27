import gl
import thirdparty.libtcod.libtcodpy as libtcod
from features import  *

SCREEN_WIDTH = 80
SCREEN_HEIGHT = 50
LIMIT_FPS = 20

class AbstractGui(object):
    def __init__(self):
        pass

    def main_loop(self, critters, map):
        pass

class LibtcodGui(AbstractGui):
    def __init__(self):
        libtcod.console_set_custom_font('fonts/arial12x12.png', libtcod.FONT_TYPE_GREYSCALE | libtcod.FONT_LAYOUT_TCOD)
        libtcod.console_init_root(SCREEN_WIDTH, SCREEN_HEIGHT, 'darktower-rl')
        self.con = libtcod.console_new(SCREEN_WIDTH, SCREEN_HEIGHT)

    def print_critter(self, x, y, char):
        libtcod.console_print_left(self.con, x, y, libtcod.BKGND_NONE, char)

    def clear_critter(self, x, y):
        libtcod.console_print_left(self.con, x, y, libtcod.BKGND_NONE, ' ')

    def render_all(self, map, player):
        if gl.__fov_recompute__:
            gl.__fov_recompute__ = False
            map.recompute_fov()

            for y in range(map.map_height):
                for x in range(map.map_width):
                    seen = map.map[y][x].seen | gl.__wizard_mode__
                    visible = libtcod.map_is_in_fov(map.fov_map, x, y)
                    #if tile is seen or visible to player - print it
                    if seen or visible:
                        libtcod.console_print_left(self.con, x, y, libtcod.BKGND_NONE, map[y][x].char)
                    #if it's not in LOS, but seen - print in dim color
                    if not visible:
                        if seen:
                            libtcod.console_set_fore(self.con, x, y, self.create_color(map[y][x].dim_color))
                            libtcod.console_set_back(self.con, x, y, self.create_color(map[y][x].dim_color_back), libtcod.BKGND_SET)
                    else:
                        #if it's in LOS - print and mark as seen
                        libtcod.console_set_fore(self.con, x, y, self.create_color(map[y][x].color))
                        libtcod.console_set_back(self.con, x, y, self.create_color(map[y][x].color_back), libtcod.BKGND_SET)
                        #if current tile is visible for now - mark as seen
                        map[y][x].seen = True

        for critter in map.map_critters:
            libtcod.console_set_foreground_color(self.con, self.create_color(critter.color))
            self.print_critter(critter.x, critter.y, critter.char)

        libtcod.console_set_foreground_color(self.con, self.create_color(player.color))
        self.print_critter(player.x, player.y, player.char)

        if gl.__wizard_mode__:
            libtcod.console_print_left(self.con, 0, 0, libtcod.BKGND_NONE, 'WIZ MODE')
        libtcod.console_blit(self.con, 0, 0, SCREEN_WIDTH, SCREEN_HEIGHT, 0, 0, 0)
        libtcod.console_flush()

    def clear_all(self, critters):
        for critter in critters:
            self.clear_critter(critter.x, critter.y)

    def print_map(self, map):
        x, y = 0, 0
        for row in map:
            for item in row:
                self.print_critter(x, y, item.char)
                y += 1
            x, y = x+1,0

    def create_color(self, color):
        return libtcod.Color(color[0], color[1], color[2])
