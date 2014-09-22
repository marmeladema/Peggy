import itertools

def product(l, r):
	return (''.join(x) for x in itertools.product(l, repeat=r))

def equal(r1, r2):
	return r1.v == r2.v and r1.o == r2.o

def valid_rule(i, patterns = []):
	r = Result()
	for p in patterns:
		if i.startswith(p):
			r.v, r.o = True, len(p)
			return r
	return r

#A1 <= 'a'
def valid_rule_A1(i):
	r = Result()
	if len(i) > 0 and i[0] == 'a':
		r.v = True
		r.o = 1
	return r

#A1 <= 'a'?
def valid_rule_A2(i):
	r = Result()
	r.v = True
	if len(i) > 0 and i[0] == 'a':
		r.o = 1
	return r

#A1 <= 'a'*
def valid_rule_A3(i):
	r = Result()
	r.v = True
	while r.o < len(i) and i[r.o] == 'a':
		r.o += 1
	return r

#A1 <= 'a'+
def valid_rule_A4(i):
	r = valid_rule_A3(i)
	if r.v and r.o == 0:
		r.v = False
	return r


def valid_rule_A5(i):
	r = Result()
	while r.o < len(i) and i[r.o] in 'ab':
		r.o += 1
	if r.o > 0:
		r.v = True
	return r

def valid_rule_A6(i):
	return valid_rule(i, patterns = ['ab', 'acd'])

def valid_rule_A7(i):
	return valid_rule(i, patterns = ['a', 'bc', 'bd'])

def valid_rule_A8(i):
	return valid_rule(i, patterns = ['abc'])

def valid_rule_A9(i):
	return valid_rule(i, patterns = ['a', 'b', 'c'])

tests = {}
tests["A1"] = (match_rule_A1, valid_rule_A1)
tests["A2"] = (match_rule_A2, valid_rule_A2)
tests["A3"] = (match_rule_A3, valid_rule_A3)
tests["A4_0"] = (match_rule_A4_0, valid_rule_A4)
tests["A4_1"] = (match_rule_A4_1, valid_rule_A4)
tests["A4_2"] = (match_rule_A4_2, valid_rule_A4)
tests["A4_3"] = (match_rule_A4_3, valid_rule_A4)
tests["A5_0"] = (match_rule_A5_0, valid_rule_A5)
tests["A5_0"] = (match_rule_A5_0, valid_rule_A5)
tests["A5_1"] = (match_rule_A5_1, valid_rule_A5)
tests["A5_2"] = (match_rule_A5_2, valid_rule_A5)
tests["A6"] = (match_rule_A6, valid_rule_A6)
tests["A7"] = (match_rule_A7, valid_rule_A7)
tests["A8_0"] = (match_rule_A8_0, valid_rule_A8)
tests["A8_1"] = (match_rule_A8_1, valid_rule_A8)
tests["A9_0"] = (match_rule_A9_0, valid_rule_A9)
tests["A9_1"] = (match_rule_A9_1, valid_rule_A9)

for t in sorted(tests.keys()):
	for s in product(['a', 'b', 'c', 'd'], 3):
		p = Parser(s, tests[t][0])
		r1 = tests[t][1](s)
		r2 = p.parse()
		if not equal(r1, r2):
			print "Rule %s failed for input %s, wanted %r,%r, got %r,%r" % (t, s, r1.v, r1.o, r2.v, r2.o)