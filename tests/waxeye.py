import peggy
import peggy.grammars
from . import util


class TestWaxeye(util.PeggyTestCase):
	def test_idempotence(self):
		data = peggy.grammars.all['waxeye']['source']
		return self.idempotence(
		    'waxeye', data, peggy.grammars.all['waxeye']['tree']
		)
