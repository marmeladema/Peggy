import peggy


def object2json(ast, data):
	assert (ast['step']['type'] == 'CALL')
	assert (ast['step']['data'] == 'Object')
	node = {}
	for member in ast['children']:
		assert (member['step']['type'] == 'CALL')
		assert (member['step']['data'] == 'Member')
		assert (len(member['children']) == 2)
		assert (member['children'][0]['step']['type'] == 'CALL')
		assert (member['children'][0]['step']['data'] == 'String')
		key = node2json(member['children'][0], data)
		value = node2json(member['children'][1], data)
		node[key] = value
	return node


def array2json(ast, data):
	assert (ast['step']['type'] == 'CALL')
	assert (ast['step']['data'] == 'Array')
	node = []
	for item in ast['children']:
		node.append(node2json(item, data))
	return node


def node2json(ast, data):
	assert (ast['step']['type'] == 'CALL')
	if ast['step']['data'] == 'Object':
		return object2json(ast, data)
	elif ast['step']['data'] == 'Array':
		return array2json(ast, data)
	elif ast['step']['data'] == 'String':
		str = peggy.astdata(ast, data)
		assert (str[0] == '"' and str[-1] == '"')
		return str[1:-1].encode('utf-8').decode('unicode_escape')
	elif ast['step']['data'] == 'Number':
		num = peggy.astdata(ast, data)
		try:
			return int(num)
		except:
			return float(num)
	elif ast['step']['data'] == 'Literal':
		literal = peggy.astdata(ast, data)
		if literal == 'true':
			return True
		elif literal == 'false':
			return False
		elif literal == 'null':
			return None
		else:
			raise RuntimeError('Invalid literal {}'.format(literal))
	else:
		raise RuntimeError('Invalid node type {}'.format(ast['step']['data']))


def grammar2json(ast, data):
	assert (ast['step']['type'] == 'CALL' and ast['step']['data'] == 'Json')
	assert (len(ast['children']) == 1)
	return node2json(ast['children'][0], data)
