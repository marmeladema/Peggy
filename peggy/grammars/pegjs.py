import peggy
import sys

EscapeChar = {
    'a': '\a',
    'b': '\b',
    'f': '\f',
    'n': '\n',
    'r': '\r',
    't': '\t',
    'v': '\v',
    '\\': '\\',
    '"': '"',
    '\'': '\'',
    '-': '-'
}

IgnoredNode = ['Ws', 'Open', 'Close', 'Alt']


def parse_range(s):
	r = ''
	l = len(s)
	i = 0
	while i < l:
		if s[i] == '\\':
			if i < l - 1 and s[i + 1] in EscapeChar:
				r += EscapeChar[s[i + 1]]
				i += 1
			elif i < l - 1 and s[i + 1] == ']':
				r += ']'
				i += 1
			else:
				r += s[i]
		elif s[i] == '-' and i > 0 and i < l - 1:
			r += ''.join(
			    [chr(o) for o in range(ord(s[i - 1]) + 1,
			                           ord(s[i + 1]) + 1)]
			)
			i += 1
		else:
			r += s[i]
		i += 1
	return r


def filter_ignored(nodes):
	return filter(
	    lambda ast: not ast['step']['type'] == 'CALL' or ast['step']['data'] not in IgnoredNode,
	    nodes
	)


def filter_node(node):
	node['children'] = list(map(filter_node, filter_ignored(node['children'])))
	return node


def unit2json(ast, data):
	unit = {'ast': 'BUILD'}
	prefix = ''
	suffix = ''
	if ast['children'][0]['step']['type'] == 'CALL' and ast['children'][0][
	    'step']['data'] == 'Prefix':
		prefix = peggy.astdata(ast['children'][0], data)
		ast['children'].pop(0)

	if ast['children'][0]['step']['type'] == 'CALL' and ast['children'][0][
	    'step']['data'] == 'Literal':
		unit['type'] = 'STRING'
		unit['data'] = peggy.astdata(
		    ast['children'][0], data
		).strip()[1:-1].encode('utf-8').decode('unicode_escape')
		unit['ast'] = 'VOID'
	elif ast['children'][0]['step']['type'] == 'CALL' and ast['children'][0][
	    'step']['data'] == 'CaseLiteral':
		unit['type'] = 'STRING'
		unit['data'] = peggy.astdata(
		    ast['children'][0], data
		).strip()[1:-1].encode('utf-8').decode('unicode_escape')
		unit['ast'] = 'VOID'
	elif ast['children'][0]['step']['type'] == 'CALL' and ast['children'][0][
	    'step']['data'] == 'Identifier':
		unit['type'] = 'CALL'
		unit['data'] = peggy.astdata(ast['children'][0],
		                             data).strip().split()[0]
	elif ast['children'][0]['step']['type'] == 'CALL' and ast['children'][0][
	    'step']['data'] == 'CharClass':
		unit['type'] = 'RANGE'
		unit['data'] = peggy.astdata(
		    ast['children'][0], data
		).strip()[1:-1].encode('utf-8').decode('unicode_escape')
		unit['data'] = parse_range(unit['data'])
		unit['ast'] = 'VOID'
	elif ast['children'][0]['step']['type'] == 'CALL' and ast['children'][0][
	    'step']['data'] == 'WildCard':
		unit['type'] = 'WILDCARD'
		unit['ast'] = 'VOID'
	else:
		unit = node2json(ast['children'][0], data)
	ast['children'].pop(0)

	if ast['children'] and ast['children'][0]['step'][
	    'type'] == 'CALL' and ast['children'][0]['step']['data'] == 'Suffix':
		suffix = peggy.astdata(ast['children'][0], data)
		ast['children'].pop(0)

	if prefix:
		if prefix == '&':
			unit['predicate'] = True
			unit['ast'] = 'VOID'
		elif prefix == '!':
			unit['predicate'] = False
			unit['ast'] = 'VOID'
		elif prefix == '$':
			pass
		else:
			raise NotImplementedError(
			    'prefix {} not implemented'.format(prefix)
			)

	if suffix:
		if suffix == '*':
			unit['min'] = 0
			unit['max'] = sys.maxsize
		elif suffix == '+':
			unit['min'] = 1
			unit['max'] = sys.maxsize
		elif suffix == '?':
			unit['min'] = 0
			unit['max'] = 1
		elif suffix == 'i':
			assert (unit['type'] == 'STRING')
			unit['type'] = 'STRINGI'
		else:
			raise NotImplementedError(
			    'suffix {} not implemented'.format(suffix)
			)

	return unit


def sequence2json(ast, data):
	assert (len(ast['children']) > 0)

	if len(ast['children']) == 1:
		return node2json(ast['children'][0], data)

	node = {
	    'type': 'SEQUENCE',
	    'data': [],
	    'ast': "SKIP",
	}
	for child in ast['children']:
		node['data'].append(node2json(child, data))
	return node


def alternation2json(ast, data):
	assert (len(ast['children']) > 0)

	if len(ast['children']) == 1:
		return node2json(ast['children'][0], data)

	a = {
	    'type': 'CHOICE',
	    'data': [],
	    'ast': "SKIP",
	}
	for i in range(0, len(ast['children'])):
		a['data'].append(node2json(ast['children'][i], data))
	return a


def node2json(node, data):
	if node['step']['type'] == 'CALL':
		if node['step']['data'] == 'Alternation':
			return alternation2json(node, data)
		elif node['step']['data'] == 'Sequence':
			return sequence2json(node, data)
		elif node['step']['data'] == 'Unit':
			return unit2json(node, data)
		else:
			raise NotImplementedError(
			    'Unknown rule {}'.format(node['step']['data'])
			)
	raise RuntimeError('Unknown step: {}'.format(node['step']))


def grammar2json(ast, data):
	g = {}
	filter_node(ast)
	assert (ast['step']['type'] == 'CALL' and ast['step']['data'] == 'Grammar')
	if ast['children'][0]['step']['type'] == 'CALL' and ast['children'][0][
	    'step']['data'] == 'Code':
		ast['children'].pop(0)
	for definition in ast['children']:
		assert (definition['step']['type'] == 'CALL')
		assert (definition['step']['data'] == 'Definition')
		identifier = definition['children'][0]
		assert (
		    identifier['step']['type'] == 'CALL'
		    and identifier['step']['data'] == 'Identifier'
		)
		definition['children'].pop(0)
		if definition['children'][0]['step']['type'] == 'CALL' and definition[
		    'children'][0]['step']['data'] == 'CaseLiteral':
			definition['children'].pop(0)
		assert (len(definition['children']) == 1)
		rule = peggy.astdata(identifier, data).strip().split()[0]
		g[rule] = {
		    'type': 'RULE',
		    'ast': 'BUILD',
		    'data': node2json(definition['children'][0], data),
		}
	return g
