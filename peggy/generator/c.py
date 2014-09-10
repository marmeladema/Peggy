from . import generators, Generator, ImperativeGenerator
from ..grammar import *
from ..expr import *

CPreamble = '''
struct peggy_result_s {
	bool v;
	size_t o;
	size_t n;
};

struct peggy_parser_s {
	char *input;
	size_t length;
};

bool peggy_parser_init(struct peggy_parser_s *parser, char *input, size_t length) {
	if(!parser | !input) {
		return false;
	}

	parser->input = input;
	parser->length = length;

	return true;
}
'''

class CGenerator(ImperativeGenerator):
	def __init__(self, g):
		ImperativeGenerator.__init__(self, g)

	def genGrammar(self, g):
		self.add("AST_STRINGS = []")
		self.add('enum peggy_rules_e {')
		self.add('};')
		self.add("AST_TYPE_UNKNOWN = 0")
		self.add("AST_STRINGS.append(\"UNKNOWN\")")
		i = 0
		for name in g.rules:
			self.add("%s = %d"%(g.rules[name].getAstName(),i+1))
			self.add("AST_STRINGS.append(\"%s\")"%(name,))
			i += 1
		self.add("AST_TYPE_MAX = %u"%(len(g.rules)+1,))
		
		self.add(CPreamble)
		for name in sorted(g.rules.keys()):
			self.add("# ---------------------- #")
			if g.rules[name].isLeftRecursive():
				self.add("# Left Recursive Rule")
			self.genExprRule(g.rules[name])