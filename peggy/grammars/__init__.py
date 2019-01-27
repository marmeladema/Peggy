import json
import os

import peggy
from . import waxeye

all = {
    'waxeye': {
        'source':
        open(os.path.join(os.path.dirname(__file__), 'waxeye.peg')).read(),
        'tree':
        json.load(
            open(os.path.join(os.path.dirname(__file__), 'waxeye.json'))
        ),
        'rule':
        'Grammar',
        'convert':
        waxeye.grammar2json,
    },
}


def parse(grammar, data, debug = False):
	parser = peggy.Peggy(all[grammar]['tree'])
	ast = parser.parse(data, all[grammar]['rule'], debug = debug)
	return ast


def convert(grammar, data, ast):
	parser = peggy.Peggy(all[grammar]['convert'](ast['nodes'][0], data))
	return parser
