class Player(object):
	cur_pos_x, cur_pos_y = 0, 0
	char = '@'
	color = [255, 255, 255]

class Critter(Player):
	def __init__(self, char, color, x=0, y=0):
		self.char = char
		self.color = color
		self.cur_pos_x = x
		self.cur_pos_y = y
  