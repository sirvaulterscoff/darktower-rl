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
		libtcod.console_set_custom_font('fonts/arial10x10.png', libtcod.FONT_TYPE_GREYSCALE | libtcod.FONT_LAYOUT_TCOD)
		libtcod.console_init_root(SCREEN_WIDTH, SCREEN_HEIGHT, 'darktower-rl', False)
		self.con = libtcod.console_new(SCREEN_WIDTH, SCREEN_HEIGHT)

	def print_critter(self, cur_pos_x, cur_pos_y, char):
		libtcod.console_print_left(self.con, cur_pos_x, cur_pos_y, libtcod.BKGND_NONE, char)

	def clear_critter(self, cur_pos_x, cur_pos_y):
		libtcod.console_print_left(self.con, cur_pos_x, cur_pos_y, libtcod.BKGND_NONE, ' ')

	def init_fov(self, map):
		self.fov_map = libtcod.map_new(map.map_width, map.map_height)
		for y in range(map.map_height):
			for x in range(map.map_width):
				libtcod.map_set_properties(self.fov_map, x, y, not map.map[y][x].flags & BLOCK_LOS, not map.map[y][x].flags & BLOCK_WALK)

	def main_loop(self, critters, map):

		for y in range(map.map_height):
			for x in range(map.map_width):
				seen = map.map[y][x].seen | gl.__wizard_mode__
				visible = libtcod.map_is_in_fov(self.fov_map, x, y)
				if seen or visible:
					libtcod.console_print_left(self.con, x, y, libtcod.BKGND_NONE, map.map[y][x].char)
				if not visible:
					if seen:
						libtcod.console_set_fore(self.con, x, y, self.create_color(map.map[y][x].dim_color))
						libtcod.console_set_back(self.con, x, y, self.create_color(map.map[y][x].dim_color_back), libtcod.BKGND_SET)
				else:
					libtcod.console_set_fore(self.con, x, y, self.create_color(map.map[y][x].color))
					libtcod.console_set_back(self.con, x, y, self.create_color(map.map[y][x].color_back), libtcod.BKGND_SET)
					map.map[y][x].seen = True

		for critter in critters:
			libtcod.console_set_foreground_color(self.con, self.create_color(critter.color))
			self.print_critter(critter.cur_pos_x, critter.cur_pos_y, critter.char)

		if gl.__wizard_mode__:
			libtcod.console_print_left(self.con, 0, 0, libtcod.BKGND_NONE, 'WIZ MODE')
		libtcod.console_blit(self.con, 0, 0, SCREEN_WIDTH, SCREEN_HEIGHT, 0, 0, 0)
		libtcod.console_flush()

		for critter in critters:
			self.clear_critter(critter.cur_pos_x, critter.cur_pos_y)

	def window_is_active(self):
		return not libtcod.console_is_window_closed()

	def print_map(self, map):
		x, y = 0, 0
		for row in map:
			for item in row:
				self.print_critter(x, y, item.char)
				y += 1
			x, y = x+1,0

	def create_color(self, color):
		return libtcod.Color(color[0], color[1], color[2])
