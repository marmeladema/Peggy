import argparse
import json
import peggy
import pprint
import sys

parser = argparse.ArgumentParser(
    description = 'Parse some input according to a Parsing Expression Grammar.'
)
parser.add_argument('grammar', type = lambda g: json.load(open(g)))
parser.add_argument('rule')
parser.add_argument('input', type = open, default = sys.stdin, nargs = '?')
parser.add_argument('-d', '--debug', default = False, action = 'store_true')


def main(cmdline = None):
	args = parser.parse_args(cmdline or sys.argv[1:])

	data = args.input.read()

	pparser = peggy.Peggy(args.grammar, debug = args.debug)
	ast = pparser.parse(data, args.rule)
	if args.debug:
		pprint.pprint(ast)
	if ast['error'] is False:
		print('Took {} iteration'.format(pparser._count))
		if len(data) != ast['nodes'][0]['length']:
			print(len(data), '!=', ast['nodes'][0]['length'])
		peggy.astprint(ast['nodes'][0], data)
	else:
		pprint.pprint(ast)
		pprint.pprint(pparser._error)


if __name__ == '__main__':
	main()
