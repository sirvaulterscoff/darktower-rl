""" Module dealing with all kind of des files - like maps, rooms, bacgrounds etc"""
from pyparsing import *
import string
import random
from collections import Iterable
#from critters import *
#from features import *
#from items import *

#chars allowed for right-hand-value
viable_chars = '!"#$%&\'()*+,-./:;<?@[\]^_`{|}~'
equals = Literal('=').suppress()
#comment = Regex(r'^#[' + alphanums + ']$')
comma = ZeroOrMore(',').suppress()
#right-hand-value(rhv) definition
rhv = Combine(Optional('$') + Word(alphanums + viable_chars + '\ '))
#assign to dictionary
dict_assign = Literal('=>').suppress()
#multiline syntax
multi_line = QuotedString(quoteChar='"""', escChar='\\', multiline=True)
line_end = ZeroOrMore(lineEnd.suppress())

#right hand value for dictionary. parses => value
dict_rhv = Group( OneOrMore(Word(alphanums + viable_chars )) + dict_assign + rhv) + comma
any_keyword = Combine(Word(alphas, min=1) + ZeroOrMore(Word(alphanums + '_-')))
#parses KEYWORD="""
multiline_keyword = any_keyword + equals +  multi_line
#end of block keyword
end_keyword  = Keyword('END').suppress() + line_end

assignment = any_keyword + equals + (OneOrMore(dict_rhv) | rhv)
ml_assignment = multiline_keyword

assignment = ml_assignment | assignment
parser =  OneOrMore(OneOrMore(assignment)  + end_keyword)

param_number = Combine(Optional('-') + Word(string.digits)).setParseAction(lambda x: int(x[0]))
param_lhv = Word(alphanums) + Literal(':').suppress()
param_rhv = (param_number | Word(alphanums +"'" + '"' + ' ')) + Optional(Literal(',')).suppress()
params_parser = dictOf(param_lhv, param_rhv)

def _parseFile(fname, ttype, lookup_dicts):
    result = [None]#None indicates that a new item should be created
    assignment.setParseAction(lambda x: process(result,ttype, x, lookup_dicts))
    end_keyword.setParseAction(lambda x : end(result))
    cont = open(fname).read()
    parser.parseString(cont)
    if result[-1] is None:
        result.pop()
    return result

def lookup_val(val, lookup_dicts):
    for lookup in lookup_dicts:
        if lookup.has_key(val):
            res = lookup[val]
            if res is None:
                raise RuntimeError('None contained in lookup dicts under the key %s' % val)
            return res
    return None

def extend_list(l, what):
    """ Extends list l with item/items from what
    If what is Iterable - calls l.extend
    if it's not - calls append(what)
    """
    if isinstance(what, Iterable):
        l.extend(what)
    else:
        l.append(what)

def parse_val(val, where, lookup_dicts):
    """Adjusts the value from des file. There are several ways to do so
    1) string.Template substitution when ${ is replaced with attribute of object
    2) $-values. Values that starts with $-sign will be parsed using eval
    3) %-blocks. Values that starts with %-sign will be parsed using compile/exec. Then
    we expect that such a block defines local named 'out'
    lookup_dicts stores dicts that holds available classes for that type of parsing
    """
    val = string.Template(val).safe_substitute(where.__dict__)
    if val.startswith('$') and not val.startswith('${'):
        val = val[1:]
        if val.find('&&') > -1:
            args = val.partition('&&')
            item = parse_val('$' + args[0].strip(), where, lookup_dicts)
            if not item:
                raise RuntimeError('No callable under the name [%s]' % args[0])
            return extend_list([item], parse_val('$'+args[2], where, lookup_dicts))
        #here we address simple value evaluation via eval
        try:
            if val.find('(') > -1:#we have a record in form $func_name(param:value)
                func = val[:val.find('(')].strip() #get function name
                args = val[val.find('(')+1:val.find(')')] #get args between '(' and ')'
                args = params_parser.parseString(args).asDict() #parse params
                target = lookup_val(func, lookup_dicts)
                if not target:
                    raise RuntimeError('No callable under the name [%s]' % func)
                #now we check two options: if this is a type - then we create new parametrized type
                #if it's function - we just call it with provided params
                if isinstance(target, type): #if this is a type - create subtype
                    return type(target.__name__, (target,), args)
                if callable(target):
                    return target(**args)
                else:
                    raise RuntimeError('Invalid target in parsing %s' % target)
            else:
                return lookup_val(val.strip(), lookup_dicts)

        except Exception ,e:
            print 'Error parsing code :\n' + val + '\n' + str(e)
            import traceback
            import sys
            t,v, tb = sys.exc_info()
            traceback.print_tb(tb)
            sys.exit(-1)
    elif val.startswith('%'): #more complex - via compile and exec
        val = val[1:]
        try:
            code = compile(val, '', 'exec')
            exec(code)
            #actualy any executed code should set 'out' variable. we take it and set to target class
            return out
        except Exception ,e:
            print 'Error compiling code :\n' + val + '\n' + str(e)
            import sys
            sys.exit(-1)
    else:
        return val

def process(items, ttype, toks, lookup_dicts):
    """Invoked on each rhv """
    where = items[-1]
    #just take previous item from results. if it's empty - it's either start of file or
    #END keyword was prior to current line
    if where is None:
        items.pop()
        where = ttype() #create new item of requested type
        items.append(where)
    key = toks[0]
    key = str(key).lower()
    value = toks[1]
    if isinstance(value, str): #if the result is plain string - parse and set
        out = parse_val(value, where, lookup_dicts)
        setattr(where,key,out)
    else: #if the result is map - parse each value
        if not hasattr(where, key):
            setattr(where, key, {})
        if hasattr(where, 'get_' + key):
            dict = getattr(where, 'get_' + key)()
        else:
            dict = getattr(where, key)
        for k, v in zip(value[::2], value[1::2]):
            dict[k] = parse_val(v, where, lookup_dicts)

def end(result):
    result.append(None)



parsed_des_files = { }
def parseFile(file_name, type, lookup_dicts):
    """parses file"""
    if parsed_des_files.has_key(file_name):
        return parsed_des_files[file_name]
    _des = _parseFile(file_name, type, lookup_dicts)
    parsed_des_files[file_name] = _des
    return _des

def parseDes(file_name, type, sub_type='des'):
    """parses des file from data/des/ folder.
    parameters:
    file_name => is the name if the file without .des
    type => class of the resource
    sub_type => 'des' subfolder inside data folder
    returns collection of type() items from parsed file
    """
    file_name = os.path.join(os.path.dirname(__file__), 'data', sub_type, file_name + '.des')
    return parseFile(file_name, type)
