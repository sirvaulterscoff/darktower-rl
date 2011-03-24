import thirdparty.libtcod.libtcodpy as libtcod

class Input(object):
	def __init__(self, player):
		self.player = player

	def handle_keys(self, call_back):
		key = libtcod.console_wait_for_keypress(True)
		if key.vk == libtcod.KEY_ENTER and libtcod.KEY_ALT:
		#Alt+Enter: toggle fullscreen
			libtcod.console_set_fullscreen(not libtcod.console_is_fullscreen())
		elif key.vk == libtcod.KEY_F10:
			return True  #exit game
		#movement keys
		#todo vi keys
		newx, newy = self.player.cur_pos_x, self.player.cur_pos_y
		if libtcod.console_is_key_pressed(libtcod.KEY_UP) or libtcod.console_is_key_pressed(libtcod.KEY_KP8):
			newy -= 1
		elif libtcod.console_is_key_pressed(libtcod.KEY_DOWN) or libtcod.console_is_key_pressed(libtcod.KEY_KP2):
			newy += 1
		elif libtcod.console_is_key_pressed(libtcod.KEY_LEFT) or libtcod.console_is_key_pressed(libtcod.KEY_KP4):
			newx -= 1
		elif libtcod.console_is_key_pressed(libtcod.KEY_RIGHT) or libtcod.console_is_key_pressed(libtcod.KEY_KP6):
			newx += 1
		elif libtcod.console_is_key_pressed(libtcod.KEY_KP1):
			newy += 1
			newx -= 1
		elif libtcod.console_is_key_pressed(libtcod.KEY_KP3):
			newy += 1
			newx += 1
		elif libtcod.console_is_key_pressed(libtcod.KEY_KP7):
			newy -= 1
			newx -= 1
		elif libtcod.console_is_key_pressed(libtcod.KEY_KP9):
			newy -= 1
			newx += 1

		if newx < 0:
			newx = 0
		if newy < 0:
			newy = 0

		if call_back(newx, newy):
			self.player.cur_pos_x, self.player.cur_pos_y = newx, newy
		else:
			print("You bump into wall")
