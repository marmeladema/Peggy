import difflib
import unittest
import tempfile
import json

import peggy
import peggy.grammars


class PeggyTestCase(unittest.TestCase):
	def assertUnifiedDiff(self, fromfile, tofile):
		with open(fromfile, 'rt') as a_fd, open(tofile, 'rt') as b_fd:
			a_lines = a_fd.readlines()
			b_lines = b_fd.readlines()
			self.assertGreater(len(a_lines), 0)
			self.assertGreater(len(b_lines), 0)
			diff = ''.join(
			    difflib.unified_diff(
			        a_lines, b_lines, fromfile = fromfile, tofile = tofile
			    )
			)
			if diff:
				self.fail('\n' + diff)

	def idempotence(self, grammar, data, ref):
		ast = peggy.grammars.parse(grammar, data)

		if ast['error'] is True:
			peggy.astprint(ast['nodes'][0], data)
			raise RuntimeError(
			    'Could not parse input grammar with {} format'.format(grammar)
			)
		elif ast['length'] < len(data):
			peggy.astprint(ast['nodes'][0], data)
			raise RuntimeError(
			    'Could only parse {} of {} bytes of input grammar with {} format'
			    .format(ast['length'], len(data), grammar)
			)

		parser = peggy.grammars.convert(grammar, data, ast)
		with tempfile.NamedTemporaryFile(
		) as src_fd, tempfile.NamedTemporaryFile() as dst_fd:
			src_fd.write(
			    json.dumps(ref, sort_keys = True, indent = 2).encode('utf-8')
			)
			src_fd.flush()
			dst_fd.write(
			    parser.json(sort_keys = True, indent = 2).encode('utf-8')
			)
			dst_fd.flush()
			self.assertUnifiedDiff(src_fd.name, dst_fd.name)
