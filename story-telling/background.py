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
import util
import world


class LambdaMap(dict):
    def __getitem__(self, y):
        item = super(LambdaMap, self).__getitem__(y)
        if inspect.isfunction(item):
            return item()
        else:
            return item

born = """You was born in ${birth_village}. You spent your childhood laying under beautifull trees, watching others fight every day.
    You was left by your parents in a dark cave near ${birth_city}. Fortunatly ${name} found you.
    You was sixth son in a big family. When you was 10 an awfull hurricane destroyed your village, leaving you as the only survivor. You wandered around the country for some time and was later adopted by ${good_npc} - $profession.
    Your father left home seeking for some mystic treasure soon after your birth. Later he was foun dead in deep caverns near ${city}. A ${adjective} amulet ${artifact_amulet} was found near his corpse, but no one wish to touch it.
    You never knew neither your parents nor your home. You was raised by gypsies and was forced to do all the hard work.
    Hidden in dark forest your home ${birth_village} was home to all sort outcasts. Not neccessary to say that your life here was not easy.
    Blue fires of inferno burn those who dare to come close to ${birth_village} of $adjective fire. This terrible place is your home.
    Unaware adventurer can occasionaly slip on slick slope and find himself surrounded by strange creatures dwelling in caves of ${village}. Though they don't possess a direct threat, they treat human beings as their own child despite of human's age. That's how your story begins.
    In the deep halls of mountain $birth_city humans and hobbits and dwarves live hand by hand since the world creation. You are realy luky to have born is such a piecfull place.
    From the depth of lake $village comes a dim light which can be seen dark nights. Deep beneath silent waters of lake there is a hidden city of ${birth_city}. City opens it doors to noone but rare guests form ${city}. In a small house ${profession}'s wife gave a birth to a boy: to you.
    Floating rocks surround the city of $Adjective ${Noun}: ${birth_city}. No one is allowed to pass through the gates. Those who dare to sneak in are squashed by floating boulders. City itself is a miserable place, ruled by ${enemy} it began to degrade long time ago. Not a surprise that your childhood there was not easy.
    Surrounded by erupppting volcanoes city of $Noun is unassailable fortress ruled by mighty ${name}. Mighty heroes and powerfull mages all around the realm of $Adjective $Noun are all born in ${birth_city}, as well as you.
    High in the mountains hidden in clouds lies the city ${city}. Once a glorious capital of ${Adjective}${noun} it lies in ruins now. Endless civil wars almost destroyed the city. Trying to escape the horrors of war your family moved to a ${birth_village}, where they gave birth to you."""

fillers = """At the age of $age you face your first enemy - $demon_npc - minor demon tried to draw your blood. Constant combats with bands of thugs made you unbelievably strong.
From an early age you find yourself constantly involved in all kind of troubles.
You was captured by slave-traders, but somehow you managed to escape alive.
Throughout your childhood you had to fight with outnumbering thugs, defending your life. Now deep scars remind you of this battles.
It's impossible to kill invulnerable enemy - that's a lesson you've learned one day. Thanks god, you managed to survive... unlike your friends.
Lock-picking and pick-pocketing made you life careless... for a shirt period of time. One day plate-covered warrior appeared before you naming himself $name and claiming that he's after justice and blah-blah-blah. Until that moment you didn't know you can run that fast.
At the age of $age you somehow you managed to enter $Adjective ${noun}: a cruel band which threatened all the surrounding villages and cities of ${city}. You left bad company soon, to make your own. So you moved to ${city} of ${Adjective}, but was charmed by it's lifestyle so that you completly forgotten your ideas to bring death to the city.
After finishing the school you came to $city where you was employed as ${profession}. All the moneys you've earned you have donated to ${deity_npc} the god of $skill. Finally you realized that diety has no interest in your donations, though priests do. Finally you left the city and began wandering around.
Hardworking employee is valued by his employers, but you was to lazy to work at all. You've read a lot of books and decided that life of a "sea wolf" is just for you. But you was too lazy even to gather your own crew or get your own ship.
Perfect at almost everything you was bad at communicating with others. Now you have no friends. Good news you are so perfect - you don't have enemies as well.
When you was $age you met a powerfull wizard $enemy who was well known for his nasty temper. He promised to teach you the art of magic, but he turned out to be an acolyte of ${demon_npc} the greater demon. Actualy his plan was to capture you and... who knows what's next. Anyway, you have managed to cheat him and escape.
After spending two years in prison for stealing few coins you gave a promise to yourself to live in accordance to laws. That's the path you have chosen.
Once you went into the woods and was not able to find your way back. However, you met a man who taught you how to understand the language of trees and forest itself, how to use the power of the wood. That knowledge was of great assistance throughout your life."""
teachers = """At the age of $age you joined the faction $Adjective $noun as a ${profession}.
    When you was $age $name from $Adjective $Noun made you his apprentice. After $age years you mastered the art of ${skill}. Later your teacher was killed under suspicious circumstances, and without having any practice you've lost most of your skills.
    Seeking for knowledge you finaly came to $name an old $profession who taught you everything he knew. Seeing that an old man has nothing more to give you you murdered him without a hessitation.
    After returning to your home-town you came to $name and asked him to teach you the art of ${skill}. After $age years of study you left for $depart_city where lives $npc the $Adjective $profession in order to ask him to teach you. But you never managed to find him.
    When you was $age a wandering $profession came to ${city}, where you met him. Twice you asked him to teach you the art of $skill and twice he refused. Then you have collected some money to pay for your education, but was not able to find neither $npc nor any other appropriate teacher.
    After you was thrown to jail for stealing few gold pieces from a noble $npc the $Noun you met $name an adept of $Adjective $name the $deity_npc devoted to $skill. He taught you everything he knew himself.
    At the age of $age you met $bad_npc the fallen king of $city who claimed that he is a powerfull wizard. He asked you to help him to get his trone back, offering his knowledge in exchange. Old rapscallion stole your cash and you was never able to find him.
    One day you met $good_npc in the pub, who turned out to be well-known $profession. He invited you to join him on his journey to $depart_city and you agreed. During your voyage you have met a lot of people and gained some knowledge of ${skill}.
    One day you was gathering herbs in a forest near $city when suddenly a strange mist enveloped you. When the mist gone you found yourself in the elven village of $depart_village. There you met $good_npc who taught you the art of ${skill}.
    At the age of $age you visited a town of $city. You drank a water from legendary $adjective fountain and surprissingly the knowledge of $skill came to you. Thus you became known as ${Adjective}${noun}.
    The city of $city is well known for its schools, where everyone can learn $skill. You entered the school $name and after $age years you left for $depart_city to practice your skills.
    Sky-city is known among fellow adventurers as a place where leaves $good_npc the high master of ${skill}. You was the one who managed to persuade him to teach you.
    Wandering around endless wastes of ${Adjective}${noun} one can meet a strange person covered in fur. Once he was a famous ${profession}. But now he sell his secrets to anyone in exchange for food. Accidently you met him in your way to $depart_village and bought several secrets of his art."""
adjectives_def = """glowing
    burning
    hellish
    ametyst
    red
    bone
    scorched
    sorcerous
    sulphurous
    demonic
    ancient
    primitive
    chaotic
    corroded
    frozen
    distant
    dying
    dull
    ivory
    turquoise
    jade
    steel
    amber
    flickering
    glittering
    smoking
    shimmering
    warped
    transparent
    pitted
    runed
    steaming
    sparkling
    crystal
    bloodstained
    iron"""

nouns_def = """moon
    torment
    sun
    turtle
    secrets
    suspicion
    mistrust
    jealousy
    regrets
    doubts
    rock
    stone
    nightmare
    realm
    tree
    palm
    hand
    esteem
    favour
    hope
    approval
    delight
    pride
    generosity
    supremacy
    benevolence"""

professions_def = """mason
advocat
metalsmith
wizard
healer
mage
summoner
bowman
alchemist
bard
hunter
assassin
crusader
"""
skills_def = """magic
thievery
necromancy
medicine
alchemy
chemistry
charms
hexes
translocations
summoning
divinations
conjuration
transmutation
"""


adjectives = map(lambda x: x.strip() , adjectives_def.splitlines())
nouns = map(lambda x: x.strip() , nouns_def.splitlines())
professions = map(lambda x: x.strip() , professions_def.splitlines())
skills = map(lambda x: x.strip() , skills_def.splitlines())
random.shuffle(adjectives)
random.shuffle(nouns)
random.shuffle(professions)
random.shuffle(skills)

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
    parts = []
    for part in (born, fillers, teachers):
        phraselist = map(lambda x: x.strip(), part.splitlines())
        random.shuffle(phraselist)
        parts.append(phraselist)
    output = chain(*islice(izip(*parts), 0, 1))
    result = textwrap.fill(' '.join(output),80)
    return process_string(result)
