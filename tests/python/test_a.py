import itertools

def product(l, r):
	return (''.join(x) for x in itertools.product(l, repeat=r))

def equal(r1, r2):
	return r1.v == r2.v and r1.o == r2.o

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
		r.o = True
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

tests = {}
tests["A1"] = (match_rule_A1, valid_rule_A1)
tests["A2"] = (match_rule_A2, valid_rule_A2)
tests["A3"] = (match_rule_A3, valid_rule_A3)
tests["A4"] = (match_rule_A4, valid_rule_A4)

for t in sorted(tests.keys()):
	for s in product(['a', 'b'], 3):
		p = Parser(s, tests[t][0])
		if not equal(p.parse(), tests[t][1](s)):
			print "Rule %s failed for input %s" % (t, s)