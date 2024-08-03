import argparse
import sys

from bits.bits import Bits


def check_region_ids(bits: Bits, map_name: str) -> bool:
    _map = bits.maps[map_name]
    print(f'Checking region ids in {map_name}...')

    seen_region_guids = set()
    num_dupe_region_guids = 0
    seen_mesh_ranges = set()
    num_dupe_mesh_ranges = 0
    seen_scid_ranges = set()
    num_dupe_scid_ranges = 0

    for region in _map.get_regions().values():
        guid = region.get_data().id
        if guid in seen_region_guids:
            print(f'Dupe region guid in {region.get_name()}: {guid}')
            num_dupe_region_guids += 1
        seen_region_guids.add(guid)

        mesh_range = region.get_data().mesh_range
        if mesh_range in seen_mesh_ranges:
            print(f'Dupe mesh range in {region.get_name()}: {mesh_range}')
            num_dupe_mesh_ranges += 1
        seen_mesh_ranges.add(mesh_range)

        scid_range = region.get_data().scid_range
        if scid_range in seen_scid_ranges:
            print(f'Dupe scid range in {region.get_name()}: {scid_range}')
            num_dupe_scid_ranges += 1
        seen_scid_ranges.add(scid_range)

    print(f'Checking region ids in {map_name}: {num_dupe_region_guids} dupe region guids, {num_dupe_mesh_ranges} dupe mesh ranges, {num_dupe_scid_ranges} dupe scid ranges')
    return num_dupe_region_guids == 0 and num_dupe_mesh_ranges == 0 and num_dupe_scid_ranges == 0


def init_arg_parser():
    parser = argparse.ArgumentParser(description='GasPy check_region_ids')
    parser.add_argument('map')
    parser.add_argument('--bits', default=None)
    return parser


def parse_args(argv):
    parser = init_arg_parser()
    return parser.parse_args(argv)


def main(argv) -> int:
    args = parse_args(argv)
    map_name = args.map
    bits_path = args.bits
    bits = Bits(bits_path)
    valid = check_region_ids(bits, map_name)
    return 0 if valid else -1


if __name__ == '__main__':
    exit(main(sys.argv[1:]))
