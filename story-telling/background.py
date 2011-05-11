#typical layout
#born where. filler1, filler2. teacher. bridge
#first we defing born-place (just a random text+random village)
#secondly take two random fillers (you like cats, you hate dogs)
#point to a person (school?) who taught you everything
#add a random bridge between intro and main story,
# like you left for town, you had to leave your village, was kidnapped and managed to escape etc

#examples
# You were born in ${birth_village}. From an early age you find yourself constantly involved in all kind of troubles
# of troubles. At the age of 16 you became an apprentice of __random_name - __random_title_, who taught
# you everything he know himself. Later on you left for a large town, seeking well-paid work
import inspect
from itertools import chain, izip, islice, islice
import random
import string
import textwrap
import world
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
import util

class LambdaMap(dict):
    def __getitem__(self, y):
	item = super(LambdaMap, self).__getitem__(y)
        if inspect.isfunction(item):
            return item()
        else:
            return item
class Background(object):
    pass

#here we substitute names into strings.
#String can refer to following names
# ${name} - random name not in global npc's names list
# ${enemy} - one of bad NPCs you have to beat (antagonist)
# ${adventurer} - just a reference to adventurer
# ${birth_city} or ${birth_village} - remember that one
# ${depart_city} or ${depart_village} - remember and use as starting point
# ${npc} - take name from mnpc list (any)
# ${good_npc} - take name from npc list (good)
# ${bad_npc} - take name from mnpc list (bad)
# ${demon_npc} - take name from mnpc list (demon)
# ${deity_npc} - take name from mnpc list (deity)

#PLEASE NOTE THAT names that refere to npcs are to neccessarily subsituted
#from list of npcs (actualy roll a dice)
# Templates are split in 3 groups. Thus we can assign a name
#from some predefined list to the 1 group - i.e. you can occasionaly visit your home
#town and keep the name from the 3rd group - as it will be departure town
#

def create_enemy():
    name = util.gen_name()
    world.antagonist = name
    return name


def create_adventurer():
    name = util.gen_name(check_unique=world.npc_names)
    world.adventurer_names.append(name)
    return name


def create_city(birth = False, city=False, depart = False):
    name = util.gen_name('city', world.cities_names)
    if birth:
        world.birth_place = name
        if city:
            world.birth_place_rank = util.roll(2, 3, 3)
        else:
            world.birth_place_rank = util.roll(1, 3, 1)
    if depart:
        world.depart_place = name
	world.current_city = name
        if city:
            world.depart_place_rank = util.roll(1, 3, 3)
        else:
            world.depart_place_rank = util.roll(1, 3)
    return name


def create_npc(npc_names, demon = False):
    if not demon:
        name = util.gen_name(check_unique=world.npc_names)
    else:
        name = util.gen_name('demon', check_unique=world.npc_names)
    if npc_names is not None:
        npc_names.append(name)
    return name


current_age = 13
def create_age():
    global current_age
    current_age += random.randrange(1, 10)
    return current_age


def process_string(s):
    substs = LambdaMap()
    result = s.strip()
    #first parse name with random one
    substs['name'] = lambda: util.gen_name()
    substs['enemy'] = lambda: create_enemy()
    substs['adventurer'] = lambda: create_adventurer()
    substs['npc'] = lambda: create_npc(None)
    substs['good_npc'] = lambda: create_npc(world.good_npc_names)
    substs['bad_npc'] = lambda: create_npc(world.bad_npc_names)
    substs['demon_npc'] = lambda: create_npc(world.demon_npc_names, demon=True)
    substs['deity_npc'] = lambda: create_npc(world.deity_npc_names)

    substs['birth_city'] = lambda: create_city(birth=True, city=True)
    substs['birth_village'] = lambda: create_city(birth=True, city=False)
    substs['city'] = lambda: create_city(city=True)
    substs['village'] = lambda: create_city()
    substs['depart_village'] = lambda: create_city(depart=True, city=False)
    substs['depart_city'] = lambda: create_city(depart=True, city=True)

    substs['noun'] = lambda: random.choice(nouns)
    substs['Noun'] = lambda: random.choice(nouns).capitalize()
    substs['Adjective'] = lambda: random.choice(adjectives).capitalize()
    substs['adjective'] = lambda: random.choice(adjectives)

    substs['skill'] = lambda: random.choice(skills)
    substs['Skill'] = lambda: random.choice(skills).capitalize()

    substs['profession'] = lambda: random.choice(professions)
    substs['Profession'] = lambda: random.choice(professions).capitalize()

    substs['age'] = lambda: create_age()

    res = string.Template(s).safe_substitute(substs)
    return res


def make_story():
    background = util.parse_des('background', Background).next()
    parts = []
    for part in (backgroun.born, bacgroun.fillers, bacgroun.teachers):
        phraselist = map(lambda x: x.strip(), part.splitlines())
        random.shuffle(phraselist)
        parts.append(phraselist)
    output = chain(*islice(izip(*parts), 0, 1))
    result = textwrap.fill(' '.join(output),80)
    print result
    return process_string(result)
make_story()

adjectives = map(lambda x: x.strip() , adjectives_def.splitlines())
nouns = map(lambda x: x.strip() , nouns_def.splitlines())
professions = map(lambda x: x.strip() , professions_def.splitlines())
skills = map(lambda x: x.strip() , skills_def.splitlines())

random.shuffle(adjectives)
random.shuffle(nouns)
random.shuffle(professions)
random.shuffle(skills)
