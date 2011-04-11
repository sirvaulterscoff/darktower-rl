import game_input
import gl
import thirdparty.libtcod.libtcodpy as libtcod
from features import  *
import util

SCREEN_WIDTH = 80
SCREEN_HEIGHT = 50
LIMIT_FPS = 20

MSG_PANEL_HEIGHT = gl.MSG_COUNT
MSG_PANEL_Y = SCREEN_HEIGHT - MSG_PANEL_HEIGHT

RIGHT_PANEL_WIDTH = 40
RIGHT_PANEL_X = SCREEN_WIDTH - RIGHT_PANEL_WIDTH
RIGHT_PANEL_HEIGHT = SCREEN_HEIGHT - MSG_PANEL_HEIGHT


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
        self.con = libtcod.console_new(SCREEN_WIDTH, SCREEN_HEIGHT)
        self.con2 = libtcod.console_new(SCREEN_WIDTH, SCREEN_HEIGHT)
        self.panel = libtcod.console_new(RIGHT_PANEL_WIDTH, SCREEN_HEIGHT)
        self.panel_msg = libtcod.console_new(SCREEN_WIDTH, MSG_PANEL_HEIGHT)
        self.message_colours[0] = libtcod.Color(128,128,128)
        self.message_colours[1] = libtcod.Color(200,200,200)
        self.message_colours[2] = libtcod.Color(128,10,10)
        self.message_colours[3] = libtcod.Color(255,10,10)
        self.message_colours[4] = libtcod.Color(255,255,255)


    def print_critter(self, x, y, char):
        libtcod.console_print_left(self.con, x, y, libtcod.BKGND_NONE, char)


    def clear_critter(self, x, y):
        libtcod.console_print_left(self.con, x, y, libtcod.BKGND_NONE, ' ')


    def render_map(self, map, player):
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
            if libtcod.map_is_in_fov(map.fov_map, critter.x, critter.y) or gl.__wizard_mode__:
                libtcod.console_set_foreground_color(self.con, self.create_color(critter.color))
                self.print_critter(critter.x, critter.y, critter.char)
                critter.last_seen_at = critter.x, critter.y
            elif critter.last_seen_at is not None:
                color = self.create_color(critter.color)
                color = self.dim_color(color)
                libtcod.console_set_foreground_color(self.con, color)
                self.print_critter(critter.x, critter.y, critter.char)

        libtcod.console_set_foreground_color(self.con, self.create_color(player.color))
        self.print_critter(player.x, player.y, player.char)

        if gl.__wizard_mode__:
            libtcod.console_print_left(self.con, 0, 0, libtcod.BKGND_NONE, 'WIZ MODE')
        libtcod.console_blit(self.con, 0, 0, SCREEN_WIDTH, SCREEN_HEIGHT, 0, 0, 0)
        libtcod.console_flush()

    def render_ui(self, player):
        #prepare to render the GUI panel
        libtcod.console_set_background_color(self.panel, libtcod.black)
        libtcod.console_clear(self.panel)
        #show the player's HP
        self.render_bar(1, 1, 13, 10, player.hp, player.base_hp,
                        HP_BAR, libtcod.darker_red, self.create_color(COLOR_STATUS_TEXT), HP_BAR_PERCENT)
        self.render_bar(1, 2, 13, 10, player.mp, player.base_mp,
                        MP_BAR, libtcod.darker_red, self.create_color(COLOR_STATUS_TEXT), MP_BAR_PERCENT)
        self.render_stats_two_column(1, 3, "AC", player.base_ac, 13, "EVADE", "player.evade", COLOR_STATUS_TEXT,
                                     COLOR_STATUS_VALUES)
        self.render_stats_two_column(1, 4, "Str", "str", 13, "To", "tough", COLOR_STATUS_TEXT, COLOR_STATUS_VALUES)
        self.render_stats_two_column(1, 5, "Dex", "des", 13, "Int", "int", COLOR_STATUS_TEXT, COLOR_STATUS_VALUES)
        self.render_stats_two_column(1, 6, "XL", player.xl, 13, "EXP", "%d/%d" % (player.xp, util.xp_for_lvl(player.xl))
                                     , COLOR_STATUS_TEXT, COLOR_STATUS_VALUES)
        #blit the contents of "panel" to the root console
        libtcod.console_blit(self.panel, 0, 0, RIGHT_PANEL_WIDTH, RIGHT_PANEL_HEIGHT, 0, RIGHT_PANEL_X, 0)

        #print the game messages, one line at a time
        y = 0
        for (line, level) in gl.__msgs__:
            if level < 1 and not gl.__wizard_mode__:
                continue
            libtcod.console_set_foreground_color(self.panel_msg, self.message_colours.get(level, libtcod.white))
            libtcod.console_print_left(self.panel_msg, 0, y, libtcod.BKGND_NONE, line.ljust(SCREEN_WIDTH, ' '))
            y += 1
        libtcod.console_blit(self.panel_msg, 0, 0, SCREEN_WIDTH, MSG_PANEL_HEIGHT, 0, 0, MSG_PANEL_Y )
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
            libtcod.console_blit(self.con, 0, 0, 80, 50, 0, 0, 0) # renders the first screen (opaque)
            libtcod.console_blit(self.con2, 0, 0, 80, 50, 0, 0, 0, i / 128.0,
                                 i / 128.0) # renders the second screen (transparent)
            libtcod.console_flush()
        libtcod.console_wait_for_keypress(True)
        for i in range(1, 128):
            libtcod.console_blit(self.con2, 0, 0, 80, 50, 0, 0, 0) # renders the first screen (opaque)
            libtcod.console_blit(self.con, 0, 0, 80, 50, 0, 0, 0, i / 128.0,
                                 i / 128.0) # renders the second screen (transparent)
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
            x, y = x + 1, 0


    def create_color(self, color):
        return libtcod.Color(color[0], color[1], color[2])

    def window_closed(self):
        return libtcod.console_is_window_closed()

    def dim_color(self, color):
        h, s, v = libtcod.color_get_hsv(color)
        # 1.0 .. 0.2
        s *= 0.25
        # 1.0 .. 0.75
        v *= 0.25
        color2 = libtcod.Color(color.r, color.g, color.b)
        libtcod.color_set_hsv(color2, h, s, v)
        return color2

    def render_dialog(self, title):
        libtcod.console_print_frame(self.con, 10, 10, 30, 3, True, libtcod.BKGND_NONE, title)
        line = ''
        while True:
            libtcod.console_print_left(self.con, 11, 11, libtcod.BKGND_NONE, ' '.rjust(len(line) + 2, ' '))
            libtcod.console_print_left(self.con, 11, 11, libtcod.BKGND_NONE, line + '_')
            libtcod.console_blit(self.con, 10, 10, 30, 3, 0, 10, 10)
            libtcod.console_flush()
            key = libtcod.console_wait_for_keypress(False)
            if key.c == 27:
                return None
            if key.c == 13:
                return line
            if key.c == 8:
                line = line[0:len(line) - 1]
            elif key.c != 0:
                line += chr(key.c)

    def clear_screen(self):
        libtcod.console_clear(self.con)

