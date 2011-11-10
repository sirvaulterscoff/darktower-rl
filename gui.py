import game_input
import gl
import thirdparty.libtcod.libtcodpy as libtcod
from features import  *
import util

SCREEN_WIDTH = 80
SCREEN_HEIGHT = 40
LIMIT_FPS = 20
MSG_PANEL_HEIGHT = gl.MSG_COUNT
MSG_PANEL_Y = SCREEN_HEIGHT - MSG_PANEL_HEIGHT

RIGHT_PANEL_WIDTH = 40
RIGHT_PANEL_X = SCREEN_WIDTH - RIGHT_PANEL_WIDTH
RIGHT_PANEL_HEIGHT = SCREEN_HEIGHT - MSG_PANEL_HEIGHT

VIEWPORT_WIDTH = SCREEN_WIDTH - RIGHT_PANEL_WIDTH
VIEWPORT_HEIGHT = SCREEN_HEIGHT - MSG_PANEL_HEIGHT


COLOR_STATUS_TEXT = (166, 102, 0)
COLOR_STATUS_VALUES = (244, 244, 244)
HP_BAR = ((0, 0, 255), (128, 0, 255), (255, 0, 0))
MP_BAR = ((115, 0, 255), (255, 136, 0), (255, 0, 0))
HP_BAR_PERCENT = (0.50, 0.35)
MP_BAR_PERCENT = (0.50, 0.35)

MSG_OLD_COLOR = (112, 112, 122)
MSG_WARNING_COLOR = (187, 96, 112)
MSG_NEW_COLOR = (255, 255, 255)

MSG_SEVERITY = { 1 : MSG_NEW_COLOR,
                 2 : MSG_WARNING_COLOR,
                 0 : MSG_OLD_COLOR}

parsed_colors = {}
class AbstractGui(object):
    def __init__(self):
        pass

    def main_loop(self, critters, map):
        pass


class LibtcodGui(AbstractGui):
    message_colours = {}
    def __init__(self):
        libtcod.console_set_custom_font('data/fonts/terminal10x10_gs_tc.png',
                                        libtcod.FONT_TYPE_GREYSCALE | libtcod.FONT_LAYOUT_TCOD)
        libtcod.console_init_root(SCREEN_WIDTH, SCREEN_HEIGHT, 'darktower-rl', False)
        self.con = libtcod.console_new(VIEWPORT_WIDTH, VIEWPORT_HEIGHT)
        self.con2 = libtcod.console_new(VIEWPORT_WIDTH, VIEWPORT_HEIGHT)
        self.panel = libtcod.console_new(RIGHT_PANEL_WIDTH, SCREEN_HEIGHT)
        self.panel_msg = libtcod.console_new(SCREEN_WIDTH, MSG_PANEL_HEIGHT)
        self.message_colours[0] = libtcod.Color(128,128,128)
        self.message_colours[1] = libtcod.Color(200,200,200)
        self.message_colours[2] = libtcod.Color(128,10,10)
        self.message_colours[3] = libtcod.Color(255,10,10)
        self.message_colours[4] = libtcod.Color(255,255,255)
        self.viewport = None

    def reset(self):
        self.viewport = None


    def print_critter(self, x, y, char):
        libtcod.console_set_char(self.con, x, y, char)


    def clear_critter(self, x, y):
        #libtcod.console_set_back(self.con, x, consoley, libtcod.black, libtcod.BKGND_SET)
        libtcod.console_set_char(self.con, x, y, ' ')


    def render_map(self, map, player):
        #todo optimize (see http://umbrarumregnum.110mb.com/cookbook/node/24)
        if not self.viewport:
            cc = self.create_color
            self.viewport = Viewport(VIEWPORT_WIDTH, VIEWPORT_HEIGHT, map)
            for y in range(0, map.height):
                for x in range(0, map.width):
                    map.tile_at(x, y).parse_color(cc)
        if gl.__fov_recompute__:
            gl.logger.debug('Recomputing fov')
            gl.__fov_recompute__ = False
            map.recompute_fov()

        consolex, consoley, xx = 0,0, 0
        self.viewport.update_coords(player.x, player.y)
        gl.logger.debug('Diplaying viewport from %d:%d to %d:%d' % (self.viewport.x, self.viewport.y, self.viewport.x2, self.viewport.y2))
        for y in xrange(self.viewport.y, self.viewport.y2):
            for x in xrange(self.viewport.x, self.viewport.x2):
                
                tile = map.tile_at(x, y)
                seen = tile.seen | gl.__wizard_mode__
                visible = libtcod.map_is_in_fov(map.fov_map, x, y)
                if isinstance(tile.color, tuple):
                    tile.parse_color(self.create_color)
                #if tile is seen or visible to player - print it
                if seen or visible:
                    if tile.items and len(tile.items):
                        char = tile.items[-1].char
                    else:
                        char = tile.char
                    libtcod.console_set_char(self.con, consolex, consoley, char)
                    #if it's not in LOS, but seen - print in dim color
                else:
                    libtcod.console_set_char(self.con, consolex, consoley, ' ')
                if not visible:
                    if seen:
                        libtcod.console_set_fore(self.con, consolex, consoley, tile.dim_color)
                        libtcod.console_set_back(self.con, consolex, consoley, tile.dim_color_back, libtcod.BKGND_SET)
                    else:
                        libtcod.console_set_back(self.con, consolex, consoley, libtcod.black, libtcod.BKGND_SET)
                else:
                    #if it's in LOS - print and mark as seen
                    libtcod.console_set_fore(self.con, consolex, consoley, tile.color)
                    if tile.items and len(tile.items) > 1:
                        libtcod.console_set_back(self.con, consolex, consoley, libtcod.desaturated_yellow, libtcod.BKGND_SET)
                    else:
                        libtcod.console_set_back(self.con, consolex, consoley, tile.color_back, libtcod.BKGND_SET)
                    #if current tile is visible for now - mark as seen
                    tile.seen = True
                consolex += 1
            xx = consolex
            consolex = 0
            consoley += 1

        gl.logger.debug('Printing critters')
        cc = self.create_color
        for critter in map.map_critters:
            if not self.viewport.in_view(critter.x, critter.y):
                continue
            if critter.last_seen_at and not self.viewport.in_view(*critter.last_seen_at):
                continue
            x, y = self.viewport.adjust_coords(critter.x, critter.y)
            if libtcod.map_is_in_fov(map.fov_map, critter.x, critter.y) or gl.__wizard_mode__:
                libtcod.console_set_fore(self.con,x, y, cc(critter.color))
                self.print_critter(x, y, critter.char)
                critter.last_seen_at = critter.x, critter.y
            elif critter.last_seen_at is not None:
                color = cc(critter.color)
                color = dim_color(color)
                libtcod.console_set_fore(self.con, x, y, color)
                self.print_critter(x, y, critter.char)


        gl.logger.debug('Printing player')
        x, y = self.viewport.adjust_coords(player.x, player.y)
        libtcod.console_set_fore(self.con ,x, y, cc(player.color))
        self.print_critter(x, y, player.char)


        if gl.__wizard_mode__:
            libtcod.console_print_left(self.con, 0, VIEWPORT_HEIGHT - 1, libtcod.BKGND_NONE, 'WIZ MODE')

        for x in xrange(0, VIEWPORT_WIDTH):
            for y in xrange(0, VIEWPORT_HEIGHT):
                if x >= xx:
                    self.clear_critter(x, y)
                #if y > consoley:
                #    self.clear_critter(x, y)
        libtcod.console_blit(self.con, 0, 0, VIEWPORT_WIDTH, VIEWPORT_HEIGHT, 0, 0, 0)
        libtcod.console_flush()

    def render_messages(self):
        #print the game messages, one line at a time
        y = 0
        for (line, level) in gl.__msgs__:
            if level < 1 and not gl.__wizard_mode__:
                continue
            libtcod.console_set_foreground_color(self.panel_msg, self.message_colours.get(level, libtcod.white))
            libtcod.console_print_left(self.panel_msg, 0, y, libtcod.BKGND_NONE, line.ljust(SCREEN_WIDTH, ' '))
            y += 1
        libtcod.console_blit(self.panel_msg, 0, 0, SCREEN_WIDTH, MSG_PANEL_HEIGHT, 0, 0, MSG_PANEL_Y)

    def render_ui(self, player):
        cc = self.create_color
        #prepare to render the GUI panel
        libtcod.console_set_background_color(self.panel, libtcod.black)
        libtcod.console_clear(self.panel)
        #show the player's HP
        self.render_bar(1, 1, 13, 10, player.hp, player.base_hp,
                        HP_BAR, libtcod.darker_red, cc(COLOR_STATUS_TEXT), HP_BAR_PERCENT)
        self.render_bar(1, 2, 13, 10, player.mp, player.base_mp,
                        MP_BAR, libtcod.darker_red, cc(COLOR_STATUS_TEXT), MP_BAR_PERCENT)
        self.render_stats_two_column(1, 3, "AC", player.base_ac, 13, "EVADE", "player.evade", COLOR_STATUS_TEXT,
                                     COLOR_STATUS_VALUES)
        self.render_stats_two_column(1, 4, "Str", "str", 13, "To", "tough", COLOR_STATUS_TEXT, COLOR_STATUS_VALUES)
        self.render_stats_two_column(1, 5, "Dex", "des", 13, "Int", "int", COLOR_STATUS_TEXT, COLOR_STATUS_VALUES)
        self.render_stats_two_column(1, 6, "XL", player.xl, 13, "EXP", "%d/%d" % (player.xp, util.xp_for_lvl(player.xl))
                                     , COLOR_STATUS_TEXT, COLOR_STATUS_VALUES)
        self.render_stats_two_column(1, 7, "Turns", gl.__turn_count__, 13, "", "", COLOR_STATUS_TEXT, COLOR_STATUS_VALUES)
        #blit the contents of "panel" to the root console
        libtcod.console_blit(self.panel, 0, 0, RIGHT_PANEL_WIDTH, RIGHT_PANEL_HEIGHT, 0, RIGHT_PANEL_X, 0)

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

    def render_stats_two_column(self, x, y, text1, value, x2, text2, value2, lbl_color, value_color):
        libtcod.console_set_foreground_color(self.panel, self.create_color(lbl_color))
        libtcod.console_print_left(self.panel, x, y, libtcod.BKGND_NONE, text1 + ':')
        libtcod.console_print_left(self.panel, x2, y, libtcod.BKGND_NONE, text2 + ':')
        libtcod.console_set_foreground_color(self.panel, self.create_color(value_color))
        libtcod.console_print_left(self.panel, x + len(text1) + 1, y, libtcod.BKGND_NONE, str(value))
        libtcod.console_print_left(self.panel, x2 + len(text2) + 1, y, libtcod.BKGND_NONE, str(value2))

    def render_intro(self, intro_text):
        libtcod.console_print_center(self.con2, SCREEN_WIDTH / 3, (SCREEN_HEIGHT /3) , libtcod.BKGND_ADD, intro_text)
        # do a cross-fading from off1 to off2
        for i in range(1, 110):
            libtcod.console_blit(self.con, 0, 0, VIEWPORT_WIDTH, VIEWPORT_HEIGHT, 0, 0, 0) # renders the first screen (opaque)
            libtcod.console_blit(self.con2, 0, 0, VIEWPORT_WIDTH, VIEWPORT_HEIGHT, 0, 0, 0, i / 128.0,
                                 i / 128.0) # renders the second screen (transparent)
            libtcod.console_flush()
        libtcod.console_wait_for_keypress(True)
        for i in range(1, 128):
            libtcod.console_blit(self.con2, 0, 0, VIEWPORT_WIDTH, VIEWPORT_HEIGHT, 0, 0, 0) # renders the first screen (opaque)
            libtcod.console_blit(self.con, 0, 0, VIEWPORT_WIDTH, VIEWPORT_HEIGHT, 0, 0, 0, i / 128.0,
                                 i / 128.0) # renders the second screen (transparent)

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
        if isinstance(color, libtcod.Color):
            return color
        if not parsed_colors.get(color):
            parsed_colors[color] = libtcod.Color(*color)
        return parsed_colors[color]

    def window_closed(self):
        return libtcod.console_is_window_closed()


    def render_dialog(self, title):
        libtcod.console_set_keyboard_repeat(1000, 500)
        libtcod.console_print_frame(self.con, 10, 10, 30, 3, True, libtcod.BKGND_NONE, title)
        line = ''
        while True:
            libtcod.console_print_left(self.con, 11, 11, libtcod.BKGND_NONE, ' '.rjust(len(line) + 2, ' '))
            libtcod.console_print_left(self.con, 11, 11, libtcod.BKGND_NONE, line + '_')
            libtcod.console_blit(self.con, 10, 10, 30, 3, 0, 10, 10)
            libtcod.console_flush()
            key = libtcod.console_wait_for_keypress(True)
            if key.c == 27:
                game_input.default_rate()
                return None
            if key.c == 13:
                game_input.default_rate()
                return line
            if key.c == 8:
                line = line[0:len(line) - 1]
            elif key.c != 0:
                line += chr(key.c)

    def clear_screen(self):
        libtcod.console_clear(self.con)

class Viewport(object):
    def __init__(self, w, h, map):
        self.w, self.h, self.map = w, h, map
        self.center = (w /2, h /2)
        self.x, self.y = 0, 0
        self.x2, self.y2 = w-1, h-1

    def update_coords(self, playerx, playery):
        self.x = util.cap_lower(playerx - self.center[0], 0, 0)
        self.y = util.cap_lower(playery - self.center[1], 0, 0)
        self.x2 = util.cap(self.x + self.w - 1, self.map.width)
        self.y2 = util.cap(self.y + self.h - 1, self.map.height)

    def adjust_coords(self, x, y):
        return x - self.x, y - self.y

    def in_view(self, x, y):
        return x>=self.x  and x<self.x2 and y >= self.y and y < self.y2


def dim_color(color):
    if isinstance(color, tuple):
        color = libtcod.Color(*color)
    h, s, v = libtcod.color_get_hsv(color)
    # 1.0 .. 0.2
    s *= 0.25
    # 1.0 .. 0.75
    v *= 0.25
    color2 = libtcod.Color(color.r, color.g, color.b)
    libtcod.color_set_hsv(color2, h, s, v)
    return color2
