import argparse
import sys

from bits.bits import Bits
from bits.maps.map import Map
from world_levels import add_map_world_levels


def check_add_map_world_levels(m: Map):
    assert m is not None
    wls = {'regular', 'veteran', 'elite'}
    map_worlds = m.get_data().worlds
    assert map_worlds is not None
    assert set(map_worlds.keys()) == wls  # did you forget to add veteran and elite? did you forget renaming normal to regular?
    m.load_start_positions()
    for start_group in m.start_positions.start_groups.values():
        for wl in start_group.levels.keys():
            assert wl in wls


def add_world_levels(map_bits: Bits, map_name: str, template_bits: Bits):
    _map = map_bits.maps[map_name]
    check_add_map_world_levels(_map)  # sanity checks
    add_map_world_levels(_map, template_bits)


def init_arg_parser():
    parser = argparse.ArgumentParser(description='GasPy add world levels')
    parser.add_argument('map_name')
    parser.add_argument('--bits', default=None)
    parser.add_argument('--template-bits', default=None)
    return parser


def parse_args(argv):
    parser = init_arg_parser()
    return parser.parse_args(argv)


def main(argv):
    args = parse_args(argv)
    map_name = args.map_name
    map_bits_path = args.bits
    template_bits_path = args.template_bits
    map_bits = Bits(map_bits_path)
    template_bits = Bits(template_bits_path) if template_bits_path is not None else map_bits
    add_world_levels(map_bits, map_name, template_bits)


if __name__ == '__main__':
    main(sys.argv[1:])
