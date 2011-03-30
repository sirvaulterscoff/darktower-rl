#typical layout
#born where. filler1, filler2. teacher. bridge
#first we defing born-place (just a random text+random village)
#secondly take two random fillers (you like cats, you hate dogs)
#point to a person (school?) who taught you everything
#add a random bridge between intro and main story,
# like you left for town, you had to leave your village, was kidnapped and managed to escape etc

#examples
# You were born in _random_village_. From an early age you find yourself constantly involved in all kind
# of troubles. At the age of 16 you became an apprentice of __random_name - __random_title_, who taught
# you everything he know himself. Later on you left for a large town, seeking well-paid work
from itertools import chain, izip, islice, islice
import os
import random
import sys
import textwrap
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from thirdparty.libtcod import libtcodpy as libtcod

born = """You were born in __village__. You spent your childhood laying under beautifull trees, watching others fight and day every day.
    You were left by your parents in a dark cave near __city__. Fortunatly __name__ found you.
    You were sixth son in a big family. When you were 10 an awfull hurricane destroyed your village, leaving you as the only survivor. You wandered around the country for some time and was later adopted by __name__ - __proffesion__.
    Your father left home seeking for some mystic treasure soon after your birth. Later he was foun dead in deep caverns near __city__. A __adjective__ amulet was found near his corpse, but no one wish to touch it.
    You never knew neither your parents nor your home. You were raised by gypsies and was forced to do all the hard work.
    Hidden in dark forest your home __village__ was home to all sort outcasts. Not neccessary to say that your life here was not easy.
    Blue fires of inferno burn those who dare to come close to __village__ of __adjective__ fire. This terrible place is your home.
    Unaware adventurer can occasionaly slip on slick slope adn find himself surrounded by strange creatures dwelling in caves of __village__. Though they don't possess a direct threat, they treat human beings as their own child despite of human's age. That's how your story begins.
    In the deep halls of mountain __city__ humans and hobbits and dwarves live hand by hand since the world creation. You are realy luky to have born is such a piecfull place.
    From the depth of lake __village__ comes a dim light which can be seen dark nights. Deep beneath silent waters of lake there is a hidden city of __city__. City opens it doors to noone but rare guests form __city__. In a small house __profession__'s wife gave a birth to a boy: to you.
    Floating rocks surround the city of __Adjective__ __Noun__: __city__. Noone is allowed to pass through the gates. Those who dare to sneak in are squashed by floating boulders. City itself is a miserable place, ruled by __name__ it began to degrade long time ago. Not a surprise that your childhood there was not easy.
    Surrounded by erupppting volcanoes city of __Noun__ is unassailable fortress ruled by mighty __name__. Mighty heroes and powerfull mages all around the realm of __Adjective__ __Noun__ are all born in __city__, as well as you.
    High in the mountains hidden in clouds lies the city __city__. Once a glorious capital of __city__ it lies in ruins now. Endless civil wars almost destroyed the city. Trying to escape the horrors of war your family moved to a __village__, where they gave birth to you.
    """

fillers = """At the age of __age__ you face your first enemy - __demon__ - minor demon tried to draw your blood. Constant combats with bands of thugs made you unbelievably strong.
From an early age you find yourself constantly involved in all kind of troubles.
You was captured by slave-traders, but somehow you managed to escape alive.
Throughout your childhood you had to fight with outnumbering thugs, defending your life. Now deep scars remind you of this battles.
It's impossible to kill invulnerable enemy - that's a lesson you've learned one day. Thanks god, you managed to survive... unlike your friends.
Lock-picking and pick-pocketing made you life careless... for a shirt period of time. One day plate-covered warrior appeared before you naming himself __name__ and claiming that he's after justice and blah-blah-blah. Until that moment you didn't know you can run that fast.
At the age of __age__ you somehow you managed to enter __Adjective__ __noun__: a cruel band which threatened all the surrounding villages and cities of __city__. You left bad company soon, to make your own. So you moved to __city__ of __Adjective__, but was charmed by it's lifestyle so that you completly forgotten your ideas to bring death to the city.
After finishing the school you came to __city__ where you were employed as __profession__. All the moneys you've earned you have donated to __name__ the god of __skill__. Finally you realized that diety has no interest in your donations, though priests do. Finally you left the city and began wandering around.
Hardworking employee is valued by his employers, but you was to lazy to work at all. You've read a lot of books and decided that life of a "sea wolf" is just for you. But you was too lazy even to gather your own crew or get your own ship.
Perfect at almost everything you was bad at communicating with others. Now you have no friends. Good news you are so perfect - you don't have enemies as well.
When you was __age__ you met a powerfull wizard __name__ who was well known for his nasty temper. He promised to teach you the art of magic, but he turned out to be an acolyte of __demon__ the greater demon. Actualy his plan was to capture you and... who knows what's next. Anyway, you have managed to cheat him and escape.
After spending two years in prison for stealing few coins you gave a promise to yourself to live in accordance to laws. That's the path you have chosen.
Once you went into the woods and was not able to find your way back. However, you met a man who taught you how to understand the language of trees and forest itself, how to use the power of the wood. That knowledge was of great assistance throughout your life
"""
teachers = """At the age of __age__ you join the faction __Adjective__ __noun__ as a __profession__.
    When you were __age__ __name__ from __Adjective__ __Noun__ made you his apprentice. After __age__ years you mastered the art of __skill__. Later your teacher was killed under suspicious circumstances, and without having any practice you've lost most of your skills.
    Seeking for knowledge you finaly came to __name__ an old __profession__ who taught you everything he knew. Seeing that an old man has nothing more to give you you murdered him without a hessitation.
    After returning to your home-town you came to __name__ and asked him to teach you the art of __skill__. After __age__ years of study you left for __city__ where lives __name__ the __Adjective__ __profession__ in order to ask him to teach you. But you never managed to find him.
    When you were __age__ a wandering __profession__ came to __city__, where you met him. Twice you asked him to teach you the art of __skill__ and twice he refused. Then you have collected some money to pay for your education, but was not able to find neither __name__ nor any other appropriate teacher.
    After you was thrown to jail for stealing few gold pieces from a noble __name__ the __Noun__ you met __name__ an adept of __Adjective__ __name__ the diety devoted to __skill__. He taught you everything he knew himself.
    
"""
adjectives = """glowing
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

nouns = """moon
    torment
    sun
    turtle
    secrets
    suspicion
    mistrust
    jealousy
    incredulity
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
    regard
    approval
    delight
    pride
    generosity
    supremacy
    benevolence
    tales"""

professions = """mason
advocat
metalsmith
wizard
healer
woodcutter
fisherman
bowman
guard
bard
hunter
assassin
crusader
"""
skills = """magic
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

def __init__(postfix):
    for file in os.listdir('../data/namegen') :
        if file.find(postfix + '.cfg') > 0 :
            libtcod.namegen_parse(os.path.join('..','data','namegen',file))
    return libtcod.namegen_get_sets()

def process_string(s = ''):
    result = s.strip()
    rng = ng_names[random.randrange(0, len(ng_names))]
    #first parse name with random one
    while result.find("__name__") > 0:
        result = result.replace("__name__", libtcod.namegen_generate(rng), 1)

    rng = ng_towns[random.randrange(0, len(ng_towns))]
    while result.find("__city__") > 0:
        result = result.replace("__city__", libtcod.namegen_generate(rng), 1)

    rng = ng_towns[random.randrange(0, len(ng_towns))]
    while result.find("__village__") > 0:
        result = result.replace("__village__", libtcod.namegen_generate(rng), 1)

    rng = ng_demons[random.randrange(0, len(ng_demons))]
    while result.find("__demon__") > 0:
        result = result.replace("__demon__", libtcod.namegen_generate(rng), 1)

    #now parse age, making any next __age__ occurance to be more than previous
    start_age = 7
    while result.find("__age__") > 0:
        rand_age = random.randrange(start_age, start_age + 7)
        result = result.replace("__age__", str(rand_age), 1)
        start_age = rand_age

    while result.find("djective__") > 0:
        rand1, rand2 = random.randrange(0, len(adjs)), random.randrange(0, len(adjs))
        result = result.replace("__Adjective__", adjs[rand1].strip().capitalize(), 1)
        result = result.replace("__adjective__", adjs[rand1].strip(), 1)

    while result.find("oun__") > 0:
        rand1, rand2 = random.randrange(0, len(nns)), random.randrange(0, len(nns))
        result = result.replace("__Noun__", nns[rand1].strip().capitalize(), 1)
        result = result.replace("__noun__", nns[rand2].strip(), 1)

    while result.find("rofession__") > 0:
        rand1, rand2 = random.randrange(0, len(profs)), random.randrange(0, len(profs))
        result = result.replace("__Profession__", profs[rand1].strip().capitalize(), 1)
        result = result.replace("__profession__", profs[rand2].strip(), 1)

    while result.find("__skill__") > 0 or result.find("__Skill__") > 0:
        rand1, rand2 = random.randrange(0, len(skls)), random.randrange(0, len(skls))
        result = result.replace("__Skill__", skls[rand1].strip().capitalize(), 1)
        result = result.replace("__skill__", skls[rand2].strip(), 1)
    return result

def make_story():
    parts = []
    for part in (born, fillers, teachers):
        phraselist = map(process_string, part.splitlines())
        random.shuffle(phraselist)
        parts.append(phraselist)
    output = chain(*islice(izip(*parts), 0, 1))
    print textwrap.fill(' '.join(output),80)

ng_names = __init__("names")
ng_towns = __init__("town")
ng_demons = __init__("demon")
adjs = adjectives.splitlines()
nns = nouns.splitlines()
profs = professions.splitlines()
skls = skills.splitlines()
random.shuffle(adjs)
random.shuffle(nns)
random.shuffle(profs)
random.shuffle(skls)

make_story()