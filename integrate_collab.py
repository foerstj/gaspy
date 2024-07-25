import argparse

import sys

from bits.bits import Bits


def integrate_collab(path: str):
    print(path)
    bits = Bits(path)
    maps = bits.maps
    print(f'Maps: {len(maps)}')
    for m in maps.values():
        m.print()


def parse_args(argv: list[str]):
    parser = argparse.ArgumentParser(description='GasPy integrate collab')
    parser.add_argument('path')
    return parser.parse_args(argv)


def main(argv):
    args = parse_args(argv)
    integrate_collab(args.path)


if __name__ == '__main__':
    main(sys.argv[1:])
