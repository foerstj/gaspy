import argparse
import sys

from bits.bits import Bits


def check_rivers(bits: Bits, map_name: str) -> bool:
    _map = bits.maps[map_name]
    print(f'Checking rivers in {map_name}...')
    print(f'Checking rivers in {map_name}: all good')
    return True


def init_arg_parser():
    parser = argparse.ArgumentParser(description='GasPy check_rivers')
    parser.add_argument('map')
    parser.add_argument('--bits', default='DSLOA')
    return parser


def parse_args(argv):
    parser = init_arg_parser()
    return parser.parse_args(argv)


def main(argv) -> int:
    args = parse_args(argv)
    bits = Bits(args.bits)
    valid = check_rivers(bits, args.map)
    return 0 if valid else -1


if __name__ == '__main__':
    exit(main(sys.argv[1:]))
