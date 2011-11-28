"""
A simple Simulink mdl file parser.

Credits:
Most of the code is based on the json parser example distributed with
pyparsing. The code in jsonParser.py was written by Paul McGuire


"""

__author__ = 'Kjell Magne Fauske'
__license__ = 'MIT'
__version__ = '1.3'

import re
import sys
from pyparsing import *

# parse actions
def convertNumbers(s,l,toks):
	"""Convert tokens to int or float"""
	# Taken from jsonParser.py
	n = toks[0]
	try:
		return int(n)
	except ValueError, ve:
		return float(n)

def joinStrings(s,l,toks):
	"""Join string split over multiple lines"""
	return ["".join(toks)]

def initializeParser():
	# Define grammar

	# Parse double quoted strings. Ideally we should have used the simple statement:
	#    dblString = dblQuotedString.setParseAction( removeQuotes )
	# Unfortunately dblQuotedString does not handle special chars like \n \t,
	# so we have to use a custom regex instead.
	# See http://pyparsing.wikispaces.com/message/view/home/3778969 for details. 
	dblString = Regex(r'\"(?:\\\"|\\\\|[^"])*\"', re.MULTILINE)
	dblString.setParseAction( removeQuotes )


	mdlNumber = Combine( Optional('-') + ( '0' | Word('123456789',nums) ) +
					 Optional( '.' + Word(nums) ) +
					 Optional( Word('eE',exact=1) + Word(nums+'+-',nums) ) )

	objectDef = Forward()
	mdlName = Word('$'+'.'+'_'+alphas+nums)
	mdlValue = Forward()
	# Strings can be split over multiple lines
	mdlString = (dblString + Optional(OneOrMore(Suppress(LineEnd()) +
				LineStart() + dblString)))
	# Stateflow vector elements are delimited by spaces, not commas. This
	# rule handles both cases.
	mdlArray = Group((Suppress('[') +
				Optional(mdlValue) +
				ZeroOrMore(Optional(Suppress(Literal(','))) + mdlValue) +
				Suppress(']')))
	mdlMatrix = Group(Suppress('[') +
				delimitedList(Group(delimitedList(mdlValue, delim=',')), ';') +
				Suppress(']'))
	mdlValue << (mdlNumber | mdlName | mdlString | mdlArray | mdlMatrix | objectDef)
	mdlMembers = dictOf(mdlName, mdlValue)
	objectDef << Suppress('{') + Optional(mdlMembers) + Suppress('}')
	mdlObjects = OneOrMore(objectDef)
	mdlModel = OneOrMore(Group(mdlName + Suppress('{') + Optional(mdlObjects | mdlMembers) + Suppress('}')))
	mdlNumber.setParseAction(convertNumbers)
	mdlString.setParseAction(joinStrings)
	# Some mdl files from Mathworks start with a comment. Ignore all
	# lines that start with a #
	singleLineComment = Group("#" + restOfLine)
	mdlModel.ignore(singleLineComment)
	objectDef.ignore(singleLineComment)

	return mdlModel

def extractStateflow(blocks):
	"From a set of blocks, extract those related to Stateflow charts"
	sf_blocks = []
	for b in blocks:
		if b[0] == 'Stateflow':
			sf_blocks.append(b)
	print 'Top-level blocks seen: ' + str(len(blocks))
	print 'Stateflow blocks retained: ' + str(len(sf_blocks))
	return sf_blocks

if __name__ == '__main__':
	import pprint

	if len(sys.argv) < 2:
		print 'usage: ' + sys.argv[0] + ' <input.mdl>'
		sys.exit(1)

	inputfilename = sys.argv[1]
	infile = open(inputfilename, 'r')
	testdata = infile.read()
	mdlParser = initializeParser()
	result = mdlParser.parseString(testdata)
	sf_blocks = extractStateflow(result)
	#pprint.pprint(sf_blocks)
	infile.close()
