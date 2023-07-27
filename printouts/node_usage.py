import argparse

import sys

from bits.bits import Bits
from gas.gas_parser import GasParser


def node_usage(bits: Bits):
    maps = bits.maps
    print('Maps: ' + str(len(maps)))
    for m in maps.values():
        m.print()


def init_arg_parser():
    parser = argparse.ArgumentParser(description='GasPy printouts node_usage')
    parser.add_argument('--bits', default=None)
    return parser


def parse_args(argv):
    parser = init_arg_parser()
    return parser.parse_args(argv)


def main(argv):
    args = parse_args(argv)
    GasParser.get_instance().print_warnings = False
    bits = Bits(args.bits)
    node_usage(bits)


if __name__ == '__main__':
    main(sys.argv[1:])
