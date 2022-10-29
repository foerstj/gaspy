import argparse
import sys

from bits.bits import Bits
from bits.maps.region import Region


def unpath_region(region: Region):
    print(region.get_name())
    region.load_terrain()
    changes = 0
    for node in region.terrain.nodes:
        for size in '04x04', '08x04', '08x08':
            if node.mesh_name.startswith(f't_xxx_pth_{size}-'):
                changes += 1
                flr_size = size if size != '08x04' else '04x08'  # sigh
                node.mesh_name = f't_xxx_flr_{flr_size}-v0'
    if changes:
        print(f'Converted {changes} nodes')
        region.save()


def unpath(bits_path: str, map_name: str, region_name: str):
    bits = Bits(bits_path)
    m = bits.maps[map_name]

    if region_name is not None:
        unpath_region(m.get_region(region_name))
    else:
        for region in m.get_regions().values():
            unpath_region(region)


def init_arg_parser():
    parser = argparse.ArgumentParser(description='GasPy Unpath')
    parser.add_argument('map')
    parser.add_argument('region', nargs='?')
    parser.add_argument('--bits', default=None)
    return parser


def parse_args(argv):
    parser = init_arg_parser()
    return parser.parse_args(argv)


def main(argv):
    args = parse_args(argv)
    unpath(args.bits, args.map, args.region)


if __name__ == '__main__':
    main(sys.argv[1:])
