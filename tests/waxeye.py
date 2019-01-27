import os
import unittest
import peggy
import peggy.grammars
import tempfile
import difflib
import json


class TestWaxeye(unittest.TestCase):
	def assertUnifiedDiff(self, fromfile, tofile):
		with open(fromfile, 'rt') as a_fd, open(tofile, 'rt') as b_fd:
			diff = ''.join(
			    difflib.unified_diff(
			        a_fd.readlines(),
			        b_fd.readlines(),
			        fromfile = fromfile,
			        tofile = tofile
			    )
			)
			if diff:
				self.fail('\n' + diff)

	def test_idempotence(self):
		data = peggy.grammars.all['waxeye']['source']
		ast = peggy.grammars.parse('waxeye', data)

		if ast['error'] is True:
			peggy.astprint(ast['nodes'][0], data)
			raise RuntimeError(
			    'Could not parse input grammar with waxeye format'
			)
		elif ast['length'] < len(data):
			peggy.astprint(ast['nodes'][0], data)
			raise RuntimeError(
			    'Could only parse {} of {} bytes of input grammar with waxeye format'
			    .format(ast['length'], len(data))
			)

		parser = peggy.grammars.convert('waxeye', data, ast)
		with tempfile.NamedTemporaryFile(
		) as src_fd, tempfile.NamedTemporaryFile() as dst_fd:
			src_fd.write(
			    json.dumps(
			        peggy.grammars.all['waxeye']['tree'],
			        sort_keys = True,
			        indent = 2
			    ).encode('utf-8')
			)
			dst_fd.write(
			    parser.json(sort_keys = True, indent = 2).encode('utf-8')
			)
			self.assertUnifiedDiff(src_fd.name, dst_fd.name)
