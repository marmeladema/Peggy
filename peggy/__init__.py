import sys
import pprint
import json
import argparse
import jsonschema
import os

grammar_schema = json.load(
    open(os.path.join(os.path.dirname(__file__), 'grammar.json'), 'r')
)

ast_priority = {
    'BUILD': 0,
    'SKIP': 1,
    'VOID': 2,
}


class Range(list):
	def append(self, c):
		assert (len(self) % 2 == 0)
		for i in range(0, len(self), 2):
			if c < self[i] - 1:
				self.insert(i, c)
				self.insert(i, c)
				return
			elif self[i] - 1 == c:
				self[i] -= 1
				return
			if self[i] <= c and c <= self[i + 1]:
				return
			elif self[i + 1] + 1 == c:
				if i + 2 < len(self) and c == self[i + 2] - 1:
					self.pop(i + 1)
					self.pop(i + 1)
				else:
					self[i + 1] += 1
				return
		super().append(c)
		super().append(c)

	def extend(self, r):
		assert (len(self) % 2 == 0)
		if isinstance(r, Range):
			assert (len(r) % 2 == 0)
			for i in range(0, len(r), 2):
				self.add(r[i], r[i+1])
		else:
			for c in r:
				self.append(c)

	def add(self, a, b):
		assert (len(self) % 2 == 0)
		assert(a <= b)
		for i in range(0, len(self), 2):
			if a <= self[i+1]+1 and b >= self[i]-1:
				a = self[i] = min(a, self[i])
				b = self[i+1] = max(b, self[i+1])
				i += 2
				while i < len(self) and a <= self[i+1]+1 and b >= self[i]-1:
					a = self[i-2] = min(a, self.pop(i))
					b = self[i-1] = max(b, self.pop(i))
				return
			elif b < self[i]:
				super().insert(i, b)
				super().insert(i, a)
				return
		super().extend([a, b])

	def __contains__(self, c):
		assert (len(self) % 2 == 0)
		for i in range(0, len(self), 2):
			if c >= self[i] and c <= self[i + 1]:
				return True
		return False


class Peggy:
	def __init__(self, grammar, debug = False):

		jsonschema.validate(grammar, grammar_schema)

		self._grammar = grammar
		self._stack = None
		self._memoize = None
		self._count = 0
		self._last_state = None
		self._error = None
		self._debug = debug

	def json(self, *args, **kwargs):
		return json.dumps(self._grammar, *args, **kwargs)

	def walk_node(self, node, func):
		if node['type'] == 'RULE':
			self.walk_node(node['data'], func)
		elif node['type'] == 'SEQUENCE':
			for child in node['data']:
				self.walk_node(child, func)
		elif node['type'] == 'CHOICE':
			for child in node['data']:
				self.walk_node(child, func)
		elif node['type'] == 'RANGE':
			pass
		elif node['type'] == 'STRING':
			pass
		elif node['type'] == 'STRINGI':
			pass
		elif node['type'] == 'CALL':
			pass
		else:
			raise RuntimeError()
		func(node)

	def walk(self, func):
		for name, rule in self._grammar.items():
			self.walk_node(rule, func)

	def compute_node_lookahead(self, node):
		if 'lookahead' in node:
			return node['lookahead']
		node['lookahead'] = {
		    'pos': '',
		    'neg': '',
		}
		lookahead = {
		    'pos': Range(),
		    'neg': Range(),
		}
		if node['type'] == 'RULE':
			tmp = self.compute_node_lookahead(node['data'])
			lookahead['pos'].extend(tmp['pos'])
			lookahead['neg'].extend(tmp['neg'])
		elif node['type'] == 'SEQUENCE':
			for child in node['data']:
				tmp = self.compute_node_lookahead(child)
				lookahead['pos'].extend(tmp['pos'])
				lookahead['neg'].extend(tmp['neg'])
				min = child.get('min', 1)
				predicate = child.get('predicate', None)
				if min != 0 and predicate is None:
					break
		elif node['type'] == 'CHOICE':
			for child in node['data']:
				tmp = self.compute_node_lookahead(child)
				lookahead['pos'].extend(tmp['pos'])
				lookahead['neg'].extend(tmp['neg'])
		elif node['type'] == 'RANGE':
			lookahead['pos'].extend(node['data'])
		elif node['type'] == 'STRING':
			lookahead['pos'].append(ord(node['data'][0]))
		elif node['type'] == 'STRINGI':
			lookahead['pos'].append(ord(node['data'][0].lower()))
			lookahead['pos'].append(ord(node['data'][0].upper()))
		elif node['type'] == 'CALL':
			tmp = self.compute_node_lookahead(self._grammar[node['data']])
			lookahead['pos'].extend(tmp['pos'])
			lookahead['neg'].extend(tmp['neg'])
		elif node['type'] == 'WILDCARD':
			lookahead['pos'].add(0, 0x10FFFF)
		else:
			raise RuntimeError('Invalid node type {}'.format(node['type']))
		if node.get('min', 1) == 0:
			lookahead['pos'].add(0, 0x10FFFF)
		if node.get('predicate', None) is False:
			node['lookahead']['neg'] = lookahead['pos']
			node['lookahead']['pos'] = lookahead['neg']
		else:
			node['lookahead']['pos'] = lookahead['pos']
			node['lookahead']['neg'] = lookahead['neg']
		return node['lookahead']

	def compute_lookahead(self):
		for name, rule in self._grammar.items():
			if 'lookahead' not in self._grammar[name]:
				self.compute_node_lookahead(rule)

	def state_init(self, step, position, error = None):
		state = {}
		state['position'] = int(position)
		state['length'] = 0
		state['index'] = 0
		state['count'] = 0
		state['error'] = error
		state['step'] = step
		try:
			if step['type'] == 'CALL':
				state['ast'] = step.get('ast', 'BUILD')
			else:
				state['ast'] = step.get('ast', 'SKIP')
		except:
			pprint.pprint(step)
			raise
		state['nodes'] = []
		state['children'] = []
		return state

	def position(self):
		if self._stack:
			return self._stack[-1]['position'] + self._stack[-1]['length']
		else:
			return 0

	def push(self, step, memoize = None):
		if len(self._stack) >= 10240:
			raise RuntimeError('stack is too deep')
		state = None
		position = self.position()
		c = None
		if position < len(self._input):
			c = self._input[position]
		pos = step.get('lookahead', {}).get('pos')
		neg = step.get('lookahead', {}).get('neg')
		lookahead = c is None
		lookahead = lookahead or (pos and ord(c) in Range(pos))
		lookahead = lookahead or (neg and ord(c) not in Range(neg))
		lookahead = lookahead or (not pos and not neg)
		if lookahead and memoize is not None and self._stack and self._stack[
		    -1]['step']['type'] == 'CALL':
			rule = self._stack[-1]['step']['data']
			if rule not in memoize:
				memoize[rule] = {}
			if position in memoize[rule]:
				state = memoize[rule][position]
				if state['error'] is None:
					if self._debug:
						print('recursive rule {} detected'.format(rule))
					state = self.state_init(step, position, error = True)
					memoize[rule][position] = state
					self._recstack.append(state)
				elif self._recstack and position == self._recstack[-1][
				    'position'] and state is not self._recstack[-1]:
					if self._debug:
						print('recursive rule {} retry'.format(rule))
					state = self.state_init(step, position)
					#raise RuntimeError('left recursive rule {} at {}'.format(rule, position))
			else:
				state = self.state_init(step, position)
				memoize[rule][position] = state
		else:
			state = self.state_init(
			    step, position, error = None if lookahead else True
			)
		self._stack.append(state)
		return state

	def pop(self, memoize = None):
		state = self._stack.pop()
		position = state['position']
		if self._recstack and position == self._recstack[-1][
		    'position'] and self._stack and self._stack[-1]['step'][
		        'type'] == 'CALL':
			rule = self._stack[-1]['step']['data']
			if memoize[rule][position] is not state:
				if state['error'] is False and state['length'] > memoize[rule][
				    position]['length']:
					if memoize[rule][position] is self._recstack[-1]:
						self._recstack[-1] = state
						self.push(state['step'])
						memoize[rule][position] = state
						if self._debug:
							print('increase rule {} bound'.format(rule))
						return self._last_state
					memoize[rule][position] = state
				else:
					if memoize[rule][position] is self._recstack[-1]:
						self._recstack.pop()
					state = memoize[rule][position]
		return state

	def parse(self, input, name):
		self._stack = []
		self._recstack = []
		self._count = 0
		self._memoize = {}
		self._input = input
		self.push(
		    {
		        'type': 'CALL',
		        'data': name,
		        'ast': 'BUILD',
		    },
		    memoize = self._memoize
		)
		self._last_state = self.state_init({'ast': 'VOID', 'type': 'CALL'}, 0)
		n = 0
		while len(self._stack) > 0:
			position = self.position()
			head = self._stack[-1]
			if self._last_state['error'] is False and self._last_state['length'
			                                                           ] > 0:
				head['length'] += self._last_state['length']
				if self._last_state['ast'] == 'PRUNE':
					for node in self._last_state['nodes']:
						if len(node['children']) == 1:
							head['children'].append(node['children'][0])
						else:
							head['children'].append(node)
				elif self._last_state['ast'] == 'BUILD':
					head['children'].extend(self._last_state['nodes'])
				elif self._last_state['ast'] == 'SKIP':
					head['children'].extend(self._last_state['children'])
				elif self._last_state['ast'] == 'VOID':
					pass
				else:
					raise NotImplementedError(
					    'ast mode \'{}\' not implemented'.format(
					        self._last_state['ast']
					    )
					)
			elif self._last_state['step']['type'] == 'CALL' and (
			    not self._error
			    or self._last_state['position'] > self._error['position']
			):
				self._error = dict(self._last_state)
			#if last_state.get('recursive', False):
			#	last_state['error'] = None

			if self._debug:
				print('########################')
				print('position:', position)
				if position < len(input):
					print('lookahead:', repr(input[position]))
				else:
					print('lookahead: EOF')
				print('stack length:', len(self._stack))
				pprint.pprint({'stack': self._stack})
				print('recstack length:', len(self._recstack))
				pprint.pprint({'recstack': self._recstack})
				pprint.pprint({'last_state': self._last_state})

			if head['error'] is None:
				if head['step']['type'] == 'SEQUENCE':
					if head['index'] >= 0 and self._last_state['error']:
						head['index'] = sys.maxsize
						head['length'] = head.get('prev_length')
					else:
						if head['index'] < len(head['step']['data']):
							if head['index'] == 0:
								head['prev_length'] = head['length']
							next_state = self.push(
							    head['step']['data'][head['index']]
							)
							if head['ast'] == 'VOID':
								next_state['ast'] = 'VOID'
							head['index'] += 1
						else:
							head['index'] = 0
				elif head['step']['type'] == 'CHOICE':
					if head['index'] > 0 and not self._last_state['error']:
						head['index'] = 0
					else:
						if head['index'] < len(head['step']['data']):
							next_state = self.push(
							    head['step']['data'][head['index']]
							)
							if head['ast'] == 'VOID':
								next_state['ast'] = 'VOID'
							head['index'] += 1
						else:
							head['index'] = sys.maxsize
				elif head['step']['type'] == 'STRING':
					assert (head['index'] == 0)
					data_len = len(head['step']['data'])
					if position + data_len <= len(input) and input[
					    position:position + data_len] == head['step']['data']:
						head['length'] += data_len
						head['index'] = 0
					else:
						head['index'] = sys.maxsize
				elif head['step']['type'] == 'STRINGI':
					assert (head['index'] == 0)
					data_len = len(head['step']['data'])
					if position + data_len <= len(input) and input[
					    position:position + data_len].lower() == head['step']['data'].lower():
						head['length'] += data_len
						head['index'] = 0
					else:
						head['index'] = sys.maxsize
				elif head['step']['type'] == 'WILDCARD':
					assert (head['index'] == 0)
					data_len = 1
					if position + data_len <= len(input):
						head['length'] += data_len
						head['index'] = 0
					else:
						head['index'] = sys.maxsize
				elif head['step']['type'] == 'CALL':
					#assert(head['index'] == 0)
					rule = head['step']['data']
					if head['index'] > 0:
						assert (self._last_state['error'] is not None)
						if self._last_state['error']:
							head['index'] = sys.maxsize
						else:
							head['index'] = 0
					else:
						next_state = self.push(
						    self._grammar[rule]['data'],
						    memoize = self._memoize
						)
						if ast_priority[self._grammar[rule]['ast']
						                ] > ast_priority[head['ast']]:
							head['ast'] = self._grammar[rule]['ast']
						#if head['ast'] == 'VOID':
						#	next_state['ast'] = 'VOID'
						head['index'] += 1
				elif head['step']['type'] == 'RANGE':
					assert (head['index'] == 0)
					assert (len(head['step']['data']) % 2 == 0)
					head['ast'] = 'VOID'
					if position < len(input) and ord(input[position]) in Range(head['step']['data']):
						head['length'] += 1
						head['index'] = 0
					else:
						head['index'] = sys.maxsize
				else:
					raise NotImplementedError(head['step'])

				self._last_state = self.state_init(
				    self._last_state['step'], self._last_state['position']
				)
				if head is self._stack[-1]:
					if head['index'] == sys.maxsize:
						head['error'] = True
						if head['count'] >= head['step'].get(
						    'min', 1
						) and head['count'] <= head['step'].get('max', 1):
							head['error'] = False
						if self._debug:
							print(
							    head['step'],
							    'of length %d has failed at %d' % (
							        head['length'],
							        head['position'],
							    )
							)
						if head['step'].get('predicate', None) is not None:
							head['error'] = not (
							    head['step']['predicate'] ^ head['error']
							)
							head['length'] = 0
					elif head['index'] == 0:
						head['error'] = False
						if head['ast'] in ['BUILD']:
							node = dict(head)
							del node['nodes']
							if head['nodes']:
								node['position'] = head['nodes'][-1][
								    'position'] + head['nodes'][-1]['length']
								node['length'] = head['position'] + head[
								    'length'] - node['position']
							head['nodes'].append(node)
							head['children'] = []
						head['count'] += 1
						if head['count'] >= head['step'].get('max', 1):
							if self._debug:
								print(
								    head['step'], 'has succeeded at %d' %
								    (head['position'], )
								)
							if head['step'].get('predicate', None) is not None:
								head['error'] = not (
								    head['step']['predicate'] ^ head['error']
								)
								head['length'] = 0
						else:
							head['error'] = None
				if self._stack[-1]['error'] is not None:
					self._last_state = self.pop(memoize = self._memoize)
			self._count += 1
		return self._last_state


def astdata(ast, data):
	return data[ast['position']:ast['position'] + ast['length']]


def astprint(state, data, indent = 0):
	name = ''
	if indent:
		name += '   ' * (indent - 1) + '+--'
	name += state['step']['type']
	if 'data' in state['step']:
		name += ':' + str(state['step']['data'])
	name += '[' + str(state['position']
	                  ) + ':' + str(state['position'] + state['length']) + ']'
	if not state['children']:
		name += '<' + repr(astdata(state, data)) + '>'
	print(name)
	count = 1
	for child in state['children']:
		astprint(child, data, indent = indent + 1)
