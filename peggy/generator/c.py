from . import generators, Generator, ImperativeGenerator
from ..grammar import *
from ..expr import *

CPreamble = '''

#include <stdlib.h>
#include <stdbool.h>
#include <string.h>
#include <strings.h>

struct peggy_node_s {
	enum peggy_node_type_e type;
	struct peggy_node_s *children;
	size_t count;
	size_t current;
	size_t i;
	const char *str;
	size_t len;
};

struct peggy_result_s {
	bool v;
	size_t o;
	size_t n;
	struct peggy_node_s node;
};

struct peggy_memoize_s {
	enum {
		PEGGY_MEMOIZE_STATE_UNKNOWN,
		PEGGY_MEMOIZE_STATE_VALID,
		PEGGY_MEMOIZE_STATE_FAILED,
	} state;
	size_t i;
	size_t o;
};

struct peggy_parser_s {
	char *input;
	size_t length;

	struct peggy_memoize_s *memoize[PEGGY_NODE_COUNT];
};

bool peggy_match_sensitive_string(struct peggy_parser_s *p, size_t i, char *str, size_t len, struct peggy_result_s *res) {
	if(!p || !str || !res) {
		return false;
	}

	if(i + len <= p->length && strncmp(p->input+i, str, len) == 0) {
		res->v = true;
		res->o = len;
	} else {
		res->v = false;
		res->o = 0;
	}

	return true;
}

bool peggy_match_insensitive_string(struct peggy_parser_s *p, size_t i, char *str, size_t len, struct peggy_result_s *res) {
	if(!p || !str || !res) {
		return false;
	}

	if(i + len <= p->length && strncasecmp(p->input+i, str, len) == 0) {
		res->v = true;
		res->o = len;
	} else {
		res->v = false;
		res->o = 0;
	}

	return true;
}

bool peggy_match_range(struct peggy_parser_s *p, size_t i, char *str, size_t len, struct peggy_result_s *res) {
	if(!p || !str || !res) {
		return false;
	}

	if(i < p->length && memchr(str, p->input[i], len)) {
		res->v = true;
		res->o = 1;
	} else {
		res->v = false;
		res->o = 0;
	}

	return true;
}

bool peggy_match_wildcard(struct peggy_parser_s *p, size_t i, struct peggy_result_s *res) {
	if(!p || !res) {
		return false;
	}

	if(i < p->length) {
		res->v = true;
		res->o = 1;
	} else {
		res->v = false;
		res->o = 0;
	}

	return true;
}

bool peggy_parser_init(struct peggy_parser_s *parser, char *input, size_t length) {
	if(!parser || !input) {
		return false;
	}

	parser->input = input;
	parser->length = length;

	return true;
}

void ast_add_child(struct peggy_node_s node, struct peggy_node_s child) {
	if(node.current >= node.count) {
		node.children = realloc(node.children, sizeof(child) * (node.count + 1));
		node.current = node.count++;
	}
	node.children[node.current] = child;
	node.current += 1;
}
'''

class CGenerator(ImperativeGenerator):
	def __init__(self, g):
		ImperativeGenerator.__init__(self, g)

	def genGrammar(self):
		self.add('#ifndef _PEGGY_PARSER_H_')
		self.add('#define _PEGGY_PARSER_H_')
		self.add('')
		self.add('enum peggy_node_type_e {')
		self.add('\tPEGGY_NODE_UNKNOWN = 0,')
		for name in self.grammar.rules:
			self.add('\t' + self.grammar.rules[name].getAstName()+',')
		self.add('\tPEGGY_NODE_COUNT')
		self.add('};')

		self.add('const char *PEGGY_NODE_NAMES[PEGGY_NODE_COUNT] = {')
		self.add('\t"UNKNOWN",')
		for name in self.grammar.rules:
			self.add('\t"' + name + '",')
		self.add('};')

		self.add(CPreamble)

		for name in sorted(self.grammar.rules.keys()):
			if self.grammar.rules[name].isLeftRecursive():
				self.add("/* Left Recursive Rule */")
			self.genExprRule(self.grammar.rules[name])
		
		self.add('')
		self.add('#endif /* _PEGGY_PARSER_H_ */')

	def genExprRule(self, e):
		self.add('/*')
		self.add(str(e))
		e.draw('', self)
		self.add('*/')
		self.add('bool peggy_parse_' + e.name + '(struct peggy_parser_s *p, size_t i, struct peggy_result_s *result, bool ast) {')
		self.incBlockLevel()
		if [c for c in e.find(Expr.TYPE_CALL) if c.ast and not c.isPredicate()]:
			self.add('struct peggy_node_s node;')
		l = len(self.lines)
		self.resetStack()
		# REC
		self.genExpr(e.data)
		# REC
		if self.max_stack_depth >= 0:
			self.add('struct peggy_result_s results[' + str(self.max_stack_depth+1) + "];", index = l)
		self.add('return true;')
		self.decBlockLevel()
		self.add('}')
		self.add('')

	def genStackReset(self):
		self.add('memset(results+' + str(self.stack_depth) + ', 0, sizeof(results[' + str(self.stack_depth) + ']));')

	def push(self):
		Generator.push(self)
		self.genStackReset()

	def pop(self):
		self.add('*result = results[' + str(self.stack_depth) + '];')
		Generator.pop(self)

	def genResultOffset(self):
		self.add('result->o = ' + '+'.join(['i']+["results[" + str(i) + "].o" for i in range(0, self.stack_depth+1)]) + ';')

	def genResultValidOffset(self):
		self.add('result->v = result->o > 0;')

	def genResultInvalidOffset(self):
		self.add('result->v = !(result->o > 0);')

	def genResultValid(self):
		self.add('result->v = true;')

	def genResultResetOffset(self):
		self.add('result->o = 0;')

	def genResultReset(self):
		self.add('result->v = false;')
		self.add('result->o = 0;')

	def genIfStart(self, cond):
		self.add('if(' + cond + ') {')
		self.incBlockLevel()

	def genElse(self):
		self.decBlockLevel()	
		self.add('} else {')
		self.incBlockLevel()

	def genIfEnd(self):
		self.decBlockLevel()
		self.add('}')

	def genIf(self, cond, code):
		self.genIfStart(cond)
		self.add(code)
		self.genIfEnd()

	def genWhileStart(self, cond):
		self.add('while(' + cond + ') {')
		self.incBlockLevel()

	def genWhileEnd(self):
		self.decBlockLevel()
		self.add('}')

	def genBreak(self):
		self.add('break;')

	def genStackAccumulateOffset(self):
		self.add("results[" + str(self.stack_depth) + "].o += result->o;")

	def genASTAddNode(self):
		if self.stack_depth >= 0:
			self.add('node.current = ' + '+'.join(["results[" + str(i) + "].n" for i in range(0, self.stack_depth+1)]) + ';')
		else:
			self.add('node.current = 0;')
		self.add("ast_add_child(node, result->node);")

	def genStackAccumulateAST(self):
		self.add("results[" + str(self.stack_depth) + "].n += 1;")

	def condResultValid(self):
		return 'result->v'

	def condResultValidStrict(self):
		return 'result->v && result->o > 0'

	def condResultInvalid(self):
		return '!result->v'

	def condTrue(self):
		return 'true'

	def condResultValidAst(self):
		return 'result->v && result->n > 0 && ast'

	def genExprString(self, e):
		self.genResultOffset()
		self.add('peggy_match_sensitive_string(p, result->o, "' + escape_string(e.data) + '", ' + str(len(e.data)) + ', result);')
	
	def genExprStringInsensitive(self, e):
		self.genResultOffset()
		self.add('peggy_match_insensitive_string(p, result->o, "' + escape_string(e.data) + '", ' + str(len(e.data)) + ', result);')
	
	def genExprRange(self, e):
		self.genResultOffset()
		self.add('peggy_match_range(p, result->o, "' + escape_string(e.data) + '", ' + str(len(e.data)) + ', result);')
		
	def genExprCall(self, e):
		#self.add("print '\t' * depth + name,'=> " + e.data + " before'")
		self.genResultOffset()
		if e.isPredicate():
			self.add("peggy_parse_" + e.data + "(p, result->o, result, false);")
		else:
			self.add("peggy_parse_" + e.data + "(p, result->o, result, ast);")
		#self.add("print '\t' * depth + name,'=> " + e.data + " after',result.v,result.o,result.n,'['+result.node.str+']'")
		
	def genExprWildcard(self, e):
		self.genResultOffset()
		self.add("peggy_match_wildcard(p, result->o, result);")

generators['c'] = CGenerator