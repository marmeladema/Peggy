import json
import os

from . import waxeye

all = {
    'waxeye': {
        'tree':
        json.load(
            open(os.path.join(os.path.dirname(__file__), 'waxeye.json'))
        ),
        'rule':
        'Grammar',
        'transform':
        waxeye.grammar2json,
    },
}
