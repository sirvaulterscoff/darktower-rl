import critters
import gl
from thirdparty.libtcod import libtcodpy as libtcod
from random import randrange
import util

class Map(object):
	map_critters = []
	critter_xy_cache = {}

	def __init__(self, map_src):
		self.map = map_src
		self.map_height = len(map_src)
		self.map_width = len(map_src[0])

	def __getitem__(self, item):
		return self.map[item]

	def place_critter(self, crit_level, crit_hd, x, y):
		crit = util.random_by_level(crit_level, critters.Critter.ALL)()
		crit.adjust_hd(crit_hd)
		self.map_critters.append(crit)
		self.critter_xy_cache[(x, y)] = crit
		crit.x, crit.y = x, y

	# basic algo: take player level (xl), and pick random number between xl - 3 and xl + 3.
	# let it be monster HD. Now take random monsters appropirate for this and prev levels (Critter.dlvl <= __dlvl__)
	# set this monster HD to a value defined earlier
	# for OOD monsters - same HD as previous case, and Critter.dlvl <= random(__dlvl__ + 2, __dlvl +3)
	def place_monsters(self):
		#choose random number of monsters
		#3d(dlvl) + 3d2 + 7 monsters total - at least 11 monsters on d1 and up-to 40 on d27
		num_monsters = util.roll(1, gl.__dlvl__, util.roll(3, 2, 7))
		#cap monster generation for now
		num_monsters = util.cap(num_monsters, 30)

		for i in range(num_monsters):
			#choose random spot for this monster
			x,y = self.find_random_square(self.has_critter_at)
			#determining critter level. it may vary from XL - 3 to XL + 3. To let is scale better multiply by 100
			#cap it to be no lower than 1
			crit_hd = util.cap_lower(randrange(gl.__xl__ - 3, gl.__xl__ + 3), 1, 1)
			self.place_critter(gl.__dlvl__, crit_hd, x, y)

		#check for OOD monster. let's create OOD 10% of the time for now
		if libtcod.random_get_int(0, 0, 100) >= 89:
			crit_level = libtcod.random_get_int(0, gl.__dlvl__ + 2, gl.__dlvl__ + 3)
			crit_hd = util.cap_lower(randrange(gl.__xl__ - 3, gl.__xl__ + 3), 1, 1)
			x,y = self.find_random_square(self.has_critter_at)
			self.place_critter(crit_level, crit_hd, x, y)

	def has_critter_at(self, coords):
		return self.critter_xy_cache.__contains__(coords)

	def find_random_square(self, occupied):
		startx = libtcod.random_get_int(0, 1, self.map_width)
		starty = libtcod.random_get_int(0, 1, self.map_height)

		for y in range(starty, self.map_height):
			for x in range(startx, self.map_width):
				if self.map[y][x].passable() and not occupied( (x, y) ):
					return x, y
		#if nothing found - let's try once again
		return self.find_random_square(occupied)

	def can_walk(self, x, y):
		return self.map[y][x].passable() and not self.has_critter_at( (x, y))
