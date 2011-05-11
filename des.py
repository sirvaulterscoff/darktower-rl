from pyparsing import *
import string
#chars allowed for right-hand-value
viable_chars = '!"#$%&\'()*+,-./:;<?@[\]^_`{|}~'
equals = Literal('=').suppress()
#comment = Regex(r'^#[' + alphanums + ']$')
comma = ZeroOrMore(',').suppress()
#right-hand-value(rhv) definition
rhv = Combine(Optional('$') + Word(alphanums + '_-()\',:'))
#assign to dictionary
dict_assign = Literal('=>').suppress()
#multiline syntax
multi_line = Literal('"""').suppress()
line_end = ZeroOrMore(lineEnd.suppress())

#right hand value for dictionary. parses => value
dict_rhv = Group(OneOrMore(Word(alphanums + viable_chars)) + dict_assign + rhv) + comma
any_keyword = Word(alphas, min=1) + ZeroOrMore(Word(alphanums + '_-'))
#parses KEYWORD="""
multiline_keyword = any_keyword + equals + FollowedBy('"""') + multi_line + Optional(line_end)
#end of block keyword
end_keyword  = Keyword('END').suppress() 

assignment = any_keyword + equals + (OneOrMore(dict_rhv) | rhv)
ml_assignment = multiline_keyword + Combine(OneOrMore(NotAny(Literal('"""')) + Word(alphanums+ viable_chars) + lineEnd)) + FollowedBy('"""') +multi_line

assignment = ml_assignment | assignment
parser =  OneOrMore(assignment)  + end_keyword + lineEnd 
def parseFile(fname, ttype):
    result = []
    assignment.setParseAction(lambda x: process(result,ttype, x))
    end_keyword.setParseAction(lambda x : end(result))
    parser.setDebug(True)
    parser.parseFile(fname)
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
	where.__dict__[key] = value
    else:
	if where.__dict__.get(key) is None:
	    where.__dict__[key] = {}
	for k, v in zip(value[::2], value[1::2]):
	    where.__dict__[key][k] = v

def end(result):
    result.append(None)

class Mapp(object):
    pass

test_str="""
x=$as
SUBST= b=>FT ,c=>FT_c
PARAM=d
SUBST= #=>FT_WALL, x=>F
ORIENT=RANDOM
MAP=\"\"\"
#####
#...#
#,,,#
#####
\"\"\"
END

SUBST=b
MAP=\"\"\"
asd
asd
asd
\"\"\"
END
"""
#print test_str
#res = parser.parseString(test_str)
#print res
res = parseFile('./data/rooms/large_tavern.map', Mapp)[0]
print res
#print res.subst
print res.__dict__
