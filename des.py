""" Module dealing with all kind of des files - like maps, rooms, bacgrounds etc"""
from pyparsing import *
import string
import random
from critters import *
from features import *
from items import *

#chars allowed for right-hand-value
viable_chars = '!"#$%&\'()*+,-./:;<?@[\]^_`{|}~'
equals = Literal('=').suppress()
#comment = Regex(r'^#[' + alphanums + ']$')
comma = ZeroOrMore(',,').suppress()
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

def _parseFile(fname, ttype):
    result = [None]#None indicates that a new item should be created
    assignment.setParseAction(lambda x: process(result,ttype, x))
    end_keyword.setParseAction(lambda x : end(result))
    cont = open(fname).read()
    parser.parseString(cont)
    if result[-1] is None:
        result.pop()
    return result

def parse_val(val, where):
    """Adjusts the value from des file. There are several ways to do so
    1) string.Template substitution when ${ is replaced with attribute of object
    2) $-values. Values that starts with $-sign will be parsed using eval
    3) %-blocks. Values that starts with %-sign will be parse using compile/exec. Then
    we expect that such a block defines local named 'out'
    """
    val = string.Template(val).safe_substitute(where.__dict__)
    if val.startswith('$') and not val.startswith('${'):
        val = val[1:]
        #here we address simple value evaluation via eval
        try:
            return eval(val)
        except Exception ,e:
            print 'Error parsing code :\n' + val + '\n' + str(e)
            import sys
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

def process(items, ttype, toks):
    """Invoked on each rhv """
    where = items[-1]
    if where is None:
        items.pop()
        where = ttype()
        items.append(where)
    key = toks[0]
    key = str(key).lower()
    value = toks[1]
    if isinstance(value, str):
        out = parse_val(value, where)
        setattr(where,key,out)
    else:
        if not hasattr(where, key):
            setattr(where, key, {})
        for k, v in zip(value[::2], value[1::2]):
            getattr(where, key)[k] = parse_val(v, where)

def end(result):
    result.append(None)



parsed_des_files = { }
def parseFile(file_name, type):
    """parses file"""
    if parsed_des_files.has_key(file_name):
        return parsed_des_files[file_name]
    _des = _parseFile(file_name, type)
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
