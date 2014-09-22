from . import generators, Generator, ImperativeGenerator
from ..grammar import *
from ..expr import *

CHeader = '''
#ifndef _PEGGY_PARSER_H_
#define _PEGGY_PARSER_H_

#include <stdlib.h>
#include <stdio.h>
#include <stdbool.h>
#include <string.h>
#include <strings.h>

struct peggy_parser_s;
struct peggy_result_s;
struct peggy_node_s;
'''

CPreamble = '''
struct peggy_string_s {
	const char *ptr;
	size_t len;
	bool allocated;
};

struct peggy_node_s {
	enum peggy_node_type_e type;
	struct peggy_node_s *children;
	size_t count;
	size_t current;	
	size_t i;
	const char *str;
	size_t len;
	bool memo;
};

struct peggy_result_s {
	bool v;
	size_t o;
	size_t n;
	struct peggy_node_s node;
};

struct peggy_memo_s {
	enum {
		PEGGY_MEMOIZE_STATE_UNKNOWN,
		PEGGY_MEMOIZE_STATE_VALID,
		PEGGY_MEMOIZE_STATE_FAILED,
	} state;
	size_t i;
	struct peggy_result_s r;
};

struct peggy_memo_array_s {
	struct peggy_memo_s *ptr;
	size_t count;
};

struct peggy_parser_s {
	char *input;
	size_t length;

	struct peggy_memo_array_s memo_table[PEGGY_NODE_COUNT];
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

bool peggy_parser_init(struct peggy_parser_s *p, char *input, size_t length) {
	if(!p || !input) {
		return false;
	}

	memset(p, 0, sizeof(*p));
	p->input = input;
	p->length = length;

	return true;
}

bool peggy_parser_clean(struct peggy_parser_s *p) {
	if(!p) {
		return false;
	}

	size_t i;
	for(i = 0; i < PEGGY_NODE_COUNT; i++) {
		free(p->memo_table[i].ptr);
		p->memo_table[i].ptr = NULL;
		p->memo_table[i].count = 0;
	}

	return true;
}

bool peggy_get_memo(struct peggy_parser_s *parser, enum peggy_node_type_e type, size_t i, struct peggy_result_s *r) {
	if(!parser || !r) {
		return false;
	}

	size_t k;
	for(k = 0; k < parser->memo_table[type].count; k++) {
		if(parser->memo_table[type].ptr[k].i == i) {
			*r = parser->memo_table[type].ptr[k].r;
			return true;
		}
	}
	return false;
}

bool peggy_set_memo(struct peggy_parser_s *parser, enum peggy_node_type_e type, size_t i, struct peggy_result_s r) {
	// printf("[peggy_set_memo] r.node.children: %p\\n", r.node.children);
	if(!parser) {
		return false;
	}
	size_t k;
	for(k = 0; k < parser->memo_table[type].count; k++) {
		if(parser->memo_table[type].ptr[k].i == i) {
			parser->memo_table[type].ptr[k].r = r;
			parser->memo_table[type].ptr[k].r.node.memo = true;
			return true;
		}
	}
	parser->memo_table[type].ptr = realloc(parser->memo_table[type].ptr, (parser->memo_table[type].count + 1) * sizeof(*parser->memo_table[type].ptr));
	parser->memo_table[type].ptr[parser->memo_table[type].count].i = i;
	parser->memo_table[type].ptr[parser->memo_table[type].count].r = r;
	parser->memo_table[type].ptr[parser->memo_table[type].count].r.node.memo = true;
	parser->memo_table[type].count++;
	return true;
}

bool peggy_rec_memo(struct peggy_parser_s *p, enum peggy_node_type_e type, size_t i, struct peggy_result_s r1) {
	struct peggy_result_s r2;
	if(!peggy_get_memo(p, type, i, &r2) || r1.o > r2.o) {
		return true;
	}
	return false;
}

void peggy_print_node(struct peggy_node_s node, const char *prefix, size_t plen) {
	size_t i;
	if(prefix) {
		fwrite(prefix, 1, plen-3, stdout);
		fwrite("  +--", 1, strlen("  +--"), stdout);
	}
	fprintf(stdout, "%s", PEGGY_NODE_NAMES[node.type]);
	
	if(node.count > 0) {
		fprintf(stdout, "\\n");
		char *tmp = calloc(plen + 3, sizeof(char));
		memcpy(tmp, prefix, plen);
		for(i = 0; i < node.count - 1; i++) {
			tmp[plen] = ' ';tmp[plen+1] = ' ';tmp[plen+2] = '|';
			peggy_print_node(node.children[i], tmp, plen+3);
		}
		tmp[plen] = ' ';tmp[plen+1] = ' ';tmp[plen+2] = ' ';
		peggy_print_node(node.children[i], tmp, plen+3);
		free(tmp);
	} else {
		fprintf(stdout, "[");
		fwrite(node.str, 1, node.len, stdout);
		fprintf(stdout, "](%lu)\\n", node.i);
	}
}

bool peggy_node_clean(struct peggy_node_s *node, bool force) {
	if(!node) {
		return false;
	}

	size_t i;
	for(i = 0; i < node->count; i++) {
		if(!node->memo || force) {
			peggy_node_clean(node->children+i, force);
		}
	}
	// printf("[peggy_node_clean] node->children: %p, node->memo: %d, force: %d\\n", node->children, node->memo, force);
	if(!node->memo || force) {
		if(node->children) {
			free(node->children);
			memset(node, 0, sizeof(*node));
		} else {
			node->type = 0;
		}
	}
	return true;
}

void ast_add_child(struct peggy_node_s *node, struct peggy_node_s child) {
	// printf("[ast_add_child] node->type: %s, node->children: %p, node->count: %lu, node->current: %lu, child.type: %s, child.children: %p\\n", PEGGY_NODE_NAMES[node->type], node->children, node->count, node->current, PEGGY_NODE_NAMES[child.type], child.children);
	if(node->current == node->count) {
		node->children = realloc(node->children, sizeof(child) * (node->count + 1));
		memset(node->children+node->count, 0, sizeof(node->children[node->count]));
		node->count++;
		// printf("[ast_add_child] node->children: %p\\n", node->children);
	}
	size_t i;
	for(i = node->current; i < node->count; i++) {
		peggy_node_clean(node->children+i, false);
	}
	node->children[node->current] = child;
	node->current += 1;
}
'''

CFooter = '''
#endif /* _PEGGY_PARSER_H_ */
'''

class CGenerator(ImperativeGenerator):
	def __init__(self, g):
		ImperativeGenerator.__init__(self, g)

	def genGrammar(self):
		self.add(CHeader)
		
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
		
		for name in self.grammar.rules:
			self.add('bool peggy_parse_' + name + '(struct peggy_parser_s *p, size_t i, struct peggy_result_s *result, bool ast);')
		
		self.add(CPreamble)

		for name in sorted(self.grammar.rules.keys()):
			if self.grammar.rules[name].isLeftRecursive():
				self.add("/* Left Recursive Rule */")
			self.genExprRule(self.grammar.rules[name])
		
		self.add(CFooter)

	def genExprRule(self, e):
		self.add('/*')
		self.add(str(e).replace('/*', '/ *').replace('*/', '* /'))
		self.add(e.draw('').replace('/*', '/ *').replace('*/', '* /'))
		self.add('*/')
		self.add('bool peggy_parse_' + e.name + '(struct peggy_parser_s *p, size_t i, struct peggy_result_s *result, bool ast) {')
		self.incBlockLevel()
		#self.add('printf("-> %s: %%lu\\n", i);'%e.name)
		#if [c for c in e.find(Expr.TYPE_CALL) if c.ast and not c.isPredicate()]:
		if e.ast:
			self.add('struct peggy_node_s node;')
			self.add('memset(&node, 0, sizeof(node));')
			self.add('node.type = %s;'%e.getAstName())
		l = len(self.lines)
		self.resetStack()
		rec = e.isLeftRecursive()
		if rec:
			self.genWhileStart('peggy_rec_memo(p, %s, i, *result)'%e.getAstName())
			if e.ast:
				self.add('result->node = node;')
			self.add('peggy_set_memo(p, %s, i, *result);'%e.getAstName())
			if e.ast:
				self.add('memset(&node, 0, sizeof(node));')
				self.add('node.type = %s;'%e.getAstName())
			# REC
		self.genExpr(e.data)
		if rec:
			self.genWhileEnd()
			self.add('peggy_get_memo(p, %s, i, result);'%e.getAstName())
			if e.ast:
				self.add('peggy_node_clean(&node, false);')
				self.add('node = result->node;');
		#if [c for c in e.find(Expr.TYPE_CALL) if c.ast and not c.isPredicate()]:
		self.add('result->n = 0;')
		if e.ast:
			self.genIfStart('result->v && ast')
			self.add('result->node = node;')
			self.add('result->n = 1;')
			self.add('result->node.str = p->input+i;')
			self.add('result->node.len = result->o;')
			self.add('result->node.i = i;')
			if e.ast:
				self.genElse()
				self.add('peggy_node_clean(&node, false);')
			self.genIfEnd()
		if self.max_stack_depth >= 0:
			self.add('struct peggy_result_s results[' + str(self.max_stack_depth+1) + "];", index = l)
		#self.add('printf("<- %s: %%d, %%lu, %%lu\\n", result->v, result->o, result->n);'%e.name)
		self.add('return true;')
		self.decBlockLevel()
		self.add('}')
		self.add('')

	def genStackReset(self):
		if self.stack_depth > 0:
			self.add('memset(results+' + str(self.stack_depth) + ', 0, sizeof(results[' + str(self.stack_depth) + ']));')
		else:
			self.add('memset(results, 0, sizeof(results[' + str(self.stack_depth) + ']));')

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
		#self.add('peggy_node_clean(&result->node, false);')
		self.add('memset(result, 0, sizeof(*result));')

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
		self.add("results[" + str(self.stack_depth) + "].n += result->n;")

	def genASTAddNode(self):
		if self.stack_depth >= 0:
			self.add('node.current = ' + '+'.join(["results[" + str(i) + "].n" for i in range(0, self.stack_depth+1)]) + ';')
		else:
			self.add('node.current = 0;')
		self.add("ast_add_child(&node, result->node);")

	def genStackAccumulateAST(self):
		pass
		#self.add("results[" + str(self.stack_depth) + "].n += 1;")

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
		if e.isPredicate() or not e.doAst():
			self.add("peggy_parse_" + e.data + "(p, result->o, result, false);")
		else:
			self.add("peggy_parse_" + e.data + "(p, result->o, result, ast);")
		#self.add("print '\t' * depth + name,'=> " + e.data + " after',result.v,result.o,result.n,'['+result.node.str+']'")
		
	def genExprWildcard(self, e):
		self.genResultOffset()
		self.add("peggy_match_wildcard(p, result->o, result);")

generators['c'] = CGenerator