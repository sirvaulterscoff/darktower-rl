import gl
import thirdparty.libtcod.libtcodpy as libtcod
from features import  *

SCREEN_WIDTH = 80
RIGHT_PANEL_WIDTH = 40
SCREEN_HEIGHT = 50
LIMIT_FPS = 20

MSG_BAR_WIDTH = 20
MSG_PANEL_HEIGHT = 7
PANEL_X = SCREEN_WIDTH - RIGHT_PANEL_WIDTH

COLOR_STATUS_TEXT = (166, 102, 0)
HP_BAR = ((0, 0, 255), (128, 0, 255), (255, 0, 0))
MP_BAR = ((115, 0, 255), (255, 136, 0), (255, 0, 0))
HP_BAR_PERCENT = (0.50, 0.35)
MP_BAR_PERCENT = (0.50, 0.35)

class AbstractGui(object):
    def __init__(self):
        pass

    def main_loop(self, critters, map):
        pass


class LibtcodGui(AbstractGui):
    def __init__(self):
        libtcod.console_set_custom_font('fonts/terminal10x10_gs_tc.png',
                                        libtcod.FONT_TYPE_GREYSCALE | libtcod.FONT_LAYOUT_TCOD)
        libtcod.console_init_root(SCREEN_WIDTH, SCREEN_HEIGHT, 'darktower-rl', False)
        self.con = libtcod.console_new(SCREEN_WIDTH, SCREEN_HEIGHT)
        self.panel = libtcod.console_new(SCREEN_WIDTH, MSG_PANEL_HEIGHT)


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
                            libtcod.console_set_back(self.con, x, y, self.create_color(map[y][x].dim_color_back),
                                                     libtcod.BKGND_SET)
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

        #prepare to render the GUI panel
        libtcod.console_set_background_color(self.panel, libtcod.black)
        libtcod.console_clear(self.panel)

        #show the player's HP
        self.render_bar(1, 1, 13, 10, player.hp, player.base_hp,
            HP_BAR, libtcod.darker_red, self.create_color(COLOR_STATUS_TEXT), HP_BAR_PERCENT)
        self.render_bar(1, 2, 13, 10, player.mp, player.base_mp,
            MP_BAR, libtcod.darker_red, self.create_color(COLOR_STATUS_TEXT), MP_BAR_PERCENT)

        #blit the contents of "panel" to the root console
        libtcod.console_blit(self.panel, 0, 0, SCREEN_WIDTH, MSG_PANEL_HEIGHT, 0, PANEL_X, 0)
        libtcod.console_flush()

    def render_bar(self, x, y, x2, total_width, value, maximum, bar_color, dim_color, text_color, color_lvls):
        TEXT_PAD = 8
        tick_price = int(maximum / total_width)

        #render the background first
        libtcod.console_set_background_color(self.panel, dim_color)
        formated_str = "HP: %i/%i" % (value, maximum)
        #if displayed value == 0 - skip rendering bar
        if maximum == 0:
            return
        libtcod.console_set_foreground_color(self.panel, text_color)
        libtcod.console_print_left(self.panel, x, y, libtcod.BKGND_NONE, formated_str)
        libtcod.console_set_foreground_color(self.panel, self.create_color(bar_color[0]))
        libtcod.console_print_left(self.panel, x2, y, libtcod.BKGND_NONE, '[' + ''.ljust(total_width, '_') + ']')
        active_ticks = value * tick_price
        severity = 0
        #now choose apropriate color depending on how much value left (compared to maximum)
        for color_lvl in color_lvls:
            if active_ticks <= maximum * color_lvl:
                severity += 1
        #now render the bar on top
        libtcod.console_set_foreground_color(self.panel, self.create_color(bar_color[severity]))
        libtcod.console_print_left(self.panel, x2 + 1 ,y, libtcod.BKGND_NONE, '#'.center(active_ticks, '#'))

    def clear_all(self, critters):
        for critter in critters:
            self.clear_critter(critter.x, critter.y)


    def print_map(self, map):
        x, y = 0, 0
        for row in map:
            for item in row:
                self.print_critter(x, y, item.char)
                y += 1
            x, y = x + 1, 0


    def create_color(self, color):
        return libtcod.Color(color[0], color[1], color[2])

    def window_closed(self):
        return libtcod.console_is_window_closed()