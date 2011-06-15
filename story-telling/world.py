mNPC = []
traders = []
quest_givers = []
#unique npcs
uniques = set()
deaders = []
king = None
queen = None
#reference in case queen is kidnapped
queen_ref = {}
heirs = []
heirs_kidnapped = {}
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
gen_requests = {}

def require_for_nextgen(what, name=None):
    """ registers a new worldgen request"""
    if not gen_requests.has_key(what):
        gen_requests[what] = []
    gen_requests[what].append(name)

""" Just what you may think about it - year in the game """
year = 1000

class City():
    """City"""
    def __init__(self, name):
        self.denizens = []
        self.deities = []
        self.name = name
        self.king = None
        #nearby cities
        self.city_map = None

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

    def was_killed(self, who):
        global deaders
        try:
            self.denizens.remove(who)
            deaders.append(who)
        except ValueError:
            pass
