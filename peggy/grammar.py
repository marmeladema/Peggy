import re, string

from expr import *

re_rule = re.compile("([a-zA-Z][a-zA-Z0-9_-]*)\s*<[:=-]\s*(.*)\s*")

#~ ExprStrings = ["OR", "AND", "STRING", "STRINGI", "RANGE", "RULE", "WILDCARD"]

prefixes = ":!&"
suffixes = "*+?"

def extract_seq(s, d):
	l = len(s)
	i = 1
	while i < l:
		if s[i] == '\\':
			i += 1
		elif s[i] in d:
			return i+1
		i += 1
	return 0

def parse_string(s):
	r = ''
	l = len(s)
	i = 0
	while i < l:
		if s[i] == '\\':
			if i < l-1 and s[i + 1] in EscapeChar:
				r += EscapeChar[s[i + 1]]
				i += 1
			elif i < l-1 and s[i + 1] == ']':
				r += ']'
				i += 1
			else:
				return None
		else:
			r += s[i]
		i += 1
	return r

def parse_range(s):
	#print "parse_range(%s)"%(s,)
	r = ''
	l = len(s)
	i = 0
	while i < l:
		if s[i] == '\\':
			if i < l-1 and s[i + 1] in EscapeChar:
				r += EscapeChar[s[i + 1]]
				i += 1
			elif i < l-1 and s[i + 1] == ']':
				r += ']'
				i += 1
			else:
				return None
		elif s[i] == '-'  and i > 0 and i < l-1:
			r += ''.join([chr(o) for o in range(ord(s[i - 1]) + 1, ord(s[i + 1]) + 1)])
			i += 1
		else:
			r += s[i]
		i += 1
	return r

def parse_expr(s, i, e, p = '', d = 0):
	#print "parse_expr",s[i:]
	e.data.append(ExprAnd())
	e.data[-1].prefix = p
	e.data[-1].data = []
	
	subrule = False
	rule_len = len(s)
	prefix = ''
	suffix = ''
	while i < rule_len:
		if s[i] in prefixes:
			prefix = s[i]
			i += 1
			#print "add prefix:",prefix
		elif s[i] in suffixes:
			#while (s[i] in prefixes or s[i] in suffixes) and i < rule_len-1:
			suffix = s[i]
			i += 1
			#print "add suffix:",suffix
		else:
			prefix = ''
			suffix = ''

		#print '\t'*d + "prefix:",prefix

		if s[i] == '.':
			e.data[-1].data.append(ExprWildcard())
			e.data[-1].data[-1].prefix = prefix
			e.data[-1].data[-1].suffix = suffix
			i += 1
		elif s[i] == '[':
			l = extract_seq(s[i:], ']')
			if l == 0:
				print "Error: range not properly ended"
				return -1
			r = parse_range(s[i+1:i+l-1])
			if not r:
				return -1
			e.data[-1].data.append(ExprRange())
			e.data[-1].data[-1].prefix = prefix
			e.data[-1].data[-1].suffix = suffix
			e.data[-1].data[-1].data = r
			i += l
		elif s[i] == '\'':
			l = extract_seq(s[i:], '\'')
			if l == 0:
				print "Error: case-sensitive string not properly ended"
				return -1
			r = parse_string(s[i+1:i+l-1])
			if not r:
				return -1
			e.data[-1].data.append(ExprStringSensitive())
			e.data[-1].data[-1].prefix = prefix
			e.data[-1].data[-1].suffix = suffix
			e.data[-1].data[-1].data = r
			i += l
		elif s[i] == '"':
			l = extract_seq(s[i:], '"')
			if l == 0:
				print "Error: case-insensitive string not properly ended"
				return -1
			r = parse_string(s[i+1:i+l-1])
			if not r:
				return -1
			e.data[-1].data.append(ExprStringInsensitive())
			e.data[-1].data[-1].prefix = prefix
			e.data[-1].data[-1].suffix = suffix
			e.data[-1].data[-1].data = r
			i += l
		elif s[i] in string.ascii_letters:
			l = 0
			while i+l < rule_len and (s[i+l] in string.ascii_letters or s[i+l] in string.digits):
				l += 1
			e.data[-1].data.append(ExprCall())
			#print "call",prefix,s[i:i+l],suffix
			e.data[-1].data[-1].prefix = prefix
			e.data[-1].data[-1].suffix = suffix
			e.data[-1].data[-1].data = s[i:i+l]
			i += l
		elif s[i] == '(':
			e.data[-1].data.append(ExprOr())
			e.data[-1].data[-1].prefix = prefix
			e.data[-1].data[-1].suffix = suffix
			e.data[-1].data[-1].data = []
			l = parse_expr(s, i+1, e.data[-1].data[-1], d=d+1)
			if l == 0 or l >= rule_len or s[l] != ')':
				print "Error: subrule not properly ended"
				return -1
			i = l+1

		if i >= rule_len:
			return i
		elif s[i] in suffixes:
			e.data[-1].data[-1].suffix = s[i]
			i += 1
		elif s[i] in ' \t':
			i += 1
			prefix = ''
			suffix = ''
		elif s[i] == ')':
			return i
		elif s[i] == '|' or s[i] == '/':
			e.data.append(ExprAnd())
			e.data[-1].data = []
			i += 1
			prefix = ''
			suffix = ''
		else:
			print "Error: bad char 2"
			return i
		#print '\t'*d + "end"
	return rule_len

def parse_rule(s, r):
	r.data = ExprOr()
	l = parse_expr(s, 0, r.data)
	return l

class Grammar:
	def __init__(self):
		self.rules = {}
		
	def addRule(self, rule):
		rule.grammar = self
		self.rules[rule.name] = rule
	
	def getRule(self, name):
		return self.rules[name]
	
	def optimize(self):
		for name in self.rules:
			self.rules[name].optimize()

	def finalize(self):
		for name in self.rules:
			self.rules[name].finalize()
	
	def parse(self, data):
		lines = data.split('\n')
		name = None
		rule = None
		start = None
		last_line = 0
		error = False
		for i in range(0, len(lines)):
			line = lines[i].strip()
			#print repr(line)
			if len(line) <= 0 or line[0] == '#' or line[0] == ';':
				continue
			match = re_rule.match(line)
			if match:
				if rule:
					l = parse_rule(rule, self.getRule(name))
					#rules[name].draw()
					if l != len(rule):
						print "Syntax error around line %d in rule %s at offset %d: %c"%(last_line+1,name,l,rule[l])
					elif not start:
						start = name
				name = match.group(1)
				rule = match.group(2)
				self.addRule(ExprRule(name, self))
				last_line = i
			else:
				if not name:
					print repr(line)
					print "Syntax error at line %d: %s"%(i+1, lines[i].strip())
					error = True
				else:
					rule += line.strip()
				last_line = i
		if rule:
			l = parse_rule(rule, self.getRule(name))
			if l != len(rule):
				print "Syntax error at line %d in rule %s at offset %d: %c"%(i+1,name,l,rule[l])
				error = True
		
		return not error