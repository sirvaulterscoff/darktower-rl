import thirdparty.libtcod.libtcodpy as libtcod

SCREEN_WIDTH = 80
SCREEN_HEIGHT = 50
LIMIT_FPS = 20

class AbstractGui(object):
	def __init__(self):
		pass

	def main_loop(self):
		pass

class LibtcodGui(AbstractGui):
	def __init__(self):
		libtcod.console_set_custom_font('fonts/arial10x10.png', libtcod.FONT_TYPE_GREYSCALE | libtcod.FONT_LAYOUT_TCOD)
		libtcod.console_init_root(SCREEN_WIDTH, SCREEN_HEIGHT, 'python/libtcod tutorial', False)
		self.con = libtcod.console_new(SCREEN_WIDTH, SCREEN_HEIGHT)

	def print_critter(self, cur_pos_x, cur_pos_y, char):
		libtcod.console_print_left(self.con, cur_pos_x, cur_pos_y, libtcod.BKGND_NONE, char)

	def clear_critter(self, cur_pos_x, cur_pos_y):
		libtcod.console_print_left(self.con, cur_pos_x, cur_pos_y, libtcod.BKGND_NONE, ' ')

	def main_loop(self, critters):
		for critter in critters:
			libtcod.console_set_foreground_color(self.con, libtcod.Color(critter.color[0],
																  critter.color[1],
																  critter.color[2]))
			self.print_critter(critter.cur_pos_x, critter.cur_pos_y, critter.char)
		libtcod.console_blit(self.con, 0, 0, SCREEN_WIDTH, SCREEN_HEIGHT, 0, 0, 0)
		libtcod.console_flush()
		for critter in critters:
			self.clear_critter(critter.cur_pos_x, critter.cur_pos_y)
	
	def window_is_active(self):
		return not libtcod.console_is_window_closed()
