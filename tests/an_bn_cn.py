import os
import json

import peggy
from . import util

peg_path = os.path.join(os.path.dirname(__file__), 'grammars', 'an_bn_cn.peg')
json_path = os.path.join(
    os.path.dirname(__file__), 'grammars', 'an_bn_cn.json'
)

with open(json_path) as json_fd:
	grammar = json.load(json_fd)


class TestAnBnCn(util.PeggyTestCase):
	def test_idempotence(self):
		with open(peg_path) as peg_fd, open(json_path) as json_fd:
			return self.idempotence('waxeye', peg_fd.read(), grammar)

	def test_simple_ok_1(self):
		parser = peggy.Peggy(grammar)
		ast = parser.parse('abc', 'S')
		self.assertFalse(ast['error'])
		self.assertEqual(ast['length'], 3)

	def test_simple_ok_2(self):
		parser = peggy.Peggy(grammar)
		ast = parser.parse('aabbcc', 'S')
		self.assertFalse(ast['error'])
		self.assertEqual(ast['length'], 6)

	def test_simple_ok_3(self):
		parser = peggy.Peggy(grammar)
		ast = parser.parse('aaabbbccc', 'S')
		self.assertFalse(ast['error'])
		self.assertEqual(ast['length'], 9)

	def test_simple_ko_1(self, ):
		parser = peggy.Peggy(grammar)
		ast = parser.parse('a', 'S')
		self.assertTrue(ast['error'])
		self.assertEqual(ast['length'], 0)

	def test_simple_ko_2(self, ):
		parser = peggy.Peggy(grammar)
		ast = parser.parse('b', 'S')
		self.assertTrue(ast['error'])
		self.assertEqual(ast['length'], 0)

	def test_simple_ko_3(self, ):
		parser = peggy.Peggy(grammar)
		ast = parser.parse('c', 'S')
		self.assertTrue(ast['error'])
		self.assertEqual(ast['length'], 0)

	def test_simple_ko_4(self, ):
		parser = peggy.Peggy(grammar)
		ast = parser.parse('aabc', 'S')
		self.assertTrue(ast['error'])
		self.assertEqual(ast['length'], 0)

	def test_simple_ko_5(self, ):
		parser = peggy.Peggy(grammar)
		ast = parser.parse('abbc', 'S')
		self.assertTrue(ast['error'])
		self.assertEqual(ast['length'], 0)

	def test_simple_ko_6(self, ):
		parser = peggy.Peggy(grammar)
		ast = parser.parse('abcc', 'S')
		self.assertTrue(ast['error'])
		self.assertEqual(ast['length'], 0)
