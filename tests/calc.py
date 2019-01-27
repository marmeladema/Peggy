import os
import json

import peggy
from . import util

peg_path = os.path.join(os.path.dirname(__file__), 'grammars', 'calc.peg')
json_path = os.path.join(os.path.dirname(__file__), 'grammars', 'calc.json')

with open(json_path) as json_fd:
	grammar = json.load(json_fd)


class TestCalc(util.PeggyTestCase):
	def test_idempotence(self):
		with open(peg_path) as peg_fd, open(json_path) as json_fd:
			return self.idempotence('waxeye', peg_fd.read(), grammar)

	def test_simple_ok(self):
		parser = peggy.Peggy(grammar)
		ast = parser.parse('1+1', 'Expr')
		self.assertFalse(ast['error'])
		self.assertEqual(ast['length'], 3)

	def test_simple_partial(self, ):
		parser = peggy.Peggy(grammar)
		ast = parser.parse('1+b', 'Expr')
		self.assertFalse(ast['error'])
		self.assertEqual(ast['length'], 1)

	def test_simple_ko(self, ):
		parser = peggy.Peggy(grammar)
		ast = parser.parse('b+b', 'Expr')
		self.assertTrue(ast['error'])
		self.assertEqual(ast['length'], 0)
