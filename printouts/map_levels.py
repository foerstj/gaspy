# Ordered regions -> how much XP, and what lvl the player will be at
import argparse
import sys

from bits.bits import Bits
from bits.maps.map import Map
from gas.gas_parser import GasParser
from printouts.common import load_regions_xp
from printouts.csv import write_csv


def write_map_levels_csv(m: Map, start_level: int = 0):
    regions_xp = load_regions_xp(m, None, start_level)
    data = [['world level', 'region', 'xp', 'weight', 'xp', 'sum', 'level pre', 'level post']]
    total_xp = 0
    for r in regions_xp:
        print(f'{r.name}: {r.xp_weighted:g} XP -> level {r.post_level}')
        total_xp += r.xp_weighted
        data.append([r.world_level, r.name, r.xp, r.weight, r.xp_weighted, r.xp_post, r.pre_level, r.post_level])
    print(f'Total XP: {total_xp:g}')
    write_csv(m.gas_dir.dir_name, data)


def map_levels(map_name: str, start_level: int = 0, bits_path: str = None):
    bits = Bits(bits_path)
    m = bits.maps[map_name]
    GasParser.get_instance().print_warnings = False  # shush
    write_map_levels_csv(m, start_level)


def init_arg_parser():
    parser = argparse.ArgumentParser(description='GasPy map_levels')
    parser.add_argument('map')
    parser.add_argument('--start-level', type=int, default=0)
    parser.add_argument('--bits', default=None)
    return parser


def parse_args(argv):
    parser = init_arg_parser()
    return parser.parse_args(argv)


def main(argv):
    args = parse_args(argv)
    map_levels(args.map, args.start_level, args.bits)


if __name__ == '__main__':
    main(sys.argv[1:])
