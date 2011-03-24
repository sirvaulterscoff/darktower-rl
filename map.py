from thirdparty.libtcod import libtcodpy as libtcod

class Map(object):
	def __init__(self, map_src):
		self.map = map_src
		self.map_height = len(map_src)
		self.map_width = len(map_src[0])
