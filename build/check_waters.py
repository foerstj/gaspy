import argparse
import sys

from bits.bits import Bits
from bits.maps.region import Region


def check_waters_in_region(region: Region) -> int:
    num_wrong = 0
    terrain = region.get_terrain()
    for node in terrain.nodes:
        mesh_name_split = node.mesh_name.split('_')
        if mesh_name_split[-1] != 'water':
            continue
        is_wrong = False
        for near_door_id, (far_node, far_door_id) in node.doors.items():
            if near_door_id == far_door_id:
                is_wrong = True
                break
        if is_wrong:
            print(f'  Water node going in the wrong direction in {region.get_name()}: {node.guid}')
            num_wrong += 1
    return num_wrong


def check_waters(bits: Bits, map_name: str) -> bool:
    _map = bits.maps[map_name]
    num_wrong = 0
    print(f'Checking waters in {map_name}...')
    for region in _map.get_regions().values():
        num_wrong += check_waters_in_region(region)
    print(f'Checking waters in {map_name}: {num_wrong} going in the wrong direction')
    return num_wrong == 0


def init_arg_parser():
    parser = argparse.ArgumentParser(description='GasPy check_waters')
    parser.add_argument('map')
    parser.add_argument('--bits', default='DSLOA')
    return parser


def parse_args(argv):
    parser = init_arg_parser()
    return parser.parse_args(argv)


def main(argv) -> int:
    args = parse_args(argv)
    bits = Bits(args.bits)
    valid = check_waters(bits, args.map)
    return 0 if valid else -1


if __name__ == '__main__':
    exit(main(sys.argv[1:]))
