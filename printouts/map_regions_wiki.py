import argparse
import sys

from bits.bits import Bits
from gas.gas_parser import GasParser


def map_regions_wiki(map_name: str, bits_path: str = None):
    bits = Bits(bits_path)
    m = bits.maps[map_name]
    GasParser.get_instance().print_warnings = False  # shush
    m.print()


def init_arg_parser():
    parser = argparse.ArgumentParser(description='GasPy map_regions_wiki')
    parser.add_argument('map')
    parser.add_argument('--bits', default=None)
    return parser


def parse_args(argv):
    parser = init_arg_parser()
    return parser.parse_args(argv)


def main(argv):
    args = parse_args(argv)
    map_regions_wiki(args.map, args.bits)


if __name__ == '__main__':
    main(sys.argv[1:])
