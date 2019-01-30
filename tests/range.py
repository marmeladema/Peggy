import peggy
from . import util


class TestRange(util.PeggyTestCase):
	def test_append(self):
		r = peggy.Range([6, 7])
		r.append(1)
		self.assertEqual(r, [1, 1, 6, 7])
		r.append(2)
		self.assertEqual(r, [1, 2, 6, 7])
		r.append(5)
		self.assertEqual(r, [1, 2, 5, 7])

	def test_extend(self):
		r = peggy.Range([6, 7])
		r.extend(peggy.Range([0, 1, 3, 5, 9, 0xFFFF]))
		self.assertEqual(r, [0, 1, 3, 7, 9, 0xFFFF])
		r.extend(peggy.Range([0, 0x10000]))
		self.assertEqual(r, [0, 0x10000])

	def test_add(self):
		r = peggy.Range([6, 7])
		self.assertEqual(r, [6, 7])
		r.add(0, 1)
		self.assertEqual(r, [0, 1, 6, 7])
		r.add(3, 4)
		self.assertEqual(r, [0, 1, 3, 4, 6, 7])
		r.add(2, 2)
		self.assertEqual(r, [0, 4, 6, 7])
		r.add(5, 5)
		self.assertEqual(r, [0, 7])
		r.add(9, 10)
		self.assertEqual(r, [0, 7, 9, 10])
		r.add(0, 0x10000)
		self.assertEqual(r, [0, 0x10000])

	def test_contains(self):
		r = peggy.Range()
		r.add(1, 3)
		r.add(5, 7)
		self.assertNotIn(0, r)
		self.assertIn(1, r)
		self.assertIn(2, r)
		self.assertIn(3, r)
		self.assertNotIn(4, r)
		self.assertIn(5, r)
		self.assertIn(6, r)
		self.assertIn(7, r)
		self.assertNotIn(8, r)
