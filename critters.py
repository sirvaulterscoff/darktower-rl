import math
import util
from thirdparty.libtcod import libtcodpy as libtcod

WALKING = 1
FLYING = 2
UNDEAD = 1 << 3
COLD_BLOODED = 1 << 4
PASS_THRU_WALLS = 1 << 5
PASS_THRU_DOORS = 1 << 6
INTELLIGENT = 1 << 7

class Critter(object):
	name = 'crit'
	ALL = []
	char = '@'
	color = [255, 255, 255]
	x = 0
	y = 0
	regen_rate = 1
	flags = WALKING
	description_past = 'Generic critter from the past'
	description_present = 'Generic critter from present time'
	description_future = 'Generic critter from distant future'
	base_hd = 1
	base_hp = 1
	speed = 1
	base_ac = 0
	base_dmg = 1
	base_hit_dice = 1, 1
	dlvl = 1
	inven = []
	common = 10
	__metaclass__ = util.AutoAdd
	skip_register = True
	fov_range = 5
	ai = None

	def __init__(self):
		self.map = None
		pass

	def adjust_hd(self, new_hd):
		#TODO implement HD rebasing
		pass

	def place(self, x, y, map):
		self.x, self.y = x, y
		self.map = map

	def move(self, dx, dy):
		newx, newy = self.x + dx, self.y + dy
		if self.map.has_critter_at( (newx, newy)):
			return
		player = self.map.player
		if player.x == newx and player.y == newy:
			self.attack(newx, newy)
			return

		next_tile = self.map[newy][newx]
		if next_tile.passable():
			self.map.critter_xy_cache.pop ( (self.x, self.y))
			self.x, self.y = newx, newy
			self.map.critter_xy_cache[(self.x, self.y)] = self

	def attack(self, newx, newy):
		print (self.name + ' tries to hit you')

	def move_towards(self, target_x, target_y):
		dx = target_x - self.x
		dy = target_y - self.y
		distance = math.sqrt(dx ** 2 + dy ** 2)

		dx = int(round(dx / distance))
		dy = int(round(dy / distance))
		self.move(dx, dy)

	def see_player(self):
		player = self.map.player
		see_range = self.fov_range
		#if it's intelligent one - let it follow source of light
		if self.flags & INTELLIGENT:
			see_range +=  player.fov_range / 2
		if libtcod.map_is_in_fov(self.map.fov_map, self.x, self.y):
			d = util.distance(self.x, self.y, player.x, player.y)
			if d <= see_range:
				return d
		return None

	def take_turn(self):
		if self.ai is None:
			if self.see_player():
				player = self.map.player
				self.move_towards(player.x, player.y)

class Player(Critter):
	x, y = 0, 0
	char = '@'
	color = [255, 255, 255]
	skip_register = True
	fov_range = 10

	def __init__(self):
		self.map = None

	def move(self, dx, dy):
		newx, newy = self.x + dx, self.y + dy
		if self.map.has_critter_at( (newx, newy)):
			self.attack(newx, newy)
			return True
		next_tile = self.map[newy][newx]
		if next_tile.passable():
			self.x, self.y = newx, newy
			return True
		else:
			print("You bump into wall")
		return False

	def attack(self, mobx, moby):
		pass



class Rat(Critter):
	char = 'r'
	name = 'Rat'
	color = [90, 30, 40]
	description_past = 'Obesity makes this plague-bearing rats realy huge. Interesting, can you even kill one that big...'
	description_present = 'Huge, fat rat somehow managed to leave sewers or households and now posess enourmous threat to unwary adventurer.'
	description_future = 'Strange mental-wave-immune creature, you have not seen ever before. According to records in central creature database (CCDB) these should be called rat'
	base_hd = 1
	base_hp = 3
	speed = 2

class Bat(Critter):
	char = 'w'
	name = 'bat'
	flags = FLYING
	color = [0, 255, 60]
	description_past = 'Strange green glow comes from afar... Maybe it\'s a lost sool seeking exit from endless caverns... Wait! It\'s a bat?! Ouch, stop biting me!'
	description_present = 'Tiny bat emmiting a strange green glow, fliting high above the ground. If you can only catch one alive it can become a nice lantern.'
	description_future = 'Flying creature, glowing with strange mutagenic radiation - it would be better if you don\'t touch it'
	base_hd = 1
	base_hp = 3
	base_dmg = 1, 1
	speed = 2
	common = 3

class Orc(Critter):
	char = 'o'
	name = 'orc'
	flags = WALKING | INTELLIGENT
	color = [255, 0, 0]
	description_past = 'Beware! This mighty ugly-looking humanoid will eat you for dinner. Nightmare comes to live. By the way, there should be it\' friends somewhere nearby'
	description_present = 'Surely you have read about orcs (remember all this books, about hobbits, elves and others). This one looks exactly... dissimilary.'
	description_future = 'This creature looks as if it managed to escape from mad-scientist lab, where it was created. Several scars are spread along it\' torso, giving you hint that this creature is not going to chat with you.'
	base_hd = 3
	base_hp = 10
	base_ac = 1
	dlvl = 3
