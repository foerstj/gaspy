import argparse

import sys

from bits.bits import Bits


def elevator_nodes(bits_path: str):
    bits = Bits(bits_path)
    elevators_file = bits.gas_dir.get_subdir('world').get_subdir('global').get_gas_file('elevators')
    elevators_file.get_gas().print()


def init_arg_parser():
    parser = argparse.ArgumentParser(description='GasPy printout elevator nodes')
    parser.add_argument('--bits', default=None)
    return parser


def parse_args(argv):
    parser = init_arg_parser()
    return parser.parse_args(argv)


def main(argv):
    args = parse_args(argv)
    elevator_nodes(args.bits)


if __name__ == '__main__':
    main(sys.argv[1:])
