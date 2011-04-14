import random
from plot import  *

#let's make uniques as subclasses for now
import util
random_artefact_here = '[place here random artefact]'
#adventurer npc
class Oddyssy(UniqueNPC, AdventureNPC):
    name = random.choice(['Odd Yssy', 'Oddyssy'])
    real_name = name
    description = 'A long journey in search of mythical relic ' + random_artefact_here + ' led him to a foreign land where this relic is hidden, according to rummors.'

  