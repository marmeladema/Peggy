import peggy
import peggy.grammars
from . import util


class TestJson(util.PeggyTestCase):
	def test_idempotence(self):
		data = peggy.grammars.all['json']['source']
		return self.idempotence(
		    'json', data, peggy.grammars.all['json']['tree']
		)
