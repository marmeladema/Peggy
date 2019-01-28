import peggy
import peggy.grammars
from . import util


class TestPEGjs(util.PeggyTestCase):
	def test_idempotence(self):
		data = peggy.grammars.all['pegjs']['source']
		return self.idempotence(
		    'pegjs', data, peggy.grammars.all['pegjs']['tree']
		)
