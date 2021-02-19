import argparse
import os
import sys

from bits import Bits
from gas import Gas, Section, Attribute
from gas_dir import GasDir


def new_map(name, screen_name):
    bits = Bits()
    assert name not in bits.maps
    map_dir = GasDir(os.path.join(bits.gas_dir.path, 'world', 'maps', name), {
        'main': Gas([
            Section('t:map,n:map', [
                Attribute('screen_name', screen_name)
            ])
        ])
    })
    map_dir.save()


def parse_args(argv):
    parser = argparse.ArgumentParser(description='GasPy MapGen')
    parser.add_argument('--new-map', action='store_true')
    parser.add_argument('--name')
    parser.add_argument('--screen-name')

    return parser.parse_args(argv)


def main(argv):
    args = parse_args(argv)
    if args.new_map:
        new_map(args.name, args.screen_name)
    else:
        print('dunno what 2 do')


if __name__ == '__main__':
    exit(main(sys.argv[1:]))
