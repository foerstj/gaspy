import argparse
import sys

from bits.bits import Bits
from region_import.check_dupe_node_ids import check_map


def check_dupe_node_ids(bits: Bits, map_name: str) -> bool:
    _map = bits.maps[map_name]
    print(f'Checking dupe node ids in {map_name}...')
    num_dupes = check_map(_map, False)
    print(f'Checking dupe node ids in {map_name}: {num_dupes} duplicate node ids')
    return num_dupes == 0


def init_arg_parser():
    parser = argparse.ArgumentParser(description='GasPy check_dupe_node_ids')
    parser.add_argument('map')
    parser.add_argument('--bits', default='DSLOA')
    return parser


def parse_args(argv):
    parser = init_arg_parser()
    return parser.parse_args(argv)


def main(argv) -> int:
    args = parse_args(argv)
    map_name = args.map
    bits_path = args.bits
    bits = Bits(bits_path)
    valid = check_dupe_node_ids(bits, map_name)
    return 0 if valid else -1


if __name__ == '__main__':
    exit(main(sys.argv[1:]))
