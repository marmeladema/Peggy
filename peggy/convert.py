import peggy
import peggy.grammars
import argparse
import json
import sys
import pprint

parser = argparse.ArgumentParser(description = 'Peggy grammar converter')
parser.add_argument(
    'input',
    type = str,
    choices = peggy.grammars.all.keys(),
    help = 'Grammar input format'
)
parser.add_argument('grammar', type = open, help = 'Grammar input file')
parser.add_argument(
    'output',
    type = lambda s: open(s, 'w+'),
    default = sys.stdout,
    nargs = '?'
)
parser.add_argument('-d', '--debug', action = 'store_true', default = False)


def main(cmdline = None):
	args = parser.parse_args(cmdline or sys.argv[1:])

	data = args.grammar.read()

	ast = peggy.grammars.parse(args.input, data, debug = args.debug)

	if ast['error'] is True:
		raise RuntimeError(
		    'Could not parse input grammar with {} format'.format(args.input)
		)
	elif ast['length'] < len(data):
		raise RuntimeError(
		    'Could only parse {} of {} bytes of input grammar with {} format'.
		    format(ast['length'], len(data), args.input)
		)
	peggy.astprint(ast['nodes'][0], data)

	pparser = peggy.grammars.convert(args.input, data, ast)
	args.output.write(pparser.json(indent = 2, sort_keys = True))


if __name__ == '__main__':
	main()
