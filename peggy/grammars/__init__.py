from json import load as json_load
import os

import peggy
from .json import grammar2json as json_grammar2json
from .pegjs import grammar2json as pegjs_grammar2json
from .waxeye import grammar2json as waxeye_grammar2json

cfd = os.path.dirname(__file__)

all = {
    'json': {
        'source': open(os.path.join(cfd, 'json.json')).read(),
        'tree': json_load(open(os.path.join(cfd, 'json.json'))),
        'rule': 'Json',
        'convert': json_grammar2json,
    },
    'pegjs': {
        'source': open(os.path.join(cfd, 'pegjs.pegjs')).read(),
        'tree': json_load(open(os.path.join(cfd, 'pegjs.json'))),
        'rule': 'Grammar',
        'convert': pegjs_grammar2json,
    },
    'waxeye': {
        'source': open(os.path.join(cfd, 'waxeye.peg')).read(),
        'tree': json_load(open(os.path.join(cfd, 'waxeye.json'))),
        'rule': 'Grammar',
        'convert': waxeye_grammar2json,
    },
}


def parse(grammar, data, debug = False):
	parser = peggy.Peggy(all[grammar]['tree'], debug = debug)
	ast = parser.parse(data, all[grammar]['rule'])
	return ast


def convert(grammar, data, ast):
	parser = peggy.Peggy(all[grammar]['convert'](ast['nodes'][0], data))
	parser.compute_lookahead()
	return parser
