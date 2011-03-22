import libtcodpy as libtcod

class Input(object):
	def __init__(self, player):
		self.player = player

	def handle_keys(self):
		key = libtcod.console_wait_for_keypress(True)
		if key.vk == libtcod.KEY_ENTER and libtcod.KEY_ALT:
			#Alt+Enter: toggle fullscreen
			libtcod.console_set_fullscreen(not libtcod.console_is_fullscreen())
		elif key.vk == libtcod.KEY_F10:
			return True  #exit game
			#movement keys
		if libtcod.console_is_key_pressed(libtcod.KEY_UP):
			self.player.cur_pos_y -= 1

		elif libtcod.console_is_key_pressed(libtcod.KEY_DOWN):
			self.player.cur_pos_y += 1

		elif libtcod.console_is_key_pressed(libtcod.KEY_LEFT):
			self.player.cur_pos_x -= 1

		elif libtcod.console_is_key_pressed(libtcod.KEY_RIGHT):
			self.player.cur_pos_x += 1
