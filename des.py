from pyparsing import *
import string
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
end_keyword  = Keyword('END').suppress() + line_end + restOfLine

assignment = any_keyword + equals + (OneOrMore(dict_rhv) | rhv)
ml_assignment = multiline_keyword

assignment = ml_assignment | assignment
parser =  OneOrMore(assignment)  + end_keyword

def parseFile(fname, ttype):
    result = []
    assignment.setParseAction(lambda x: process(result,ttype, x))
    end_keyword.setParseAction(lambda x : end(result))
    parser.parseFile(fname)
    if result[-1] is None:
        tail = result.pop()
    return result

def process(items, ttype, toks):
    if len(items) < 1:
	where = ttype()
	items.append(where)
    else:
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

