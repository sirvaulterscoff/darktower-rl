BLOCK_WALK = 1
BLOCK_LOS = 2
NONE = 4

def passable(feat):
	return not feat.flags & BLOCK_WALK

class DungeonFeature(object):
	def __init__(self, char, color, dim_color, flags = NONE, is_wall = False):
		self.char = char
		self.color = color
		self.flags = flags
		self.is_wall = is_wall
		self.dim_color = dim_color

FT_FIXED_WALL = DungeonFeature('#', [130, 110, 50], [0, 0, 100], BLOCK_LOS | BLOCK_WALK, True)
FT_ROCK_WALL = DungeonFeature("#", [130, 110, 50], [0, 0, 100], BLOCK_LOS | BLOCK_WALK, True)
FT_GLASS_WALL = DungeonFeature("|", [0, 16, 1], [0, 0, 100], BLOCK_LOS | BLOCK_WALK, True)
FT_FLOOR = DungeonFeature(" ", [200, 180, 50], [50, 50, 150])