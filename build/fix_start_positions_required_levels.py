""" Preprocessing script for building maps: Fix the required_level params in start_positions.gas """
import argparse
import sys

from bits.bits import Bits


def fix_start_positions_required_levels(bits: Bits, map_name: str):
    _map = bits.maps[map_name]

    start_positions_gas_file = _map.gas_dir.get_subdir('info').get_gas_file('start_positions')
    attr_fixed = False
    start_positions_gas = start_positions_gas_file.get_gas()
    for start_group_section in start_positions_gas.get_section('start_positions').get_sections():
        for world_level_section in start_group_section.get_section('world_levels').get_sections():
            required_level_attr = world_level_section.get_attr('required_level')
            if required_level_attr.datatype:
                print(required_level_attr)
                required_level_attr.datatype = None
                attr_fixed = True

    if attr_fixed:
        start_positions_gas_file.save()

    print('done')


def parse_args(argv):
    parser = argparse.ArgumentParser(description='GasPy fix_start_positions_required_levels')
    parser.add_argument('map_name')
    parser.add_argument('--bits', default='DSLOA')
    return parser.parse_args(argv)


def main(argv):
    args = parse_args(argv)
    map_name = args.map_name
    bits_path = args.bits
    bits = Bits(bits_path)
    fix_start_positions_required_levels(bits, map_name)


if __name__ == '__main__':
    main(sys.argv[1:])
