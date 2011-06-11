mNPC = []
traders = []
quest_givers = []
#unique npcs
uniques = set()

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

good_npc_names = []
bad_npc_names = []
demon_npc_names = []
deity_npc_names = []
#to ensure uniqueness
cities_names = {}
""" Stores already generated quest items (artefact and general items together"""
generated_quest_items = {}

