from __builtin__ import max
import game_input
import gl
import thirdparty.libtcod.libtcodpy as libtcod
from features import  *
import util
from string import  ascii_letters, digits
import rlfl

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
BLACK = (0,0,0)
valid_inventory_chars = ascii_letters + digits
class AbstractGui(object):
    def __init__(self):
        pass

    def main_loop(self, critters, map):
        pass


class LibtcodGui(AbstractGui):
    message_colours = {}
    def __init__(self):
        self.key = libtcod.Key()
        self.mouse = libtcod.Mouse()
        libtcod.console_set_custom_font('data/fonts/BrogueFont3.png',
                                        libtcod.FONT_TYPE_GREYSCALE | libtcod.FONT_LAYOUT_ASCII_INROW)
        libtcod.console_init_root(SCREEN_WIDTH, SCREEN_HEIGHT, 'darktower-rl', False, renderer=libtcod.RENDERER_OPENGL)
        self.con = libtcod.console_new(VIEWPORT_WIDTH, VIEWPORT_HEIGHT)
        self.con2 = libtcod.console_new(VIEWPORT_WIDTH, VIEWPORT_HEIGHT)
        self.panel = libtcod.console_new(RIGHT_PANEL_WIDTH, SCREEN_HEIGHT)
        self.panel_msg = libtcod.console_new(SCREEN_WIDTH, MSG_PANEL_HEIGHT)
        self.con_full = libtcod.console_new(SCREEN_WIDTH, SCREEN_HEIGHT)
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


    def render_map(self, map, player):
        #todo optimize (see http://umbrarumregnum.110mb.com/cookbook/node/24)
        if not self.viewport:
            self.viewport = Viewport(VIEWPORT_WIDTH, VIEWPORT_HEIGHT, map)
        if gl.__fov_recompute__:
            gl.logger.debug('Recomputing fov')
            gl.__fov_recompute__ = False
            map.recompute_fov()

        consolex, consoley, xx = 0,0, 0
        self.viewport.update_coords(player.x, player.y)
        gl.logger.debug('Diplaying viewport from %d:%d to %d:%d' % (self.viewport.x, self.viewport.y, self.viewport.x2, self.viewport.y2))
        buffer = libtcod.ConsoleBuffer(VIEWPORT_WIDTH, VIEWPORT_HEIGHT)
        for y in xrange(self.viewport.y, self.viewport.y2):
            for x in xrange(self.viewport.x, self.viewport.x2):

                tile = map.tile_at(x, y)
                if not tile:
                    consolex += 1
                    continue
                xy = (x, y)
                seen = rlfl.has_flag(map.current.fov_map0, xy, rlfl.CELL_MEMO) | gl.__wizard_mode__
                #                visible = libtcod.map_is_in_fov(map.current.fov_map, x, y)
                visible = rlfl.has_flag(map.current.fov_map0, xy, rlfl.CELL_SEEN)
                del xy
                #if tile is seen or visible to player - print it
                char = None
                if seen or visible:
                    if tile.items and len(tile.items):
                        char = tile.items[-1].char
                    else:
                        char = tile.char
                    #                    libtcod.console_set_char(self.con, consolex, consoley, char)
                    #if it's not in LOS, but seen - print in dim color
                else:
                    char = ' '
                fc = tile.dim_color
                bc = None
                if not visible and not seen:
                    bc = BLACK
                else:
                    #if it's in LOS - print
                    fc = tile.color
                    if tile.items and len(tile.items) > 1:
                        bc = libtcod.desaturated_yellow
                    else:
                        bc = tile.color_back
                buffer.set(consolex, consoley, bc[0], bc[1], bc[2], fc[0], fc[1], fc[2], char)
                consolex += 1
            xx = consolex
            consolex = 0
            consoley += 1

        gl.logger.debug('Printing critters')
        for critter in map.critters:
            if not self.viewport.in_view(critter.x, critter.y):
                continue
            if critter.last_seen_at and not self.viewport.in_view(*critter.last_seen_at):
                continue
            fc = critter.color
            x, y = self.viewport.adjust_coords(critter.x, critter.y)
            if rlfl.has_flag(map.current.fov_map0, (critter.x, critter.y), rlfl.CELL_SEEN) or gl.__wizard_mode__:
                critter.last_seen_at = critter.x, critter.y
                buffer.set_fore(x, y, fc[0], fc[1], fc[2], critter.char)
            elif critter.last_seen_at is not None:
                color = dim_color(critter.color)
                fc = color
                buffer.set_fore(x, y, fc[0], fc[1], fc[2], critter.char)

        gl.logger.debug('Printing player')
        x, y = self.viewport.adjust_coords(player.x, player.y)
        buffer.set_fore(x, y, player.color[0], player.color[1], player.color[2], player.char)
        tile = map.tile_at(player.x, player.y)
        if tile.color_back > (200, 200, 200):
            buffer.set_back(x, y, 200, 200, 200)

        if gl.__wizard_mode__:
            libtcod.console_print(self.con, 0, VIEWPORT_HEIGHT - 1, 'WIZ MODE')

        for x in xrange(0, VIEWPORT_WIDTH):
            for y in xrange(0, VIEWPORT_HEIGHT):
                if x >= xx:
                    buffer.set_fore(x, y, 0, 0, 0, ' ')

        if gl.__lookmode__:
            buffer.set_back(self.viewport.look_x - self.viewport.x, self.viewport.look_y - self.viewport.y, 255, 255, 255)
        buffer.blit(self.con)
        libtcod.console_blit(self.con, 0, 0, VIEWPORT_WIDTH, VIEWPORT_HEIGHT, 0, 0, 0)
        libtcod.console_flush()


    def toggle_lookmode(self):
        if not self.viewport:
            raise RuntimeError('No viewport')
        self.viewport.look_x, self.viewport.look_y = self.viewport.playerxy
        libtcod.console_clear(self.panel_msg)

    def clear_critter(self, x, y):
        libtcod.console_set_char(self.con, x, y, ' ')

    def render_messages(self, map, player):
        if gl.__lookmode__:
            self.render_tile_description(map, player)
            libtcod.console_blit(self.panel_msg, 0, 0, SCREEN_WIDTH, MSG_PANEL_HEIGHT, 0, 0, MSG_PANEL_Y)
            return
        #print the game messages, one line at a time
        y = 0
        for (line, level) in gl.__msgs__:
            if level < 1 and not gl.__wizard_mode__:
                continue
            libtcod.console_set_default_foreground(self.panel_msg, self.message_colours.get(level, libtcod.white))
            libtcod.console_print(self.panel_msg, 0, y, line.ljust(SCREEN_WIDTH, ' '))
            y += 1
        libtcod.console_blit(self.panel_msg, 0, 0, SCREEN_WIDTH, MSG_PANEL_HEIGHT, 0, 0, MSG_PANEL_Y)

    def render_tile_description(self, map, player):
        libtcod.console_clear(self.panel_msg)
        _x, _y = self.viewport.look_x, self.viewport.look_y
        if (_x, _y) == self.viewport.playerxy:
            #starting point of view
            libtcod.console_set_default_foreground(self.panel_msg, libtcod.white)
            libtcod.console_print(self.panel_msg, 0, 0, 'Look-around mode. Use keys to move cursor'.ljust(SCREEN_WIDTH, ' '))
        else:
            visible = rlfl.has_flag(map.current.fov_map0, (_x, _y), rlfl.CELL_MEMO)
            if not visible:
                libtcod.console_set_default_foreground(self.panel_msg, libtcod.white)
                libtcod.console_print(self.panel_msg, 0, 0, 'You can\'t see this far'.ljust(SCREEN_WIDTH, ' '))
                return

            result = ''
            crit = map.critter_at(_x, _y)
            if crit:
                result += 'You see ' + crit.name + '.\n'
            tile_at = map.tile_at(_x, _y)
            result += tile_at.get_view_description()
            result += 'Press e to examine'
            libtcod.console_set_default_foreground(self.panel_msg, libtcod.white)
            libtcod.console_print(self.panel_msg, 0, 0, result.ljust(SCREEN_WIDTH, ' '))

    def handle_lookaround(self, dx, dy, map):
        self.viewport.look_x+= dx
        self.viewport.look_y += dy

    def render_ui(self, player):
        cc = self.create_color
        #prepare to render the GUI panel
        libtcod.console_set_default_background(self.panel, libtcod.black)
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
        #this is totaly incorrect! should be total_width/maximum instead
        tick_price = 0.0
        tick_price = float(total_width) / float(maximum)

        libtcod.console_set_default_background(self.panel, dim_color)
        formated_str = "HP: %i/%i" % (value, maximum)
        #if displayed value == 0 - skip rendering bar
        if not maximum:
            return
        libtcod.console_set_default_foreground(self.panel, text_color)
        libtcod.console_print(self.panel, x, y, formated_str)
        libtcod.console_set_default_foreground(self.panel, self.create_color(bar_color[0]))
        libtcod.console_print(self.panel, x2, y, '[' + ''.ljust(total_width, '_') + ']')
        active_ticks = min(int(value * tick_price), total_width)
        severity = 0
        #now choose apropriate color depending on how much value left (compared to maximum)
        for color_lvl in color_lvls:
            if active_ticks <= maximum * color_lvl:
                severity += 1
        #now render the bar on top
        libtcod.console_set_default_foreground(self.panel, self.create_color(bar_color[severity]))
        libtcod.console_print(self.panel, x2 + 1 ,y, '#'.center(active_ticks, '#'))

    def render_stats_two_column(self, x, y, text1, value, x2, text2, value2, lbl_color, value_color):
        libtcod.console_set_default_foreground(self.panel, self.create_color(lbl_color))
        libtcod.console_print(self.panel, x, y, text1 + ':')
        libtcod.console_print(self.panel, x2, y, text2 + ':')
        libtcod.console_set_default_foreground(self.panel, self.create_color(value_color))
        libtcod.console_print(self.panel, x + len(text1) + 1, y, str(value))
        libtcod.console_print(self.panel, x2 + len(text2) + 1, y,str(value2))

    def render_intro(self, intro_text):
        libtcod.console_print(self.con2, SCREEN_WIDTH / 3, (SCREEN_HEIGHT /3) , intro_text)
        # do a cross-fading from off1 to off2
        for i in range(1, 110):
            libtcod.console_blit(self.con, 0, 0, VIEWPORT_WIDTH, VIEWPORT_HEIGHT, 0, 0, 0) # renders the first screen (opaque)
            libtcod.console_blit(self.con2, 0, 0, VIEWPORT_WIDTH, VIEWPORT_HEIGHT, 0, 0, 0, i / 128.0,
                                 i / 128.0) # renders the second screen (transparent)
            libtcod.console_flush()
        libtcod.sys_check_for_event(libtcod.EVENT_KEY_PRESS, self.key, self.mouse)
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
            libtcod.console_print(self.con, 11, 11, ' '.rjust(len(line) + 2, ' '))
            libtcod.console_print(self.con, 11, 11, line + '_')
            libtcod.console_blit(self.con, 10, 10, 30, 3, 0, 10, 10)
            libtcod.console_flush()
            libtcod.sys_check_for_event(libtcod.EVENT_KEY_PRESS, self.key, self.mouse)
            key = self.key
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

    def render_yn_dialog(self, title, warn=False):
        if warn:
            libtcod.console_set_default_foreground(self.con, libtcod.red)
        else:
            libtcod.console_set_default_foreground(self.con, libtcod.white)
        libtcod.console_set_keyboard_repeat(1000, 500)
        libtcod.console_print_frame(self.con, 10, 10, 30, 3, True, libtcod.BKGND_NONE, title)
        line = ''
        #todo - adjust the size of window to match line's size
        while True:
            libtcod.console_print_ex(self.con, 11, 11, libtcod.BKGND_NONE, libtcod.LEFT, ' '.rjust(len(line) + 2, ' '))
            libtcod.console_print_ex(self.con, 11, 11, libtcod.BKGND_NONE, libtcod.LEFT, line + '_')
            libtcod.console_blit(self.con, 10, 10, 30, 3, 0, 10, 10)
            libtcod.console_flush()
            libtcod.sys_check_for_event(libtcod.KEY_PRESSED, self.key, self.mouse)
            key = self.key
            if chr(key.c) == 'y' or chr(key.c) == 'Y' or key.c == 13:
                game_input.default_rate()
                return True
            if chr(key.c) == 'n' or chr(key.c) == 'N' or key.c == 27:
                game_input.default_rate()
                return False

    def clear_screen(self):
        libtcod.console_clear(self.con)

    def render_examine(self, player, map):
        libtcod.console_clear(self.con_full)
        _x, _y = self.viewport.look_x, self.viewport.look_y
        if (_x, _y) == self.viewport.playerxy:
            #starting point of view
            libtcod.console_set_default_foreground(self.panel_msg, libtcod.white)
            libtcod.console_print(self.con_full, 1, 0, 'This is you'.ljust(SCREEN_WIDTH, ' '))
            libtcod.console_print(self.con_full, 1, 1, 'Press e to go back to look-around mode'.ljust(SCREEN_WIDTH, ' '))
        else:
            visible = rlfl.has_flag(map.current.fov_map0, (_x, _y), rlfl.CELL_MEMO)
            if not visible:
                libtcod.console_set_default_foreground(self.panel_msg, libtcod.white)
                libtcod.console_print(self.con_full, 1, 0, 'You can\'t see this far'.ljust(SCREEN_WIDTH, ' '))
                libtcod.console_print(self.con_full, 1, 1, 'Press e to go back to look-around mode'.ljust(SCREEN_WIDTH, ' '))
                return

            result = ''
            crit = map.critter_at(_x, _y)
            if crit:
                result +=  getattr(crit, 'description_' + player.time)
            tile_at = map.tile_at(_x, _y)
            result += tile_at.get_full_description(player.time)
            result += '\n\nPress e to go back to look-around mode.'
            libtcod.console_set_default_foreground(self.panel_msg, libtcod.white)
            libtcod.console_print(self.con_full, 0, 0, result.ljust(SCREEN_WIDTH, ' '))
            libtcod.console_blit(self.con_full, 0, 0, SCREEN_WIDTH, SCREEN_HEIGHT, 0, 0, 0)
            libtcod.console_flush()

    def render_inventory(self, player, action, handler):
        mapped_items = {}
        key = self._render_inventory(player, action, mapped_items)
        if key:
            return handler(player, mapped_items[key])
        else:
            return None

    def _render_inventory(self, player, action, mapped_items):
        libtcod.console_clear(self.con_full)

        inven = player.get_inventory_categorized()
        y = 1
        letter = ord('a')

        msgs = ScrollList()
        msgs.append(('Select letter to ' + action).center(SCREEN_WIDTH), libtcod.white)
        for category, items in inven.items():
            msgs.append(category + ":", libtcod.dark_han)
            y += 1
            for item in items:
                msgs.append(chr(letter), libtcod.dark_orange, False)
                line =  " - " + item.name
                mapped_items[chr(letter)] = item
                if letter > 122:
                    letter = ord('A')
                msgs.append(line, libtcod.white)
                y += 1
        for x in xrange(120):
            msgs.append('Line ' + str(x), libtcod.white)
        sp = ScrollPane(self.con_full, SCREEN_WIDTH, SCREEN_HEIGHT, msgs)
        sp.render()
        while True:
            key = sp.handle_input()
            if not isinstance(key, str) or key not in valid_inventory_chars:
                return None
            if not key in mapped_items:
                continue #todo maybe we should exit here or give a warning?
            return key


class ScrollList(object):
    def __init__(self):
        self.lines = []
        self.current_line = None

    def append(self, text, color, new_line=True):
        self.text(text)
        self.color(color)
        self.current_line[2] = new_line
        self.next_line()

    def next_line(self):
        self.current_line = None

    def color(self, color):
        self._add_new_line()
        self.current_line[1] = color


    def text(self, text):
        self._add_new_line()
        self.current_line[0] = text

    def no_new_line(self):
        self._add_new_line()
        self.current_line[2] = False

    def _add_new_line(self):
        if self.current_line is None:
            self.current_line = [None] * 3
            self.current_line[2] = True
            self.lines.append(self.current_line)

    def __iter__(self):
        for line in self.lines:
            yield line

    def __len__(self):
        return len(self.lines)

    def __getitem__(self, item):
        return self.lines.__getitem__(item)


class ScrollPane(object):
    def __init__(self, console, width, height, content):
        self.console = console
        self.width = width
        self.height = height
        self.content = content
        self.offset = 0

    def render(self):
        libtcod.console_clear(self.console)
        pages = len(self.content) / (self.height - 2)
        pages += 1 if len(self.content) % (self.height - 2) != 0 else 0
        x = 0
        y = 1
        if self.offset:
            libtcod.console_set_default_foreground(self.console, libtcod.dark_crimson)
            libtcod.console_print(self.console, 0, 0, "---  [-][PgDwn] Scroll up ---" .center(self.width))
        for line, rgb, newline in self.content[self.offset:]:
            libtcod.console_set_default_foreground(self.console, rgb)
            libtcod.console_print(self.console, x, y, line)
            if newline:
                x = 0
                y+= 1
            else:
                x += len(line)
        y = self.height - 1
        if pages > 1:
            libtcod.console_set_default_foreground(self.console, libtcod.dark_crimson)
            footer = "---  [+][PgDwn] Scroll down \t Line [%d]/[%d] ---" % (self.offset, len(self.content))
            libtcod.console_print(self.console, 0, y, footer.center(self.width))

        libtcod.console_blit(self.console, 0, 0, self.width, self.height, 0, 0, 0)
        libtcod.console_flush()

    def handle_input(self):
        while True:
            key = game_input.readkey()
            if key == '+' or key == libtcod.KEY_DOWN:
                self.offset = min(self.offset + 1, len(self.content) - 1)
            elif key == '-' or key == libtcod.KEY_UP:
                self.offset = max(self.offset - 1, 0)
            elif key == libtcod.KEY_PAGEUP:
                self.offset = max(self.offset - self.height, 0)
            elif key == libtcod.KEY_PAGEDOWN or key == ' ':
                self.offset = min(self.offset + self.height, len(self.content) - 1)
            elif key == libtcod.KEY_ESCAPE or key == libtcod.KEY_ENTER:
                break
            else:
                return key
            self.render()


class Viewport(object):
    def __init__(self, w, h, map):
        self.w, self.h, self.map = w, h, map
        self.center = (w /2, h /2)
        self.x, self.y = 0, 0
        self.x2, self.y2 = w-1, h-1
        self.look_x, self.look_y = 0, 0
        self.playerxy = (0, 0)

    def update_coords(self, playerx, playery):
        self.x = util.cap_lower(playerx - self.center[0], 0, 0)
        self.y = util.cap_lower(playery - self.center[1], 0, 0)
        self.x2 = util.cap(self.x + self.w - 1, self.map.width)
        self.y2 = util.cap(self.y + self.h - 1, self.map.height)
        self.playerxy = (playerx, playery)

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
