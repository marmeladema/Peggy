EscapeChar = {'a': '\a', 'b': '\b', 'f': '\f', 'n': '\n', 'r': '\r', 't': '\t', 'v': '\v', '\\': '\\', '"': '"', '\'': '\''}
CharEscape = dict((v,k) for k,v in EscapeChar.items())

def escape_string(s):
	e = ''
	for c in s:
		if c in CharEscape:
			e += '\\' + CharEscape[c]
		else:
			e += c
	return e

def sum_gen_python(depth):
	s = '+'.join(["results[" + str(i) + "].o" for i in range(0, depth)])
	if s:
		s = 'i+'+s
	else:
		s = 'i'
	return s

def prefixMerge(p1, p2):
	if p1 == p2:
		return p1
	if not p1:
		return p2
	if not p2:
		return p1
	return False

def suffixMerge(s1, s2):
	if s1 == s2:
		return s1
	if not s1:
		return s2
	if not s2:
		return s1
	return False

prefixes = "!&"
suffixes = "+?*"

class Expr:
	TYPE_RULE = 0
	TYPE_OR = 1
	TYPE_AND = 2
	TYPE_STRING = 3
	TYPE_STRINGI = 4
	TYPE_RANGE = 5
	TYPE_CALL = 6
	TYPE_WILDCARD = 7

	def __init__(self, t, ast):
		self.modifier = ''
		self.ast = ast
		self.type = t
		self.data = None
		self.final = False
		self.parent = None

	def __str__(self):
		s = ''
		if not self.ast and self.type == Expr.TYPE_CALL:
			s += ':'
		if self.modifier and self.modifier in prefixes:
				s += self.modifier
		s += "%s"
		if self.modifier and self.modifier in suffixes:
				s += self.modifier
		return s
	
	def draw(self, prefix='', generator=None):
		if prefix:
			line = prefix[:-3]+'  +--'+str(self)
		else:
			line = str(self)
		
		if generator:
			generator.add(line)
		else:
			print line

	def getDepth(self):
		return int(self.suffix == '*' or self.suffix == '+')
	
	def getRoot(self):
		current = self
		while current.parent:
			current = current.parent
		return current
	
	def optimize(self):
		pass

	def finalize(self):
		pass

	def isAtomic(self):
		return True
	
	def isLeftRecursive(self, seen):
		return False

	def isPredicate(self):
		if self.modifier and self.modifier in prefixes:
			return True
		if self.parent:
			return self.parent.isPredicate()
		return False

	def doAst(self):
		if not self.ast:
			return False
		elif self.parent:
			return self.parent.doAst()
		else:
			return True

	def find(self, t, rec = True):
		if self.type == t:
			return [self]
		else:
			return []

class ExprRule(Expr):
	def __init__(self, name, grammar, ast = True):
		Expr.__init__(self, Expr.TYPE_RULE, ast = ast)
		self.name = name
		self.grammar = grammar
	
	def __str__(self):
		return "%s <= %s"%(self.name, str(self.data))
	
	def draw(self, prefix='', generator=None):
		line = prefix+self.name
		if generator:
			generator.add(line)
		else:
			print line
		self.data.draw(prefix+'   ', generator)
	
	def getDepth(self):
		return 1+self.data.getDepth()
	
	def getAstName(self):
		return "PEGGY_NODE_%s"%(self.name.upper(),)
	
	def optimize(self):
		self.data.optimize()
		if (self.data.type == Expr.TYPE_OR or self.data.type == Expr.TYPE_AND):
			#if len(self.data.data) == 1 and len(self.data.prefix+self.data.data[0].prefix) < 2 and len(self.data.suffix+self.data.data[0].suffix) < 2:
			if len(self.data.data) == 1 and (not self.data.modifier or not self.data.data[0].modifier):
				m = self.data.modifier + self.data.data[0].modifier
				self.data = self.data.data[0]
				self.data.modifier = m

	def finalize(self):
		self.data.finalize()
		self.data.parent = self
	
	def isLeftRecursive(self, seen=None):
		if seen is None:
			seen = []
		if self.name not in seen:
			seen.append(self.name)
			return self.data.isLeftRecursive(seen)
		return False

	def find(self, t, rec = True):
		res = Expr.find(self, t, rec)
		if rec:
			res.extend(self.data.find(t, True))
		return res

class ExprOr(Expr):
	def __init__(self, ast = True):
		Expr.__init__(self, Expr.TYPE_OR, ast = ast)
		self.data = []

	def __str__(self):
		s = ''
		if self.modifier or len(self.data) > 1:
			s += '('
		s += " | ".join([str(c) for c in self.data])
		if self.modifier or len(self.data) > 1:
			s += ')'
		return Expr.__str__(self)%(s,)
	
	def draw(self, prefix='', generator=None):
		p,s = '',''
		if self.modifier and self.modifier in prefixes:
			p = self.modifier
		elif self.modifier and self.modifier in suffixes:
			s = self.modifier

		line = prefix[:-3]+'  +--'+p+'ExprOr'+s
		if generator:
			generator.add(line)
		else:
			print line
		for e in self.data[:-1]:
			e.draw(prefix+'  |', generator)
		self.data[-1].draw(prefix+'   ', generator)

	def getDepth(self):
		return max([e.getDepth() for e in self.data])+Expr.getDepth(self)

	def optimize(self):
		for i in range(0, len(self.data)):
			self.data[i].optimize()
			if self.data[i].type == Expr.TYPE_AND:
				#if len(self.data[i].data) == 1 and len(self.data[i].prefix+self.data[i].data[0].prefix) < 2 and len(self.data[i].suffix+self.data[i].data[0].suffix) < 2:
				if len(self.data[i].data) == 1 and (not self.data[i].modifier or not self.data[i].data[0].modifier):
					m = self.data[i].modifier + self.data[i].data[0].modifier
					self.data[i] = self.data[i].data[0]
					self.data[i].modifier = m

	def finalize(self):
		for i in range(0, len(self.data)):
			self.data[i].finalize()
			self.data[i].parent = self

	def isAtomic(self):
		for e in self.data:
			if e.type == Expr.TYPE_OR or e.type == Expr.TYPE_AND:
				return False
		return True
	
	def isLeftRecursive(self, seen):
		for e in self.data:
			if e.isLeftRecursive(seen):
				return True
		return False

	def find(self, t, rec = True):
		res = Expr.find(self, t, rec)
		if rec:
			for child in self.data:
				res.extend(child.find(t, True))
		return res

class ExprAnd(Expr):
	def __init__(self, ast = True):
		Expr.__init__(self, Expr.TYPE_AND, ast = ast)
		self.data = []

	def __str__(self):
		s = ''
		# if self.modifier or len(self.data) > 1:
		if self.modifier:
			s += '('
		s += " ".join([str(c) for c in self.data])
		# if self.modifier or len(self.data) > 1:
		if self.modifier:
			s += ')'
		return Expr.__str__(self)%(s,)
	
	def draw(self, prefix='', generator=None):
		p,s = '',''
		if self.modifier and self.modifier in prefixes:
			p = self.modifier
		elif self.modifier and self.modifier in suffixes:
			s = self.modifier

		line = prefix[:-3]+'  +--'+p+'ExprAnd'+s
		if generator:
			generator.add(line)
		else:
			print line
		for e in self.data[:-1]:
			e.draw(prefix+'  |', generator)
		self.data[-1].draw(prefix+'   ', generator)

	def getDepth(self):
		return max([int(e.type == Expr.TYPE_OR)+e.getDepth() for e in self.data])+Expr.getDepth(self)
		#return 1+Expr.getDepth(self)

	def optimize(self):
		for i in range(0, len(self.data)):
			self.data[i].optimize()
			if self.data[i].type == Expr.TYPE_OR:
				if len(self.data[i].data) == 1 and (not self.data[i].modifier or not self.data[i].data[0].modifier):
					m = self.data[i].modifier + self.data[i].data[0].modifier
					self.data[i] = self.data[i].data[0]
					self.data[i].modifier = m

	def finalize(self):
		for i in range(0, len(self.data)):
			self.data[i].finalize()
			self.data[i].parent = self

	def isAtomic(self):
		return False
	
	def isLeftRecursive(self, seen):
		for e in self.data:
			if e.isLeftRecursive(seen):
				return True
			elif (not e.modifier or e.modifier not in '&!') and (not e.modifier or e.modifier not in '?*'):
				return False
		return False

	def find(self, t, rec = True):
		res = Expr.find(self, t, rec)
		if rec:
			for child in self.data:
				res.extend(child.find(t, True))
		return res

class ExprStringSensitive(Expr):
	def __init__(self, ast = False):
		Expr.__init__(self, Expr.TYPE_STRING, ast = ast)
		self.data = ''

	def __str__(self):
		return Expr.__str__(self)%("'%s'"%(escape_string(self.data),),)

class ExprStringInsensitive(Expr):
	def __init__(self, ast = False):
		Expr.__init__(self, Expr.TYPE_STRINGI, ast = ast)
		self.data = ''

	def __str__(self):
		return Expr.__str__(self)%("\"%s\""%(escape_string(self.data),),)

class ExprRange(Expr):
	def __init__(self, ast = False):
		Expr.__init__(self, Expr.TYPE_RANGE, ast = ast)
		self.data = ''

	def __str__(self):
		return Expr.__str__(self)%("[%s]"%(escape_string(self.data),),)

class ExprCall(Expr):
	def __init__(self, name, ast = True):
		Expr.__init__(self, Expr.TYPE_CALL, ast = ast)
		self.data = name

	def __str__(self):
		return Expr.__str__(self)%(self.data,)
	
	def isLeftRecursive(self, seen):
		if self.data == seen[0]:
			return True
		else:
			return self.getRoot().grammar.rules[self.data].isLeftRecursive(seen)

class ExprWildcard(Expr):
	def __init__(self, ast = False):
		Expr.__init__(self, Expr.TYPE_WILDCARD, ast = ast)
		self.data = ''

	def __str__(self):
		return Expr.__str__(self)%('.',)
