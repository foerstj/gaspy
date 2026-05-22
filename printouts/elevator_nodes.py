import argparse

import sys

from bits.bits import Bits
from elevator_nodes import read_elevators_gas, evaluate_map


def elevator_nodes(map_names: list[str], asserts: list[str], bits_path: str):
    bits = Bits(bits_path)
    list_data = read_elevators_gas(bits)

    if map_names is not None:
        for map_name in map_names:
            evaluate_map(map_name, bits, list_data, asserts)


def init_arg_parser():
    parser = argparse.ArgumentParser(description='GasPy printout elevator-nodes')
    parser.add_argument('--eval-maps', nargs='+', help='evaluate these maps (extract ele guids and compare with lists)')
    parser.add_argument('--asserts', nargs='*', choices=['map-in-list', 'guids-in-list', 'no-unspecified-meshes'], default=list())
    parser.add_argument('--bits', default=None)
    return parser


def parse_args(argv):
    parser = init_arg_parser()
    return parser.parse_args(argv)


def main(argv):
    args = parse_args(argv)
    elevator_nodes(args.eval_maps, args.asserts, args.bits)


if __name__ == '__main__':
    main(sys.argv[1:])
