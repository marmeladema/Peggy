from . import generators, Generator, ImperativeGenerator
from ..grammar import *
from ..expr import *

PythonPreamble = """
import traceback, sys
def match_sensitive_string(p, i, s):
	if i + len(s) <= p.length and p.input[i:i+len(s)] == s:
		return len(s)
	else:
		return 0

def match_insensitive_string(p, i, s):
	if i + len(s) <= p.length and p.input[i:i+len(s)].lower() == s.lower():
		return len(s)
	else:
		return 0

def match_range(p, i, r):
	if i < p.length and p.input[i] in r:
		return 1
	else:
		return 0

def match_wildcard(p, i):
	if i < p.length:
		return 1
	else:
		return 0

class AstNode:
	def __init__(self, t = 0):
		self.type =  t
		self.children = []
		self.current = 0
		self.str = ''
		self.i = 0
	
	def assign(self, n):
		self.type = n.type
		self.children = n.children
		self.current = n.current
		self.str = n.str
		self.i = n.i

class Result:
	def __init__(self):
		self.o = 0
		self.v = False
		self.n = 0
		self.node = AstNode()
	
	def assign(self, r):
		self.o = r.o
		self.v = r.v
		self.n = r.n
		self.node.assign(r.node)

class Parser:
	def __init__(self, input, start):
		self.input = input
		self.length = len(input)
		self.start = start
		self.rec = [[] for i in range(AST_TYPE_MAX)]

	def parse(self):
		return self.start(self, 0)

def ast_add_child(node, child):
	#print "ast_add_child:",AST_STRINGS[node.type], AST_STRINGS[child.type]
	#traceback.print_stack(file=sys.stdout)
	if node.current >= len(node.children):
		#node.children.append(child)
		node.children.append(AstNode())
		node.current = len(node.children)-1
	node.children[node.current].assign(child)
	node.current += 1

def ast_print(node, prefix=''):
	if prefix:
		print prefix[:-3]+'  +--'+AST_STRINGS[node.type]+' [' + node.str + '](' + str(node.i) + ')'
	else:
		print AST_STRINGS[node.type]+' [' + node.str + '](' + str(node.i) + ')'
	
	if len(node.children):
		for child in node.children[:-1]:
			ast_print(child, prefix+'  |')
		ast_print(node.children[-1], prefix+'   ')

def parser_get_recursion(p, r, i):
	for entry in p.rec[r]:
		if entry[0] == i:
			return entry[1]
	return None

def parser_set_recursion(p, r, i, o):
	for entry in p.rec[r]:
		if entry[0] == i:
			entry[1].assign(o)
			return True
	p.rec[r].append([i, Result()])
	p.rec[r][-1][1].assign(o)
	return None
	
"""		

class PythonGenerator(ImperativeGenerator):
	def __init__(self, g):
		ImperativeGenerator.__init__(self, g)

	def genStackReset(self):
		self.add("results[" + str(self.stack_depth) + "].v = False")
		self.add("results[" + str(self.stack_depth) + "].o = 0")
		self.add("results[" + str(self.stack_depth) + "].n = 0")

	def push(self):
		Generator.push(self)
		self.genStackReset()

	def pop(self):
		self.add('result.assign(results[' + str(self.stack_depth) + '])')
		Generator.pop(self)

	def genResultOffset(self):
		self.add('result.o = ' + '+'.join(['i']+["results[" + str(i) + "].o" for i in range(0, self.stack_depth+1)]))

	def genResultValidOffset(self):
		self.add('result.v = result.o > 0')

	def genResultInvalidOffset(self):
		self.add('result.v = not (result.o > 0)')

	def genResultValid(self):
		self.add('result.v = True')

	def genResultResetOffset(self):
		self.add('result.o = 0')

	def genResultReset(self):
		self.add('result.v = False')
		self.add('result.o = 0')

	def genIfStart(self, cond):
		self.add('if ' + cond + ':')
		self.incBlockLevel()

	def genElse(self):
		self.decBlockLevel()
		self.add('else:')
		self.incBlockLevel()

	def genIfEnd(self):
		self.decBlockLevel()

	def genIf(self, cond, code):
		self.genIfStart(cond)
		self.add(code)
		self.genIfEnd()

	def genWhileStart(self, cond):
		self.add('while ' + cond + ':')
		self.incBlockLevel()

	def genWhileEnd(self):
		self.decBlockLevel()

	def genBreak(self):
		self.add('break')

	def genStackAccumulateOffset(self):
		self.add("results[" + str(self.stack_depth) + "].o += result.o")

	def genASTAddNode(self):
		if self.stack_depth >= 0:
			self.add('node.current = ' + '+'.join(["results[" + str(i) + "].n" for i in range(0, self.stack_depth+1)]))
		else:
			self.add('node.current = 0')
		self.add("ast_add_child(node, result.node)")

	def genStackAccumulateAST(self):
		self.add("results[" + str(self.stack_depth) + "].n += 1")

	def condResultValid(self):
		return 'result.v'

	def condResultValidStrict(self):
		return 'result.v and result.o > 0'

	def condResultInvalid(self):
		return 'not result.v'

	def condTrue(self):
		return 'True'

	def condResultValidAst(self):
		return 'result.v and result.n > 0 and ast'

	def genGrammar(self):
		self.add("AST_STRINGS = []")
		i = 0
		for name in self.grammar.rules:
			self.add("%s = %d"%(self.grammar.rules[name].getAstName(),i))
			self.add("AST_STRINGS.append(\"%s\")"%(name,))
			i += 1
		self.add("AST_TYPE_MAX = %u"%(len(self.grammar.rules)+1,))
		
		self.add(PythonPreamble)
		for name in sorted(self.grammar.rules.keys()):
			self.add("# ---------------------- #")
			if self.grammar.rules[name].isLeftRecursive():
				self.add("# Left Recursive Rule")
			self.genExprRule(self.grammar.rules[name])

	def genExprRule(self, e):
		self.add("# "+str(e))
		e.draw('#', self)
		self.add("def match_rule_" + e.name + "(p, i, ast = True, depth = 0):")
		self.block_level += 1
		#self.add("print '\t' * depth + '" + e.name + "(p, ' + str(i) + ')'")
		self.add("name = '" + e.name + "'")
		self.add("node = AstNode(" + e.getAstName() + ")")
		self.add("result = Result()")
		l = len(self.lines)
		self.resetStack()
		rec = e.isLeftRecursive()
		if rec:
			self.add("rec = parser_get_recursion(p, %s, i)"%(e.getAstName()))
			self.add("while rec is None or result.o > rec.o:")
			self.block_level += 1
			self.add("parser_set_recursion(p, %s, i, result)"%(e.getAstName()))
			self.add("rec = parser_get_recursion(p, %s, i)"%(e.getAstName()))
			self.add("rec.node.assign(node)")
			self.add("node = AstNode(" + e.getAstName() + ")")
		self.genExpr(e.data)
		if rec:
			self.block_level -= 1
			self.add("result.assign(rec)")
			self.add("node = rec.node")

		self.add('if result.v:')
		self.add("\tresult.node = node")
		self.add("\tresult.n = 1")
		self.add("\tresult.node.str = p.input[i:i+result.o]")
		self.add("\tresult.node.i = i")
		#self.genIfEnd()
		if self.max_stack_depth >= 0:
			self.add("results = [" + ",".join(["Result()"] * (self.max_stack_depth+1)) + "]", index = l)
		self.add("return result")
		self.block_level -= 1

	def genExprString(self, e):
		self.genResultOffset()
		self.add("result.o = match_sensitive_string(p, result.o, '" + escape_string(e.data) + "')")
	
	def genExprStringInsensitive(self, e):
		self.genResultOffset()
		self.add("result.o = match_insensitive_string(p, result.o, '" + escape_string(e.data) + "')")
	
	def genExprRange(self, e):
		self.genResultOffset()
		self.add("result.o = match_range(p, result.o, '"+ escape_string(e.data) + "')")
		
	def genExprCall(self, e):
		#self.add("print '\t' * depth + name,'=> " + e.data + " before'")
		self.genResultOffset()
		if e.isPredicate():
			self.add("result.assign(match_rule_" + e.data + "(p, result.o, False, depth+1))")
		else:
			self.add("result.assign(match_rule_" + e.data + "(p, result.o, ast, depth + 1))")
		#self.add("print '\t' * depth + name,'=> " + e.data + " after',result.v,result.o,result.n,'['+result.node.str+']'")
		
	def genExprWildcard(self, e):
		self.genResultOffset()
		self.add("result.o = match_wildcard(p, result.o)")

	def write(self, output, append=None):
		output = open(output + '.py', 'w')
		output.write(str(self))
		if append:
			output.write(append)
		output.close()


class PythonGenerator2(Generator):
	def __init__(self, g):
		Generator.__init__(self, g)
		self.block_depth = 0

	def generate(self):
		self.gen(self.grammar)

	def gen(self, e):
		if isinstance(e, Grammar):
			return self.genGrammar(e)
		if isinstance(e, ExprRule):
			return self.genExprRule(e)
		elif isinstance(e, ExprOr):
			self.genExprOr(e)
		elif isinstance(e, ExprAnd):
			self.genExprAnd(e)
		elif isinstance(e, ExprStringSensitive):
			self.genExprString(e)
		elif isinstance(e, ExprStringInsensitive):
			self.genExprStringI(e)
		elif isinstance(e, ExprRange):
			self.genExprRange(e)
		elif isinstance(e, ExprCall):
			self.genExprCall(e)
		elif isinstance(e, ExprWildcard):
			self.genExprWildcard(e)
		
		#if e.prefix:
		#if not isinstance(e, ExprOr) and not isinstance(e, ExprAnd):
		#self.genSuffix(e)

	def push(self):
		Generator.push(self)
		self.add("results[" + str(self.stack_depth) + "].o = 0")
		self.add("results[" + str(self.stack_depth) + "].v = False")

	def pop(self):
		self.add('result.assign(results[" + str(self.stack_depth) + "])')
		Generator.push(pop)

	def incIndent(self):
		self.block_depth += 1

	def decIndent(self):
		self.block_depth -= 1

	def genIfStart(self, cond):
		self.add('if ' + cond + ':')
		self.incIndent()

	def genIfEnd(self):
		self.decIndent()

	def genIf(self, cond, code):
		self.genIfStart(cond)
		self.add(code)
		self.genIfEnd()

	def genWhileStart(self, cond):
		self.add('while ' + cond + ':')
		self.incIndent()

	def genWhileEnd(self):
		self.decIndent()
	
	def genGrammar(self, g):
		self.add("AST_STRINGS = []")
		self.add("AST_TYPE_UNKNOWN = 0")
		self.add("AST_STRINGS.append(\"UNKNOWN\")")
		i = 0
		for name in g.rules:
			self.add("%s = %d"%(g.rules[name].getAstName(),i+1))
			self.add("AST_STRINGS.append(\"%s\")"%(name,))
			i += 1
		self.add("AST_TYPE_MAX = %u"%(len(g.rules)+1,))
		
		self.add(PythonPreamble)
		for name in sorted(g.rules.keys()):
			self.add("# ---------------------- #")
			if g.rules[name].isLeftRecursive():
				self.add("# Left Recursive Rule")
			self.gen(g.rules[name])

	def genOffset(self):
		self.add('result.o = ' + '+'.join(['i']+["results[" + str(i) + "].o" for i in range(0, self.stack_depth+1)]))

	def genNode(self, block=0):
		self.add('\t' * block + 'node.current = ' + '+'.join(['0']+["results[" + str(i) + "].n" for i in range(0, self.stack_depth+1)]))
	
	def genSuffix(self, e):
		if '?' == e.modifier:
			self.gen(e)
			self.add('result.v = True')
		elif '*' == e.modifier:
			self.push()
			#self.add("results[" + str(self.stack_depth) + "].o = 0")
			#self.add("results[" + str(self.stack_depth) + "].v = False")
			self.add('while True:')
			self.block_depth += 1
			self.gen(e)
			self.add('if result.v != True or result.o <= 0:')
			
			self.block_depth += 1
			self.add('break')
			self.block_depth -= 1
			
			self.add('else:')
			
			self.block_depth += 1
			self.add("results[" + str(self.stack_depth) + "].o += result.o")
			self.genAst(e)
			self.block_depth -= 1
			
			self.block_depth -= 1
			self.add("results[" + str(self.stack_depth) + "].v = True")
			self.add("result.assign(results[" + str(self.stack_depth) + "])")
			self.pop()
		elif '+' == e.modifier:
			self.push()
			#self.add("results[" + str(self.stack_depth) + "].o = 0")
			#self.add("results[" + str(self.stack_depth) + "].v = False")
			self.add('while True:')
			self.block_depth += 1
			self.gen(e)
			self.add('if result.v != True or result.o <= 0:')
			self.add('\tbreak')
			self.add('else:')
			self.add("\tresults[" + str(self.stack_depth) + "].o += result.o")
			self.add("\tresults[" + str(self.stack_depth) + "].n += result.n")
			self.add("\tresults[" + str(self.stack_depth) + "].v = True")
			self.genAst(e)
			self.block_depth -= 1
			self.add("result.assign(results[" + str(self.stack_depth) + "])")
			self.pop()
		elif '&' == e.modifier:
			self.gen(e)
			self.add("result.v = result.o > 0")
			self.add("result.o = 0")
		elif '!' == e.modifier:
			self.gen(e)
			self.add("result.v = not (result.o > 0)")
			self.add("result.o = 0")
		else:
			self.gen(e)
			self.add("result.v = result.o > 0")

	def genExprRule(self, e):
		self.add("# "+str(e))
		e.draw('#', self)
		self.add("def match_rule_" + e.name + "(p, i, ast = True, depth = 0):")
		self.block_depth += 1
		#self.add("print '\t' * depth + '" + e.name + "(p, ' + str(i) + ')'")
		self.add("name = '" + e.name + "'")
		self.add("node = AstNode(" + e.getAstName() + ")")
		self.add("result = Result()")
		l = len(self.lines)
		self.resetStack()
		self.genSuffix(e.data)
		del self.lines[l:]
		if self.max_stack_depth >= 0:
			self.add("results = [" + ",".join(["Result()"] * (self.max_stack_depth+1)) + "]")
		rec = e.isLeftRecursive()
		if rec:
			self.add("rec = parser_get_recursion(p, %s, i)"%(e.getAstName()))
			self.add("while rec is None or result.o > rec.o:")
			self.block_depth += 1
			self.add("parser_set_recursion(p, %s, i, result)"%(e.getAstName()))
			self.add("rec = parser_get_recursion(p, %s, i)"%(e.getAstName()))
			self.add("rec.node.assign(node)")
			self.add("node = AstNode(" + e.getAstName() + ")")
		self.genSuffix(e.data)
		if rec:
			self.block_depth -= 1
			self.add("result.assign(rec)")
			self.add("node = rec.node")
		self.add('if result.v:')
		self.add("\tresult.node = node")
		self.add("\tresult.n = 1")
		self.add("\tresult.node.str = p.input[i:i+result.o]")
		self.add("\tresult.node.i = i")
		self.add("return result")
		self.block_depth -= 1
	
	def genExprOr(self, e, ast = False):
		#self.add("# ExprOr(depth=%d, ast=%d): start"%(self.stack_depth, ast))
		if not e.isAtomic():
			self.push()
		self.add("result.v = False")
		for i in range(0, len(e.data)):
			#self.add("if not result.v:")
			#self.block_depth += 1
			self.genIfStart('not result.v')
			if not e.isAtomic() and not e.data[i].isPredicate():
					self.add("results[" + str(self.stack_depth) + "].n = 0")
					self.genNode()
			self.genSuffix(e.data[i])
			if e.data[i].isAtomic():
				#self.add("if result.v and result.n > 0 and ast:")
				#self.add("\tast_add_child(node, result.node)")
				self.genIf('result.v and result.n > 0 and ast', 'ast_add_child(node, result.node)')
			#self.block_depth -= 1
			self.genIfEnd()
		if not e.isAtomic():
			self.pop()
		#self.add("# ExprOr(depth=%d, ast=%d): end"%(self.stack_depth, ast))
	"""
	def genExprOr(self, e, ast = False):
		#self.add("# ExprOr(depth=%d, ast=%d): start"%(self.stack_depth, ast))
		self.add("result.v = False")
		block = self.block_depth
		for i in range(0, len(e.data)):
			self.add("if not result.v:")
			self.block_depth += 1
			if not e.data[i].isAtomic():
				self.push()
				self.add("results[" + str(self.stack_depth) + "].o = 0")
				self.add("results[" + str(self.stack_depth) + "].v = False")
				if not e.data[i].isPredicate():
					self.genNode()
					self.add("results[" + str(self.stack_depth) + "].n = 0")
			self.genSuffix(e.data[i])
			if not e.data[i].isAtomic():
				self.pop()
			else:
				self.add("if result.v and result.n > 0 and ast:")
				self.add("\tast_add_child(node, result.node)")
			self.block_depth -= 1
"""

	def genExprAnd(self, e, ast = False):
		#self.add("# ExprAnd(depth=%d, ast=%d): start"%(self.stack_depth, ast))
		#if e.suffix == '*' or e.suffix == '+':
		if not e.parent or e.parent.type != Expr.TYPE_OR:
			self.push()
			#self.add("results[" + str(self.stack_depth) + "].o = 0")
			#self.add("results[" + str(self.stack_depth) + "].v = False")
		depth = self.block_depth
		for i in range(0, len(e.data)):
			self.genSuffix(e.data[i])
			#self.add("if result.v:")
			#self.block_depth += 1
			self.genIfStart('result.v')
			self.add("results[" + str(self.stack_depth) + "].o += result.o")
			if e.data[i].modifier != '*' and e.data[i].modifier != '+':
				self.genAst(e.data[i])
			#else:
			#	self.add("results[" + str(self.stack_depth) + "].n += result.n")
			if i+1 == len(e.data):
				self.add("results[" + str(self.stack_depth) + "].v = True")
		self.add("result.assign(results[" + str(self.stack_depth) + "])")
		self.block_depth = depth
		#if e.suffix == '*' or e.suffix == '+':
		if not e.parent or e.parent.type != Expr.TYPE_OR:
			self.pop()
		#self.add("# ExprAnd(depth=%d, ast=%d): end"%(self.stack_depth, ast))
	
	def genExprString(self, e):
		self.genOffset()
		self.add("result.o = match_sensitive_string(p, result.o, '" + escape_string(e.data) + "')")
	
	def genExprStringI(self, e):
		self.genOffset()
		self.add("result.o = match_insensitive_string(p, result.o, '" + escape_string(e.data) + "')")
	
	def genExprRange(self, e):
		self.genOffset()
		self.add("result.o = match_range(p, result.o, '"+ escape_string(e.data) + "')")
		
	def genExprCall(self, e):
		self.add("print '\t' * depth + name,'=> " + e.data + " before'")
		self.genOffset()
		if e.isPredicate():
			self.add("result.assign(match_rule_" + e.data + "(p, result.o, False, depth+1))")
		else:
			self.add("result.assign(match_rule_" + e.data + "(p, result.o, ast, depth + 1))")
		self.add("print '\t' * depth + name,'=> " + e.data + " after',result.v,result.o,result.n,'['+result.node.str+']'")
		
	def genExprWildcard(self, e):
		self.genOffset()
		self.add("result.o = match_wildcard(p, result.o)")
	
	def genAst(self, e):
		if e.type == Expr.TYPE_CALL:
			self.add("# "+e.data+","+str(self.grammar.rules[e.data].ast))
		if e.type == Expr.TYPE_CALL and not e.isPredicate() and e.ast and self.grammar.rules[e.data].ast:
			self.add("if result.n > 0 and ast:")
			self.add("\tast_add_child(node, result.node)")
			self.add("\tresults[" + str(self.stack_depth) + "].n += 1")
		#else:
		#	self.add("results[" + str(self.stack_depth) + "].n += result.n")

	def write(self, output, append=None):
		output = open(output + '.py', 'w')
		output.write(str(self))
		if append:
			output.write(append)
		output.close()

generators['python'] = PythonGenerator