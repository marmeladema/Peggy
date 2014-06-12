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

def prefix_gen_python(e, depth, ast = True):
	lines = ["#expr: " + str(e)]
	if e.suffix == '+' or e.suffix == '*':
		lines.append("results[" + str(depth) + "].o = 0")
		lines.append("results[" + str(depth) + "].v = False")
		lines.append("while True:")
		lines += ["\t" + line for line in e.gen_python(depth + 1, ast)]
		lines += ["\tif l > 0:"]
		lines += ["\t\tresults[" + str(depth) + "].o += l"]
		lines += ["\telse:"]
		lines += ["\t\tbreak"]
		lines += ["l = results[" + str(depth) + "].o"]
		lines += ["m = results[" + str(depth) + "].v"]
	else:
		lines = e.gen_python(depth, ast)
	return lines

def sum_gen_python(depth):
	s = '+'.join(["results[" + str(i) + "].o" for i in range(0, depth)])
	if s:
		s = 'i+'+s
	else:
		s = 'i'
	return s

class Expr:
	TYPE_RULE = 0
	TYPE_OR = 1
	TYPE_AND = 2
	TYPE_STRING = 3
	TYPE_STRINGI = 4
	TYPE_RANGE = 5
	TYPE_CALL = 6
	TYPE_WILDCARD = 7

	def __init__(self, t):
		self.prefix = ''
		self.suffix = ''
		self.type = t
		self.data = None
		self.final = False

	def __str__(self):
		return self.prefix + "%s" + self.suffix

	def getDepth(self):
		return int(self.suffix == '*' or self.suffix == '+')

class ExprOr(Expr):
	def __init__(self):
		Expr.__init__(self, Expr.TYPE_OR)
		self.data = []

	def __str__(self):
		s = ''
		if len(self.data) > 1:
			s += '('
		s += " | ".join([str(c) for c in self.data])
		if len(self.data) > 1:
			s += ')'
		return Expr.__str__(self)%(s,)

	def gen_python(self, depth, ast = True):
		lines = []
		lines += ["# ExprOr(depth=%d, ast=%d)"%(depth, ast)]
		lines += ["results[" + str(depth) + "].o = 0"]
		lines += ["results[" + str(depth) + "].v = False"]
		#lines.append("n.append([])")
		for i in range(0, len(self.data)):
			lines += ["if results[" + str(depth) + "].o == 0:"]
			lines += ["\t" + line for line in prefix_gen_python(self.data[i], depth + 1, ast)]
		lines += ["l = results[" + str(depth) + "].o"]
		lines += ["m = results[" + str(depth) + "].v"]
		#lines.append("a = n.pop()")
		#lines.append("if len(n) > 1:")
		#lines.append("\ta = n.pop()")
		#lines.append("\tn[-1] += a")
		#lines.append("else:")
		#lines.append("\tn += a")
		return lines

	def getDepth(self):
		return 1+max([e.getDepth() for e in self.data])+Expr.getDepth(self)

	def optimize(self):
		for i in range(0, len(self.data)):
			if self.data[i].type == Expr.TYPE_AND:
				if len(self.data[i].data) == 1:
					self.data[i] = self.data[i].data[0]


class ExprAnd(Expr):
	def __init__(self):
		Expr.__init__(self, Expr.TYPE_AND)
		self.data = []

	def __str__(self):
		s = ''
		if self.prefix or len(self.data) > 1:
			s += '('
		s += " ".join([str(c) for c in self.data])
		if self.prefix or len(self.data) > 1:
			s += ')'
		return Expr.__str__(self)%(s,)

	def gen_python(self, depth, ast = True):
		#print self.prefix
		lines = []
		lines += ["# ExprAnd(depth=%d, ast=%d)"%(depth, ast)]
		block = 0
		for i in range(0, len(self.data)):
			lines += ["\t"*block + line for line in prefix_gen_python(self.data[i], depth, ast)]
			#lines += ["\t"*block + "# prefix:" + str(repr(self.data[i].prefix)) + "" + str(self.data[i - 1].prefix != '?' and self.data[i - 1].prefix != '*')]
			if self.data[i].prefix == '!':
				lines += ["\t"*block + "if l == 0:"]
				block += 1
			elif self.data[i].suffix != '?' and self.data[i].suffix != '*':
				lines.append("\t"*block + "if l > 0 or m:")
				block += 1
			if self.data[i].prefix != '!' and self.data[i].prefix != '&':
				lines += ["\t"*block + "# o[-1] += l"]
				lines += ["\t"*block + "results[" + str(depth - 1) + "].o += l"]
				if self.data[i].type == Expr.TYPE_CALL:
					lines.append("\t"*block + "results[0].node.children.append(result.node)")
					lines += ["\t"*block + "results[" + str(depth - 1) + "].n += 1"]
				#	lines.append("\t"*block + "n[-1].append(\"" + self.data[i].data + "\")")

		if self.data[-1].prefix == '!' or self.data[-1].prefix == '&':
			lines += ["\t"*block + "results[" + str(depth - 1) + "].v = True"]
		while block:
			block -= 1
			lines += ["\t"*block + "else:"]
			lines += ["\t"*(block + 1) + "# o[-1] = 0"]
			lines += ["\t"*(block + 1) + "results[" + str(depth - 1) + "].o = 0"]
			#lines.append("\t"*(block + 1) + "del results[0].node.children[-results[" + str(depth - 1) + "].n:]")
			#lines.append("\t"*(block + 1) + "del results[" + str(depth - 1) + "].node")
			lines.append("\t"*(block + 1) + "results[" + str(depth - 1) + "].n = 0")
			#lines.append("\t"*(block + 1) + "while results[" + str(depth - 1) + "].n > 0:")
			#lines.append("\t"*(block + 2) + "results[0].node.children.pop()")
			#lines.append("\t"*(block + 2) + "results[" + str(depth - 1) + "].n -= 1")
			#lines.append("\t" * (block + 1) + "del n[-1][:]")
		return lines

	def getDepth(self):
		return sum([e.getDepth() for e in self.data])+Expr.getDepth(self)
		#return 1+Expr.getDepth(self)

	def optimize(self):
		for i in range(0, len(self.data)):
			if self.data[i].type == Expr.TYPE_OR:
				if len(self.data[i].data) == 1:
					self.data[i] = self.data[i].data[0]

class ExprStringSensitive(Expr):
	def __init__(self):
		Expr.__init__(self, Expr.TYPE_STRING)
		self.data = ''

	def __str__(self):
		return Expr.__str__(self)%("'%s'"%(escape_string(self.data),),)

	def gen_python(self, depth, ast = True):

		lines = ["l = match_sensitive_string(p, " + sum_gen_python(depth) + ", '" + escape_string(self.data) + "')"]
		return lines

class ExprStringInsensitive(Expr):
	def __init__(self):
		Expr.__init__(self, Expr.TYPE_STRINGI)
		self.data = ''

	def __str__(self):
		return Expr.__str__(self)%("\"%s\""%(escape_string(self.data),),)

	def gen_python(self, depth, ast = True):
		lines = ["l = match_insensitive_string(p, " + sum_gen_python(depth) + ", '" + escape_string(self.data) + "')"]
		return lines

class ExprRange(Expr):
	def __init__(self):
		Expr.__init__(self, Expr.TYPE_RANGE)
		self.data = ''

	def __str__(self):
		return Expr.__str__(self)%("[%s]"%(escape_string(self.data),),)

	def gen_python(self, depth, ast = True):
		lines = ["l = match_range(p, " + sum_gen_python(depth) + ", '"+ escape_string(self.data) + "')"]
		return lines

class ExprRule(Expr):
	def __init__(self):
		Expr.__init__(self, Expr.TYPE_RULE)
		self.data = ''

	def __str__(self):
		return Expr.__str__(self)%(self.data,)

	def gen_python(self, depth, ast = True):
		lines = ["result = match_rule_" + self.data + "(p, " + sum_gen_python(depth) + ")"]
		lines.append("l = result.o")
		lines.append("m = result.v")
		return lines

class ExprWildcard(Expr):
	def __init__(self):
		Expr.__init__(self, Expr.TYPE_WILDCARD)
		self.data = ''

	def __str__(self):
		return Expr.__str__(self)%('.',)

	def gen_python(self, depth, ast = True):
		lines = ["l = match_wildcard(p, " + sum_gen_python(depth) + ")"]
		return lines