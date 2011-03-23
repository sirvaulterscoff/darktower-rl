class DungeonFeature(object):
    def __init__(self, char, color):
        self.char = char
        self.color = color

FT_FIXED_WALL = DungeonFeature('#', [128, 128, 128])
FT_ROCK_WALL = DungeonFeature("#", [128, 128, 128])
FT_GLASS_WALL = DungeonFeature("|", [0, 16, 1])
FT_FLOOR = DungeonFeature(" ", [0, 0, 0])