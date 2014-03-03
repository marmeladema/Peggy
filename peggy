#!/usr/bin/env python

import sys
import re
import shlex
import string

re_rule = re.compile("([a-zA-Z][a-zA-Z0-9_-]*)\s*<[:=-]\s*(.*)\s*")

EXPR_TYPE_OR = 0
EXPR_TYPE_SEQ = 1
EXPR_TYPE_STRING_SENSITIVE = 2
EXPR_TYPE_STRING_INSENSITIVE = 3
EXPR_TYPE_RANGE = 4
EXPR_TYPE_RULE = 5
EXPR_TYPE_WILDCARD = 6

ExprStrings = ["OR", "SEQ", "STRING", "STRINGI", "RANGE", "RULE", "WILDCARD"]

EscapeChar = {'a': '\a', 'b': '\b', 'f': '\f', 'n': '\n', 'r': '\r', 't': '\t', 'v': '\v', '\\': '\\', '"': '"', '\'': '\''}
CharEscape = dict((v,k) for k,v in EscapeChar.items())

class Node:
	def __init__(self, t):
		self.type = t
		self.children = []
		self.str = None

def prefix_gen_python(e, depth, ret = False):
	lines = []
	if e.prefix == '+' or e.prefix == '*':
		lines.append("# o.append(0)")
		lines.append("results[" + str(depth) + "].o = 0")
		lines.append("# v.append(False)")
		lines.append("results[" + str(depth) + "].v = False")
		lines.append("while True:")
		lines += ["\t" + line for line in e.gen_python(depth + 1, ret)]
		lines += ["\tif l > 0:"]
		lines += ["\t\t# o[-1] += l"]
		lines += ["\t\tresults[" + str(depth) + "].o += l"]
		lines += ["\telse:"]
		lines += ["\t\tbreak"]
		lines += ["# l = o.pop()"]
		lines += ["l = results[" + str(depth) + "].o"]
		lines += ["# m = v.pop()"]
		lines += ["m = results[" + str(depth) + "].v"]
	else:
		lines = e.gen_python(depth, ret)
	return lines

def sum_gen_python(depth):
	s = '+'.join(["results[" + str(i) + "]" for i in range(0, depth)])
	if s:
		s = 'i+'+s
	else:
		s = 'i'
	return s

class Expr:
	def __init__(self, t):
		self.prefix = None
		self.type = t
		self.data = None
		self.final = False

	def __str__(self):
		if self.prefix:
			return self.prefix
		else:
			return ''

	def getDepth(self):
		return int(self.prefix == '*' or self.prefix == '+')

class ExprOr(Expr):
	def __init__(self):
		Expr.__init__(self, EXPR_TYPE_OR)
		self.data = []

	def __str__(self):
		s = Expr.__str__(self)
		if len(self.data) > 1:
			s += '('
		s += " | ".join([str(c) for c in self.data])
		if len(self.data) > 1:
			s += ')'
		return s

	def gen_python(self, depth, ret = False):
		lines = []
		lines += ["# ExprOr(depth=%d, ret=%d)"%(depth, ret)]
		lines += ["# o.append(0)"]
		lines += ["results[" + str(depth) + "].o = 0"]
		lines += ["# v.append(False)"]
		lines += ["results[" + str(depth) + "].v = False"]
		lines.append("n.append([])")
		for i in range(0, len(self.data)):
			lines += ["# if o[-1] == 0:"]
			lines += ["if results[" + str(depth) + "].o == 0:"]
			lines += ["\t" + line for line in prefix_gen_python(self.data[i], depth + 1, ret)]
		lines += ["# l = o.pop()"]
		lines += ["l = results[" + str(depth) + "].o"]
		lines += ["# m = v.pop()"]
		lines += ["m = results[" + str(depth) + "].v"]
		lines.append("a = n.pop()")
		lines.append("if len(n) > 1:")
		lines.append("\ta = n.pop()")
		lines.append("\tn[-1] += a")
		lines.append("else:")
		lines.append("\tn += a")
		return lines

	def getDepth(self):
		return 1+max([e.getDepth() for e in self.data])+Expr.getDepth(self)

	def optimize(self):
		for i in range(0, len(self.data)):
			if self.data[i].type == EXPR_TYPE_SEQ:
				if len(self.data[i].data) == 1:
					self.data[i] = self.data[i].data[0]


class ExprSeq(Expr):
	def __init__(self):
		Expr.__init__(self, EXPR_TYPE_SEQ)
		self.data = []

	def __str__(self):
		s = Expr.__str__(self)
		if self.prefix or len(self.data) > 1:
			s += '('
		s += " ".join([str(c) for c in self.data])
		if self.prefix or len(self.data) > 1:
			s += ')'
		return s

	def gen_python(self, depth, ret = False):
		#print self.prefix
		lines = []
		lines += ["# ExprSeq(depth=%d, ret=%d)"%(depth, ret)]
		block = 0
		for i in range(0, len(self.data)):
			lines += ["\t"*block + line for line in prefix_gen_python(self.data[i], depth, ret)]
			lines += ["\t"*block + "# prefix:" + str(repr(self.data[i].prefix)) + "" + str(self.data[i - 1].prefix != '?' and self.data[i - 1].prefix != '*')]
			if self.data[i].prefix == '!':
				lines += ["\t"*block + "if l == 0:"]
				block += 1
			elif self.data[i].prefix != '?' and self.data[i].prefix != '*':
				lines.append("\t"*block + "if l > 0 or m:")
				block += 1
			if self.data[i].prefix != '!' and self.data[i].prefix != '&':
				lines += ["\t"*block + "# o[-1] += l"]
				lines += ["\t"*block + "results[" + str(depth - 1) + "].o += l"]
				if self.data[i].type == EXPR_TYPE_RULE:
					lines.append("\t"*block + "n[-1].append(\"" + self.data[i].data + "\")")

		if self.data[-1].prefix == '!' or self.data[-1].prefix == '&':
			lines += ["\t"*block + "v[-1] = True"]
		while block:
			block -= 1
			lines += ["\t"*block + "else:"]
			lines += ["\t"*(block + 1) + "# o[-1] = 0"]
			lines += ["\t"*(block + 1) + "results[" + str(depth - 1) + "].o = 0"]
			lines.append("\t" * (block + 1) + "del n[-1][:]")
		return lines

	def getDepth(self):
		return sum([e.getDepth() for e in self.data])+Expr.getDepth(self)
		#return 1+Expr.getDepth(self)

	def optimize(self):
		for i in range(0, len(self.data)):
			if self.data[i].type == EXPR_TYPE_OR:
				if len(self.data[i].data) == 1:
					self.data[i] = self.data[i].data[0]

class ExprStringSensitive(Expr):
	def __init__(self):
		Expr.__init__(self, EXPR_TYPE_STRING_SENSITIVE)
		self.data = ''

	def __str__(self):
		s = Expr.__str__(self)
		return s + "'%s'"%(escape_string(self.data),)

	def gen_python(self, depth, ret = False):

		lines = ["l = match_sensitive_string(p, " + sum_gen_python(depth) + ", '" + escape_string(self.data) + "')"]
		return lines

class ExprStringInsensitive(Expr):
	def __init__(self):
		Expr.__init__(self, EXPR_TYPE_STRING_INSENSITIVE)
		self.data = ''

	def __str__(self):
		s = Expr.__str__(self)
		return s + "\"%s\""%(escape_string(self.data),)

	def gen_python(self, depth, ret = False):
		lines = ["l = match_insensitive_string(p, " + sum_gen_python(depth) + ", '" + escape_string(self.data) + "')"]
		return lines

class ExprRange(Expr):
	def __init__(self):
		Expr.__init__(self, EXPR_TYPE_RANGE)
		self.data = ''

	def __str__(self):
		s = Expr.__str__(self)
		return s + "[%s]"%(escape_string(self.data),)

	def gen_python(self, depth, ret = False):
		lines = ["l = match_range(p, " + sum_gen_python(depth) + ", '"+ escape_string(self.data) + "')"]
		return lines

class ExprRule(Expr):
	def __init__(self):
		Expr.__init__(self, EXPR_TYPE_RULE)
		self.data = ''

	def __str__(self):
		s = Expr.__str__(self)
		return s + self.data

	def gen_python(self, depth, ret = False):
		lines = ["l,m = match_rule_" + self.data + "(p, " + sum_gen_python(depth) + ")"]
		return lines

class ExprWildcard(Expr):
	def __init__(self):
		Expr.__init__(self, EXPR_TYPE_WILDCARD)
		self.data = ''

	def __str__(self):
		s = Expr.__str__(self)
		return s + '.'

	def gen_python(self, depth, ret = False):
		lines = ["l = match_wildcard(p, " + sum_gen_python(depth) + ")"]
		return lines

class Rule:
	def __init__(self):
		self.terminal = True
		self.name = None
		self.expr = None
		self.depth = 0

	def __str__(self):
		return "%s <= %s"%(self.name, str(self.expr))

	def gen_python(self):
		lines = ["def match_rule_" + self.name + "(p, i):"]
		lines.append("\tprint \"match_rule_%s(input, %%d)\"%%(i,)"%(self.name))
		lines.append("\tresults = [" + ",".join(["Result()"] * self.expr.getDepth()) + "]")
		lines.append("\tl = 0")
		lines.append("\tm = False")
		lines.append("\ts = 0")
		lines.append("\tn = []")
		for line in self.expr.gen_python(0, True):
			lines.append("\t" + line)
		lines.append("\tprint n")
		lines.append("\treturn l,m")
		lines.append("")
		return lines

	def optimize(self):
		self.expr.optimize()

	def getAstName(self):
		return "AST_TYPE_%s"%(self.name.upper(),)

prefixes = ":*+?!&"

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

def escape_string(s):
	e = ''
	for c in s:
		if c in CharEscape:
			e += '\\' + CharEscape[c]
		else:
			e += c
	return e

def parse_expr(s, i, e, p = None):
	#print "parse_expr",s[i:]
	e.data.append(ExprSeq())
	e.data[-1].prefix = p
	e.data[-1].data = []
	
	subrule = False
	rule_len = len(s)
	prefix = ''
	while i < rule_len:
		if s[i] in prefixes:
			while s[i] in prefixes and i < rule_len-1:
				prefix += s[i]
				i += 1
		else:
			prefix = ''

		if s[i] == '.':
			e.data[-1].data.append(ExprWildcard())
			e.data[-1].data[-1].prefix = prefix
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
			e.data[-1].data[-1].data = r
			i += l
		elif rule[i] in string.ascii_letters:
			l = 0
			while i+l < rule_len and (s[i+l] in string.ascii_letters or s[i+l] in string.digits):
				l += 1
			e.data[-1].data.append(ExprRule())
			e.data[-1].data[-1].prefix = prefix
			e.data[-1].data[-1].data = s[i:i+l]
			i += l
		elif s[i] == '(':
			e.data[-1].data.append(ExprOr())
			e.data[-1].data[-1].prefix = prefix
			e.data[-1].data[-1].data = []
			l = parse_expr(s, i+1, e.data[-1].data[-1])
			if l == 0 or l >= rule_len:
				print "Error: subrule not properly ended"
				return -1
			elif l < rule_len and s[l] != ')':
				return l
			#print s[l]
			i = l+1
		elif s[i] == ')':
			return i
		elif s[i] == '|':
			e.data.append(ExprSeq())
			e.data[-1].data = []
			i += 1
		elif s[i] in ' \t':
			i += 1
		else:
			#print "error 2"
			print "Error: unknown char"
			return i
		#print "s[i:]=",s[i:]
	return rule_len

def parse_rule(s, r):
	r.expr = ExprOr()
	r.expr.data = []
	l = parse_expr(s, 0, r.expr)
	return l

if __name__ == "__main__":
	rules = {}
	if len(sys.argv) < 2:
		print "Usage: %s <grammar>"%(sys.argv[0],)
		sys.exit(1)
	f = open(sys.argv[1])
	lines = f.readlines()
	name = None
	rule = None
	start = None
	last_line = 0
	for i in range(0, len(lines)):
		line = lines[i]
		#print repr(line)
		if line[0] == '#' or line[0] == '\n':
			continue
		match = re_rule.match(line)
		if match:
			if rule:
				l = parse_rule(rule, rules[name])
				if l != len(rule):
					print "Syntax error around line %d in rule %s at offset %d: %c"%(last_line+1,name,l,rule[l])
				elif not start:
					start = name
			name = match.group(1)
			rule = match.group(2)
			rules[name] = Rule()
			rules[name].name = name
			last_line = i
		else:
			rule += line.strip()
			last_line = i
	if rule:
		l = parse_rule(rule, rules[name])
		if l != len(rule):
			print "Syntax error at line %d in rule %s at offset %d: %c"%(i+1,name,l,rule[l])
	
	print """
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
		self.type = t
		self.children = []

class Result:
	def __init__(self):
		self.o = 0
		self.v = False
		self.s = []

class Parser:
	def __init__(self, input, start):
		self.input = input
		self.length = len(input)
		self.start = start

	def parse(self):
		return self.start(self, 0)
"""

	#if "-p" in sys.argv:
	i = 0
	for name in rules:
		print "%s = %d"%(rules[name].getAstName(),i)
		i += 1

	for name in rules:
		# rules[name].optimize()
		print "# " + str(rules[name])
		print "# depth:",rules[name].expr.getDepth()
		for line in rules[name].gen_python():
			print line
		#print print_rule(rules[name])

	print "Lol1 = Parser('ab', parse_rule_Lol1)"
	print "print len(Lol1.input),Lol1.parse()"
	print "Lol2 = Parser('b\"', parse_rule_Lol2)"
	print "print len(Lol2.input),Lol2.parse()"
	print "SComment = Parser('# lolilol ', parse_rule_SComment)"
	print "print len(SComment.input),SComment.parse()"