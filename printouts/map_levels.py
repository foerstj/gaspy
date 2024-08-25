# Ordered regions -> how much XP, and what lvl the player will be at
import argparse
import sys

from bits.bits import Bits
from bits.maps.map import Map
from gas.gas_parser import GasParser
from printouts.common import load_regions_xp
from printouts.csv import write_csv


def write_map_levels_csv(m: Map):
    regions_xp = load_regions_xp(m)
    data = [['world level', 'region', 'xp', 'weight', 'xp', 'sum', 'level pre', 'level post']]
    for r in regions_xp:
        print(f'{r.name} {r.xp*r.weight}')
        data.append([r.world_level, r.name, r.xp, r.weight, r.xp*r.weight, r.xp_post, r.pre_level, r.post_level])
    write_csv(m.gas_dir.dir_name, data)


def map_levels(map_name: str, bits_path: str):
    bits = Bits(bits_path)
    m = bits.maps[map_name]
    GasParser.get_instance().print_warnings = False  # shush
    write_map_levels_csv(m)


def init_arg_parser():
    parser = argparse.ArgumentParser(description='GasPy map_levels')
    parser.add_argument('map')
    parser.add_argument('--bits', default=None)
    return parser


def parse_args(argv):
    parser = init_arg_parser()
    return parser.parse_args(argv)


def main(argv):
    args = parse_args(argv)
    map_levels(args.map, args.bits)


if __name__ == '__main__':
    main(sys.argv[1:])
