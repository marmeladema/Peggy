from . import Generator
from ..expr import *

preamble = """
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
	def __init__(self):
		self.type =  0
		self.children = []
		self.str = None
		self.len = 0

class Result:
	def __init__(self):
		self.o = 0
		self.v = False
		self.n = 0
		self.node = [] # AstNode()

class Parser:
	def __init__(self, input, start):
		self.input = input
		self.length = len(input)
		self.start = start

	def parse(self):
		return self.start(self, 0)

def ast_print(node, block):
	print "\t" * block + AST_STRINGS[node.type] + "<" + node.str + ">"
	for child in node.children:
		ast_print(child, block+1)
"""

class PythonGenerator(Generator):
	def __init__(self):
		Generator.__init__(self)
	
	def gen(self, e):
		if e.type == Expr.TYPE_OR:
			self.genExprOr(e)
		elif e.type == Expr.TYPE_AND:
			self.genExprAnd(e)
		elif e.type == Expr.TYPE_STRING:
			self.genExprString(e)
		elif e.type == Expr.TYPE_STRINGI:
			self.genExprStringI(e)
		elif e.type == Expr.TYPE_RANGE:
			self.genExprRange(e)
		elif e.type == Expr.TYPE_CALL:
			self.genExprRule(e)
		elif e.type == Expr.TYPE_WILDCARD:
			self.genExprWildcard(e)
			
		#if e.prefix:
		if e.type != Expr.TYPE_OR and e.type != Expr.TYPE_AND:
			self.genPrefix(e)
	
	def genOffset(self):
		self.add('result.o = ' + '+'.join(['i']+["results[" + str(i) + "].o" for i in range(0, self.stack_depth+1)]))
		
	def genPrefix(self, e):
		if '&' == e.prefix:
			self.add("result.v = result.o > 0")
			self.add("result.o = 0")
		elif '!' == e.prefix:
			self.add("result.v = not (result.o > 0)")
			self.add("result.o = 0")
		else:
			self.add("result.v = result.o > 0")
	
	def genSuffix(self, e):
		if '?' == e.suffix:
			self.gen(e)
			self.add('result.v = True')
		elif '*' == e.suffix:
			self.add('while True:')
			self.depth += 1
			self.gen(e)
			self.add('\tif result.v != True or result.o <= 0')
			self.add('\t\tbreak')
			self.add('\telse:')
			self.add('\t\tresults[].o += result.o')
			self.depth -= 1
			self.add('result[+1].v = True')
			#self.add('result = result[]')
		elif '+' == e.suffix:
			self.add('while True:')
			self.depth += 1
			self.gen(e)
			self.add('if result.v != True or result.o <= 0')
			self.add('\tbreak')
			self.add('else:')
			self.add('\tresults[].o += result.o')
			self.add('\tresults[].v += True')
			self.depth -= 1
			#self.add('result = result[]')
		else:
			self.gen(e)
		
	def genExprOr(self, e, ast = False):
		self.add("# ExprOr(depth=%d, ast=%d)"%(self.stack_depth, ast))
		#self.add("results[" + str(self.stack_depth) + "].o = 0")
		#self.add("results[" + str(self.stack_depth) + "].v = False")
		self.add("result.v = False")
		for i in range(0, len(e.data)):
			#self.add("if not results[" + str(self.stack_depth) + "].v:")
			self.add("if not result.v:")
			self.block_depth += 1
			self.stack_depth += 1
			self.add("results[" + str(self.stack_depth) + "].o = 0")
			self.add("results[" + str(self.stack_depth) + "].v = False")
			self.genSuffix(e.data[i])
			self.stack_depth -= 1
			self.add("if result.v:")
			self.add("\tresults[" + str(self.stack_depth) + "].o += result.o")
			self.add("\tresults[" + str(self.stack_depth) + "].v = True")
			self.block_depth -= 1
		#self.add('result = result[]')
		self.add("result = results[" + str(self.stack_depth) + "]")
	
	def genExprAnd(self, e, ast = False):
		self.add("# ExprAnd(depth=%d, ast=%d)"%(self.stack_depth, ast))
		#self.add("results[" + str(self.stack_depth) + "].o = 0")
		#self.add("results[" + str(self.stack_depth) + "].v = False")
		depth = self.block_depth
		for i in range(0, len(e.data)):
			self.genSuffix(e.data[i])
			#self.add("if not result.v:")
			#self.add("\tresults[" + str(self.stack_depth) + "].v = False")
			#self.add("else:")
			self.add("if result.v:")
			self.block_depth += 1
			self.add("results[" + str(self.stack_depth) + "].o += result.o")
			#self.add("results[" + str(self.stack_depth) + "].v = True")
		self.add("result = results[" + str(self.stack_depth) + "]")
		self.block_depth = depth
	
	def genExprString(self, e):
		self.genOffset()
		self.add("result.o = match_sensitive_string(p, result.o, '" + escape_string(e.data) + "')")
	
	def genExprStringI(self, e):
		self.genOffset()
		self.add("result.o = match_insensitive_string(p, result.o, '" + escape_string(e.data) + "')")
	
	def genExprRange(self, e):
		self.genOffset()
		self.add("result.o = match_range(p, result.o, '"+ escape_string(e.data) + "')")
		
	def genExprRule(self, e):
		self.genOffset()
		self.add("result = match_rule_" + e.data + "(p, result.o)")
		
	def genExprWildcard(self, e):
		self.genOffset()
		self.add("result.o = match_wildcard(p, result.o)")
	
	def __str__(self):
		return "\n".join(self.lines)