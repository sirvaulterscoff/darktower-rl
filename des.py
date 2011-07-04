""" Module dealing with all kind of des files - like maps, rooms, bacgrounds etc"""
from pyparsing import *
import string
import random
import util
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

def parseFile(fname, ttype):
    result = [None]#None indicates that a new item should be created
    assignment.setParseAction(lambda x: process(result,ttype, x))
    end_keyword.setParseAction(lambda x : end(result))
    cont = open(fname).read()
    parser.parseString(cont)
    if result[-1] is None:
        result.pop()
    return result

def process(items, ttype, toks):
    where = items[-1]
    if where is None:
        items.pop()
        where = ttype()
        items.append(where)
    key = toks[0]
    key = str(key).lower()
    value = toks[1]
    if isinstance(value, str):
        val = value
        val = string.Template(val).safe_substitute(where.__dict__)
        if val.startswith('$') and not val.startswith('${'):
            val = val[1:]
            #here we address simple value evaluation via eval
            try:
                where.__dict__[key] = eval(val)
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
                setattr(where,key,out)
            except Exception ,e:
                print 'Error parsing code :\n' + value[1:] + '\n' + str(e)
                import sys
                sys.exit(-1)
        else: #simple assignment case
            setattr(where,key,val)
    else:
        if where.__dict__.get(key) is None:
            where.__dict__[key] = {}
        for k, v in zip(value[::2], value[1::2]):
            where.__dict__[key][k] = v

def end(result):
    result.append(None)

class HouseDes(object):
    pass

class Temple(object):
    """Temple description """
    def __init__(self, map_src):
        super(Temple, self).__init__(map_src)


a= 'import util;\ndef free_action(self, city):\n    print "YEEEEEEEEEEEEEEEEEEESSSSSSSSSSSSSS"\n\ndef action(who, world):\n    if isinstance(who, BadWizardNPC):\n        who.__dict__[free_action] = free_action'
print a
exec(a)
free_action(None, None)
