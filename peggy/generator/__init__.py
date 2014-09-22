from ..expr import *

generators = {}

class Generator:
	def __init__(self, g):
		self.grammar = g
		self.lines = []
		self.resetStack()

	def add(self, line, index = None):
		if index is None:
			self.lines.append(line)
		else:
			self.lines.insert(index, line)

	def resetStack(self):
		self.stack_depth = -1
		self.max_stack_depth = -1

	def push(self):
		self.stack_depth += 1
		if self.stack_depth > self.max_stack_depth:
			self.max_stack_depth = self.stack_depth

	def pop(self):
		self.stack_depth -= 1

	def generate(self):
		self.genGrammar()
	
	def __str__(self):
		return '\n'.join(self.lines)+'\n\n'

class ImperativeGenerator(Generator):
	def __init__(self, g):
		Generator.__init__(self, g)
		self.block_level = 0

	def add(self, line, index = None):
		Generator.add(self, '\t' * self.block_level + line, index)

	def saveBlockLevel(self):
		return self.block_level

	def restoreBlockLevel(self, bl):
		self.block_level = bl

	def incBlockLevel(self):
		self.block_level += 1

	def decBlockLevel(self):
		self.block_level -= 1

	def genIfStart(self, cond):
		raise NotImplementedError()

	def genIfEnd(self):
		raise NotImplementedError()

	def genIf(self, cond, code):
		raise NotImplementedError()

	def genElse(self):
		raise NotImplementedError()

	def genWhileStart(self, conf):
		raise NotImplementedError()

	def genWhileEnd(self):
		raise NotImplementedError()

	def genWhile(self, cond, code):
		raise NotImplementedError()

	def genBreak(self):
		raise NotImplementedError()

	def genResultReset(self):
		raise NotImplementedError()

	def genResultResetValid(self):
		raise NotImplementedError()

	def genResultResetOffset(self):
		raise NotImplementedError()

	def genResultValidOffset(self):
		raise NotImplementedError()

	def genResultInvalidOffset(self):
		raise NotImplementedError()

	def genResultValid(self):
		raise NotImplementedError()

	def genResultOffset(self):
		raise NotImplementedError()

	def genStackReset():
		raise NotImplementedError()

	def genStackAccumulateOffset(self):
		raise NotImplementedError()

	def genStackAccumulateAST(self):
		raise NotImplementedError()

	def genExprValidAST(self, e):
		if e.type == Expr.TYPE_CALL and not e.isPredicate() and e.doAst() and self.grammar.rules[e.data].ast:
			self.genIfStart(self.condResultValidAst())
			self.genASTAddNode()
			if self.stack_depth >= 0:
				self.genStackAccumulateAST()
			self.genIfEnd()

	def condTrue(self):
		raise NotImplementedError()

	def condResultValid(self):
		raise NotImplementedError()

	def condResultValidStrict(self):
		raise NotImplementedError()

	def condResultInvalid(self):
		raise NotImplementedError()

	def condResultValidAst(self):
		raise NotImplementedError()

	def genExpr(self, e):
		#'''
		if e.modifier == '*' or e.modifier == '+':
			self.push()
			self.genWhileStart(self.condTrue())
		#'''

		if e.type == Expr.TYPE_OR:
			self.genExprOr(e)
		elif e.type == Expr.TYPE_AND:
			self.genExprAnd(e)
		elif e.type == Expr.TYPE_STRING:
			self.genExprString(e)
		elif e.type == Expr.TYPE_STRINGI:
			self.genExprStringInsensitive(e)
		elif e.type == Expr.TYPE_RANGE:
			self.genExprRange(e)
		elif e.type == Expr.TYPE_CALL:
			self.genExprCall(e)
		elif e.type == Expr.TYPE_WILDCARD:
			self.genExprWildcard(e)
		else:
			raise ValueError()

		if e.modifier == '?':
			self.genResultValid()
		elif e.modifier == '&':
			self.genResultValidOffset()
			self.genResultResetOffset()
		elif e.modifier == '!':
			self.genResultInvalidOffset()
			self.genResultResetOffset()
		else:
			self.genResultValidOffset()

		self.genExprValidAST(e)

		#'''
		if e.modifier == '*' or e.modifier == '+':
			#self.genIfExprValid(e, self.condResultValidStrict(), True)
			self.genIfStart(self.condResultValidStrict())
			self.genStackAccumulateOffset()
			self.genElse()
			self.genBreak()
			self.genIfEnd()
			self.genWhileEnd()
			self.pop()
			if e.modifier == '*':
				self.genResultValid()
			elif e.modifier == '+':
				self.genResultValidOffset()
			else:
				raise ValueError()
		#'''

	def genExprOr(self, e):
		""" Generate code for OR expression """

		# reset result before OR expression
		#if len(e.data) > 0:
		#	self.genResultReset()
		
		for child in e.data:
			# if the previous result is invalid
			if child != e.data[0]:
				self.genIfStart(self.condResultInvalid())
			self.genExpr(child)
			if child != e.data[0]:
				self.genIfEnd()
			#self.genIfExprValid(child, self.condResultValid(), child.modifier != '*' and child.modifier != '+')
			#if child != e.data[-1]:
			#	self.genElse()

		#for child in e.data:
		#	self.genIfEnd()

	def genExprAnd(self, e):
		""" Generate code for AND expression """

		#self.add('# Before AND(%s) block_level: %s'%(repr(e), str(self.block_level)))

		if len(e.data) > 1:
			self.push()
		
		for child in e.data:
			self.genExpr(child)
			if len(e.data) > 1:
				#self.genIfExprValid(child, self.condResultValid(), child.modifier != '*' and child.modifier != '+')
				self.genIfStart(self.condResultInvalid())
				self.genStackReset()
				self.genElse()
				self.genStackAccumulateOffset()
		for child in e.data:
			self.genIfEnd()

		if len(e.data) > 1:
			self.pop()

		#self.add('# After AND(%s) block_level: %s'%(repr(e), str(self.block_level)))

	def genExprString(self, e):
		raise NotImplementedError()

	def genExprStringInsensitive(self, e):
		raise NotImplementedError()

	def genExprRange(self, e):
		raise NotImplementedError()

	def genExprCall(self, e):
		raise NotImplementedError()

	def genExprWildcard(self, e):
		raise NotImplementedError()