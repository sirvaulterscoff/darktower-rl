import sys, os
import random
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
import des
import util
import dungeon_generators

mNPC = []
traders = []
quest_givers = []
#unique npcs
uniques = set()
deaders = []
king = None
royalties = []
royalties_kidnapped = {}
global_quests = []

#global artefacts.
artefacts = []
#global check for artefact unique-ness
artefact_names = {}
#artefacts still available
free_artefacts = []
### =============================
### VARIABLES BELOW are GENERATED DURING BACKGROUN GEN
#The name of the city player was born
birth_place = None
#rank - city or village
birth_place_rank = 1
# one of the evil-npcs from your past. you can occasionly meet em and get your revenge
antagonist = None
#the name of city used as departure (if such scenario is generated)
depart_place = None
#same as birth_place_rank except for depart city
depart_place_rank = 1
#names already used during background generation and can be used during mnpc gen
adventurer_names =[]
#npc's names generated during background-gen stage. just a global set to assure uniqueness
npc_names = {}
#used to store current city name to be refered from quests
current_city = None
#capital of current region
capital = None

good_npc_names = []
bad_npc_names = []
demon_npc_names = []
deity_npc_names = []
#to ensure uniqueness
cities_names = {}
""" Stores already generated quest items (artefact and general items together"""
generated_quest_items = {}
#Stores already generate book names
book_names = {}

#To store rooms that was already generated
unique_rooms = {}
gen_requests = {}
def require_for_nextgen(region, what, name=None, mapgenparm={}, unique=True):
    """ this method is used to issue requests for map_gen for certain features.
    For example a quest needs forest to be generated nearby - it should ask world to generate
    a forest for next map_gen.
    what - denotes a type of feature to be generated
    function returns the holder for requested feature.
    """
    global gen_requests
    target = None
    while True:
        whats = util.parseDes(what, dungeon_generators.MapDef, 'rooms')
        target = random.choice(whats)
        if not unique: break
        if hasattr(target, 'id') and not getattr(target, 'id') in gen_requests.keys():
            break
    request = dungeon_generators.FeatureRequest(target, mapgenparm)
    """ registers a new worldgen request"""
    if not gen_requests.has_key(region):
        gen_requests[region] = {}
    if not gen_requests[region].has_key(what):
        gen_requests[region][what] = []
    gen_requests[region][what].append(request)
    return request

""" Just what you may think about it - year in the game """
year = 1000

BUILT = 1
DESTROYED = 2
class City():
    """City"""
    def __init__(self, name):
        self.denizens = []
        self.deities = []
        self.name = name
        self.king = None
        #nearby cities
        self.city_map = None
        """ if set to NPC - then that NPC unleashed a plague in the city"""
        self.plague_src = None
        self.temples = {}

    def add_denizen(self, npc):
        global year
        self.denizens.append(npc)
        npc.history.append('In year %d %s came to city of %s' % (year, npc.name, self.name))

    def add_deity(self, deity):
        global year
        self.deities.append(deity)
        deity.history.append('In year %d %s became deity of the city of %s' % (year, deity.name, self.name))

    def set_king(self, king):
        global year
        self.king = king
        king.history.append('In year %d the ruler of the realm %s settled in %s' %(year, king.name, self.name))

    def create_temple(self, deity):
        global BUILT
        #util.parseFile("temple", 
        self.temples[deity] = BUILT
        #todo actualy build temple from real .des file
        return BUILT

    def was_killed(self, who):
        global deaders
        if who in self.denizens:
            self.denizens.remove(who)
        deaders.append(who)
def reset():
    mNPC = []
    traders = []
    quest_givers = []
    uniques = set()
    deaders = []
    king = None
    royalties = []
    royalties_kidnapped = {}
    global_quests = []
    artefacts = []
    artefact_names = {}
    free_artefacts = []
    birth_place = None
    birth_place_rank = 1
    antagonist = None
    depart_place = None
    depart_place_rank = 1
    adventurer_names =[]
    npc_names = {}
    current_city = None
    capital = None

    good_npc_names = []
    bad_npc_names = []
    demon_npc_names = []
    deity_npc_names = []
    cities_names = {}
    generated_quest_items = {}
    gen_requests = {}
    book_names = {}
