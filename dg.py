from dungeon_generators import MapDef, MapRequest, get_map_name, parse_file 
from random import choice
from util import random_from_list_weighted, roll

generators = {}
transformation_pipe = []
class DungeonGenerator(object):
    """Generates new map of given width/heigh and style taking in account player's HD
    It works as follows:
        1. it chooses apropriate generator. If we request forest - use forest generator etc
        2. using selected generator it creates terrain
        3. if there is a request fro some feature - it searches for specific 2nd level generator
        4. then it morph result from 2 and 3 producing the result adjusting size of the map as needed
        Any level (is generated using 1 level generator). There should be following types of lvl1 generators:
            a. forest
            b. desert ?
            c. seashore
            d. cave-like
            e. maze-like
            f. canyon
            g. city
            h. village ?
            i. null - used for static levels from des-files
        lvl2 generators can be following:
            0. static big_map generator - used only with null lvl1 generator
            a. pool/lava pool generator
            b. random feature generator (like placing some chests or another apropriate stuff)
            c. trap generator
            d. small features generator (those are from des files)
            e. house generator* (actualy will be only used by lvl1 generators)
            f. river/lava river generator (if apropriate lvl1 was selected)
            g. bridge generator (if lvl2.f was selected)
            h. items generator
            i. checker - checks for lvl connectivity, and number of desired features/items
            Lvl2 generators should be piped in stated order
    """
    def generate_map(width=400, height=300, player_hd=1, generator_type=None, requests=None, params={}, name='', theme=''):
        if not generators.has_key(generator_type):
            raise RuntimeError('Unknow style [%s] for dungeon generator' % generator_type)
        map_draft = generators[generator_type]() #okay we just take requested generator and invoke it. Now we have draft map
    generate_map = staticmethod(generate_map)

def null_generator():
    """Special cased generator - used when we need full sized, untransformed map from des file
    """
    return MapDef()

generators['null'] = null_generator
class PipeItem(object):
    def __init__(self, transformer):
        self.transformer = transformer
        self.ttype = transformer.__name__

    def decide(self, player_hd, generator_type, requests, theme,  params={}):
        if self.ttype == 'static_transformer':
            if generator_type == 'null': #if it's null generator - then definetly static_transformer is what we need
                return True
            #now check if we have MapRequests
            map_requests = filter(lambda x: isinstance(x, MapRequest), requests)
            return len(map_requests) > 0
        if self.ttype == 'pool_transformer':
            return False #stub for now

unique_maps_already_generated = {}
def __check_static_params(generator_type, hd, x, params):
    """ Check params for MapDef loaded from des file. Check that map theme matches that of generator.
        Player HD is higher or equals that defined in des file etc... """
    if generator_type != 'null':
        if generator_type != x.terrain:
            return False
    if x.HD >  hd:
        return False
    if x.unique and unique_maps_already_generated.has_key(x.id):
        return False
    return True
    #todo i guess we need to check params here


def static_transformer(map_draft, player_hd, generator_type, requests, theme, params={}):
    #first we need to know what type of map we need
    if theme == '' or theme is None:
        map_requests = filter(lambda x: isinstance(x, MapRequest), requests)
        if len(map_requests < 1):
            raise RuntimeError('Neither theme nor MapRequests specified for static_transfomer')
        for request in map_requests:
            av_maps = parse_file(get_map_name(request.type))
            if len(av_maps) < 1: raise RuntimeError('No maps for MapRequest with type [%s]' % request.type)
            av_maps = filter(lambda x: __check_static_params(generator_type, player_hd, x, params), av_maps)
            while True:
                # choose a random map from a weighed list
                tmap = random_from_list_weighted(av_maps)
                if tmap.chance > 0:
                    if roll(1, tmap.chance) == 1:
                        break
                else:
                    break
            unique_maps_already_generated[tmap.id] = 1





transformation_pipe.append(PipeItem(static_transfomer))
