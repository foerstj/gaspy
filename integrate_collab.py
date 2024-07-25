import argparse
import os

import sys

from bits.bits import Bits
from bits.maps.map import Map
from gas.gas_writer import GasWriter


def integrate_collab(path: str, name: str):
    print(path)
    bits = Bits(path)
    m = bits.maps[name]
    m.print()

    parts_path = os.path.join(path, 'parts')
    assert os.path.isdir(parts_path)
    part_maps: list[Map] = list()
    for part in os.listdir(parts_path):
        part_path = os.path.join(parts_path, part)
        part_bits = Bits(part_path)
        for part_map_name, part_map in part_bits.maps.items():
            if not part_map_name.lower().startswith(name.lower()):
                continue
            part_map.print()
            part_maps.append(part_map)
    assert len(part_maps) > 0, 'No part maps found'

    # check hotpoints are matching, copy first
    print('integrate hotpoints')
    w = GasWriter()
    hotpoints_gases = [pm.gas_dir.get_subdir('info').get_gas_file('hotpoints').get_gas() for pm in part_maps]
    hotpoints_strs = {'\n'.join(w.format_gas(hs)) for hs in hotpoints_gases}
    assert len(hotpoints_strs) == 1, 'Hotpoints not matching'
    info_dir = m.gas_dir.get_or_create_subdir('info')
    info_dir.get_or_create_gas_file('hotpoints').gas = hotpoints_gases[0]
    info_dir.save()


def parse_args(argv: list[str]):
    parser = argparse.ArgumentParser(description='GasPy integrate collab')
    parser.add_argument('path')
    parser.add_argument('name')
    return parser.parse_args(argv)


def main(argv):
    args = parse_args(argv)
    integrate_collab(args.path, args.name)


if __name__ == '__main__':
    main(sys.argv[1:])
